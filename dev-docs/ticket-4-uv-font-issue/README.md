# Ticket 4: Font Rendering Issues with uv-managed Python

**Issue**: Chinese characters appear pixelated/jagged or as square marks (tofu) when running via `uv run python`, but render correctly when running with system Python.

**Date**: 2026-05-25  
**Status**: 🔶 Known Limitation (Workaround Available)

---

## Problem Description

When running the GUI application via `uv run python src/parkbot/main.py`:
- Chinese characters appear **pixelated with jagged edges**
- Some characters display as **square marks** (tofu)
- Fonts look "blocky" and unprofessional

When running with system Python directly (`python3 src/parkbot/main.py`):
- Chinese characters render correctly with smooth anti-aliasing
- All characters display properly

## Root Cause

The issue stems from how uv's standalone Python builds are compiled:

### System Python (working)
- Uses Tk 8.6.x compiled **with Xft/fontconfig support**
- Can access system TrueType fonts (Noto Sans CJK, etc.)
- Renders fonts with anti-aliasing

### uv-managed Python (broken)
- Uses Tk 9.0.x compiled **WITHOUT Xft/fontconfig support**
- Falls back to legacy X11 core fonts (bitmap fonts only)
- X11 core fonts are pixelated and have limited Unicode coverage

### Technical Details

```bash
# System Python - has modern fonts
$ python3 -c "import tkinter.font as f; print(len(f.families()))"
96  # Includes Noto Sans CJK, DejaVu, etc.

# uv Python - only X11 core fonts
$ uv run python -c "import tkinter.font as f; print(len(f.families()))"
47  # Only bitmap fonts like 'song ti', 'helvetica', etc.
```

### Why This Happens

Uv's Python builds are designed to be portable and minimize external dependencies. To achieve this:
1. They compile Tcl/Tk from source
2. They disable Xft/fontconfig to avoid runtime dependencies
3. This limits Tk to X11 core fonts only (bitmap fonts from the 1980s/90s)

## Workarounds

### Option 1: Run without uv (Recommended)

Install dependencies in a virtual environment and run with system Python:

```bash
# Create virtual environment with system Python
python3 -m venv .venv-system
source .venv-system/bin/activate
pip install -r requirements.txt

# Run application
python src/parkbot/main.py
```

### Option 2: Use pyenv instead of uv

pyenv compiles Python from source with full system library support:

```bash
# Install Python via pyenv
pyenv install 3.12.3
pyenv local 3.12.3

# Install dependencies
pip install -r requirements.txt

# Run application
python src/parkbot/main.py
```

### Option 3: Use uv with system Python

Configure uv to use the system Python instead of downloading its own:

```bash
# Tell uv to use system Python
uv venv --python python3
uv pip install -r requirements.txt

# May still have issues if system Tk isn't compatible
```

### Option 4: Accept the limitation

For development/testing purposes, the pixelated fonts don't affect functionality. The application still works correctly.

## Code Changes

Added font configuration module (`src/parkbot/gui/font_config.py`) that:
1. Detects if Tk has Xft support
2. Selects the best available font for CJK characters
3. Provides graceful degradation to X11 fonts when necessary

```python
# In App.__init__
from .font_config import configure_cjk_fonts

# Configure fonts before creating widgets
configure_cjk_fonts()
```

## Detection

You can check your font environment with:

```python
from parkbot.gui.font_config import check_font_environment

info = check_font_environment()
print(info)
# {
#     "total_fonts": 47,
#     "has_xft_support": False,  # <-- This indicates the issue
#     "has_noto_cjk": False,
#     "has_x11_cjk": True,
#     "warning": "Fonts may appear pixelated. Consider running without uv."
# }
```

## References

- [Tk font documentation](https://www.tcl.tk/man/tcl/TkCmd/font.htm)
- [Xft vs X11 core fonts](https://wiki.archlinux.org/title/X_Logical_Font_Description)
- uv Python builds: [astral-sh/python-build-standalone](https://github.com/astral-sh/python-build-standalone)
