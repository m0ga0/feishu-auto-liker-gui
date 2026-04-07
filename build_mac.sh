#!/bin/bash
# Build script for macOS
# Run this on a Mac to create a standalone .app

set -e

echo "🔨 Building Feishu Auto-Liker GUI for macOS..."

# Install pyinstaller if not present
pip install pyinstaller --quiet

# Build command
pyinstaller --name "飞书自动点赞助手" \
    --onefile \
    --windowed \
    --hidden-import customtkinter \
    --hidden-import playwright \
    --hidden-import yaml \
    --hidden-import loguru \
    main.py

echo "✅ Build complete! Check the 'dist' folder."
