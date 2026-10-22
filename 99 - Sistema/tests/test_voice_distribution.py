"""Installer boundary tests: no application imports, network, databases or migrations."""
import io
import json
from pathlib import Path
import stat
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_distribution as distribution
import prepare_cortez_voice as installer

class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def archive(self,entries):
        p=self.root/'source.zip'
        with zipfile.ZipFile(p,'w') as z:
            for name,data in entries:z.writestr(name,data)
        return p
    def test_regular_files(self):
        distribution.extract(self.archive([('root/file.txt','safe')]),self.root/'out')
        self.assertEqual((self.root/'out/root/file.txt').read_text(),'safe')
    def test_rejects_traversal_and_windows_ambiguous_paths(self):
        for name in ('../escape','/absolute','C:/escape','dir\\escape','CON.txt','file:stream','name.'):
            with self.subTest(name=name):
                archive=self.archive([(name,'bad')])
                with tempfile.TemporaryDirectory(dir=self.root) as d:
                    with self.assertRaises(ValueError):distribution.extract(archive,Path(d)/'out')
        self.assertFalse((self.root.parent/'escape').exists())
    def test_rejects_symlinks(self):
        member=zipfile.ZipInfo('link');member.create_system=3;member.external_attr=(stat.S_IFLNK|0o777)<<16
        p=self.root/'link.zip'
        with zipfile.ZipFile(p,'w') as z:z.writestr(member,'../../escape')
        with self.assertRaises(ValueError):distribution.extract(p,self.root/'out')
    def test_rejects_case_collisions(self):
        with self.assertRaises(ValueError):distribution.extract(self.archive([('File','1'),('file','2')]),self.root/'out')
    def test_rejects_tar_links(self):
        p=self.root/'source.tar'
        with tarfile.open(p,'w') as t:
            member=tarfile.TarInfo('link');member.type=tarfile.SYMTYPE;member.linkname='../escape';t.addfile(member)
        with self.assertRaises(ValueError):distribution.extract(p,self.root/'out')
    def test_https_expected_hosts_only(self):
        for url in ('http://github.com/a','https://github.com.evil/a','https://user@github.com/a','https://github.com:444/a'):
            with self.assertRaises(ValueError):distribution.checked_url(url)
        self.assertEqual(distribution.checked_url('https://codeload.github.com/a'),'https://codeload.github.com/a')
    def test_existing_destination_never_overwritten(self):
        dest=self.root/'out';dest.mkdir();(dest/'private').write_text('preserve')
        with self.assertRaises(FileExistsError):distribution.extract(self.archive([('file','1')]),dest)
        self.assertEqual((dest/'private').read_text(),'preserve')
    def test_download_hash_failure_removes_partial(self):
        class Response(io.BytesIO):pass
        with patch.object(distribution.urllib.request,'build_opener') as build:
            build.return_value.open.return_value=Response(b'changed')
            with self.assertRaises(ValueError):distribution.download({'url':'https://github.com/a','size':7,'sha256':'0'*64},self.root/'download')
        self.assertFalse((self.root/'download').exists())
    def spec(self):
        sha='a'*40
        spec={'repository':'Empire-Business/cortez-voz','commit':sha,
              'archive':{'url':f'https://codeload.github.com/Empire-Business/cortez-voz/zip/{sha}','size':1,'sha256':'0'*64},
              'platforms':{k:'not_run' for k in ('Darwin-arm64','Windows-x86_64','Linux-x86_64')}}
        (self.root/'config').mkdir();(self.root/'config/cortez-voice.json').write_text(json.dumps(spec));return spec
    def test_platform_previews_have_no_side_effects(self):
        self.spec()
        for system,machine in (('Darwin','arm64'),('Windows','AMD64'),('Linux','x86_64')):
            with patch.object(installer.platform,'system',return_value=system),patch.object(installer.platform,'machine',return_value=machine),patch.object(installer,'download') as network:
                result=installer.prepare(self.root)
                self.assertEqual(result['status'],'preview');self.assertFalse(result['database_started']);network.assert_not_called()
        self.assertFalse((self.root/'.factory').exists())
    def test_upstream_or_mutable_ref_rejected(self):
        spec=self.spec();spec['commit']='main';(self.root/'config/cortez-voice.json').write_text(json.dumps(spec))
        with self.assertRaises(ValueError):installer.specification(self.root)
    def test_start_requires_explicit_database_authorization(self):
        self.spec()
        with patch.object(installer.subprocess,'call') as run:
            with self.assertRaisesRegex(ValueError,'initialize-data'):installer.start(self.root)
            run.assert_not_called()

    def test_reuse_checks_all_source_files_against_pinned_archive(self):
        archive=self.archive([('source/cortez/install.py','installer'),('source/uv.lock','locked'),('source/backend/main.py','original')])
        spec={'archive':{'size':archive.stat().st_size,'sha256':distribution.digest(archive)}}
        distribution.extract(archive,self.root/'unpack');source=self.root/'unpack/source'
        installer.verify_source(source,archive,spec)
        for name in ('sitecustomize.py', 'cortez/sitecustomize.py', 'backend/injected.py'):
            path=source/name;path.write_text('injected')
            with self.assertRaisesRegex(ValueError,'Arquivo extra'):installer.verify_source(source,archive,spec)
            path.unlink()
        generated=source/'.cortez';generated.mkdir();(generated/'installed.json').write_text('{}')
        cache=source/'backend/__pycache__';cache.mkdir()
        bytecode=cache/'main.cpython-312.pyc';bytecode.write_bytes(b'untrusted cached code')
        installer.verify_source(source,archive,spec)
        self.assertFalse(bytecode.exists())
        for name in ('uv.lock','backend/main.py'):
            with self.subTest(name=name):
                path=source/name;old=path.read_bytes();path.write_text('changed')
                with self.assertRaisesRegex(ValueError,'Código de voz alterado'):installer.verify_source(source,archive,spec)
                path.write_bytes(old)
        archive.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'origem ausente ou divergente'):installer.verify_source(source,archive,spec)

if __name__=='__main__':unittest.main()
