#### Comments round 2  

Generated on: 5/22/2026, 2:37:52 PM

---

##### 📦 FeishuMessage Model Design

what about merge mark_reacted , mark_matched and mark_no_match , modifying is_reacted , matched_pattern at the same time ?

---

##### 🎭 Business Scenarios Explained

scenario 2,  very rare, but possible, depends on how we save model to storage and when we modify attr values :
- if we batch save messages into storage and then batch change attr values and save again, scenario 2 will happen it means somehow the app shutdown in the middle of 2 operations. but if we create model and do pattern matching and then save in 1 operation, this will not happen, this is same as scenario 1.

scenario 3:  matched_pattern should target_patten, if is_reacted is False that means not matching the pattern and we can save miss matched pattern into target_pattern field.

in above cases we should also update the reacted_time

---

##### 🔌 DAO Interface Design (Batch Operations)

1. can we also define a iteration version of get_by_ids
2. do we need async version of get_by_ids
3. do we need async version of save_batch and other update functions ?

---

##### 📦 Repository Implementations

db_messages = session.exec(statement).all() what is all() means ?

---
