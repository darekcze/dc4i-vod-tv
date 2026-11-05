import unittest,tempfile,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from release_contract import candidate, safe_error
class ReleaseTests(unittest.TestCase):
 def test_metadata_and_version_guard(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'appinfo.json').write_text(json.dumps({'id':'com.dc4i.vodtv','version':'1.2.20'}))
   self.assertEqual(candidate(p)[1],'1.2.20');self.assertEqual(candidate(p,'1.2.20')[1],'1.2.20')
   (p/'appinfo.json').write_text(json.dumps({'id':'com.dc4i.vodtv','version':'1.2.19'}));self.assertEqual(candidate(p)[1],'1.2.19');(p/'appinfo.json').write_text(json.dumps({'id':'com.dc4i.vodtv','version':'1.2.20'}))
   for v in ['1.2.21','../bad','1.2.20?key=x']:
    with self.assertRaises(ValueError):candidate(p,v)
   (p/'appinfo.json').write_text(json.dumps({'id':'com.dc4i.vodtv.offlinefixture','version':'1.2.20'}))
   with self.assertRaises(ValueError):candidate(p)
 def test_no_error_secret_disclosure(self):
  for message in ['https://x.invalid?api_key=SENTINEL&token=SENTINEL','Authorization: Bearer SENTINEL','Cookie: session=SENTINEL','password=SENTINEL','https://user:SENTINEL@x.invalid']:
   self.assertNotIn('SENTINEL',safe_error(RuntimeError(message)))
 def test_isolated_catalogue(self):
  from PIL import Image
  repo=Path(__file__).resolve().parents[1]
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)/'source';out=Path(t)/'output';(r/'build/dc4i-vodtv').mkdir(parents=True);(r/'private').mkdir();(r/'api').mkdir();(r/'assets/brand').mkdir(parents=True)
   (r/'build/dc4i-vodtv/appinfo.json').write_text(json.dumps({'id':'com.dc4i.vodtv','version':'1.2.20'}))
   (r/'private/com.dc4i.vodtv_1.2.20_all.ipk').write_bytes(b'SYNTHETIC CATALOGUE TEST ONLY NOT AN IPK')
   Image.new('RGB',(80,80)).save(r/'assets/brand/DC4I_VOD_TV_Neon_Approved_2026-10-24.png')
   (r/'packages/dstore').mkdir(parents=True);(r/'icons/dstore').mkdir(parents=True);(r/'browse').mkdir();
   public={'packages/dstore/other.ipk':b'UNRELATED PACKAGE','icons/dstore/other.png':b'UNRELATED ICON','browse/index.html':b'<html>browse</html>','browse/style.css':b'body{}','packages/com.dc4i.vodtv_1.2.18_all.ipk':b'OLD PUBLIC PACKAGE PRESERVED'}
   for name,value in public.items():(r/name).write_bytes(value)
   others=[{'id':'other.'+str(i),'manifest':{'version':'1'}} for i in range(32)];feed={'packages':[{'id':'com.dc4i.vodtv'}]+others};others[0].update({'iconUri':'https://lg.darc.dev/icons/dstore/other.png','fullDescriptionUrl':'https://lg.darc.dev/browse/'});others[0]['manifest']['ipkUrl']='https://lg.darc.dev/packages/dstore/other.ipk';original=json.dumps(feed);(r/'api/apps.json').write_text(original)
   p=subprocess.run([sys.executable,str(repo/'publish_vod_tv.py'),'--root',str(r),'--output-root',str(out)],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stderr);result=json.loads((out/'api/apps.json').read_text());self.assertEqual(result['packages'][1:],others);self.assertEqual(result['packages'][0]['manifest']['version'],'1.2.20');self.assertEqual((r/'api/apps.json').read_text(),original)
   for name,value in public.items():self.assertEqual((out/'dist'/name).read_bytes(),value);self.assertEqual((r/name).read_bytes(),value)
   (r/'packages/dstore/other.ipk').unlink();missing=Path(t)/'missing';rejected=subprocess.run([sys.executable,str(repo/'publish_vod_tv.py'),'--root',str(r),'--output-root',str(missing)],capture_output=True,text=True);self.assertNotEqual(rejected.returncode,0);self.assertIn('Missing retained local asset',rejected.stderr);self.assertFalse((missing/'dist/api/apps.json').exists())
   (r/'packages/dstore/other.ipk').symlink_to(Path(t)/'outside');(Path(t)/'outside').write_bytes(b'PRIVATE OUTSIDE');escaped=subprocess.run([sys.executable,str(repo/'publish_vod_tv.py'),'--root',str(r),'--output-root',str(Path(t)/'escaped')],capture_output=True,text=True);self.assertNotEqual(escaped.returncode,0)
   bad=subprocess.run([sys.executable,str(repo/'publish_vod_tv.py'),'--root',str(r),'--output-root',str(r)],capture_output=True,text=True);self.assertNotEqual(bad.returncode,0);self.assertEqual((r/'api/apps.json').read_text(),original)
   again=subprocess.run([sys.executable,str(repo/'publish_vod_tv.py'),'--root',str(r),'--output-root',str(out)],capture_output=True,text=True);self.assertNotEqual(again.returncode,0)
if __name__=='__main__':unittest.main()
