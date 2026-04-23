#!/usr/bin/env bash
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$SKILL_ROOT"

echo "Installing design-artifact skill dependencies..."

npm install --no-audit --no-fund

echo "Installing Playwright Chromium browser..."

npx playwright install chromium

echo "design-artifact skill setup complete."
