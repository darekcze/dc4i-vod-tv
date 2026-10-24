#!/usr/bin/env python3
"""Snapshot and inspect DStore IPKs without executing them.
Only a curated allowlist becomes Homebrew-installable. All indexed files remain
visible as unverified source links in the browser catalogue.
"""
from __future__ import annotations
import concurrent.futures
from datetime import date
from io import BytesIO
import hashlib, json, re, tarfile, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE="http://dstore.net.swtest.ru/ipk/"
INDEX=ROOT/"private/dstore-index-20261024.txt"
DATA=ROOT/"data"
ICONS=ROOT/"dist/icons/dstore"
LIMIT=16*1024*1024
ALLOW=[
"my.tuner.radio.ipk",
"jellyfin.ipk",
"org.jellyfin.webos_1.1.0_all.ipk",
"wikipedia.app_0.0.4_all.ipk",
"siptv_3.0.3_all.ipk",
"com.ottplay.foss_0.0.4_all.ipk",
"com.ottplay-foss_lg_webos_v0.1.6.ipk",
"org.webosbrew.streamkatze_0.1.1_all.ipk",
"webos.screen.off_1.0.5_all.ipk",
"tv.ottplayer.widget_0.0.3_all.ipk",
"com.openspeedtest_0.0.1_all.ipk",
"org.hola.cdndemo_1.25.530_all.ipk",
"couchplay_0.0.2_all.ipk",
"opera.gametreetv_0.0.2_all.ipk",
"games.tv_0.0.2_all.ipk",
"smartgames.tv_0.0.1_all.ipk",
"smartgames.tv2_0.0.2_all.ipk",
"justdance.ipk",
"slither.ipk",
"tiktok.djvreditel.v1_1.1.0_all.ipk",
"org.chocolate-doom.demo_0.0.3_arm.ipk",
"com.github.k4zmu2a.space-cadet-pinball_0.0.3_arm.ipk",
"com.limelight.webos_1.6.2_arm.ipk",
"com.crunchyroll.webos_1.9.3_all.ipk",
"org.webosbrew.custom-screensaver_1.0.1_all.ipk",
"org.webosbrew.piccap_0.4.3_all.ipk",
"org.webosbrew.safeupdate_0.1.0_all.ipk",
"com.pirate.refresh_1.0.4_all.ipk",
"moe.exkc.accessusb_0.0.3_all.ipk",
"org.mariotaku.ihsplay_0.2.8_arm.ipk",
"com.willinux.tvh.app_0.8.3_all.ipk",
"webos.manager.input_5.11.22_all.ipk",
"webos.energy.saving_3.0.1.ipk",
"com.ssiptv.app_1.0.612_all.ipk",
]
ROOT_IDS={"org.webosbrew.piccap","org.webosbrew.safeupdate","org.webosbrew.inputhook","org.webosbrew.hyperion.ng.loader",
"org.webosbrew.hyperhdr.loader","org.webosbrew.vncserver","org.webosbrew.custom-screensaver"}
TITLES={
"my.tuner.radio.ipk":"myTuner Radio","jellyfin.ipk":"Jellyfin (legacy)","org.jellyfin.webos_1.1.0_all.ipk":"Jellyfin",
"siptv_3.0.3_all.ipk":"Smart IPTV","com.ottplay.foss_0.0.4_all.ipk":"OTT Play FOSS",
"com.ottplay-foss_lg_webos_v0.1.6.ipk":"OTT Play FOSS",
"org.webosbrew.streamkatze_0.1.1_all.ipk":"Streamkatze",
"webos.screen.off_1.0.5_all.ipk":"Screen Off",
"tv.ottplayer.widget_0.0.3_all.ipk":"OTTPlayer",
"com.openspeedtest_0.0.1_all.ipk":"OpenSpeedTest",
"couchplay_0.0.2_all.ipk":"CouchPlay",
"opera.gametreetv_0.0.2_all.ipk":"GameTree TV",
"tiktok.djvreditel.v1_1.1.0_all.ipk":"TikTok",
"org.chocolate-doom.demo_0.0.3_arm.ipk":"Chocolate Doom",
"com.github.k4zmu2a.space-cadet-pinball_0.0.3_arm.ipk":"3D Pinball Space Cadet",
"com.limelight.webos_1.6.2_arm.ipk":"Moonlight",
"com.crunchyroll.webos_1.9.3_all.ipk":"Crunchyroll (community)",
"org.webosbrew.custom-screensaver_1.0.1_all.ipk":"Custom Screensaver",
"org.webosbrew.piccap_0.4.3_all.ipk":"PicCap",
"org.webosbrew.safeupdate_0.1.0_all.ipk":"Homebrew Safe Update",
"com.pirate.refresh_1.0.4_all.ipk":"Developer Mode Refresh",
"moe.exkc.accessusb_0.0.3_all.ipk":"AccessUSB Emulator",
"org.mariotaku.ihsplay_0.2.8_arm.ipk":"IHSplay",
"com.willinux.tvh.app_0.8.3_all.ipk":"TVHeadend Client",
"webos.manager.input_5.11.22_all.ipk":"Input Manager",
"webos.energy.saving_3.0.1.ipk":"Energy Saving",
"com.ssiptv.app_1.0.612_all.ipk":"SS IPTV",
"org.hola.cdndemo_1.25.530_all.ipk":"HolaCDN Demo",
}
CATEGORIES={
"my.tuner.radio.ipk":"Music","jellyfin.ipk":"Video","org.jellyfin.webos_1.1.0_all.ipk":"Video","wikipedia.app_0.0.4_all.ipk":"Education",
"siptv_3.0.3_all.ipk":"IPTV","com.ottplay.foss_0.0.4_all.ipk":"IPTV","com.ottplay-foss_lg_webos_v0.1.6.ipk":"IPTV",
"org.webosbrew.streamkatze_0.1.1_all.ipk":"Video","webos.screen.off_1.0.5_all.ipk":"Utilities","tv.ottplayer.widget_0.0.3_all.ipk":"IPTV","com.openspeedtest_0.0.1_all.ipk":"Utilities",
"org.hola.cdndemo_1.25.530_all.ipk":"Games","couchplay_0.0.2_all.ipk":"Games","opera.gametreetv_0.0.2_all.ipk":"Games",
"games.tv_0.0.2_all.ipk":"Games","smartgames.tv_0.0.1_all.ipk":"Games","smartgames.tv2_0.0.2_all.ipk":"Games","justdance.ipk":"Games","slither.ipk":"Games",
"tiktok.djvreditel.v1_1.1.0_all.ipk":"Video","org.chocolate-doom.demo_0.0.3_arm.ipk":"Games","com.github.k4zmu2a.space-cadet-pinball_0.0.3_arm.ipk":"Games",
"com.limelight.webos_1.6.2_arm.ipk":"Games","com.crunchyroll.webos_1.9.3_all.ipk":"Video","org.webosbrew.custom-screensaver_1.0.1_all.ipk":"Personalization",
"org.webosbrew.piccap_0.4.3_all.ipk":"Personalization","org.webosbrew.safeupdate_0.1.0_all.ipk":"Utilities","com.pirate.refresh_1.0.4_all.ipk":"Utilities",
"moe.exkc.accessusb_0.0.3_all.ipk":"Utilities","org.mariotaku.ihsplay_0.2.8_arm.ipk":"Games","com.willinux.tvh.app_0.8.3_all.ipk":"IPTV",
"webos.manager.input_5.11.22_all.ipk":"Utilities","webos.energy.saving_3.0.1.ipk":"Utilities","com.ssiptv.app_1.0.612_all.ipk":"IPTV",
}
def parse_listing():
    # Fresh checkouts do not include the gitignored DStore index.
    if not INDEX.exists():
        INDEX.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(
            urllib.request.Request(SOURCE, headers={"User-Agent":"DC4I-webOS-indexer/1.0"}), timeout=20
        ) as response:
            listing=response.read(256*1024+1)
        if len(listing)>256*1024: raise ValueError("DStore listing exceeds 256 KiB")
        INDEX.write_bytes(listing)
    lines=INDEX.read_text(encoding="utf-8").splitlines()
    ix=next(i for i,l in enumerate(lines) if "Имя пакета" in l)+2
    results=[]
    for line in lines[ix:]:
        if line.count("-")>30: break
        cells=[c.strip() for c in line.split("|")]
        if len(cells)<4: continue
        filename=cells[2].strip()
        if not filename.lower().endswith(".ipk"): continue
        if "/" in filename or "\\" in filename or len(filename)>180: continue
        results.append(dict(filename=filename, date=cells[0], declaredSize=cells[1],description=" ".join(cells[3:]).strip(),
                            sourceUrl=SOURCE+urllib.parse.quote(filename), verified=False))
    return results

def ar_members(data):
    if data[:8]!=b"!<arch>\n": raise ValueError("not a Debian ar/IPK archive")
    i=8; out={}
    while i+60<=len(data):
        h=data[i:i+60]
        if h[58:60]!=b"\x60\n":raise ValueError("invalid ar header")
        name=h[:16].decode("utf-8","replace").strip().strip("/")
        size=int(h[48:58].strip())
        chunk=data[i+60:i+60+size]
        if len(chunk)!=size: raise ValueError("truncated ar member")
        if name.startswith(("control.tar","data.tar")):out[name.split(".tar")[0]]=chunk
        i+=60+size+(size%2)
    return out
def extract_package(data):
    chunks=ar_members(data)
    control={}
    if "control" in chunks:
        with tarfile.open(fileobj=BytesIO(chunks["control"]),mode="r:*") as tf:
            for m in tf:
                if m.name.lstrip("./")=="control" and m.isfile() and m.size<100000:
                    raw=tf.extractfile(m).read().decode("utf-8","replace")
                    for line in raw.splitlines():
                        if ": " in line:
                            k,v=line.split(": ",1); control[k]=v
                    break
    info={}; icon=None
    if "data" in chunks:
        with tarfile.open(fileobj=BytesIO(chunks["data"]),mode="r:*") as tf:
            paths=[m for m in tf if m.isfile() and m.size<3000000]
            infos=[m for m in paths if m.name.endswith("/appinfo.json") or m.name=="appinfo.json"]
            for member in infos[:6]:
                try:
                    tmp=json.load(tf.extractfile(member))
                    if isinstance(tmp,dict) and tmp.get("id"):
                        info=tmp; app_dir=member.name.rsplit("/",1)[0]
                        wanted=str(tmp.get("icon","icon.png"))
                        choices=[m for m in paths if (m.name==app_dir+"/"+wanted or m.name==app_dir+"/icon.png") and m.size<800000 and m.name.lower().endswith(".png")]
                        if choices:
                            raw=tf.extractfile(choices[0]).read()
                            if raw.startswith(b"\x89PNG\r\n\x1a\n"):icon=raw
                        break
                except Exception: pass
    return control,info,icon

def inspect(row):
    filename=row["filename"]
    try:
        with urllib.request.urlopen(urllib.request.Request(row["sourceUrl"],headers={"User-Agent":"DC4I-repo-metadata-indexer/1.0"}),timeout=18) as response:
            advertised=int(response.headers.get("Content-Length","0"))
            if advertised>LIMIT:raise ValueError("size exceeds 16 MiB import limit")
            data=response.read(LIMIT+1)
        if len(data)>LIMIT:raise ValueError("package exceeds 16 MiB limit")
        ctl,info,icon=extract_package(data)
        package_id=str(info.get("id") or ctl.get("Package") or "").strip()
        version=str(info.get("version") or ctl.get("Version") or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,120}",package_id):raise ValueError("no trustworthy app identifier")
        if not re.fullmatch(r"[0-9a-zA-Z][0-9a-zA-Z._+-]{0,45}",version):raise ValueError("missing or invalid version")
        name=(TITLES.get(filename) or str(info.get("title") or package_id))
        if not name or len(name)>100: name=package_id
        icon_path=None
        if icon:
            icon_path="icons/dstore/"+hashlib.sha256(filename.encode()).hexdigest()[:16]+".png"
            (ROOT/"dist"/icon_path).parent.mkdir(parents=True,exist_ok=True)
            (ROOT/"dist"/icon_path).write_bytes(icon)
        return dict(filename=filename,id=package_id,version=version,title=name,category=CATEGORIES.get(filename,"Other"),
                    description=row["description"],size=len(data),sha256=hashlib.sha256(data).hexdigest(),
                    url=row["sourceUrl"],sourceDate=row["date"],iconPath=icon_path,
                    rootRequired=package_id in ROOT_IDS or "нужен root" in row["description"].lower(),
                    architecture=ctl.get("Architecture",""),verified=True)
    except Exception as exc:
        return dict(filename=filename,verified=False,error=str(exc)[:180])

def main():
    DATA.mkdir(parents=True,exist_ok=True)
    ICONS.mkdir(parents=True,exist_ok=True)
    rows=parse_listing()
    (DATA/"dstore-index.json").write_text(json.dumps({"source":SOURCE,"retrievedAt":date.today().isoformat(),"entries":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    selected={r["filename"]:r for r in rows if r["filename"] in ALLOW}
    print("DSTORE_LISTING",len(rows),"CURATED_FOR_CHECK",len(selected),flush=True)
    verified=[]; errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        tasks={pool.submit(inspect,row):key for key,row in selected.items()}
        for task in concurrent.futures.as_completed(tasks):
            r=task.result()
            if r["verified"]:
                verified.append(r);print("VERIFIED",r["id"],r["version"],r["size"],flush=True)
            else:
                errors.append(r);print("UNAVAILABLE",r["filename"],r["error"],flush=True)
    # One app id -> one entry; prioritize newer package over legacy duplicates.
    ranked={}
    for r in verified:
        old=ranked.get(r["id"])
        if old is None or (r["sourceDate"],r["version"])>(old["sourceDate"],old["version"]):ranked[r["id"]]=r
    result=sorted(ranked.values(),key=lambda r:(r["category"],r["title"]))
    (DATA/"dstore-verified.json").write_text(json.dumps({"source":SOURCE,"checkedAt":date.today().isoformat(),"packages":result,"errors":errors},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("DSTORE_DONE","indexed",len(rows),"verified",len(result),"errors",len(errors),"dup_removed",len(verified)-len(result),flush=True)
if __name__=="__main__":main()
