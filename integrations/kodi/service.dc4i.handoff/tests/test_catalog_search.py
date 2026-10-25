import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from catalog_search import find_matches

class SearchTests(unittest.TestCase):
    def setUp(self):
        self.catalog={
          'movie':{'603':[123,'mkv','EN - Matrix (1999)'],'62':[7,'mp4','Żółta łódź'], '13':[88,'mp4','The Matrix Revolutions']},
          'series':{'1396':[22,'EN - Breaking Bad'], '1399':[45,'PL - Gra o tron']}}
    def test_case_and_locale(self):
        matches=find_matches(self.catalog,'maTRIX',20)
        self.assertEqual(matches[0][1],'603')
        self.assertEqual(matches[0][0],'movie')
    def test_polish_accents(self):
        matches=find_matches(self.catalog,'zolta',20)
        self.assertEqual(matches[0][1],'62')
    def test_series(self):
        matches=find_matches(self.catalog,'breaking bad',20)
        self.assertEqual(matches[0][1],'1396')
        self.assertEqual(matches[0][0],'series')
    def test_empty_long_and_no_result(self):
        self.assertEqual(find_matches(self.catalog,'',20),[])
        self.assertEqual(find_matches(self.catalog,'q'*130,20),[])
        self.assertEqual(find_matches(self.catalog,'madeup',20),[])
    def test_limit(self):
        self.assertEqual(len(find_matches(self.catalog,'matrix',1)),1)

if __name__=='__main__':unittest.main(verbosity=2)