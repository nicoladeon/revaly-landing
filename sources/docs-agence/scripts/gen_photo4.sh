#!/bin/zsh
# Une 4e photo (la 2e avait la feuille en losange, inutilisable pour un A4 portrait).
set -e
OUT=/private/tmp/claude-501/-Users-julien/2c656203-82e3-4310-b6cf-7d40d4ccb250/scratchpad/docs-agence/work/photos
set -a; source ~/.config/revaly-film/cles.env; set +a
before=$(curl -s https://ai-gateway.vercel.sh/v1/credits -H "Authorization: Bearer $AI_GATEWAY_API_KEY" | python3 -I -c 'import sys,json;print(json.load(sys.stdin)["balance"])')
P="Editorial still-life photograph, premium real-estate agency mood. A single blank white A4 sheet of paper, completely empty, no text, no logo, no marks, lying flat on a pale oak kitchen table in PORTRAIT orientation: its short edge faces the camera and its long edges run away from the camera, roughly aligned with the frame, seen from about 35 degrees above with slight perspective; the sheet fills roughly 55% of the frame and all four corners are fully visible. Beside it, a folded natural linen napkin and a small white ceramic bowl of green apples, slightly out of focus. Soft morning daylight from a window on the left, gentle shadows, shallow depth of field, subtle paper grain, realistic. No people, no hands, no faces, no text anywhere in the image."
python3 -I - "$P" > "$OUT/req4.json" <<'PY'
import json,sys
print(json.dumps({"model":"openai/gpt-image-2","prompt":sys.argv[1],"size":"1536x1024","quality":"high","n":1}))
PY
curl -s https://ai-gateway.vercel.sh/v1/images/generations -H "Authorization: Bearer $AI_GATEWAY_API_KEY" -H "Content-Type: application/json" --data-binary @"$OUT/req4.json" > "$OUT/resp4.json"
python3 -I - "$OUT/resp4.json" "$OUT/photo4.png" <<'PY'
import json,sys,base64
r=json.load(open(sys.argv[1]))
if "data" not in r: print("ERREUR", json.dumps(r)[:400]); sys.exit(1)
open(sys.argv[2],"wb").write(base64.b64decode(r["data"][0]["b64_json"])); print("ok photo4")
PY
after=$(curl -s https://ai-gateway.vercel.sh/v1/credits -H "Authorization: Bearer $AI_GATEWAY_API_KEY" | python3 -I -c 'import sys,json;print(json.load(sys.stdin)["balance"])')
python3 -I -c "print('coût photo4 :', round(float('$before')-float('$after'),4), '\$ ; solde', '$after')"
