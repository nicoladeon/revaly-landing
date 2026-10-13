#!/bin/zsh
# Génère 3 photos éditoriales (feuille A4 blanche vierge) avec openai/gpt-image-2
# via le Vercel AI Gateway. Corps JSON (jamais curl -F). Plafond : 1,50 $.
set -e
OUT=/private/tmp/claude-501/-Users-julien/2c656203-82e3-4310-b6cf-7d40d4ccb250/scratchpad/docs-agence/work/photos
mkdir -p "$OUT"
set -a; source ~/.config/revaly-film/cles.env; set +a

before=$(curl -s https://ai-gateway.vercel.sh/v1/credits -H "Authorization: Bearer $AI_GATEWAY_API_KEY" | python3 -I -c 'import sys,json;print(json.load(sys.stdin)["balance"])')
echo "solde avant : $before"

COMMON="Editorial still-life photograph, premium real-estate agency mood. A single blank white A4 sheet of paper, completely empty, no text, no logo, no marks, lying flat with a slight perspective (camera about 35 degrees above, sheet occupying roughly 60% of the frame, all four corners of the sheet fully visible inside the frame). Natural daylight from a window, soft shadows, shallow depth of field, subtle paper grain, realistic. No people, no hands, no faces, no text anywhere in the image."

PROMPTS=(
"$COMMON Setting: a light oak wooden desk, a fountain pen with a dark green cap resting beside the sheet, a small ceramic cup of espresso slightly out of focus in the background, warm morning light."
"$COMMON Setting: a bright kitchen table in pale wood, a glass of water and a small sprig of eucalyptus in a ceramic vase in the soft background, cool diffused daylight, airy Scandinavian interior."
"$COMMON Setting: a light birch desk near a window, a pair of tortoiseshell reading glasses and a closed linen notebook beside the sheet, a leafy plant blurred in the background, late-afternoon golden light."
)

i=0
for p in "${PROMPTS[@]}"; do
  i=$((i+1))
  python3 -I - "$p" > "$OUT/req$i.json" <<'PY'
import json,sys
print(json.dumps({"model":"openai/gpt-image-2","prompt":sys.argv[1],"size":"1536x1024","quality":"high","n":1}))
PY
  curl -s https://ai-gateway.vercel.sh/v1/images/generations \
    -H "Authorization: Bearer $AI_GATEWAY_API_KEY" -H "Content-Type: application/json" \
    --data-binary @"$OUT/req$i.json" > "$OUT/resp$i.json"
  python3 -I - "$OUT/resp$i.json" "$OUT/photo$i.png" <<'PY'
import json,sys,base64,urllib.request
r=json.load(open(sys.argv[1]))
if "data" not in r:
    print("ERREUR", json.dumps(r)[:400]); sys.exit(1)
d=r["data"][0]
if d.get("b64_json"):
    open(sys.argv[2],"wb").write(base64.b64decode(d["b64_json"]))
else:
    urllib.request.urlretrieve(d["url"], sys.argv[2])
print("ok", sys.argv[2], r.get("usage"))
PY
done

after=$(curl -s https://ai-gateway.vercel.sh/v1/credits -H "Authorization: Bearer $AI_GATEWAY_API_KEY" | python3 -I -c 'import sys,json;print(json.load(sys.stdin)["balance"])')
echo "solde après : $after"
python3 -I -c "print('coût photos :', round(float('$before')-float('$after'),4), '\$')"
