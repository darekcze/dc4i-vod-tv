#!/usr/bin/env python3
"""Offline regression checks for Homebrew and browser catalog."""
import hashlib,json,re
from pathlib import Path
from urllib.parse import unquote,urlparse
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/"dist"
packages=json.loads((DIST/"api/apps.json").read_text(encoding="utf8"))["packages"]
assert packages,"empty Homebrew repo"
count=len(packages)
for rel in ["index.html","api/apps.json","apps.json"]:
    s=json.loads((DIST/rel).read_text(encoding="utf8"))
    assert s["paging"]["count"]==count and s["paging"]["itemsTotal"]==count,rel
    assert s["packages"]==packages,rel
ids=set();dstore=0;first_party=0
verified=json.loads((ROOT/"data/dstore-verified.json").read_text(encoding="utf8"))["packages"]
dstore_ids={r["id"] for r in verified}
for pkg in packages:
    mid=pkg["id"];m=pkg["manifest"]
    assert mid and mid==m["id"] and mid not in ids,mid
    ids.add(mid)
    assert m["version"] and m["title"],mid
    assert re.fullmatch(r"[0-9a-f]{64}",m["ipkHash"]["sha256"]),mid
    assert m["ipkSize"]>0 and m["ipkUrl"].startswith("https://"),mid
    if mid in dstore_ids:
        dstore+=1
        assert "/packages/dstore/" in m["ipkUrl"],mid
        file=DIST/"packages/dstore"/unquote(urlparse(m["ipkUrl"]).path.split("/")[-1])
        assert file.exists(),(mid,file)
        assert hashlib.sha256(file.read_bytes()).hexdigest()==m["ipkHash"]["sha256"],mid
    else:
        first_party+=1
        assert m["ipkUrl"].startswith("https://lg.darc.dev/packages/"),mid
        file=DIST/"packages"/unquote(urlparse(m["ipkUrl"]).path.split("/")[-1])
        assert file.exists(),(mid,file)
        assert hashlib.sha256(file.read_bytes()).hexdigest()==m["ipkHash"]["sha256"],mid
assert dstore==len(verified),(dstore,len(verified))
browser=json.loads((DIST/"catalog/dstore.json").read_text(encoding="utf8"))
assert browser["total"]==len(browser["entries"])>=100
assert sum(r["verified"] for r in browser["entries"])>=dstore
for rel in ["browse/index.html","assets/catalog.css","assets/catalog.js","_worker.js","assets/app-fallback.png"]:
    assert (DIST/rel).exists() and (DIST/rel).stat().st_size>100,rel
assert b"\x89PNG"==(DIST/"assets/app-fallback.png").read_bytes()[:4]
html=(DIST/"browse/index.html").read_text(encoding="utf8")
assert "/assets/catalog.js" in html and "https://lg.darc.dev/" in html
worker=(DIST/"_worker.js").read_text(encoding="utf8")
assert "__ALLOWED_NAMES__" not in worker and "/source/ipk/" in worker and "text/html" in worker
print("PASS homebrew",count,"first_party",first_party,"dstore",dstore,"indexed",browser["total"])
