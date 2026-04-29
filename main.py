"""
Feishu Auto-Liker GUI Application

Backward compatibility shim - imports from src/ package.
Run as: python main.py
Or: python -m src
"""

from src.__main__ import main

if __name__ == "__main__":
    main()
