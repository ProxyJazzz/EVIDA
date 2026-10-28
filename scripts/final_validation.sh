#!/usr/bin/env bash
set -e

echo "=================================================="
echo "          EVIDA FINAL VALIDATION SUITE            "
echo "        AI proposes. Evidence decides.            "
echo "=================================================="

# Determine project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo ""
echo "[1/7] Running backend test suite (pytest)..."
apps/api/.venv/bin/pytest

echo ""
echo "[2/7] Running Python linter (ruff check)..."
apps/api/.venv/bin/ruff check .

echo ""
echo "[3/7] Verifying Python code formatting (ruff format --check)..."
apps/api/.venv/bin/ruff format --check .

echo ""
echo "[4/7] Running static type checker (mypy)..."
apps/api/.venv/bin/mypy apps/api/app

echo ""
echo "[5/7] Running frontend test suite (vitest)..."
npm --prefix apps/web test

echo ""
echo "[6/7] Running frontend linter (next lint)..."
npm --prefix apps/web run lint

echo ""
echo "[7/7] Verifying frontend production build (next build)..."
npm --prefix apps/web run build

echo ""
echo "=================================================="
echo "    ALL 7 EVIDA QUALITY GATES PASSED (100%)       "
echo "  System is production hardened and demo-ready!   "
echo "=================================================="

