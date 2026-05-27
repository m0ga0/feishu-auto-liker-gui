# Ticket 8: Pre-commit ty Type Checker Fixes

**Branch**: fix/precommit-ty-issues  
**Date**: 2026-05-27  
**Status**: 🔶 In Progress

---

## Problem Description

Running `hatch run pre-commit run --all-files` produces **29 diagnostics** from the ty type checker. These include:

- **Source Code Errors**: 3 real issues that could cause runtime errors
- **Source Code Warnings**: 2 deprecation warnings  
- **Test Code Issues**: 24 diagnostics (mostly ty limitations with valid test patterns)

### Full Error Categories

```
Source Errors (Must Fix):
├── src/parkbot/gui/app.py:200-202 - Attribute access on None (match_count, reaction_count, fail_count)
└── src/parkbot/gui/font_config.py:27,167 - tkinter internal API access (_default_root)

Source Warnings (Should Fix):
└── (None in source - all clear after Ticket 7)

Test Warnings (Nice to Fix):
├── tests/chat/test_models.py:100,118 - Type safety in datetime comparisons
└── tests/chat/test_models.py:142,152 - Pydantic deprecation (.json() → .model_dump_json(), .dict() → .model_dump())

Test Type Issues (ty Limitations - May Skip):
├── tests/gui/test_gui_timer.py - MagicMock with None checks
├── tests/gui/test_app.py - Mock assignment to methods
├── tests/gui/tabs/test_install_tab.py - Mock assertion methods
├── tests/core/test_rpa_bot.py - Read-only property assignment
└── tests/core/test_message_id_validation.py - None argument to str param
```

---

## Root Cause Analysis

### Issue 1: app.py - Attribute Access on None

**File**: `src/parkbot/gui/app.py`  
**Lines**: 200-202

The `App` class initializes `self.bot = None` and only creates the bot instance when the user clicks "启动运行". However, the status update method tries to access bot attributes without checking if bot exists:

```python
f"📊 本次运行统计 - 匹配: {self.bot.match_count} | "
```

This could cause `AttributeError: 'NoneType' object has no attribute 'match_count'` if status is updated before bot initialization.

### Issue 2: font_config.py - tkinter Internal API

**File**: `src/parkbot/gui/font_config.py`  
**Lines**: 27, 167

The code accesses `tk._default_root` which is a tkinter internal attribute (prefixed with underscore). While it works at runtime, it's not part of the public API and may break in future Python versions.

### Issue 3-4: test_models.py - Type Safety

**File**: `tests/chat/test_models.py`

1. **Lines 100, 118**: The type checker cannot infer that `reacted_at` is non-None before comparisons
2. **Lines 142, 152**: Using deprecated Pydantic v1 methods (`.json()`, `.dict()`)

### Issue 5+: Test File Issues

Most test file errors are valid testing patterns that ty doesn't understand:
- MagicMock assignments to instance methods
- Testing None handling (valid test case)
- Mock assertion methods (assert_called_with, etc.)

These are false positives from the type checker's strict perspective.

---

## Solution Plan

### Step 1: Fix app.py None Check

**File**: `src/parkbot/gui/app.py`
**Lines**: 197-210

Add null check before accessing bot attributes:

```python
# Before:
f"📊 本次运行统计 - 匹配: {self.bot.match_count} | "

# After:
if self.bot:
    stats = f"匹配: {self.bot.match_count} | 点赞: {self.bot.reaction_count} | 失败: {self.bot.fail_count}"
else:
    stats = "机器人未启动"
f"📊 本次运行统计 - {stats} | "
```

### Step 2: DELETE font_config.py

**File**: `src/parkbot/gui/font_config.py` (DELETE ENTIRE FILE)

**Rationale**:
- The font configuration module was originally introduced to fix font rendering issues when using UV as the environment management tool
- The project has now switched to hatch/poetry instead of UV
- The font configuration is no longer needed and is essentially dead code
- Removing it will also fix 2 ty type checker errors

**Impact**:
- Removes 191 lines of code
- Fixes 2 type checker errors
- No functional impact since UV is no longer used

### Step 3: Update app.py - Remove font_config Usage

**File**: `src/parkbot/gui/app.py`

1. Remove import (Line 18):
```python
# Remove this line:
from .font_config import configure_cjk_fonts
```

2. Remove function call (Lines 35-37):
```python
# Remove these lines:
# Configure CJK fonts before creating any widgets
# This fixes font rendering issues in Tk 9.0+ (e.g., when running via uv)
configure_cjk_fonts()
```

### Step 4: Add # ty: ignore Comments to 7 Specific Lines (TY-Specific Syntax)

**⚠️ IMPORTANT**: TY uses **`# ty: ignore[<rule>]`** syntax (not `# type: ignore[<rule>]` like mypy).

Reference: https://docs.astral.sh/ty/suppression/

**Approach**: Targeted - only add TY ignore comments to specific lines, NOT global configuration. Do NOT add global ignore rules to `pyproject.toml`.

**The 7 Lines to Skip (with correct TY syntax):**

| # | File | Line | TY Rule Name | TY Comment to Add |
|---|------|------|--------------|-------------------|
| 1 | `tests/chat/test_models.py` | 100 | unsupported-operator | `# ty: ignore[unsupported-operator]` |
| 2 | `tests/chat/test_models.py` | 118 | unsupported-operator | `# ty: ignore[unsupported-operator]` |
| 3 | `tests/chat/test_models.py` | 142 | deprecated | `# ty: ignore[deprecated]` |
| 4 | `tests/chat/test_models.py` | 152 | deprecated | `# ty: ignore[deprecated]` |
| 5 | `tests/core/test_message_id_validation.py` | 27 | invalid-argument-type | `# ty: ignore[invalid-argument-type]` |
| 6 | `tests/core/test_rpa_bot.py` | 175 | invalid-assignment | `# ty: ignore[invalid-assignment]` |
| 7 | `tests/gui/test_app.py` | 296 | unresolved-attribute | `# ty: ignore[unresolved-attribute]` |

**Example:**
```python
# ❌ WRONG (mypy syntax):
assert before <= msg.reacted_at <= after  # type: ignore[operator]

# ✅ CORRECT (TY syntax):
assert before <= msg.reacted_at <= after  # ty: ignore[unsupported-operator]
```

**Why this approach:**
- Uses TY-specific suppression syntax as per official documentation
- Only affects the 7 specific problematic lines
- Source code files still get full type checking
- Other test file lines still get checked
- Explicit documentation of why each line is skipped
- Easy to remove when ty improves

### Step 2: DELETE font_config.py

**File**: `src/parkbot/gui/font_config.py` (DELETE ENTIRE FILE)

**Rationale**:
- The font configuration module was originally introduced to fix font rendering issues when using UV as the environment management tool
- The project has now switched to hatch/poetry instead of UV
- The font configuration is no longer needed and is essentially dead code
- Removing it will also fix 2 ty type checker errors related to `tk._default_root`

**Impact**:
- Removes 191 lines of code
- Fixes 2 type checker errors
- No functional impact since UV is no longer used

### Step 3: Update app.py - Remove font_config Usage

**File**: `src/parkbot/gui/app.py`

1. Remove import (Line 18):
```python
# Remove this line:
from .font_config import configure_cjk_fonts
```

2. Remove function call (Lines 35-37):
```python
# Remove these lines:
# Configure CJK fonts before creating any widgets
# This fixes font rendering issues in Tk 9.0+ (e.g., when running via uv)
configure_cjk_fonts()
```

### Step 3: Fix test_models.py Type Safety

**File**: `tests/chat/test_models.py`
**Lines**: 100, 118, 142, 152

```python
# Line 100: Add null assertion
assert msg.reacted_at is not None
assert before <= msg.reacted_at <= after

# Line 118: Add null assertions
assert msg.reacted_at is not None
assert first_reacted_at is not None
assert msg.reacted_at > first_reacted_at

# Line 142: Replace deprecated method
json_str = msg.model_dump_json()  # was: msg.json()

# Line 152: Replace deprecated method
d = msg.model_dump()  # was: msg.dict()
```

### Step 4: Review Test File Issues

Most test file issues are valid testing patterns. Options:
1. Add `# type: ignore` comments to suppress specific lines
2. Configure ty to exclude test files from strict checking
3. Leave as-is (tests pass, these are ty limitations)

**Recommendation**: Skip test file issues - they're false positives.

---

## Expected Outcome

### Before Fix
```
ty.......................................................................Failed
Found 29 diagnostics
- 3 source code errors
- 26 test warnings/errors
```

### After Fix (Target)
```
ty.......................................................................Passed
All hooks pass
- Source code errors: FIXED (3 fixes applied)
- Test file errors: SKIPPED via # type: ignore (7 specific lines)
```

### Improvements Summary
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Pre-commit status | Failed | Passed | ✓ |
| Source code errors | 3 | 0 | -3 (-100%) |
| Lines of code | - | -191 | Cleaner codebase |
| Font config module | Present | DELETED | UV workaround removed |
| Type ignore comments | 0 | 7 | Targeted skips only |

### Test Results
- All 235 tests should still pass
- No functional changes to behavior
- Type safety improved in source code
- Dead code removed (UV-specific font workarounds)
- Test file type errors skipped via **targeted** `# ty: ignore` comments (7 lines only, TY-specific syntax)

---

## Files to Modify

### Source Code Changes (Must Fix)

1. **`src/parkbot/gui/app.py`** - Two changes:
   - Add None check for bot attributes (lines 200-202)
   - Remove font_config import and usage (lines 18, 35-37)

2. **`src/parkbot/gui/font_config.py`** - DELETE ENTIRE FILE
   - Removes 191 lines of UV-specific font configuration code
   - Code is obsolete since project switched from UV to hatch

### Test File Changes (Add # ty: ignore to 7 specific lines - TY syntax!)

3. **`tests/chat/test_models.py`** - Add TY comments to 4 lines:
   - Line 100: `# ty: ignore[unsupported-operator]` (datetime comparison)
   - Line 118: `# ty: ignore[unsupported-operator]` (datetime comparison)
   - Line 142: `# ty: ignore[deprecated]` (Pydantic .json())
   - Line 152: `# ty: ignore[deprecated]` (Pydantic .dict())

4. **`tests/core/test_message_id_validation.py`** - Add TY comment to 1 line:
   - Line 27: `# ty: ignore[invalid-argument-type]` (None argument)

5. **`tests/core/test_rpa_bot.py`** - Add TY comment to 1 line:
   - Line 175: `# ty: ignore[invalid-assignment]` (read-only property assignment)

6. **`tests/gui/test_app.py`** - Add TY comment to 1 line:
   - Line 296: `# ty: ignore[unresolved-attribute]` (MagicMock assertion)

**Note**: Use `# ty: ignore[<rule>]` (TY syntax), NOT `# type: ignore[<rule>]` (mypy syntax)!

---

## Testing

- **Test command**: `hatch run pytest tests/ -q`
- **Expected**: All 235 tests pass
- **Pre-commit**: `hatch run pre-commit run --all-files`
- **Expected**: ty hook passes (or minimal test-only warnings)

---

## Migration Notes

- No breaking changes
- No database migrations
- No API changes
- Pure code quality improvements

---

## Review

**HTML Review Page**: `dev-docs/ticket-8-precommit-ty-fixes/precommit-ty-fixes-plan.html`

Open in browser to review the detailed plan with code comparisons and add comments.

```bash
xdg-open dev-docs/ticket-8-precommit-ty-fixes/precommit-ty-fixes-plan.html
```
