#!/usr/bin/env bash
set -e

echo "🐕 Installing Watchdog TUI..."

# Check if pipx is available (recommended for isolated global install)
if command -v pipx >/dev/null 2>&1; then
    echo "📦 Using pipx for installation..."
    pipx install --force .
    echo "✅ Watchdog installed successfully! Run 'watchdog' to start."
    exit 0
fi

# Fallback to pip install --user
if command -v python3 >/dev/null 2>&1; then
    echo "📦 Using python3 -m pip install --user..."
    python3 -m pip install --user . --upgrade 2>/dev/null || python3 -m pip install --user --break-system-packages . --upgrade
    
    # Ensure ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo "⚠️  Note: Make sure ~/.local/bin is in your PATH. Add this to your ~/.bashrc or ~/.zshrc:"
        echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
    echo "✅ Watchdog installed successfully! Run 'watchdog' to start."
    exit 0
fi

echo "❌ Error: Python 3 is required but not found."
exit 1
