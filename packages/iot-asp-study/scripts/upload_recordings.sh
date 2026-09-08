#!/usr/bin/env bash
# Upload local MediaRecorder exports to a *private* recordings bucket.
# Bucket name from IOT_ASP_GCS_BUCKET (no gs://) — never hardcode a private URI.
set -euo pipefail

ACCOUNT="${GCLOUD_ACCOUNT:-betty@bearresearch.io}"
PROJECT="${GOOGLE_CLOUD_PROJECT:-bear-iot-asp-rec}"
BUCKET_NAME="${IOT_ASP_GCS_BUCKET:?set IOT_ASP_GCS_BUCKET to the private bucket name (no gs://)}"
# Strip accidental gs:// prefix if an operator pastes a URI.
BUCKET_NAME="${BUCKET_NAME#gs://}"
BUCKET_NAME="${BUCKET_NAME%%/*}"
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

DEST="gs://${BUCKET_NAME}/${NODE}/${DAY}/"
echo "Uploading $SRC -> $DEST (private bucket; public access prevention)"
# Command-scoped flags only — do not mutate the caller's active gcloud config.
gcloud --account="$ACCOUNT" --project="$PROJECT" storage cp -r "${SRC%/}/"* "$DEST"
echo "Done. List with: gcloud --account=$ACCOUNT --project=$PROJECT storage ls $DEST"
