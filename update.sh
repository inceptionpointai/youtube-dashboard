#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# YouTube API key
YT_KEY=$(cat /home/ubuntu/clawd/.secrets/youtube.json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('api_key',''))" 2>/dev/null)
if [ -z "$YT_KEY" ]; then
  echo "ERROR: No YouTube API key found"
  exit 1
fi

echo "Fetching YouTube data..."
python3 fetch_data.py "$YT_KEY" > data.json
echo "Generating dashboard..."
python3 generate_html.py data.json > index.html
echo "Done. Dashboard updated at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
