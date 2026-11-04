#!/usr/bin/env bash
# One-time setup on a Linux server (Ubuntu/Debian). Run from inside the uploaded bot folder:
#   cd ~/nhl-propsbot && bash deploy/setup_server.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_USER="$(id -un)"

echo "==> Installing Python and setting the clock to Swedish time"
sudo apt-get update -y
sudo apt-get install -y python3 tzdata
sudo timedatectl set-timezone Europe/Stockholm

PY_OK=$(python3 -c 'import sys; print(int(sys.version_info >= (3, 10)))')
if [ "$PY_OK" != "1" ]; then
  echo "Python 3.10+ is required (found $(python3 --version)). Use Ubuntu 22.04 or newer." >&2
  exit 1
fi

if [ ! -f "$APP_DIR/.env" ] && [ -z "${ODDS_API_KEY:-}" ]; then
  echo "NOTE: no .env with ODDS_API_KEY found. US-book references will be off until you add one:"
  echo "      echo 'ODDS_API_KEY=your_key' > $APP_DIR/.env"
fi

echo "==> Checking that the odds sources are reachable from this server"
cd "$APP_DIR"
python3 -m propsbot kambi-probe | head -n 4 || true
python3 - <<'PY'
from propsbot.bot_settings import BotSettings
from propsbot.config import Settings
from propsbot.http import JsonClient
from propsbot.sources.pinnacle import PinnacleClient
s = BotSettings.load()
if s.use_pinnacle:
    try:
        games = PinnacleClient(JsonClient(Settings().cache_dir), s.pinnacle_api_key, s.pinnacle_league_id).games()
        print(f"Pinnacle: OK ({len(games)} NHL games)")
    except Exception as exc:
        print(f"Pinnacle: NOT reachable from this server ({exc}). Pick a Swedish/Nordic server location.")
PY

echo "==> Installing the background service"
sed -e "s|__USER__|$APP_USER|" -e "s|__DIR__|$APP_DIR|" "$APP_DIR/deploy/nhl-propsbot.service" \
  | sudo tee /etc/systemd/system/nhl-propsbot.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now nhl-propsbot

echo
echo "Done. The bot now runs 24/7 and restarts itself after crashes and reboots."
echo "  Live log:   journalctl -u nhl-propsbot -f"
echo "  Status:     systemctl status nhl-propsbot"
echo "  Restart:    sudo systemctl restart nhl-propsbot   (after editing settings.json)"
