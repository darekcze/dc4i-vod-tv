#!/usr/bin/env python3
"""Build dual-mode webOS catalogue. The root remains Homebrew JSON."""
from pathlib import Path
from urllib.parse import quote
import hashlib, json, shutil, struct, zlib

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/"dist"
BASE="https://lg.darc.dev"
DATA=ROOT/"data"
WEB=ROOT/"web"

def dump(o):return json.dumps(o,ensure_ascii=False,indent=2)+"\n"
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(dump(obj),encoding="utf-8")
def make_fallback(path):
    # Standalone opaque PNG, no third-party app logo or branding implied.
    n=128; raw=bytearray()
    for y in range(n):
        raw.append(0)
        for x in range(n):
            p=(34<=x<94 and 29<=y<87 and (x in (34,35,92,93) or y in (29,30,85,86)))
            foot=(51<=x<77 and 90<=y<94)
            gl=(38<=x<90 and 34<=y<83)
            r,g,b=((215,237,255) if (p or foot) else ((42,88,176) if gl else (9,23,53)))
            raw.extend((r,g,b,255))
    def block(tag,d):return struct.pack(">I",len(d))+tag+d+struct.pack(">I",zlib.crc32(tag+d)&0xffffffff)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n"+block(b"IHDR",struct.pack(">IIBBBBB",n,n,8,6,0,0,0))+block(b"IDAT",zlib.compress(raw,9))+block(b"IEND",b""))
def main():
    source=json.loads((DATA/"dstore-verified.json").read_text(encoding="utf8"))
    indexed=json.loads((DATA/"dstore-index.json").read_text(encoding="utf8"))
    verified=source["packages"]
    base=json.loads((ROOT/"api/apps.json").read_text(encoding="utf8"))
    imported_ids={x["id"] for x in verified}
    # Never overwrite or mutate locally maintained first-party packages.
    primary=[p for p in base.get("packages",[]) if p.get("id") not in imported_ids and not
             str(p.get("manifest",{}).get("ipkUrl","")).startswith((BASE+"/source/ipk/",BASE+"/packages/dstore/"))]
    entries=list(primary)
    for row in verified:
        encoded=quote(row["filename"],safe="")
        url=BASE+"/packages/dstore/"+encoded
        src=ROOT/"private/dstore-packages"/row["filename"]
        dst=DIST/"packages/dstore"/row["filename"]
        if not src.exists() or hashlib.sha256(src.read_bytes()).hexdigest()!=row["sha256"]:
            raise RuntimeError("DStore package missing or modified: "+row["filename"]+". Run scripts/mirror_dstore.py first.")
        dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():
            try: dst.hardlink_to(src)
            except OSError: shutil.copy2(src,dst)
        ico=BASE+"/"+(row["iconPath"] if row.get("iconPath") else "assets/app-fallback.png")
        description="Pakiet z niezależnego katalogu DStore, bez audytu bezpieczeństwa DC4I. Sprawdź pochodzenie przed instalacją."
        if row["rootRequired"]:description+=" Wymaga roota."
        manifest=dict(id=row["id"],version=row["version"],type="web",title=row["title"],
            appDescription=description,iconUri=ico,sourceUrl=source["source"],
            rootRequired=bool(row["rootRequired"]),ipkUrl=url,ipkHash={"sha256":row["sha256"]},
            ipkSize=row["size"])
        entries.append(dict(id=row["id"],title=row["title"],iconUri=ico,manifest=manifest,
            shortDescription="DStore | "+row["category"]+" | zewnętrzna aplikacja",
            fullDescriptionUrl=BASE+"/browse/?q="+quote(row["title"])))
    seen=set();unique=[]
    for p in entries:
        if p["id"] in seen:continue
        seen.add(p["id"]);unique.append(p)
    catalog={"paging":{"page":1,"count":len(unique),"maxPage":1,"itemsTotal":len(unique)},"packages":unique}
    for file in [ROOT/"index.html",ROOT/"apps.json",ROOT/"api/apps.json",
                 DIST/"index.html",DIST/"apps.json",DIST/"api/apps.json"]:
        write(file,catalog)
    for file in [ROOT/"packages.json",DIST/"packages.json"]:
        write(file,unique)
    matched={row["filename"]:row for row in verified}
    browser_rows=[]
    for row in indexed["entries"]:
        cur=matched.get(row["filename"])
        name=(cur["title"] if cur else row["filename"].removesuffix(".ipk").replace("_"," "))
        browser_rows.append(dict(filename=row["filename"],title=name,sourceUrl=row["sourceUrl"],
          description=row["description"],date=row["date"],declaredSize=row["declaredSize"],
          verified=bool(cur),category=cur["category"] if cur else "External",
          id=cur["id"] if cur else None,iconUri=BASE+"/"+(cur["iconPath"] or "assets/app-fallback.png") if cur else BASE+"/assets/app-fallback.png"))
    write(DIST/"catalog/dstore.json",dict(source=indexed["source"],retrievedAt=indexed["retrievedAt"],
       entries=browser_rows,verified=len(verified),total=len(browser_rows)))
    for x,y in [(WEB/"index.html",DIST/"browse/index.html"),(WEB/"catalog.css",DIST/"assets/catalog.css"),(WEB/"catalog.js",DIST/"assets/catalog.js")]:
        if not x.exists():raise RuntimeError("Missing web asset "+str(x))
        y.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(x,y)
    make_fallback(DIST/"assets/app-fallback.png")
    brand=ROOT/"assets/brand/DC4I_Official_Circuit_Profile_2026-10-24.png"
    if brand.exists():shutil.copy2(brand,DIST/"assets/dc4i-logo.png")
    worker=(WEB/"worker.template.js").read_text(encoding="utf8").replace("__ALLOWED_NAMES__",json.dumps(sorted({r["filename"] for r in verified}),ensure_ascii=False))
    (DIST/"_worker.js").write_text(worker,encoding="utf8")
    (DIST/"_headers").write_text("/\n  Content-Type: application/json; charset=utf-8\n/index.html\n  Content-Type: application/json; charset=utf-8\n/apps.json\n  Content-Type: application/json; charset=utf-8\n/api/apps.json\n  Content-Type: application/json; charset=utf-8\n/catalog/dstore.json\n  Content-Type: application/json; charset=utf-8\n",encoding="utf8")
    print("CATALOG_BUILT",len(unique),"HOME_BREW",len(primary),"FIRST_PARTY",len(verified),"DSTORE_VERIFIED",len(browser_rows),"DSTORE_INDEX")
if __name__=="__main__":main()
