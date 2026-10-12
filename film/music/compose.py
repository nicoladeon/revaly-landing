# -*- coding: utf-8 -*-
"""Musique originale du film Revaly (page de vente v3) — synthèse additive, Python pur,
puis une réverbération et un peu d'aigu passés par ffmpeg.

Adaptée de ~/kwestim-video/film/music/compose.py (même moteur à tables d'onde).
Ré majeur lumineux, 96 BPM (mesure de 2,5 s). Trois fonds, un par montage, écrits
sur leurs propres repères (aucune coupe au milieu d'une mesure) :
  film  : 47 s (le film de 45 s s'efface à 44,3 s dans mux.sh)
  pub30 : la pub verticale de 30 s
  pub15 : la pub carrée de 15 s
Dans chaque fond : la notification (deux notes de cloche), le tap sur « Valider »
(un clic doux), « ✓ Validé » (deux notes qui montent), la montée sur « ce que voient
tes clients » (arpèges en doubles croches, basse qui pulse), un souffle au repli de
l'équipe, puis l'accord de ré qui résonne sous l'écran de fin.
Pour un haut-parleur de téléphone : la mélodie vit entre 500 Hz et 4 kHz (arpèges,
cloches, une doublure à l'octave) ; la basse tient sans trou d'une mesure à l'autre.
Aucun échantillon, aucune licence en jeu.
Usage : python3 film/music/compose.py [film|pub30|pub15|tout]   (tout par défaut)
  → film/music/musique.wav, musique-pub30.wav, musique-pub15.wav (48 kHz, stéréo, 16 bits)
"""
import math, os, random, struct, subprocess, sys, tempfile, wave
from array import array

SR, TBL = 48000, 4096
ICI = os.path.dirname(os.path.abspath(__file__))
BAR = 2.5            # 96 BPM, 4 temps
CROCHE = BAR / 8

# Repères de chaque montage (secondes du montage). Pubs : voir film/pubs.sh.
PLANS = {
    'film':  dict(dur=47.0, intro=5.0, notif=0.55, tap=8.30, valide=9.25, montee=34.0, repli=38.6, fin=40.0, sortie='musique.wav'),
    'pub30': dict(dur=30.0, intro=1.25, notif=0.05, tap=4.70, valide=5.65, montee=20.967, repli=25.567, fin=26.967, sortie='musique-pub30.wav'),
    'pub15': dict(dur=15.0, intro=1.25, notif=0.05, tap=3.40, valide=4.35, montee=5.1, repli=9.7, fin=11.1, sortie='musique-pub15.wav'),
}

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

# timbres : nappe douce mais ouverte, cloche claire, sub rond, pincé brillant
PAD = table([(1, 1.0), (2, 0.42), (3, 0.24), (4, 0.12), (5, 0.07), (6, 0.04)])
BELL = table([(1, 1.0), (2, 0.55), (3, 0.32), (4, 0.2), (5, 0.1), (6, 0.08), (8, 0.05)])
SUB = table([(1, 1.0), (2, 0.18), (3, 0.05)])
PLUCK = table([(1, 1.0), (2, 0.7), (3, 0.45), (4, 0.28), (5, 0.18), (6, 0.1), (7, 0.07), (9, 0.03)])

VOIX = {   # nappe : basse + voix au médium (audible au téléphone)
    'D': ['D3', 'A3', 'F#4', 'A4'], 'A': ['A2', 'E3', 'C#4', 'E4'], 'Bm': ['B2', 'F#3', 'D4', 'F#4'],
    'G': ['G2', 'D3', 'B3', 'D4'], 'Asus': ['A2', 'E3', 'D4', 'E4'], 'Em': ['E3', 'B3', 'D4', 'G4'],
}
HAUT = {   # arpèges
    'D': ['D5', 'F#5', 'A5', 'E5'], 'A': ['C#5', 'E5', 'A5', 'B4'], 'Bm': ['B4', 'D5', 'F#5', 'A5'],
    'G': ['B4', 'D5', 'G5', 'F#5'], 'Asus': ['D5', 'E5', 'A5', 'E5'], 'Em': ['B4', 'E5', 'G5', 'D5'],
}
CORPS = ['D', 'D', 'A', 'Bm', 'G', 'D', 'A', 'Bm', 'G', 'Em', 'A', 'D', 'G', 'Bm', 'Em', 'A']
MONTEE = ['G', 'A', 'Bm', 'G', 'A', 'Asus', 'G', 'A', 'Bm', 'Asus']


def composer(p):
    dur = p['dur']; N = int(SR * dur)
    L = array('f', bytes(4 * N)); R = array('f', bytes(4 * N))
    m0, fin = p['montee'], p['fin']

    def gain(t):
        if t < p['intro']: g = 0.5 + 0.1 * (t / max(p['intro'], 0.01))
        elif t < m0: g = 0.62
        elif t < fin: g = 0.62 + 0.38 * ((t - m0) / (fin - m0)) ** 1.3          # la montée
        else: g = 1.0
        return g * min(1.0, (dur - t) / 0.6)                                        # fondu final

    def note(tbl, f, start, d, amp, atk, tau, pan=0.0, det=0.0, suit=True):
        i0 = int(start * SR); n = min(int(d * SR), N - i0)
        if i0 < 0 or n <= 0: return
        gl = amp * math.sqrt((1 - pan) / 2 + 0.5); gr = amp * math.sqrt((1 + pan) / 2 + 0.5)
        ai = max(1, int(atk * SR)); rel = int(0.08 * SR)
        for buf, g, dd in ((L, gl, 0.0), (R, gr, det)):
            step = (f * (1 + dd)) * TBL / SR; ph = 0.0
            for k in range(n):
                e = (k / ai) if k < ai else math.exp(-(k - ai) / (tau * SR))
                if k > n - rel: e *= (n - k) / rel
                if e < 0.0005 and k > ai: break
                buf[i0 + k] += tbl[int(ph) & (TBL - 1)] * e * g * (gain((i0 + k) / SR) if suit else 1.0)
                ph += step

    def souffle(start, d, amp):
        i0, n = int(start * SR), int(d * SR); y = 0.0
        for k in range(min(n, N - i0)):
            y += 0.06 * (random.uniform(-1, 1) - y)
            e = math.sin(math.pi * k / n) ** 2
            L[i0 + k] += y * e * amp; R[i0 + k] += y * e * amp * 0.9

    def clic(start, amp):
        i0, n = int(start * SR), int(0.009 * SR); y = 0.0
        for k in range(n):
            y += 0.35 * (random.uniform(-1, 1) - y)
            e = math.exp(-k / (0.002 * SR))
            L[i0 + k] += y * e * amp; R[i0 + k] += y * e * amp
        note(BELL, freq('A5'), start, 0.12, amp * 0.3, 0.001, 0.03, suit=False)

    # --- l'enchaînement des accords : mesures de 2,5 s, puis des demi-mesures dans la montée
    segs, t, i = [], 0.0, 0
    while t < m0 - 1e-6:
        d = min(BAR, m0 - t); segs.append((t, d, CORPS[i % len(CORPS)], 'corps')); t += d; i += 1
    i = 0
    while t < fin - 1e-6:
        d = min(BAR / 2, fin - t); segs.append((t, d, MONTEE[i % len(MONTEE)], 'montee')); t += d; i += 1
    segs.append((fin, dur - fin, 'D', 'fin'))

    for t0, d, ch, sec in segs:
        # nappe : se tuile d'un accord à l'autre (attaque courte, queue longue)
        for j, nm in enumerate(VOIX[ch]):
            note(PAD, freq(nm), t0, d + 1.2, (0.1 if j == 0 else 0.14) * (1.12 if sec == 'montee' else 1), 0.35, 2.6 if sec != 'fin' else 3.6,
                 pan=(-0.45 + j * 0.3), det=0.003)
        # basse continue : pas de trou d'une mesure à l'autre
        note(SUB, freq(VOIX[ch][0]) / 2, t0, d + 0.25, 0.1 if sec != 'montee' else 0.12, 0.04, 6.0)
        if sec == 'fin':
            continue
        if t0 < p['intro'] and sec == 'corps':
            for s in range(int(round(d / (BAR / 2)))):      # intro : une cloche par demi-mesure
                note(BELL, freq(HAUT[ch][s * 2 % 4]), t0 + s * BAR / 2 + 0.05, 1.8, 0.16, 0.004, 1.1, pan=0.2 - 0.4 * (s % 2))
            continue
        pas = CROCHE / (2 if sec == 'montee' else 1)
        for s in range(int(round(d / pas))):
            ts = t0 + s * pas
            idx = [0, 1, 2, 1, 3, 2, 1, 2][s % 8]
            amp = 0.2 if sec == 'corps' else 0.21 + 0.06 * ((ts - m0) / (fin - m0))
            f = freq(HAUT[ch][idx])
            note(PLUCK, f, ts, 0.5, amp, 0.002, 0.26 if sec == 'corps' else 0.18, pan=(-0.3 if s % 2 else 0.3))
            note(PLUCK, 2 * f, ts + 0.006, 0.3, amp * 0.38, 0.002, 0.12, pan=(0.35 if s % 2 else -0.35))   # doublure
        if sec == 'montee':
            note(SUB, freq(VOIX[ch][0]) / 2, t0, 0.5, 0.07, 0.01, 0.25)                                   # la basse pulse

    # la promesse : l'accord de ré en cloches, qui résonne
    for j, nm in enumerate(['D4', 'F#4', 'A4', 'E5', 'A5', 'D6']):
        note(BELL, freq(nm), fin + j * 0.035, dur - fin, 0.16 - j * 0.014, 0.004, 3.0, pan=-0.35 + j * 0.14)
    # repères sonores de l'interface (au-dessus de la musique)
    note(BELL, freq('A5'), p['notif'], 1.2, 0.12, 0.003, 0.5, pan=0.35, suit=False)
    note(BELL, freq('D6'), p['notif'] + 0.12, 1.4, 0.1, 0.003, 0.6, pan=0.35, suit=False)
    clic(p['tap'], 0.17)
    note(BELL, freq('F#5'), p['valide'], 0.9, 0.09, 0.003, 0.35, pan=0.35, suit=False)
    note(BELL, freq('A5'), p['valide'] + 0.12, 1.1, 0.09, 0.003, 0.45, pan=0.35, suit=False)
    souffle(p['repli'] - 0.25, 0.85, 0.05)
    return L, R


def ecrire(path, L, R, crete=0.85):
    peak = max(max(abs(x) for x in L), max(abs(x) for x in R)) or 1.0
    k = crete / peak
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b''.join(struct.pack('<hh', int(max(-1, min(1, L[i] * k)) * 32000),
                                           int(max(-1, min(1, R[i] * k)) * 32000)) for i in range(len(L))))


def reponse_salle(path, duree=1.8, tau=0.3):
    """Réponse impulsionnelle d'une petite salle claire : bruit qui décroît, un
    peu assombri, différent à gauche et à droite (espace stéréo)."""
    n = int(duree * SR); pre = int(0.014 * SR)
    L = array('f', bytes(4 * n)); R = array('f', bytes(4 * n))
    for buf in (L, R):
        y = 0.0
        for k in range(pre, n):
            t = (k - pre) / SR
            y += 0.45 * (random.uniform(-1, 1) - y)
            buf[k] = y * math.exp(-t / tau)
    ecrire(path, L, R, crete=0.5)


def main(noms):
    random.seed(12102026)
    with tempfile.TemporaryDirectory() as tmp:
        ir = os.path.join(tmp, 'salle.wav'); reponse_salle(ir)
        for nom in noms:
            p = PLANS[nom]
            L, R = composer(p)
            sec = os.path.join(tmp, nom + '-sec.wav'); ecrire(sec, L, R)
            sortie = os.path.join(ICI, p['sortie'])
            # son direct et 30 % de salle ; +5 dB au-dessus de 4 kHz ; rien sous 35 Hz
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', sec, '-i', ir, '-filter_complex',
                            '[0:a]asplit=2[d][w];[w][1:a]afir=gtype=peak:wet=1[r];[d][r]amix=inputs=2:weights=1 0.3:normalize=0,'
                            'treble=g=5:f=4000,highpass=f=35,atrim=0:%.3f,alimiter=limit=0.89:level=false' % p['dur'],
                            '-ar', str(SR), '-c:a', 'pcm_s16le', sortie], check=True)
            print('%s écrite : %.1f s, ré majeur, 96 BPM' % (p['sortie'], p['dur']))


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else 'tout'
    main(list(PLANS) if arg == 'tout' else [arg])
