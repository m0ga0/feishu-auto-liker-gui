# Ticket 7: Fix datetime.utcnow() Deprecation Warnings

**Branch**: `fix/message-db`  
**Date**: 2026-05-27  
**Status**: 🔶 In Progress

---

## Problem Description

Pre-commit hook (`ty` type checker) is reporting deprecation warnings for `datetime.utcnow()` usage across multiple files. The function is deprecated in Python 3.12+ and will be removed in future versions.

### Warning Messages

```
warning[deprecated]: The function `utcnow` is deprecated
  --> src/parkbot/chat/models.py:43:59
   |
43 |     created_at: datetime = Field(default_factory=datetime.utcnow)
   |                                                           ^^^^^^
   | Use timezone-aware objects to represent datetimes in UTC;
   | e.g. by calling .now(datetime.timezone.utc)
```

**Total occurrences:** 6 instances across 3 files  
**Additional issue:** Pydantic `.json()` method deprecated, should use `.model_dump_json()`

---

## Root Cause Analysis

### Why This Happened

1. **Python 3.12 deprecation**: `datetime.utcnow()` was deprecated because it returns a naive datetime (no timezone info), which can cause bugs when working with timezone-aware systems
2. **Best practice change**: Python now recommends always using timezone-aware datetime objects
3. **Pydantic v2 migration**: The `.json()` method was replaced with `.model_dump_json()` in Pydantic v2

### Affected Locations

| File | Line | Current Code |
|------|------|--------------|
| `src/parkbot/chat/models.py` | 43 | `datetime.utcnow` |
| `src/parkbot/chat/models.py` | 68 | `datetime.utcnow()` |
| `src/parkbot/dao_impl/chat/models_impls.py` | 26 | `datetime.utcnow` |
| `src/parkbot/dao_impl/chat/repo_impls.py` | 51 | `datetime.utcnow()` |
| `src/parkbot/dao_impl/chat/repo_impls.py` | 134 | `.json()` |
| `src/parkbot/dao_impl/chat/repo_impls.py` | 138 | `datetime.utcnow()` |
| `src/parkbot/dao_impl/chat/repo_impls.py` | 183 | `datetime.utcnow()` |

---

## Solution (Improved with Utility Class)

### Step 1: Create Centralized Utility Function

**File:** `src/parkbot/utils/datetime_utils.py` (new file)

Create a utility module that provides a centralized way to get UTC datetime. This ensures:
- **Single source of truth**: All UTC datetime creation logic in one place
- **Easy maintenance**: Changes to datetime logic only need to be made once
- **Consistent behavior**: All modules use the same implementation
- **Testability**: Can mock the utility function for testing

**Implementation:**
```python
"""Utility functions for datetime operations."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return timezone-aware UTC datetime.

    Replaces deprecated datetime.utcnow() which returns naive datetime.
    All datetime objects should be timezone-aware for consistency.

    Returns:
        datetime: Current UTC time with timezone info

    Example:
        >>> from parkbot.utils.datetime_utils import utcnow
        >>> created_at = utcnow()
        >>> print(created_at)
        2026-05-27 12:34:56.789012+00:00
    """
    return datetime.now(timezone.utc)
```

### Step 2: Update All Occurrences to Use Utility

**Before (scattered throughout code):**
```python
from datetime import datetime, timezone

# Multiple variations across files
created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
now = datetime.now(timezone.utc)
```

**After (centralized via utility):**
```python
from parkbot.utils.datetime_utils import utcnow

# Consistent usage across all files
created_at: datetime = Field(default_factory=utcnow)
now = utcnow()
```

### Step 3: Fix Pydantic json() Deprecation

**Before:**
```python
json.loads(msg.json())
```

**After:**
```python
json.loads(msg.model_dump_json())
```

---

## Files Changed

### New File
1. `src/parkbot/utils/datetime_utils.py`
   - New utility module with `utcnow()` function
   - Provides centralized UTC datetime creation

### Modified Files
2. `src/parkbot/chat/models.py`
   - Replace `datetime.utcnow` with `from parkbot.utils.datetime_utils import utcnow`
   - Update 2 usages to use `utcnow()` and `utcnow`

3. `src/parkbot/dao_impl/chat/models_impls.py`
   - Replace `datetime.utcnow` with utility import
   - Update 1 usage

4. `src/parkbot/dao_impl/chat/repo_impls.py`
   - Replace `datetime.utcnow()` with utility import
   - Update 3 usages
   - Fix 1 `.json()` → `.model_dump_json()` (separate deprecation)

---

## Benefits of Utility Approach

1. **Maintainability**: One place to change datetime logic
2. **Consistency**: All code uses same UTC datetime implementation
3. **Readability**: `utcnow()` is cleaner than `datetime.now(timezone.utc)`
4. **Future-proof**: Easy to add more datetime utilities later
5. **Type safety**: Function is properly typed with return annotation

---

## Testing

**Command:** `hatch run pre-commit run --all-files`

**Expected results:**
- All `utcnow` deprecation warnings eliminated
- All `json()` deprecation warnings eliminated
- No new type errors introduced
- All 235 pytest tests still pass

**Verification:**
```bash
# Run pre-commit to check for warnings
hatch run pre-commit run --all-files

# Run tests to ensure no regressions
hatch run pytest tests/ -q

# Import check
hatch run python -c "from parkbot.utils.datetime_utils import utcnow; print(utcnow())"
```

---

## Migration Notes

- **Backward compatible**: The change is internal, no API changes
- **Data format unchanged**: SQLite stores datetime as ISO strings
- **Behavior improved**: Now properly timezone-aware (UTC)
- **No migration needed**: Existing data will continue to work
- **Import path**: New utility at `parkbot.utils.datetime_utils`

---

## References

- [Python 3.12 Deprecation Notice](https://docs.python.org/3.12/library/datetime.html#datetime.datetime.utcnow)
- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/#changes-to-pydanticbasemodel)
- Code Review Feedback: Use centralized utility class for maintainability
