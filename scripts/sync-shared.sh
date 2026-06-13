#!/usr/bin/env bash
# Sync the shared single-source-of-truth data into the mobile app's assets.
# (Web imports /shared directly via externalDir; Flutter needs it bundled.)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cp "$ROOT/shared/i18n/strings.json" "$ROOT/mobile/assets/i18n/strings.json"
echo "Synced shared/i18n -> mobile/assets/i18n"
