# F22 Colagem de Papel — roteiro de cenas do vídeo de exemplo "Santos Dumont x irmãos Wright"
# Cada frase da narração = uma cena. Faixas entram na palavra dita; peças entram na palavra que as justifica.
# Fica em jobs/<trabalho>/render/cenas.py; recortes em assets/cut e palavras em analysis/words_final.json.
import os
J = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCENT = (242, 183, 5)
CUT_DIR = J + '/assets/cut'
WORDS = J + '/analysis/words_final.json'
_TIGHT = [4.387771, 2.445292, 5.774250, 5.078979, 4.689458, 5.009188, 4.555021, 1.629708, 1.384625, 5.848229,
          3.079979, 2.860854, 5.059229, 7.465500]
SCENE_DUR = [d / 1.07 for d in _TIGHT]
TAIL = 0.6

S = lambda text, x, y, size=90, style='w', rot=0, **k: dict(t='strip', text=text, x=x, y=y, size=size, style=style, rot=rot, **k)
I = lambda src, x, y, w, at=0, rot=0, **k: dict(t='img', src=src, x=x, y=y, w=w, at=at, rot=rot, **k)
D = lambda kind, at=0, **k: dict(t='doodle', kind=kind, at=at, **k)

SCENES = [
    # 01 abertura: protagonista sobre raios
    dict(bg='burst', center=(.5, .62), els=[
        I('sd_bust', 540, 1180, 780, at=0),
        S('ALBERTO', 120, 250, 70, 'k', -2, anchor='l'),
        S('SANTOS DUMONT', 80, 380, 128, 'w', -1.5, anchor='l', keys=['Santos', 'Dumont']),
        S('O BRASILEIRO', 540, 1490, 80, 'k', 2),
        S('QUE FEZ O HOMEM', 540, 1615, 66, 'w', -1),
        S('VOAR!', 540, 1790, 170, 'a', -3),
        D('rays', at='voar', x=540, y=1790, s=250, n=7, a0=3.6, spread=2.2, color='a'),
    ]),
    # 02 "pelo menos é o que a gente aprende na escola"
    dict(bg='cream', els=[
        I('sheet', 560, 1060, 700, at=0, rot=3, anim='slide_up'),
        I('sd_head', 560, 1060, 380, at='@0.15', rot=-4),
        S('PELO MENOS...', 540, 330, 120, 'k', -3),
        S('É O QUE A GENTE APRENDE', 540, 520, 62, 'w', 1, keys=['é', 'o', 'que', 'a', 'gente', 'aprende']),
        S('NA ESCOLA', 540, 1620, 140, 'a', -2),
        D('stars', at='escola', x=540, y=1450, s=180, n=4),
    ]),
    # 03 ficha do personagem
    dict(bg='kraft', els=[
        S('PRA QUEM NÃO CONHECE', 540, 170, 64, 'k', -1, keys=['pra', 'quem', 'não', 'conhece']),
        I('sheet', 540, 720, 640, at=0, rot=-2),
        I('sd_head', 520, 700, 360, at='@0.1', rot=3),
        S('MINAS GERAIS', 90, 1170, 100, 'w', -2, anchor='l'),
        S('1873', 760, 1300, 150, 'a', 6, keys=['1873']),
        I('coffee', 300, 1600, 430, at='filho', rot=-5),
        D('crown', at='rei', x=300, y=1330, s=95, color='k'),
        S('FILHO DO', 830, 1530, 70, 'k', 2),
        S('REI DO CAFÉ', 760, 1650, 110, 'a', -2),
    ]),
    # 04 Paris e balão
    dict(bg='black', els=[
        S('FOI MORAR EM', 540, 200, 70, 'w', -1),
        S('PARIS', 540, 340, 170, 'a', 2),
        I('p_eiffel', 540, 720, 660, at='paris', rot=-3),
        S('VIROU', 300, 1060, 70, 'w', -2),
        S('CELEBRIDADE', 540, 1170, 120, 'a', 1),
        I('sd_head', 280, 1560, 360, at='celebridade', rot=-6),
        D('stars', at='celebridade', x=280, y=1330, s=110, n=5),
        I('p_balloon', 760, 1560, 420, at='balão', rot=6, anim='slide_up'),
        S('DE BALÃO', 760, 1830, 80, 'w', -2, keys=['de', 'balão']),
    ]),
    # 05 dirigível e "estacionava"
    dict(bg='cream', wipe_in=True, els=[
        S('DIZEM QUE IA ALMOÇAR', 540, 230, 70, 'k', -1, keys=['dizem', 'que', '@0.45', '@0.62']),
        S('DE DIRIGÍVEL', 540, 380, 140, 'a', 2, keys=['@0.9', 'dirigível']),
        I('p_no9', 540, 850, 860, at='dirigível', rot=2),
        S('E ESTACIONAVA', 120, 1300, 90, 'w', -2, anchor='l', keys=['e', 'estacionava']),
        I('sign_e', 820, 1480, 300, at='estacionava', rot=8),
        S('NA PORTA DO', 120, 1560, 70, 'k', 1, anchor='l'),
        S('RESTAURANTE', 90, 1700, 120, 'w', -1, anchor='l'),
        D('arrow', at='restaurante', x=470, y=1610, x1=560, y1=1050, bend=-160),
    ]),
    # 06 14-bis (impacto)
    dict(bg='burst', center=(.5, .45), els=[
        S('EM 1906', 540, 220, 80, 'k', -2, keys=['em', '1906']),
        S('14-BIS', 540, 400, 190, 'w', 2, keys=['14']),
        I('p_14bis', 540, 880, 900, at='14', rot=-3),
        S('DECOLOU SOZINHO', 540, 1300, 110, 'a', -1),
        S('NA FRENTE DE UMA MULTIDÃO', 540, 1460, 62, 'k', 1),
        D('crowd', at='multidão', x=540, y=1700, s=360, n=9, width=7),
    ]),
    # 07 do outro lado do oceano
    dict(bg='kraft', els=[
        S('SÓ QUE, DO OUTRO LADO', 540, 200, 66, 'k', -1),
        S('DO OCEANO', 540, 330, 130, 'w', 1),
        D('waves', at='oceano', x=540, y=520, s=420, n=3, color='k'),
        I('orville_bust', 330, 1050, 500, at='dois', rot=-4, sil=True),
        I('wilbur_bust', 760, 1080, 500, at='dois', rot=5, sil=True),
        S('DOIS IRMÃOS', 540, 1480, 120, 'a', -2),
        S('DIZIAM QUE TINHAM', 540, 1640, 66, 'k', 1),
        S('VOADO ANTES', 540, 1770, 110, 'w', -1),
    ]),
    # 08 "em 1903" — silhuetas e interrogação
    dict(bg='black', els=[
        I('orville_bust', 330, 1150, 500, at=0, rot=-4, sil=True, anim='none'),
        I('wilbur_bust', 760, 1180, 500, at=0, rot=5, sil=True, anim='none'),
        dict(t='doodle', kind='question', at=0, x=330, y=1050, s=260, draw=.1),
        dict(t='doodle', kind='question', at=0, x=760, y=1080, s=260, draw=.1),
        S('EM 1903.', 540, 420, 190, 'a', -3, keys=['@0', '1903']),
        D('circle', at='1903', x=560, y=420, rx=430, ry=170),
    ]),
    # 09 revelação
    dict(bg='burst', center=(.5, .6), els=[
        I('orville_bust', 320, 1130, 560, at=0, rot=-4),
        I('wilbur_bust', 770, 1160, 560, at=0, rot=5),
        S('OS IRMÃOS', 540, 300, 90, 'k', -2),
        S('WRIGHT', 540, 470, 210, 'w', 2),
    ]),
    # 10 o detalhe
    dict(bg='cream', els=[
        S('O DETALHE:', 120, 200, 110, 'k', -2, anchor='l'),
        I('p_firstflight', 540, 640, 900, at='@0.2', rot=2),
        S('QUASE NINGUÉM VIU', 540, 1010, 100, 'a', -1),
        D('eyex', at='viu', x=880, y=1150, s=90),
        S('E O AVIÃO SAIU DE', 120, 1220, 66, 'w', 1, anchor='l'),
        S('UM TRILHO', 120, 1350, 120, 'k', -2, anchor='l'),
        D('arrow', at='trilho', x=420, y=1290, x1=300, y1=850, bend=120),
        S('COM VENTO FORTE', 540, 1560, 110, 'a', 2),
        S('AJUDANDO', 540, 1700, 80, 'w', -1),
        D('wind', at='vento', x=300, y=1830, s=260),
    ]),
    # 11 a briga
    dict(bg='black', wipe_in=True, els=[
        S('PRONTO.', 540, 380, 200, 'w', -3),
        I('sd_head', 270, 1100, 380, at='começou', rot=-8),
        I('wilbur_head', 810, 1100, 340, at='começou', rot=8),
        D('stars', at='briga', x=540, y=1050, s=80, n=6, color='a'),
        S('COMEÇOU A BRIGA', 540, 1500, 120, 'a', 2),
        S('QUE DURA ATÉ HOJE', 540, 1650, 80, 'w', -1),
    ]),
    # 12 versus
    dict(bg='burst', center=(.5, .5), els=[
        D('octagon', at=0, x=540, y=1050, s=500, draw=.25, width=13),
        I('sd_bust', 290, 1120, 520, at=0, rot=-3),
        I('orville_bust', 760, 1060, 380, at='contra', rot=4),
        I('wilbur_bust', 850, 1250, 380, at='irmãos', rot=7),
        S('SANTOS DUMONT', 90, 300, 120, 'w', -2, anchor='l'),
        S('CONTRA', 540, 760, 110, 'a', 3),
        S('OS IRMÃOS WRIGHT', 540, 1680, 110, 'k', -1),
    ]),
    # 13 pai da aviação x resto do mundo
    dict(bg='kraft', els=[
        S('PRA NÓS,', 120, 200, 80, 'k', -2, anchor='l', keys=['pra', 'nós']),
        S('PAI DA AVIAÇÃO', 540, 340, 130, 'a', 1, keys=['pai', 'da', 'viação']),
        I('sd_bust', 330, 880, 540, at='@0.1', rot=-3),
        D('medal', at='pai', x=780, y=880, s=120, color='k', width=10),
        S('PRO RESTO DO MUNDO...', 540, 1360, 80, 'w', -1, keys=['pro', 'resto', 'do', 'mundo']),
        D('globe', at='mundo', x=780, y=1600, s=150, color='k'),
        S('NEM TANTO', 120, 1650, 130, 'k', -4, anchor='l'),
    ]),
    # 14 relógio de pulso (fecho)
    dict(bg='cream', wipe_in=True, els=[
        S('MAS UMA COISA', 120, 200, 76, 'k', -1, anchor='l'),
        S('NINGUÉM TIRA DELE', 540, 330, 110, 'w', 1),
        I('watch', 330, 900, 330, at='relógio', rot=-12),
        I('sd_head', 720, 860, 400, at='ajudou', rot=5),
        S('AJUDOU A POPULARIZAR', 540, 1260, 66, 'k', -1),
        S('O RELÓGIO DE PULSO', 540, 1400, 120, 'a', 2),
        D('arrow', at='pulso', x=200, y=1330, x1=260, y1=1110, bend=-80),
        S('SÓ PRA VER A HORA', 540, 1600, 80, 'w', -1),
        S('SEM LARGAR O CONTROLE', 540, 1730, 90, 'k', 1),
        D('underline', at='controle', x=540, y=1800, s=330, color='a'),
    ]),
]
