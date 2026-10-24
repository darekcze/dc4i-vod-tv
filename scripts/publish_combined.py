#!/usr/bin/env python3
"""Canonical publish preparation, preserving both first-party VOD and DStore apps."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]

def run(script:Path):
    subprocess.run([sys.executable,str(script)],cwd=ROOT,check=True)

def main():
    publisher=ROOT/"publish_vod_tv.py"
    if not publisher.exists():
        publisher=ROOT/"publish_dc4i.py"
    if not publisher.exists():
        raise SystemExit("Missing first-party app publisher")
    run(publisher)
    if (ROOT/"data/dstore-verified.json").exists():
        run(ROOT/"scripts/mirror_dstore.py")
        run(ROOT/"scripts/build_catalog.py")
        run(ROOT/"scripts/test_catalog.py")
    print("READY_TO_DEPLOY: npx --no-install wrangler pages deploy dist --project-name lg-webos-repo --branch main")
if __name__=="__main__":main()
