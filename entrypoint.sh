#!/usr/bin/env bash
set -euo pipefail

# Simple container entrypoint: requires TWITCH_CHANNEL env var
if [ -z "${TWITCH_CHANNEL:-}" ]; then
  echo "Environment variable TWITCH_CHANNEL is required"
  exit 2
fi

OUT_DIR=/out
mkdir -p "$OUT_DIR"

python prototype.py --channel "$TWITCH_CHANNEL" --out "$OUT_DIR/out.mp4" --model "small"
