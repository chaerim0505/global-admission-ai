#!/usr/bin/env bash
# Start the backend (FastAPI :8001) and the screen (Streamlit :8501) together.
# Usage:  bash scripts/run_local.sh      Stop: Ctrl + C (stops both)
set -e
cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/python ]; then
  echo "Creating .venv ..."
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install -q -r requirements.txt streamlit openpyxl

# Free the ports if an old run is still holding them.
lsof -ti :8001 | xargs kill -9 2>/dev/null || true
lsof -ti :8501 | xargs kill -9 2>/dev/null || true

PYTHONPATH=src python -m uvicorn admission.main:app --port 8001 > /tmp/admission-backend.log 2>&1 &
BACKEND=$!
trap 'kill $BACKEND 2>/dev/null' EXIT

for i in $(seq 1 30); do
  if curl -s http://127.0.0.1:8001/health >/dev/null; then break; fi
  sleep 1
done
if ! curl -s http://127.0.0.1:8001/health >/dev/null; then
  echo "Backend did not start. Last lines of the log:"
  tail -30 /tmp/admission-backend.log
  exit 1
fi
echo "Backend OK  -> http://127.0.0.1:8001/health"
echo "Backend log -> /tmp/admission-backend.log"

API_BASE_URL=http://127.0.0.1:8001 python -m streamlit run frontend/app.py
