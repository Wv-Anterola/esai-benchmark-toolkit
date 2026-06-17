#!/usr/bin/env bash
# One-shot setup: creates a virtualenv, installs deps, and checks for the workbook.
# Usage:  bash setup.sh
set -e

echo "==> Creating virtual environment (.venv)"
python -m venv .venv

# Activate (works on macOS/Linux; on Windows use: .venv\Scripts\activate)
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
elif [ -f .venv/Scripts/activate ]; then
  source .venv/Scripts/activate
fi

echo "==> Installing requirements"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

mkdir -p data outputs

if ls data/*.xlsx >/dev/null 2>&1; then
  echo "==> Found a workbook in data/. You're ready."
else
  echo "==> NOTE: drop your ESAI workbook export (.xlsx) into ./data/ before running the tools."
fi

echo ""
echo "Done. Next:"
echo "  python tools/workbook_health_check.py     # integrity + coverage audit"
echo "  python tools/coverage_gap_dashboard.py    # gap dashboard -> outputs/gap_analysis/index.html"
