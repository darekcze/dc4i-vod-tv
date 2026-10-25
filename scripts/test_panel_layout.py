#!/usr/bin/env python3
"""Chromium geometry regression test for the 1920x1080 LG quick drawer."""
from pathlib import Path
import json,re,subprocess,tempfile
R=Path(__file__).resolve().parents[1]
chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
with tempfile.TemporaryDirectory(prefix="dc4i-panel-test-",dir=R/"private") as profile:
 command=[chrome,"--headless=new","--disable-gpu","--no-first-run","--disable-extensions","--disable-background-networking",
          "--user-data-dir="+profile,"--window-size=1920,1080","--force-device-scale-factor=1","--virtual-time-budget=1200",
          "--dump-dom",(R/"build/dc4i-vodtv/preview-quick-panel.html").as_uri()]
 result=subprocess.run(command,capture_output=True,text=True,timeout=35)
assert result.returncode==0,result.stderr[-800:]
match=re.search(r'<pre id="metrics"[^>]*>(.*?)</pre>',result.stdout,re.S)
assert match,"Chrome did not expose layout metrics"
metrics=json.loads(match.group(1))
print("PANEL_LAYOUT",metrics)
assert metrics["pwidth"]>=890
assert not metrics["scrollNeeded"],"All panel text must fit at 1920x1080, scroll required"
assert metrics["items"][".dc4i-dedication"]["bottom"] <= (metrics["items"][".qhead"]["top"] + metrics["pheight"]),"Dedication clipped"
print("PANEL_LAYOUT_PASS")
