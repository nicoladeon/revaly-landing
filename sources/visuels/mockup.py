"""Mockup photo : la feuille A4 blanche de la photo reçoit le document rendu, par homographie (4 coins détectés),
avec un mélange multiplicatif qui garde les ombres et le grain du papier.
Usage : mockup.py <photo> <document.png> <sortie.png> [--debug]"""
import sys
import cv2, numpy as np

def coins_feuille(img):
    """Le plus grand quadrilatère clair de la photo (la feuille), coins ordonnés TL, TR, BR, BL."""
    H, W = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    clair = cv2.inRange(hsv, (0, 0, 190), (180, 40, 255))
    clair = cv2.morphologyEx(clair, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    clair = cv2.morphologyEx(clair, cv2.MORPH_OPEN, np.ones((25, 25), np.uint8))
    cnts, _ = cv2.findContours(clair, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # la feuille est entière dans le cadre : on écarte les zones qui touchent le bord (fenêtres, rideaux)
    def dedans(c):
        x, y, w, h = cv2.boundingRect(c)
        return x > 8 and y > 8 and x + w < W - 8 and y + h < H - 8
    cands = [c for c in cnts if dedans(c)] or cnts
    c = max(cands, key=cv2.contourArea)
    peri = cv2.arcLength(c, True)
    for eps in (0.01, 0.02, 0.03, 0.05):
        q = cv2.approxPolyDP(c, eps * peri, True)
        if len(q) == 4: break
    else:
        r = cv2.minAreaRect(c); q = cv2.boxPoints(r)
    q = q.reshape(4, 2).astype(np.float32)
    s = q.sum(1); d = np.diff(q, axis=1).ravel()
    return np.array([q[np.argmin(s)], q[np.argmin(d)], q[np.argmax(s)], q[np.argmax(d)]], np.float32)

def pose(photo, doc, sortie, debug=False, coins=None):
    img = cv2.imread(photo); H, W = img.shape[:2]
    coins_auto = coins is None
    coins = np.float32(coins) if coins is not None else coins_feuille(img)
    d = cv2.imread(doc); h, w = d.shape[:2]
    # la feuille est en portrait : si le quadrilatère détecté est « couché », on tourne les coins
    larg = np.linalg.norm(coins[1] - coins[0]); haut = np.linalg.norm(coins[3] - coins[0])
    if coins_auto and larg > haut * 1.15: coins = np.roll(coins, 1, axis=0)
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), coins)
    doc_w = cv2.warpPerspective(d, M, (W, H), flags=cv2.INTER_AREA, borderValue=(255, 255, 255))
    masque = cv2.warpPerspective(np.full((h, w), 255, np.uint8), M, (W, H))
    masque = cv2.GaussianBlur(masque, (3, 3), 0).astype(np.float32)[..., None] / 255
    # mélange multiplicatif : le document assombrit la feuille (encre), les ombres de la photo restent
    mult = img.astype(np.float32) * (doc_w.astype(np.float32) / 255)
    out = img.astype(np.float32) * (1 - masque) + mult * masque
    cv2.imwrite(sortie, np.clip(out, 0, 255).astype(np.uint8), [cv2.IMWRITE_PNG_COMPRESSION, 6])
    if debug:
        dbg = img.copy(); cv2.polylines(dbg, [coins.astype(np.int32)], True, (0, 0, 255), 4)
        for k, (x, y) in enumerate(coins): cv2.putText(dbg, "TL TR BR BL".split()[k], (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        cv2.imwrite(sortie.replace(".png", "-debug.png"), dbg)
    print(sortie, coins.astype(int).tolist())

if __name__ == "__main__":
    coins = None
    if "--coins" in sys.argv:  # « x,y x,y x,y x,y » : TL TR BR BL, quand la détection se trompe
        coins = [[float(v) for v in pt.split(",")] for pt in sys.argv[sys.argv.index("--coins") + 1].split()]
    pose(sys.argv[1], sys.argv[2], sys.argv[3], "--debug" in sys.argv, coins)
