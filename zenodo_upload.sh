#!/bin/bash
# zenodo_upload.sh — Upload the IEEE TIFS data bundle to Zenodo
# Usage:  ./zenodo_upload.sh
# Prereq: a Zenodo personal access token in $ZENODO_TOKEN
#         (get one at https://zenodo.org/account/settings/applications/tokens/new/
#          with scope "deposit:write deposit:actions")
# Result: prints the new Zenodo DOI on success
set -eu

ZENODO_API="https://zenodo.org/api"
BUNDLE_DIR="$(cd "$(dirname "$0")" && pwd)"
ZIP_FILE="${BUNDLE_DIR}/zenodo_data.zip"
METADATA="${BUNDLE_DIR}/zenodo_data/metadata.yaml"
ZENODO_TOKEN="${ZENODO_TOKEN:-}"

if [ -z "$ZENODO_TOKEN" ]; then
  echo "ERROR: ZENODO_TOKEN environment variable is not set."
  echo "       Create a personal token at:"
  echo "       https://zenodo.org/account/settings/applications/tokens/new/"
  echo "       Scope: deposit:write + deposit:actions"
  echo "       Then: export ZENODO_TOKEN=...; $0"
  exit 1
fi

if [ ! -f "$ZIP_FILE" ]; then
  echo "ERROR: $ZIP_FILE not found. Run the bundle-build step first."
  exit 1
fi

# Compute zip size and sha256 for the metadata
ZIP_SIZE=$(stat -c%s "$ZIP_FILE" 2>/dev/null || stat -f%z "$ZIP_FILE")
ZIP_SHA=$(sha256sum "$ZIP_FILE" | awk '{print $1}')

echo "============================================================"
echo "Zenodo upload — IEEE TIFS masked-AES data bundle"
echo "============================================================"
echo "  File:     $ZIP_FILE"
echo "  Size:     $ZIP_SIZE bytes ($((ZIP_SIZE/1024/1024)) MB)"
echo "  SHA-256:  $ZIP_SHA"
echo "  Metadata: $METADATA"
echo "============================================================"

# 1. Create a new deposition
echo ""
echo "[1/3] Creating deposition..."
DEPOSITION=$(curl -s -X POST \
  -H "Authorization: Bearer ${ZENODO_TOKEN}" \
  -H "Content-Type: application/json" \
  "${ZENODO_API}/deposit/depositions" \
  -d '{}')
DEP_ID=$(echo "$DEPOSITION" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "  Deposition ID: $DEP_ID"

# 2. Upload the file
echo ""
echo "[2/3] Uploading $ZIP_FILE ..."
UPLOAD=$(curl -s -X POST \
  -H "Authorization: Bearer ${ZENODO_TOKEN}" \
  -H "Content-Type: application/octet-stream" \
  "${ZENODO_API}/deposit/depositions/${DEP_ID}/files" \
  --data-binary "@${ZIP_FILE}")
FILE_ID=$(echo "$UPLOAD" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
FILE_LINK=$(echo "$UPLOAD" | python3 -c "import sys, json; print(json.load(sys.stdin).get('links',{}).get('self',''))")
echo "  File uploaded: $FILE_LINK"

# 3. Apply metadata from metadata.yaml
echo ""
echo "[3/3] Applying metadata..."
# Convert metadata.yaml to JSON using python (since zenodo wants JSON payload)
# Or use a minimal JSON payload directly here. We use python to do the conversion.
python3 - "$METADATA" "$ZIP_SIZE" "$ZIP_SHA" <<'PYEOF'
import sys, json, yaml, urllib.request, os
metadata_path, zip_size, zip_sha = sys.argv[1], int(sys.argv[2]), sys.argv[3]
with open(metadata_path) as fp:
    md = yaml.safe_load(fp)
md.pop("files", None)
md["doi"] = ""  # Let Zenodo assign
# Note: Zenodo does not take 'doi' as part of the metadata patch; the doi is generated
# upon publish. Setting empty avoids the API complaining.
if "doi" in md:
    del md["doi"]
# Add file size
md["files"] = [{"filename": "zenodo_data.zip", "size": zip_size}]
# Send
url = f"https://zenodo.org/api/deposit/depositions/{os.environ['DEP_ID']}"
body = json.dumps(md).encode("utf-8")
req = urllib.request.Request(url, data=body, method="PUT",
                              headers={"Authorization": f"Bearer {os.environ['ZENODO_TOKEN']}",
                                       "Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    print("  Metadata response:", resp.status)
PYEOF

# 4. (Optional) Publish immediately, or save as draft for manual review
#    Uncomment the next block to auto-publish:
# curl -s -X POST -H "Authorization: Bearer ${ZENODO_TOKEN}" \
#   "${ZENODO_API}/deposit/depositions/${DEP_ID}/actions/publish" \
#   | python3 -c "import sys, json; d = json.load(sys.stdin); print('DOI:', d.get('doi')); print('URL:', d.get('links',{}).get('record_html',''))"

echo ""
echo "============================================================"
echo "DEPOSITION CREATED — review before publishing"
echo "============================================================"
echo "  Deposition ID:  $DEP_ID"
echo "  Edit metadata:  ${ZENODO_API}/deposit/depositions/${DEP_ID}"
echo "  Edit in browser: https://zenodo.org/uploads/${DEP_ID}"
echo "  Publish:        ${ZENODO_API}/deposit/depositions/${DEP_ID}/actions/publish"
echo "============================================================"
echo ""
echo "To publish and obtain the DOI, run:"
echo "  curl -s -X POST -H \"Authorization: Bearer \${ZENODO_TOKEN}\" \\"
echo "    \"${ZENODO_API}/deposit/depositions/${DEP_ID}/actions/publish\""
echo ""
echo "After publish, the DOI will be printed and is of the form:"
echo "  10.5281/zenodo.XXXXXXX"
