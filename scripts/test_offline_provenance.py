import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('fixture',Path(__file__).with_name('build_offline_fixture.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ProvenanceTests(unittest.TestCase):
    def test_deferred_local_styles_are_active_without_inline_handlers(self):
        from html.parser import HTMLParser
        class Links(HTMLParser):
            def handle_starttag(self, tag, attrs):
                if tag == 'link': self.links.append(dict(attrs))
        original = '<link rel="stylesheet" href="style.css" media="print" onload="this.media=\'all\'">'
        parser=Links();parser.links=[];parser.feed(module.activate_fixture_styles(original))
        self.assertEqual(parser.links,[{'rel':'stylesheet','href':'style.css','media':'all'}])
        with self.assertRaises(ValueError):
            module.activate_fixture_styles(original.replace('style.css','https://example.invalid/style.css'))

    def test_dirty_working_copy_is_not_used_and_exact_commit_is_recorded(self):
        self.assertTrue(hasattr(module,'snapshot_project'),'snapshot_project must pin and record project inputs')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'repo';root.mkdir();dest=Path(directory)/'snapshot';dest.mkdir()
            def git(*args):return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.DEVNULL,text=True).strip()
            git('init');(root/'test.txt').write_text('committed')
            git('add','test.txt');git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','fixture')
            sha=git('rev-parse','HEAD');(root/'test.txt').write_text('dirty');(root/'untracked.txt').write_text('local')
            provenance=module.snapshot_project(root,dest)
            self.assertEqual(provenance['projectCommit'],sha)
            self.assertTrue(provenance['workingTreeDirty'])
            self.assertEqual((dest/'test.txt').read_text(),'committed')
            self.assertFalse((dest/'untracked.txt').exists())
            self.assertEqual(provenance['inputPolicy'],'committed-tree-only')

if __name__=='__main__':unittest.main(verbosity=2)
