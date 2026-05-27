# Ticket 6: Fix target_pattern Storage - Store Actual Pattern Instead of Hardcoded Strings

**Branch**: `fix/message-db`  
**Date**: 2026-05-27  
**Status**: ✅ Completed

---

## Problem Description

The `target_pattern` column in the `feishu_messages` database table was storing hardcoded strings `"matched"` or `"checked"` instead of the actual regex pattern that was used to match the message text.

### Database Evidence

```sql
SELECT target_pattern, COUNT(*) as count
FROM feishu_messages
WHERE target_pattern IS NOT NULL
GROUP BY target_pattern;
```

**Result:**
| target_pattern | Count |
|----------------|-------|
| checked        | 54    |
| matched        | 5     |

**Expected:**
| target_pattern | Count |
|----------------|-------|
| re:.*(出\|整出).*(车位\|停车位\|首赞)*.* | 59 |

---

## Root Cause Analysis

### Problem Location
**File**: `src/parkbot/core/bot.py`  
**Lines**: 482, 485, and 506

### Original Code (Wrong)

```python
# Line 482 - When reaction succeeds
msg.mark_processed(is_reacted=True, target_pattern="matched")

# Line 485 - When reaction fails but pattern matched  
msg.mark_processed(is_reacted=False, target_pattern="matched")

# Line 506 - When pattern doesn't match
msg.mark_processed(is_reacted=False, target_pattern="checked")
```

### Why This Happened

1. **PatternMatcher.matches()** only returns `True/False`, not **which** pattern matched
2. The code was written with placeholder strings ("matched"/"checked") that were never replaced with actual pattern retrieval
3. When processing messages, the code didn't track the specific pattern that caused the match

---

## Review Feedback & Corrections

During code review, the following issues were identified and fixed:

### Review Point 1: Target Pattern Should Only Be Set on Match
**Issue**: The original plan suggested setting `target_pattern` even for non-matching messages.

**Correction**:
- ✅ When message matches → `target_pattern = actual_pattern_string`
- ✅ When message does NOT match → `target_pattern = None` (not set)

### Review Point 2: Incorrect Key Access in Line 506
**Issue**: Original plan had `msg_data.get("checked_pattern")` which is not a valid field.

**Correction**: Use `target_pattern=None` for non-matching messages instead.

---

## Solution

### Step 1: Add Method to PatternMatcher

**File**: `src/parkbot/core/matcher.py`

Add a new method that returns the actual pattern string instead of just boolean:

```python
def get_matching_pattern(self, text: str) -> Optional[str]:
    """Return the first pattern that matches the text, or None if no match.

    Args:
        text: The text to match against patterns

    Returns:
        The pattern string that matched, or None if no match
    """
    for compiled_pattern in self._compiled:
        if compiled_pattern.search(text):
            return compiled_pattern.pattern
    return None
```

### Step 2: Update Message Processing to Capture Pattern

**File**: `src/parkbot/core/bot.py` (Lines 410-421)

**Before:**
```python
for msg_data in messages:
    msg_id = msg_data["id"]
    msg_text = msg_data["text"]
    is_match = self.matcher.matches(msg_text)  # Only returns True/False

    if is_match:
        self.match_count += 1
        matched_messages.append(msg_data)  # No pattern info!
    else:
        no_match_messages.append(msg_data)
```

**After:**
```python
for msg_data in messages:
    msg_id = msg_data["id"]
    msg_text = msg_data["text"]

    # Get actual pattern that matched
    matched_pattern = self.matcher.get_matching_pattern(msg_text)
    is_match = matched_pattern is not None

    if is_match:
        self.match_count += 1
        # Store the actual pattern
        msg_data["matched_pattern"] = matched_pattern
        matched_messages.append(msg_data)
    else:
        no_match_messages.append(msg_data)
```

### Step 3: Update mark_processed Calls with Actual Pattern

**File**: `src/parkbot/core/bot.py`

**Lines 482-485 (Matched Messages):**

**Before:**
```python
if success:
    msg.mark_processed(is_reacted=True, target_pattern="matched")
    self.reaction_count += 1
else:
    msg.mark_processed(is_reacted=False, target_pattern="matched")
    self.fail_count += 1
```

**After:**
```python
# Get the matched pattern from msg_data
target_pattern = msg_data.get("matched_pattern")
if success:
    msg.mark_processed(is_reacted=True, target_pattern=target_pattern)
    self.reaction_count += 1
else:
    msg.mark_processed(is_reacted=False, target_pattern=target_pattern)
    self.fail_count += 1
```

**Line 506 (Non-Matching Messages):**

**Before:**
```python
msg.mark_processed(is_reacted=False, target_pattern="checked")
```

**After:**
```python
# Mark as checked but no match - target_pattern remains None
msg.mark_processed(is_reacted=False, target_pattern=None)
```

---

## Expected Outcome

### Before Fix

| message_id | text | target_pattern |
|------------|------|----------------|
| 7643842788513042144 | 出明天车位 | matched |
| 7643843255869214428 | 你还在加班吗？ | checked |

### After Fix

| message_id | text | target_pattern |
|------------|------|----------------|
| 7643842788513042144 | 出明天车位 | re:.*(出\|整出).*(车位\|停车位).* |
| 7643843255869214428 | 你还在加班吗？ | None |

---

## Files Changed

1. `src/parkbot/core/matcher.py` - Added `get_matching_pattern()` method
2. `src/parkbot/core/bot.py` - Updated message processing to capture and use actual patterns

## Testing

All tests pass (235 tests, 85% coverage):

```bash
hatch run pytest tests/ -q
# 235 passed, 2464 warnings in 17.48s
```

### Manual Verification

After running the bot, verify with SQL:

```bash
sqlite3 app.db "SELECT DISTINCT target_pattern FROM feishu_messages WHERE target_pattern IS NOT NULL;"
```

Should show actual pattern strings like:
- `re:.*(出|整出).*(车位|停车位|首赞)*.*`

Instead of:
- `matched`
- `checked`

---

## Migration Notes

- Existing data with "matched"/"checked" will remain as-is (historical records)
- Only new messages processed after this fix will have the correct pattern strings
- Existing data can be updated via SQL migration if needed:
  ```sql
  UPDATE feishu_messages
  SET target_pattern = 're:.*(出|整出).*(车位|停车位|首赞)*.*'
  WHERE target_pattern IN ('matched', 'checked');
  ```

---

## Related Documentation

- **HTML Plan**: `dev-docs/htmls/fix-target-pattern-plan.html` - Interactive review page with code diffs
- **Review Comments**: See 2026-05-27.md in daily working log for review discussion
