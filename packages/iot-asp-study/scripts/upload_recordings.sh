#!/usr/bin/env bash
# Upload local MediaRecorder exports to a *private* recordings bucket.
# Bucket MUST come from the environment — never hardcode a private gs:// URI here.
set -euo pipefail

ACCOUNT="${GCLOUD_ACCOUNT:-betty@bearresearch.io}"
PROJECT="${GCP_PROJECT:-bear-iot-asp-rec}"
BUCKET="${GCS_BUCKET:?set GCS_BUCKET to gs://YOUR_PRIVATE_BUCKET (from private IoT-ASP-study)}"
SRC="${1:?usage: upload_recordings.sh <local-dir> [node1|node2|node3]}"
NODE="${2:-node1}"
DAY="$(date -u +%Y%m%d)"

case "$NODE" in
  node1|node2|node3) ;;
  *) echo "node must be node1|node2|node3" >&2; exit 2 ;;
esac

if [[ ! -d "$SRC" ]]; then
  echo "not a directory: $SRC" >&2
  exit 2
fi

gcloud config set account "$ACCOUNT" >/dev/null
gcloud config set project "$PROJECT" >/dev/null

DEST="${BUCKET%/}/${NODE}/${DAY}/"
echo "Uploading $SRC -> $DEST (private bucket; public access prevention)"
gcloud storage cp -r "${SRC%/}/"* "$DEST"
echo "Done. List with: gcloud storage ls $DEST"
