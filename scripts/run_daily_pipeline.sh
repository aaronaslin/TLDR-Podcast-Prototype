#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

# Ensure logs directory exists
mkdir -p "data/logs"

PYTHON="$REPO_ROOT/venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Error: Python venv not found at $PYTHON" >&2
  echo "Create it with: python3 -m venv venv && ./venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

LOG_FILE="$REPO_ROOT/data/logs/daily_$(date +%Y-%m-%d).log"

# Timezone-pinned scheduling:
# launchd runs on the machine's local time. When traveling, that would shift.
# Instead, we run this script frequently (via StartInterval) and only execute
# the pipeline when it's TARGET_TIME in TARGET_TZ.
TARGET_TZ="${TARGET_TZ:-America/Los_Angeles}"
TARGET_TIME="${TARGET_TIME:-0645}"  # HHMM in TARGET_TZ

today_tz="$(TZ="$TARGET_TZ" date +%Y-%m-%d)"
now_hhmm="$(TZ="$TARGET_TZ" date +%H%M)"

STATE_FILE="$REPO_ROOT/data/logs/last_success_${TARGET_TZ//\//_}.txt"

if [[ "$now_hhmm" != "$TARGET_TIME" ]]; then
  exit 0
fi

if [[ -f "$STATE_FILE" ]]; then
  last="$(cat "$STATE_FILE" 2>/dev/null || true)"
  if [[ "$last" == "$today_tz" ]]; then
    exit 0
  fi
fi

echo "[$(date -Is)] Starting TLDR Podcast pipeline" >> "$LOG_FILE"
"$PYTHON" main.py >> "$LOG_FILE" 2>&1
echo "[$(date -Is)] Finished TLDR Podcast pipeline" >> "$LOG_FILE"

echo "$today_tz" > "$STATE_FILE"
