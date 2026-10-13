#!/usr/bin/env bash
set -euo pipefail
for tool in git python3 claude; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "Fehlt: $tool. Voraussetzungen: https://github.com/simon-schaeferai/claude-brand-kit/blob/main/SETUP.md" >&2
    exit 1
  }
done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || {
  echo 'Python 3.10 oder neuer erforderlich.' >&2; exit 1;
}
brand_setup_tmp=$(mktemp -d)
trap 'rm -rf "$brand_setup_tmp"' EXIT
git clone --quiet --depth 1 https://github.com/simon-schaeferai/claude-brand-kit.git "$brand_setup_tmp/repo"
brand_setup_home=${BRAND_SETUP_HOME:-"$HOME"}
python3 "$brand_setup_tmp/repo/scripts/install.py" skill --source "$brand_setup_tmp/repo" --home "$brand_setup_home"
if [[ $# -gt 0 ]]; then
  brand_setup_url=$1
else
  printf 'Deine eigene Website (https://…): ' >/dev/tty
  IFS= read -r brand_setup_url </dev/tty
fi
python3 - "$brand_setup_url" <<'PY'
import sys
from urllib.parse import urlsplit
u = urlsplit(sys.argv[1])
if u.scheme not in {'http', 'https'} or not u.hostname or u.username or u.password or any(c.isspace() for c in sys.argv[1]):
    sys.exit('Bitte eine öffentliche HTTP(S)-URL ohne Zugangsdaten angeben.')
PY
mkdir -p "$brand_setup_home/brand-work"
cd "$brand_setup_home/brand-work"
claude "/brand-setup $brand_setup_url"
