#!/bin/bash
set -e

echo "Running openclaw doctor --fix..."
openclaw doctor --fix || true

echo "Starting openclaw gateway..."
exec openclaw gateway --port 18789
