#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR/backend"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

PORT="${PORT:-8001}"

echo "🚀 Starting ContentGuard on http://localhost:$PORT"
exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload
