import sys, unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from find_hidden_retakes import find, voiced


def W(text, s, e):
    return {'w': text, 'n': ''.join(c for c in text.lower() if c.isalnum()), 's': s, 'e': e}


class HiddenRetakeTests(unittest.TestCase):
    def test_long_word_with_hidden_speech(self):
        env = np.full(1000, -80.0); env[300:340] = -20; env[420:460] = -20   # two speech islands inside a 2,4 s "word"
        words = [W('Agora', 0.0, 0.5), W('pessoas', 2.5, 4.9), W('fazendo', 5.0, 5.5)]
        lw = [x for x in find(words, env) if x['type'] == 'long_word']
        self.assertEqual(len(lw), 1)
        self.assertEqual(len(lw[0]['voiced']), 2)

    def test_voiced_gap_and_repeat(self):
        env = np.full(1500, -80.0); env[300:360] = -25
        words = [W('aqui', 0.0, 0.3), W('na', 0.35, 0.5), W('empire', 0.55, 1.0), W('nós', 1.05, 1.3),
                 W('aqui', 8.0, 8.3), W('na', 8.35, 8.5), W('empire', 8.55, 9.0), W('nós', 9.05, 9.3)]
        c = find(words, env, repeat_window=10.0)
        self.assertTrue(any(x['type'] == 'voiced_gap' for x in c))
        self.assertTrue(any(x['type'] == 'repeat' and x['phrase'].startswith('aqui na empire') for x in c))

    def test_clean_take_has_no_candidates(self):
        env = np.full(500, -80.0)
        words = [W('uma', 0.0, 0.2), W('outra', 0.25, 0.5), W('IA', 0.55, 0.7)]
        self.assertEqual(find(words, env), [])

    def test_voiced_merges_close_islands(self):
        env = np.full(300, -80.0); env[10:20] = -20; env[25:40] = -20
        self.assertEqual(voiced(env, 0, 3, -45), [[0.1, 0.4]])


if __name__ == '__main__':
    unittest.main()
