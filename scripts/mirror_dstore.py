#!/usr/bin/env python3
"""Mirror checksum-pinned DStore packages on AI-Hot, not on the system disk."""
import concurrent.futures,hashlib,os,shutil,tempfile,urllib.request,urllib.parse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=json.loads((ROOT/"data/dstore-verified.json").read_text(encoding="utf8"))
ROWS=SOURCE["packages"]
CACHE=ROOT/"private/dstore-packages"
DIST=ROOT/"dist/packages/dstore"
CACHE.mkdir(parents=True,exist_ok=True);DIST.mkdir(parents=True,exist_ok=True)
ORIGINS=["http://dstore.net.swtest.ru/ipk/","http://dstore4.ydns.eu/ipk/"]
def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def mirror(row):
    name=row["filename"]
    if name.startswith(".") or "/" in name or "\\" in name:raise ValueError("Invalid filename "+name)
    target=CACHE/name
    if target.exists() and target.stat().st_size==row["size"] and sha(target)==row["sha256"]:
        return name,"CACHED"
    errors=[]
    for source in ORIGINS:
        temp=None
        try:
            with tempfile.NamedTemporaryFile(prefix="dstore-",suffix=".tmp",dir=CACHE,delete=False) as fout:
                temp=Path(fout.name);h=hashlib.sha256();size=0
                with urllib.request.urlopen(urllib.request.Request(source+urllib.parse.quote(name),headers={"User-Agent":"DC4I-WebOS-PackageMirror/1"}),timeout=25) as fin:
                    while True:
                        chunk=fin.read(256*1024)
                        if not chunk:break
                        size+=len(chunk)
                        if size>row["size"]+1024:raise ValueError("Upstream package size exceeded signed snapshot")
                        fout.write(chunk);h.update(chunk)
            if size!=row["size"] or h.hexdigest()!=row["sha256"]:
                raise ValueError("Upstream bytes changed from pinned SHA-256")
            os.replace(temp,target)
            return name,"MIRRORED"
        except Exception as ex:
            errors.append(str(ex))
            if temp and temp.exists():temp.unlink()
    raise RuntimeError(name+": "+" | ".join(errors))
def main():
    errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(mirror,r) for r in ROWS]
        for f in concurrent.futures.as_completed(futures):
            try:
                name,status=f.result();print(status,name,flush=True)
            except Exception as e:
                errors.append(str(e));print("FAILED",e,flush=True)
    if errors:raise RuntimeError("Cannot mirror "+str(len(errors))+" signed DStore packages.")
    for r in ROWS:
        name=r["filename"];src=CACHE/name;dst=DIST/name
        if dst.exists():
            if dst.stat().st_size==r["size"] and sha(dst)==r["sha256"]:continue
            dst.unlink()
        try:os.link(src,dst)
        except OSError:shutil.copy2(src,dst)
    print("MIRROR_OK",len(ROWS),"packages",sum(r["size"] for r in ROWS),"bytes",flush=True)
if __name__=="__main__":
    main()
