#!/usr/bin/env bash
set -euo pipefail

VERSION=${1:-0.1.0}
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
DIST_DIR="$PROJECT_ROOT/dist"
WHEEL="$DIST_DIR/nicemail-$VERSION-py3-none-any.whl"

if ! command -v fpm >/dev/null 2>&1; then
  echo "fpm is required. Install with: gem install --user-install fpm" >&2
  exit 1
fi

python -m build --wheel

if [ ! -f "$WHEEL" ]; then
  echo "Expected wheel $WHEEL not found. Check the version argument." >&2
  exit 2
fi

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

python -m pip install "$WHEEL" --prefix "$WORKDIR/usr" --no-compile --no-deps
install -Dm755 "$PROJECT_ROOT/scripts/nicemail-launcher" "$WORKDIR/usr/bin/nicemail"
install -Dm644 "$PROJECT_ROOT/assets/nicemail.desktop" "$WORKDIR/usr/share/applications/nicemail.desktop"
install -Dm644 "$PROJECT_ROOT/assets/icon.svg" "$WORKDIR/usr/share/icons/hicolor/scalable/apps/nicemail.svg"

fpm -s dir -t deb -n nicemail -v "$VERSION" \
  --depends "python3 (>= 3.11)" \
  --depends "python3-pyside6" \
  --depends "python3-httpx" \
  --description "Friendly email client for seniors" \
  --vendor "NiceMail" \
  --license "MIT" \
  -C "$WORKDIR" .

mkdir -p "$DIST_DIR"
mv nicemail_${VERSION}_amd64.deb "$DIST_DIR" 2>/dev/null || mv nicemail_${VERSION}_all.deb "$DIST_DIR" 2>/dev/null || true

echo "Debian package ready in $DIST_DIR"
