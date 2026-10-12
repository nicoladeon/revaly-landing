# -*- coding: utf-8 -*-
"""Musique originale du film Revaly (page de vente v3) — synthèse additive, Python pur.

Adaptée de ~/kwestim-video/film/music/compose.py (même moteur à tables d'onde).
Ré majeur lumineux, 96 BPM, mesure de 2,5 s ; 47 s écrites pour que l'accord final
résonne sous l'écran de fin (le film de 45 s s'efface à 44,3 s dans mux.sh, la pub
verticale de 30 s finit sur cet accord).

Repères du film (ouverture B) :
  0,55 s  la notification arrive      → deux notes de cloche, discrètes
  8,3 s   le tap sur « Valider »      → un clic doux
  9,25 s  « ✓ Validé »                → deux notes qui montent
  34-40 s ce que voient tes clients   → montée : nappe qui s'ouvre, arpèges en doubles, basse
  37,4 s  l'équipe se replie          → un souffle
  40 s    la promesse                 → l'accord de ré, qui résonne jusqu'à la fin
Composée et synthétisée ici : aucun échantillon, aucune licence en jeu.
Usage : python3 film/music/compose.py  → film/music/musique.wav (48 kHz, stéréo, 16 bits)
"""
import math, os, random, struct, wave
from array import array

SR, DUR = 48000, 47.0
N = int(SR * DUR)
TBL = 4096
ICI = os.path.dirname(os.path.abspath(__file__))
random.seed(12102026)

def freq(name):
    step = {'C': 0, 'C#': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'Bb': 10, 'B': 11}
    n, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((step[n] + (o - 4) * 12 - 9) / 12.0)

def table(harm):
    t = array('f', bytes(4 * TBL))
    for i in range(TBL):
        t[i] = sum(a * math.sin(2 * math.pi * h * i / TBL) for h, a in harm)
    m = max(abs(x) for x in t) or 1.0
    for i in range(TBL):
        t[i] /= m
    return t

# timbres : nappe douce, cloche claire (piano électrique), sub rond, pincé léger
PAD = table([(1, 1.0), (2, 0.38), (3, 0.20), (4, 0.08), (5, 0.04)])
BELL = table([(1, 1.0), (2, 0.50), (3, 0.26), (4, 0.14), (6, 0.07), (8, 0.03)])
SUB = table([(1, 1.0), (2, 0.12)])
PLUCK = table([(1, 1.0), (2, 0.6), (3, 0.35), (4, 0.2), (5, 0.12), (7, 0.05)])

def gain(t):
    """Le film respire : calme, présence sous les scènes, montée sur la révélation."""
    if t < 4.0:   return 0.48 + 0.07 * (t / 4.0)
    if t < 12.0:  return 0.55 + 0.05 * ((t - 4.0) / 8.0)
    if t < 34.0:  return 0.60 + 0.04 * ((t - 12.0) / 22.0)
    if t < 40.0:  return 0.64 + 0.36 * ((t - 34.0) / 6.0) ** 1.4      # la montée
    return 1.0

L = array('f', bytes(4 * N))
R = array('f', bytes(4 * N))

def note(tbl, f, start, dur, amp, atk, tau, pan=0.0, det=0.0, suit=True):
    i0 = int(start * SR)
    n = min(int(dur * SR), N - i0)
    if i0 < 0 or n <= 0: return
    gl = amp * math.sqrt((1 - pan) / 2 + 0.5)
    gr = amp * math.sqrt((1 + pan) / 2 + 0.5)
    for buf, g, d in ((L, gl, 0.0), (R, gr, det)):
        step = (f * (1 + d)) * TBL / SR
        ph = 0.0
        ai = max(1, int(atk * SR))
        rel = int(0.08 * SR)
        for k in range(n):
            e = (k / ai) if k < ai else math.exp(-(k - ai) / (tau * SR))
            if k > n - rel: e *= (n - k) / rel          # pas de clic en fin de note
            if e < 0.0005 and k > ai: break
            gg = gain((i0 + k) / SR) if suit else 1.0
            buf[i0 + k] += tbl[int(ph) & (TBL - 1)] * e * g * gg
            ph += step

def souffle(start, dur, amp, pan=0.0):
    """Bruit filtré qui gonfle puis retombe (repli de l'équipe)."""
    i0, n = int(start * SR), int(dur * SR)
    a, y = 0.06, 0.0
    for k in range(min(n, N - i0)):
        x = random.uniform(-1, 1)
        y += a * (x - y)
        e = math.sin(math.pi * k / n) ** 2
        L[i0 + k] += y * e * amp * (1 - pan * 0.5)
        R[i0 + k] += y * e * amp * (1 + pan * 0.5)

def clic(start, amp):
    """Le tap : un clic court, adouci (bruit filtré de 9 ms + une note très brève)."""
    i0, n = int(start * SR), int(0.009 * SR)
    y = 0.0
    for k in range(n):
        y += 0.35 * (random.uniform(-1, 1) - y)
        e = math.exp(-k / (0.002 * SR))
        L[i0 + k] += y * e * amp
        R[i0 + k] += y * e * amp
    note(BELL, freq('A5'), start, 0.12, amp * 0.25, 0.001, 0.03, suit=False)

BAR = 2.5            # 96 BPM, 4 temps
CROCHE = BAR / 8
voix = {             # nappe (trois ou quatre voix, aigu ouvert)
    'D':   ['D3', 'A3', 'E4', 'F#4'], 'A':  ['A2', 'E3', 'C#4', 'E4'], 'Bm': ['B2', 'F#3', 'D4', 'F#4'],
    'G':   ['G2', 'D3', 'B3', 'F#4'], 'Asus': ['A2', 'E3', 'D4', 'E4'], 'Em': ['E3', 'B3', 'D4', 'G4'],
}
haut = {             # notes de l'arpège
    'D': ['D5', 'F#5', 'A5', 'E5'], 'A': ['C#5', 'E5', 'A5', 'B4'], 'Bm': ['B4', 'D5', 'F#5', 'A5'],
    'G': ['B4', 'D5', 'G5', 'F#5'], 'Asus': ['D5', 'E5', 'A5', 'E5'], 'Em': ['B4', 'E5', 'G5', 'D5'],
}
# 19 mesures (47,5 s) : intro, la journée, la soirée, la montée, la résolution
prog = ['D', 'D', 'D', 'A', 'Bm', 'G', 'D', 'A', 'Bm', 'G', 'Em', 'A', 'D', 'G', 'Bm', 'Asus', 'D', 'D', 'D']

for b, ch in enumerate(prog):
    t0 = b * BAR
    if t0 >= DUR: break
    montee = 13.6 <= b < 16          # 34-40 s
    fin = b >= 16
    for j, nm in enumerate(voix[ch] if not (fin and b > 16) else []):
        note(PAD, freq(nm), t0, BAR + 1.6 if not fin else DUR - t0, (0.24 if not montee else 0.28) - j * 0.03,
             0.9 if b else 1.4, 2.4 if not fin else 3.4, pan=(-0.4 + j * 0.27), det=0.003)
    if b < 2:
        # intro : une note de cloche par demi-mesure, très douce
        for s in range(2):
            note(BELL, freq(haut[ch][s * 2]), t0 + s * BAR / 2 + 0.05, 1.8, 0.10, 0.004, 1.1, pan=0.2 - 0.4 * s)
    elif not fin:
        # arpège en croches, puis en doubles croches pendant la montée
        pas = CROCHE / (2 if montee else 1)
        n_pas = int(BAR / pas)
        for s in range(n_pas):
            idx = [0, 1, 2, 1, 3, 2, 1, 2][s % 8]
            amp = 0.075 if not montee else 0.085 + 0.03 * ((t0 + s * pas - 34.0) / 6.0)
            note(PLUCK, freq(haut[ch][idx]), t0 + s * pas, 0.5, amp, 0.002, 0.24 if not montee else 0.18,
                 pan=(-0.3 if s % 2 else 0.3))
    if b >= 5 and not fin:
        note(SUB, freq(voix[ch][0]) / 2, t0, 2.0, 0.17 if not montee else 0.23, 0.03, 1.0)
        if montee:
            note(SUB, freq(voix[ch][0]) / 2, t0 + BAR / 2, 1.2, 0.18, 0.03, 0.7)

# la promesse : l'accord de ré, cloches qui sonnent ensemble à 40 s, et qui résonnent
for j, nm in enumerate(['D4', 'F#4', 'A4', 'E5', 'A5']):
    note(BELL, freq(nm), 40.0 + j * 0.035, DUR - 40.0, 0.12 - j * 0.012, 0.004, 3.2, pan=-0.3 + j * 0.15)
note(SUB, freq('D2'), 40.0, DUR - 40.0, 0.22, 0.05, 3.0)

# repères sonores de l'interface (discrets, au-dessus de la musique)
note(BELL, freq('A5'), 0.55, 1.2, 0.11, 0.003, 0.5, pan=0.35, suit=False)    # notification
note(BELL, freq('D6'), 0.67, 1.4, 0.09, 0.003, 0.6, pan=0.35, suit=False)
clic(8.30, 0.16)                                                                # tap sur « Valider »
note(BELL, freq('F#5'), 9.25, 0.9, 0.08, 0.003, 0.35, pan=0.35, suit=False)    # ✓ Validé
note(BELL, freq('A5'), 9.37, 1.1, 0.08, 0.003, 0.45, pan=0.35, suit=False)
souffle(37.15, 0.85, 0.05)                                                      # l'équipe se replie

peak = max(max(abs(x) for x in L), max(abs(x) for x in R)) or 1.0
k = 0.85 / peak
sortie = os.path.join(ICI, 'musique.wav')
with wave.open(sortie, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b''.join(struct.pack('<hh',
        int(max(-1, min(1, L[i] * k)) * 32000),
        int(max(-1, min(1, R[i] * k)) * 32000)) for i in range(N)))
print('musique.wav écrite : %.0f s, ré majeur, 96 BPM, crête normalisée' % DUR)
