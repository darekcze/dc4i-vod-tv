"""Offline installer contracts. Never execute prepare_cli, HOME changes or TV calls."""
from pathlib import Path
import io, subprocess, tarfile, tempfile, unittest
SCRIPT=Path(__file__).with_name('install-vodtv.sh')
SOURCE=SCRIPT.read_text()
def function(name):
 start=SOURCE.index(name+'() {')
 end=SOURCE.index('\n}\n',start)+3
 return SOURCE[start:end]
class Contracts(unittest.TestCase):
 def test_package_identity(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)
   for identity,expected in [('com.dc4i.vodtv',0),('com.synthetic.fixture',25)]:
    data=f'Package: {identity}\nVersion: 1.2.20\n'.encode()
    with tarfile.open(p/'control.tar.gz','w:gz') as archive:
     member=tarfile.TarInfo('control');member.size=len(data);archive.addfile(member,io.BytesIO(data))
    package=p/'candidate.ipk'
    package.unlink(missing_ok=True)
    payload=(p/'control.tar.gz').read_bytes()
    header=f'{"control.tar.gz":<16}{0:<12}{0:<6}{0:<6}{"100644":<8}{len(payload):<10}`\n'.encode()
    package.write_bytes(b'!<arch>\n'+header+payload+(b'\n' if len(payload)%2 else b''))
    shell='set -o pipefail\nAPP_ID=com.dc4i.vodtv\nPACKAGE='+str(package)+'\nfail(){ exit "$1"; }\n'+function('verify_package_identity')+'\nverify_package_identity'
    result=subprocess.run(['bash','-c',shell],capture_output=True,text=True,timeout=5)
    self.assertEqual(result.returncode,expected,result.stderr)
 def test_dry_run_has_no_profile_or_tv_call(self):
  start=SOURCE.index('if ((DRY_RUN)); then\n verify_package_identity')
  block=SOURCE[start:SOURCE.index('\nfi',start)]
  self.assertIn('verify_package_identity',block)
  for forbidden in ['prepare_cli','export HOME','check_tv','run_bounded']:
   self.assertNotIn(forbidden,block)
 def test_launch_running_contract(self):
  a=SOURCE.index(' local_running=');b=SOURCE.index('\nelse\n',a);fragment=SOURCE[a:b]
  for value,query_exit,expected in [('com.dc4i.vodtv',0,0),('other.app',0,23),('',1,23)]:
   shell='APP_ID=com.dc4i.vodtv\nNODE=mock\nCLI=mock\nDEVICE=mock\nfail(){ exit "$1"; }\nrun_bounded(){ printf "%s" "'+value+'"; return '+str(query_exit)+'; }\n'+fragment
   result=subprocess.run(['bash','-c',shell],capture_output=True,text=True,timeout=5)
   self.assertEqual(result.returncode,expected,result.stderr)
if __name__=='__main__':unittest.main()
