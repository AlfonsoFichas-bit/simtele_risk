#!/usr/bin/env bash
# Builds the frontend and collects Django's static files.
# Usage: ./build.sh
set -e

cd "$(dirname "$0")"

if command -v bun >/dev/null 2>&1; then
    echo "==> Using Bun"
    bun install
    bun run build
else
    echo "==> Bun not available; using npm"
    npm install
    npm run build
fi

echo "==> collectstatic"
python manage.py collectstatic --noinput
echo "==> Build complete"
