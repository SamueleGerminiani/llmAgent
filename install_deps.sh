#!/usr/bin/env bash
# ==========================================================
# install_deps.sh — Install dependencies for llmAgent
# ==========================================================

set -e  # Exit immediately on error

echo "🔧 Installing dependencies for llmAgent..."

# Check for Python
if ! command -v python3 &>/dev/null; then
  echo "❌ Python3 not found. Please install Python 3.8 or higher."
  exit 1
fi

# Check for pip
if ! command -v pip3 &>/dev/null; then
  echo "❌ pip3 not found. Please install pip for Python 3."
  exit 1
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip3 install --upgrade pip

# Install required Python packages
echo "📥 Installing google-genai..."
pip3 install google-genai

echo "✅ All dependencies installed successfully."

