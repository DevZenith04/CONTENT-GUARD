#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR/backend"

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate

if ! python -c "import fastapi, transformers, torch" 2>/dev/null; then
  pip install -r requirements.txt
fi

PORT="${PORT:-8001}"
echo "🚀 Starting ContentGuard on http://localhost:$PORT"
exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload
