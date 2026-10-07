"""Real registration against temporary stores, without touching personal formats."""
from pathlib import Path
import io
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from client_memory import Memory
from format_catalog import HUB, create as actual_create, formats, interactive, refresh


def create(root,name,format_id=None):
    return actual_create(root,name,format_id,example_url='https://example.com/reference-video')


class FormatCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_name_registers_in_canonical_store_without_preferences(self):
        receipt = create(self.root, 'Aulas da empresa')
        self.assertEqual(receipt['format'], 'aulas-da-empresa')
        self.assertTrue(receipt['verified'])
        memory = Memory(self.root)
        self.assertEqual(memory.name(receipt['format']), 'Aulas da empresa')
        with sqlite3.connect(memory.path(receipt['format'])) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM records').fetchone()[0], 0)
        self.assertFalse((self.root/'context/.runtime/state.sqlite3').exists())

    def test_same_name_reuses_store(self):
        receipt = create(self.root, 'Aulas da empresa')
        path = self.root/receipt['store']
        before = path.read_bytes()
        self.assertEqual(create(self.root, 'Aulas da empresa')['status'], 'existing')
        self.assertEqual(path.read_bytes(), before)

    def test_collision_preserves_existing_database(self):
        receipt = create(self.root, 'Ação')
        path = self.root/receipt['store']; before=path.read_bytes()
        with self.assertRaises(ValueError):
            create(self.root, 'Acao')
        self.assertEqual(path.read_bytes(), before)

    def test_catalogue_read_does_not_modify_stores_and_escapes_html(self):
        receipt = create(self.root, 'Aulas <empresa>')
        path=self.root/receipt['store'];before=path.read_bytes()
        result=refresh(self.root)
        self.assertTrue(result['ok'])
        self.assertIn('Aulas &lt;empresa&gt;', (self.root/'04 - Formatos'/result['folders'][0]/'COMO USAR.html').read_text())
        self.assertEqual(path.read_bytes(), before)
        detail=self.root/'04 - Formatos'/result['folders'][0]/'COMO USAR.html'
        self.assertIn('Aulas &lt;empresa&gt;', detail.read_text())
        self.assertFalse(any(p.is_symlink() for p in (self.root/HUB).rglob('*')))

    def test_interactive_registration_and_cancel(self):
        with patch('builtins.input', side_effect=['Série de aulas','https://example.com/reference-video']), patch('sys.stdout', new=io.StringIO()) as output:
            self.assertEqual(interactive(self.root), 0)
            self.assertIn('Registro confirmado', output.getvalue())
        self.assertEqual(formats(self.root)[0][0]['name'], 'Série de aulas')
        with patch('builtins.input', return_value=''), patch('sys.stdout', new=io.StringIO()):
            self.assertEqual(interactive(self.root), 0)
        self.assertEqual(len(formats(self.root)[0]), 1)

    def test_symlinked_store_and_catalogue_are_rejected(self):
        outside=self.root/'outside';outside.mkdir()
        (self.root/'context').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            create(self.root, 'Aulas')
        (self.root/'04 - Formatos').symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):
            refresh(self.root)


if __name__ == '__main__':
    unittest.main()

class RenameTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        create(self.root,'Nome de teste','legacy');refresh(self.root)
    def test_rename_preserves_preferences_id_and_custom_files(self):
        from format_catalog import rename
        memory=Memory(self.root)
        memory.commit('legacy',[{'kind':'preference','key':'motion.intensity','setting':'motion.intensity','value':'restrained','scope':'format','scope_id':'legacy','basis':'user_explicit','source':'user_message','quote':'Use movimento discreto.','reason':'Synthetic fixture.'}],'fixture')
        before=memory.context('legacy')['fingerprint']
        folder=self.root/'04 - Formatos/FP01 - Nome de teste';(folder/'extra.txt').write_text('preserve')
        result=rename(self.root,'legacy','Conversa Animada','User requests descriptive names','rename-test')
        self.assertTrue(result['verified']);self.assertEqual(memory.name('legacy'),'Conversa Animada')
        self.assertEqual(memory.context('legacy')['fingerprint'],before)
        self.assertTrue((self.root/'04 - Formatos/FP01 - Conversa Animada/extra.txt').exists())
        self.assertFalse(folder.exists())
        self.assertEqual(rename(self.root,'legacy','Conversa Animada','User requests descriptive names','rename-test')['name'],'Conversa Animada')
    def test_duplicate_name_is_blocked_before_mutation(self):
        from format_catalog import rename
        create(self.root,'Outro','other');refresh(self.root)
        with self.assertRaises(ValueError):rename(self.root,'legacy','Outro','Synthetic request','rename-test')
        self.assertEqual(Memory(self.root).name('legacy'),'Nome de teste')
    def test_existing_destination_is_not_overwritten(self):
        from format_catalog import rename
        (self.root/'04 - Formatos/FP01 - Destino').mkdir();(self.root/'04 - Formatos/FP01 - Destino/manual.txt').write_text('user file')
        with self.assertRaises(ValueError):rename(self.root,'legacy','Destino','Synthetic request','rename-test')
        self.assertEqual(Memory(self.root).name('legacy'),'Nome de teste')
