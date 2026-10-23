"""Portable effects layers and safeguards. No database, services, downloads or model calls."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from effect_catalog import catalogue, effect, prepare, validate_props
from studio_render import inspect


class Effects(unittest.TestCase):
    def setUp(self):
        (ROOT/'tmp').mkdir(exist_ok=True)
        self.directory=tempfile.TemporaryDirectory(dir=ROOT/'tmp')
        self.root=Path(self.directory.name)
        self.props={'text':'Uma ideia','accent':'#d8ef77','foreground':'#f3f1e9','background':'#101411','fontFamily':'sans-serif','duration':3}

    def tearDown(self):
        self.directory.cleanup()

    def test_complete_index_and_provenance(self):
        entries=catalogue()['effects']
        self.assertEqual(len(entries),50)
        self.assertEqual(len({e['code'] for e in entries}),50)
        self.assertEqual(len({e['id'] for e in entries}),len(entries))
        refs=json.loads((ROOT/'motion/effects/references.json').read_text())['sources']
        reference_ids={s['id'] for s in refs}
        for item in entries:
            self.assertIsInstance(item['reference_ids'],list,item['code'])
            self.assertLessEqual(set(item['reference_ids']),reference_ids)
            self.assertTrue(item['caution'])
            self.assertEqual(effect(item['code'])['id'],item['id'])

    def test_production_appearance_is_explicit(self):
        for key in ('accent','foreground','background','fontFamily'):
            props=dict(self.props);props.pop(key)
            with self.assertRaises(ValueError):validate_props(props)

    def test_bad_data_is_rejected(self):
        for values in ([float('nan')],[True],[-1],[],['40']):
            with self.assertRaises(ValueError):validate_props({**self.props,'values':values})
        with self.assertRaises(ValueError):validate_props({**self.props,'wordCues':[{'text':'ideia','start':2,'end':4}]})
        with self.assertRaises(ValueError):validate_props({**self.props,'surprise':'not allowed'})

    def test_timed_words_and_data_are_accepted(self):
        validate_props({**self.props,'values':[10,20,0],'labels':['A','B','C'],'wordCues':[{'text':'Uma','start':.1,'end':.3},{'text':'ideia','start':.4,'end':.9}]})

    def test_layer_is_compatible_and_text_is_data(self):
        destination=self.root/'layer'
        props={**self.props,'text':'</script><script>throw Error("untrusted")</script>'}
        prepare('FX01',destination,props,child_id='test-child')
        spec,resources,protected,report=inspect(destination/'spec.json')
        self.assertEqual(spec['mode'],'overlay')
        self.assertEqual(spec['child_id'],'test-child')
        self.assertEqual(spec['duration_frames'],90)
        self.assertFalse(report['network_access'])
        html=(destination/'effect.html').read_text()
        self.assertIn('\\u003c/script>',html)
        self.assertNotIn('</script><script>throw',html)
        with self.assertRaises(ValueError):prepare('FX01',destination,self.props,child_id='test-child')

    def test_logo_and_external_assets_are_blocked(self):
        with self.assertRaises(ValueError):prepare('FX36',self.root/'logo',self.props,child_id='test-child')
        with self.assertRaises(ValueError):prepare('FX16',self.root/'external',self.props,child_id='test-child',assets={'screenshot':'/etc/hosts'})
        self.assertFalse((self.root/'external').exists())

    def test_catalogue_demo_never_claims_a_real_job(self):
        destination=self.root/'demo'
        prepare('counter',destination,{},child_id='library-demo',demo=True)
        spec=json.loads((destination/'spec.json').read_text())
        self.assertTrue(spec['effect']['illustrative_demo'])
        self.assertEqual(spec['mode'],'full_frame')


if __name__=='__main__':unittest.main()
