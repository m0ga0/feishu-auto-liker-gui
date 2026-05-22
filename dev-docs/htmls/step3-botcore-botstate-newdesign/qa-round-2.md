# Design Review - Round 2 Q&A

Generated on: 5/22/2026, 3:54:02 PM

---

## ✅ Answered

**Q: Should reacted_at be updated even when is_reacted=False (no match)?**
**A:** Yes - update reacted_at in all cases.

---

## ❓ Open Questions

### Question 1: Unified State Method

**Context:** Merge mark_reacted(), mark_matched(), mark_no_match() into one method.

**Answer:** can name the method as mark_processed

---

### Question 2: target_pattern on No-Match

**Context:** When is_reacted=False (no match), what should target_pattern store?

**Answer:** A

---

### Question 3: Iteration Version of get_by_ids

**Context:** Should we provide a generator/iterator version for memory efficiency?

**Answer:** yes, this is good, i want this

---

### Question 4: Async DAO Methods

**Context:** Do we need async versions of repository methods?

**Answer:** ok , for now we don't need async version of repository methods

---

### Question 5: SQLAlchemy .all() vs .yield_per()

**Context:** Should we use .yield_per(n) for streaming large results?

**Answer:** we can use all() for current business since we already have batch_size

---

### Question 6: Scenario 2 Handling

**Context:** Should we keep handling Scenario 2 or simplify the design?

**Answer:** A

---
