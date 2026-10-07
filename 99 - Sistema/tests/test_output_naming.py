"""Short, deterministic filenames for user-facing previews and final videos."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from output_naming import next_version, output_filename, proportion_label
import product_motion


class OutputNamingTests(unittest.TestCase):
    def test_preview_and_final_show_name_proportion_format_and_final_version(self):
        preview=output_filename('Minha Aula','9:16','OMNX SDR AI',4,'preview')
        final=output_filename('Minha Aula','16:9','OMNX SDR AI',4,'final')
        self.assertEqual(preview,'minha-aula_9x16_omnx-sdr-ai_PREVIEW_V4.mp4')
        self.assertEqual(final,'minha-aula_16x9_omnx-sdr-ai_V4.mp4')
        self.assertRegex(preview,r'_V4\.mp4$')

    def test_version_is_shared_across_proportions_and_preview_final_are_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            (d/'aula_9x16_x_PREVIEW_V1.mp4').touch()
            (d/'aula_16x9_x_PREVIEW_V3.mp4').touch()
            (d/'aula_9x16_x_V4.mp4').touch()
            self.assertEqual(next_version(d,'aula','x','preview'),4)
            self.assertEqual(next_version(d,'aula','x','final'),5)

    def test_variant_versions_do_not_collide(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            (d/'aula_9x16_x_HOOK_PREVIEW_V2.mp4').touch()
            (d/'aula_9x16_x_PREVIEW_V4.mp4').touch()
            self.assertEqual(next_version(d,'aula','x','preview',variant='hook'),3)
            self.assertEqual(next_version(d,'aula','x','preview'),5)

    def test_resolution_dimensions_are_reduced_to_proportion(self):
        self.assertEqual(proportion_label('1080x1920'),'9x16')

    def test_product_motion_render_uses_job_name_profile_proportion_and_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            job=Path(tmp);(job/'src').mkdir();(job/'renders').mkdir()
            (job/'src'/'scenes.json').write_text('{}')
            (job/'src'/'brand.json').write_text(json.dumps({'jobId':'demo','videoName':'Minha Demo','formatId':'reels'}))
            args=type('Args',(),{'job':str(job),'proportion':'both','legacy_fmt':None,'quality':'looks',
                                 'kind':'preview','version':None})()
            calls=[]
            with patch.object(product_motion,'job_dir',return_value=job),patch.object(product_motion,'run',side_effect=lambda cmd,cwd,**kw:calls.append(cmd)):
                product_motion.cmd_render(args)
            outputs=[cmd[-1] for cmd in calls]
            self.assertEqual(outputs,['renders/minha-demo_16x9_reels_PREVIEW_V1.mp4',
                                      'renders/minha-demo_9x16_reels_PREVIEW_V1.mp4'])


if __name__=='__main__':unittest.main()
