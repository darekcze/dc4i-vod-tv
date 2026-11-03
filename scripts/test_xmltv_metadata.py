#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('xmltv_metadata', ROOT / 'scripts/xmltv_metadata.py')
module = None
if (ROOT / 'scripts/xmltv_metadata.py').exists():
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
NOW = 1792890000000  # 2026-10-25 01:00 UTC

class XmltvTests(unittest.TestCase):
    def parse(self, data):
        self.assertIsNotNone(module, 'XMLTV metadata importer must exist')
        return module.parse_xmltv(data, 'synthetic-test', NOW)

    def test_dst_and_utc_default_are_absolute(self):
        result = self.parse((ROOT / 'tests/fixtures/epg/synthetic.xml').read_bytes())
        self.assertEqual([e['start'] for e in result['events']], [1792888200000,1792891800000,1792900800000])
        self.assertEqual(result['diagnostics']['skipped'], 1)
        self.assertEqual(result['events'][0]['end'] - result['events'][0]['start'], 1200000)

    def test_provenance_does_not_claim_tmdb_or_verified_tracks(self):
        data=(ROOT / 'tests/fixtures/epg/synthetic.xml').read_bytes().replace(b'<tv>',b'<tv source-data-url="https://private.invalid/?password=secret">')
        result=self.parse(data); event=result['events'][0]
        self.assertEqual(event['provenance'], {'source':'synthetic-test','kind':'xmltv','fetchedAt':NOW})
        self.assertEqual(event['originalLanguage'], 'English')
        self.assertEqual(event['rating'], {'value':'4/5','system':'editorial','verified':False})
        self.assertEqual(event['tracks'], {'audio':'unknown','subtitles':'unknown'})
        self.assertNotIn('private.invalid', str(result)); self.assertNotIn('tmdb',event)

    def test_invalid_partial_and_reversed_times_skip_without_inference(self):
        for start,end in [('202610','20261025040000'),('20260230000000','20260301000000'),('20261025040000','20261025030000'),('20261025023000 +2460','20261025050000')]:
            data=f'<tv><programme channel="x" start="{start}" stop="{end}"><title>A</title></programme></tv>'.encode()
            self.assertEqual(self.parse(data)['events'], [])

    def test_duplicate_events_collapse_but_conflicting_channels_are_removed(self):
        row='<programme channel="x" start="20261025010000" stop="20261025020000"><title>A</title></programme>'
        self.assertEqual(len(self.parse(('<tv><channel id="x"><display-name>X</display-name></channel>'+row+row+'</tv>').encode())['events']),1)
        data=('<tv><channel id="x"><display-name>One</display-name></channel><channel id="x"><display-name>Two</display-name></channel>'+row+'</tv>').encode()
        result=self.parse(data)
        self.assertEqual(result['channels'],[]);self.assertEqual(result['events'],[])
        self.assertEqual(result['diagnostics']['conflictingChannels'],1)

    def test_orphan_programmes_are_skipped_and_counted(self):
        declared='<channel id="known"><display-name>Known</display-name></channel>'
        orphan='<programme channel="ghost" start="20261025010000" stop="20261025020000"><title>Orphan</title></programme>'
        valid='<programme channel="known" start="20261025010000" stop="20261025020000"><title>Valid</title></programme>'
        result=self.parse(('<tv>'+declared+orphan+valid+'</tv>').encode())
        self.assertEqual([e['channelId'] for e in result['events']], ['known'])
        self.assertEqual(result['diagnostics']['skipped'], 1)

    def test_spring_transition_duration(self):
        result=self.parse(b'<tv><channel id="x"><display-name>X</display-name></channel><programme channel="x" start="20260329015000 +0100" stop="20260329031000 +0200"><title>A</title></programme></tv>')
        self.assertEqual(result['events'][0]['end']-result['events'][0]['start'],1200000)

    def test_malformed_entities_and_size_limit_fail_atomically(self):
        self.assertIsNotNone(module, 'XMLTV metadata importer must exist')
        for data in [b'<tv><programme',b'<!DOCTYPE tv [<!ENTITY x "expanded">]><tv/>', b'<tv>'+b' '*2_000_001+b'</tv>']:
            with self.assertRaises(ValueError):self.parse(data)
        with self.assertRaises(ValueError):module.parse_xmltv(b'<tv/>','https://host/?password=x',NOW)

    def test_depth_record_limits_and_compression_are_rejected(self):
        import gzip
        cases=[b'<tv>'+b'<x>'*40+b'</x>'*40+b'</tv>',gzip.compress(b'<tv/>'),
               b'<tv>'+b'<channel id="x"><display-name>A</display-name></channel>'*1001+b'</tv>',
               b'<tv>'+b'<programme/>'*20001+b'</tv>',
               '<!DOCTYPE tv [<!ENTITY x "bad">]><tv/>'.encode('utf-16')]
        for data in cases:
            with self.subTest(size=len(data)):
                with self.assertRaises(ValueError):self.parse(data)

if __name__=='__main__':unittest.main(verbosity=2)
