"""Physical relocation, symlink-free operation, ledger preservation and rollback."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from reorganize_project import migrate, rollback
from project_layout import SYSTEM, engine_root, translate, managed_path, surface_root
from factory_state import State
from client_memory import Memory
from design_catalog import register_visual
from edit_support import read_data
from factory_common import sha


class StructureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()/'Fábrica com espaços';self.root.mkdir()
        for name in ('config','patterns','adapters'):
            shutil.copytree(ROOT/name,self.root/name,ignore=shutil.ignore_patterns('__pycache__','*.local.json','.env*','CHAVES DAS INTEGRAÇÕES.txt','github-access.json'))
        (self.root/'tools').mkdir();(self.root/'tools/factory_common.py').write_text('fixture marker')
        (self.root/'entrada').mkdir();self.source=self.root/'entrada/Gravação.txt';self.source.write_bytes(b'synthetic original')
        (self.root/'saida').mkdir()

    def test_preview_and_conflict_preserve_every_source(self):
        migrate(self.root)
        self.assertFalse((self.root/SYSTEM).exists())
        (self.root/SYSTEM/'tools').mkdir(parents=True)
        with self.assertRaises(ValueError):migrate(self.root,apply=True)
        self.assertTrue(self.source.is_file())

    def test_physical_move_without_compatibility_and_rollback(self):
        inode=self.source.stat().st_ino
        migrate(self.root,apply=True,compatibility=False)
        self.assertFalse((self.root/'tools').exists())
        self.assertTrue((self.root/SYSTEM/'tools').is_dir())
        self.assertEqual((self.root/'01 - Enviar vídeos/Gravação.txt').stat().st_ino,inode)
        self.assertFalse(any(p.is_symlink() for p in self.root.rglob('*')))
        rollback(self.root)
        self.assertEqual(self.source.read_bytes(),b'synthetic original')

    def test_existing_format_and_batch_survive_without_legacy_links(self):
        memory=Memory(self.root);memory.init('aulas','Aulas')
        register_visual(self.root,'Fixture',{'background':'#FFFFFF','text':'#111111','primary':'#336699'},{'headline':'Arial','body':'Arial','labels':'monospace'})
        state=State(self.root)
        request={'id':'aula','sources':[str(self.source)],'format':'aulas','visual_identity':'IDP01','budget':{'mode':'usd','limit_usd':'2'}}
        state.intake(request)
        before=state.budget('aula');store=memory.path('aulas');contents=store.read_bytes()
        migrate(self.root,apply=True,compatibility=False)
        state=State(self.root)
        self.assertEqual(state.root,self.root/SYSTEM)
        self.assertEqual(Memory(self.root).path('aulas').read_bytes(),contents)
        self.assertEqual(Memory(self.root).name('aulas'),'Aulas')
        self.assertEqual(state.budget('aula'),before)
        self.assertEqual(state.intake(request)['status'],'resume')
        self.assertEqual(state.resume('aula')['input_changes'],[])

    def test_legacy_edl_read_keeps_evidence_bytes(self):
        (self.root/'jobs/example/edit').mkdir(parents=True)
        edl=self.root/'jobs/example/edit/edl.json'
        edl.write_text(json.dumps({'segments':[{'source':str(self.source),'in':0,'out':1}]}))
        before=sha(edl)
        migrate(self.root,apply=True,compatibility=False)
        edl=self.root/SYSTEM/'jobs/example/edit/edl.json'
        self.assertEqual(read_data(edl)['segments'][0]['source'],str(self.root/'01 - Enviar vídeos/Gravação.txt'))
        self.assertEqual(sha(edl),before)

    def test_native_configuration_stays_at_outer_root(self):
        migrate(self.root,apply=True,compatibility=False)
        self.assertEqual(managed_path(self.root/SYSTEM,'.codex/config.toml'),self.root/'.codex/config.toml')
        self.assertEqual(managed_path(self.root/SYSTEM,'jobs/example/job.yaml'),self.root/SYSTEM/'jobs/example/job.yaml')

    def test_path_translation_is_idempotent(self):
        migrate(self.root,apply=True,compatibility=False)
        old={'source':str(self.source),'plan':str(self.root/'jobs/example/edit/edl.json')}
        once=translate(old,self.root)
        self.assertEqual(translate(once,self.root),once)
        self.assertEqual(translate(once,self.root,reverse=True),old)

    def test_fresh_clone_uses_outer_root_without_private_state(self):
        system=self.root/SYSTEM;system.mkdir()
        (self.root/'tools').rename(system/'tools')
        (self.root/'.factory-root.json').write_text('{"version":1,"engine":"99 - Sistema"}')
        self.assertFalse((system/'.factory/layout.json').exists())
        self.assertEqual(surface_root(system),self.root)
        self.assertEqual(managed_path(system,'.claude/settings.json'),self.root/'.claude/settings.json')


if __name__=='__main__':unittest.main()
