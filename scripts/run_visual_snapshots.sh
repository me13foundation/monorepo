#!/usr/bin/env bash

# Run Percy visual regression snapshots against the static Next.js export.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="$ROOT_DIR/src/web"
PORT="${PERCY_STATIC_PORT:-4173}"

if [ -z "${PERCY_TOKEN:-}" ]; then
    echo "❌ PERCY_TOKEN is not set. Visual snapshots require a Percy project token."
    exit 1
fi

echo "▶ Building Next.js application..."
(cd "$WEB_DIR" && npm run build >/dev/null)

echo "▶ Exporting static assets..."
(cd "$WEB_DIR" && npx next export >/dev/null)

echo "▶ Serving exported site on port ${PORT}..."
pushd "$WEB_DIR/out" >/dev/null
python3 -m http.server "$PORT" >/tmp/percy-static-server.log 2>&1 &
SERVER_PID=$!
popd >/dev/null

cleanup() {
    if ps -p $SERVER_PID >/dev/null 2>&1; then
        kill $SERVER_PID
    fi
}
trap cleanup EXIT

echo "▶ Capturing Percy snapshots..."
(cd "$WEB_DIR" && npx percy snapshot percy-snapshots.yml --base-url "http://localhost:${PORT}")

echo "✅ Visual regression snapshots complete."
