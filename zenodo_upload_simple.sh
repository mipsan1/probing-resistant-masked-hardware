#!/bin/bash
# zenodo_upload_simple.sh — minimal curl-only upload to Zenodo
# Step 1: obtain a personal access token at
#   https://zenodo.org/account/settings/applications/tokens/new/
#   (scope: deposit:write, deposit:actions)
# Step 2: export ZENODO_TOKEN=...
# Step 3: run this script
set -eu
BUNDLE_DIR="$(cd "$(dirname "$0")" && pwd)"
ZIP_FILE="${BUNDLE_DIR}/zenodo_data.zip"
METADATA="${BUNDLE_DIR}/zenodo_data/metadata.yaml"
API="https://zenodo.org/api"

[ -z "${ZENODO_TOKEN:-}" ] && { echo "ERROR: set ZENODO_TOKEN env var"; exit 1; }
[ -f "$ZIP_FILE" ] || { echo "ERROR: $ZIP_FILE not found"; exit 1; }
[ -f "$METADATA" ] || { echo "ERROR: $METADATA not found"; exit 1; }

ZIP_SIZE=$(stat -c%s "$ZIP_FILE")
echo "== Uploading: $ZIP_FILE ($ZIP_SIZE bytes) =="

# 1. Create deposition
DEP_ID=$(curl -sS -X POST \
  -H "Authorization: Bearer $ZENODO_TOKEN" \
  "$API/deposit/depositions" \
  -d '{}' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created deposition: $DEP_ID"

# 2. Upload file
echo "Uploading file..."
curl -sS -X POST \
  -H "Authorization: Bearer $ZENODO_TOKEN" \
  -H "Content-Type: application/octet-stream" \
  "$API/deposit/depositions/$DEP_ID/files" \
  --data-binary "@$ZIP_FILE" | python3 -c "import sys, json; r=json.load(sys.stdin); print('OK' if r.get('id') else 'FAIL')"

# 3. Apply metadata
echo "Applying metadata..."
META_JSON=$(python3 -c "
import yaml, json
with open('$METADATA') as f:
    md = yaml.safe_load(f)
md.pop('doi', None)
md['files'] = [{'filename': 'zenodo_data.zip', 'size': $ZIP_SIZE}]
print(json.dumps(md))
")
curl -sS -X PUT \
  -H "Authorization: Bearer $ZENODO_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$META_JSON" \
  "$API/deposit/depositions/$DEP_ID" > /dev/null

echo ""
echo "============================================================"
echo "SUCCESS — Deposition $DEP_ID created as DRAFT"
echo "============================================================"
echo "Edit:    https://zenodo.org/uploads/$DEP_ID"
echo "Publish: curl -X POST -H \"Authorization: Bearer \$ZENODO_TOKEN\" \\"
echo "           $API/deposit/depositions/$DEP_ID/actions/publish"
echo "============================================================"
