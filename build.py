"""
Build script for Feishu Auto-Liker GUI.
Creates a standalone executable using PyInstaller.
"""

import os
import subprocess
import sys


def main():
    print("🔨 Building Feishu Auto-Liker GUI...")

    # Install pyinstaller if not present
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "飞书自动点赞助手",
        "--onefile",
        "--windowed",
        "--collect-all",
        "customtkinter",
        "--collect-all",
        "playwright",
        "--hidden-import",
        "yaml",
        "--hidden-import",
        "loguru",
        "--add-data",
        "config.example.yaml:.",
        "main.py",
    ]

    # On Windows, data separator is ;
    if os.name == "nt":
        cmd[-2] = "config.example.yaml;."

    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    print("✅ Build complete! Check the 'dist' folder.")


if __name__ == "__main__":
    main()
