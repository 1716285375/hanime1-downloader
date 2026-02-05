#!/bin/bash
set -e

echo "===================================="
echo " Hanime1 Downloader v1.0 - Setup    "
echo "===================================="
echo ""

# Check uv
echo "[1/5] Checking uv..."
if ! command -v uv &> /dev/null; then
    echo "✗ uv not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
else
    echo "✓ uv is installed"
fi

# Switch dir
echo "[2/5] Switching to project directory..."
if [ -d "hentai" ]; then
    cd hentai
    echo "✓ Switched to hentai directory"
else
    echo "✗ 'hentai' directory not found!"
    exit 1
fi

# Sync
echo ""
echo "[3/5] Syncing project dependencies..."
uv sync
echo "✓ Dependencies synced successfully"

# Playwright
echo ""
echo "[4/5] Installing Playwright browsers..."
uv run playwright install chromium
echo "✓ Playwright browsers installed successfully"

# Dirs
echo ""
echo "[5/5] Creating necessary directories..."
mkdir -p downloads logs database
echo "✓ Directories created"

echo ""
echo "===================================="
echo "      Setup completed!              "
echo "===================================="
echo ""
echo "To start the server, run:"
echo "    ./run.sh"
echo ""
