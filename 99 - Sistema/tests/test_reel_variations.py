import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import reel_variations as rv

IDENTITY = {'code': 'ID99', 'palette': {'background': '#F7F4FB', 'text': '#17092C', 'primary': '#820AD1', 'muted': '#5C0F8B'},
            'typography': {'headline': 'Manrope', 'body': 'Manrope', 'labels': 'JetBrains Mono'},
            'font_faces': [{'family': 'Manrope', 'path': 'assets/fonts/portable/manrope-variable.ttf'}]}


def post_row(i, photo='a.png', phrase='Essa frase', video='v.mp4'):
    return {'id': f'VAR{i:02d}', 'strategy': 'post', 'video': video, 'photo': {'src': photo, 'fit': 'cover'},
            'lines': [[[phrase, False]], [['e o ', False], ['destaque', True]]], 'output': f'x_VAR{i:02d}.mp4'}


class ReelVariationTests(unittest.TestCase):
    def test_plan_any_quantity_with_distinct_hooks(self):
        p = rv.plan(7, 'hook', 'br')
        self.assertEqual(len(p['variations']), 7)
        self.assertEqual(len({r['hook'] for r in p['variations']}), 7)
        self.assertEqual(len({r['output'] for r in p['variations']}), 7)
        self.assertTrue(rv.check(p)['ok'])

    def test_plan_beyond_catalogue_still_unique_combinations(self):
        p = rv.plan(len(rv.HOOKS) + 3, 'hook')
        r = rv.check(p)
        self.assertTrue(r['ok'], r['problems'])
        self.assertTrue(r['warnings'])           # hooks repeat → warned, the rest differs

    def test_mixed_plan_alternates(self):
        p = rv.plan(4, 'mixed')
        self.assertEqual([r['strategy'] for r in p['variations']], ['hook', 'post', 'hook', 'post'])

    def test_same_photo_and_phrase_rejected(self):
        p = {'header': {'name': 'Conta', 'handle': '@conta'}, 'variations': [post_row(1), post_row(2)]}
        r = rv.check(p)
        self.assertFalse(r['ok'])
        self.assertTrue(any('mesma foto e a mesma frase' in x for x in r['problems']))

    def test_post_needs_header_identity(self):
        p = {'header': {'name': ''}, 'variations': [post_row(1), post_row(2, photo='b.png')]}
        self.assertTrue(any('cabeçalho' in x for x in rv.check(p)['problems']))

    def test_layer_uses_identity_palette(self):
        from PIL import Image
        row = post_row(1)
        img = rv.layer(row, {'name': 'Conta', 'handle': '@conta'}, IDENTITY, Path('.'), photo_img=Image.new('RGB', (400, 700), (10, 200, 10)))
        self.assertEqual(img.size, (1080, 1920))
        self.assertEqual(img.getpixel((5, 5)), (247, 244, 251))           # background from the ID
        self.assertEqual(img.getpixel((rv.PX + 50, rv.PY + 50)), (10, 200, 10))   # photo panel

    def test_too_long_line_rejected(self):
        from PIL import Image
        row = post_row(1, phrase='Uma frase longa demais que não cabe de jeito nenhum na largura do post')
        with self.assertRaises(ValueError):
            rv.layer(row, {'name': 'Conta', 'handle': '@conta'}, IDENTITY, Path('.'), photo_img=Image.new('RGB', (10, 10)))


if __name__ == '__main__':
    unittest.main()
