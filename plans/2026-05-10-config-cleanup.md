# Config Architecture Cleanup Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove hardcoded defaults from Pydantic models, reorganize DAO implementations by domain, and implement a composite repository for fallback logic.

**Architecture:**
- **`config/models.py`**: No defaults.
- **DAO Organization**: `src/dao/config/monitor_settings.py` (Sqlite + Yaml + Composite) and `src/dao/config/internal_settings.py` (Yaml).
- **Composite Pattern**: `CompositeMonitorSettingsRepository` attempts `Sqlite` -> `Yaml` (default) -> `Raise Error`.

---

### Task 1: Clean Up Config Models
**Files:**
- Modify: `src/config/models.py`

- [ ] **Step 1: Remove hardcoded defaults**
```python
class MonitorSettings(BaseModel):
    patterns: List[str]
    reaction_emoji: str
    check_interval: float
    max_messages_per_check: int
    monitored_groups: List[str]
```
- [ ] **Step 2: Commit**
```bash
git add src/config/models.py
git commit -m "refactor: remove hardcoded defaults from models"
```

### Task 2: Reorganize and Implement Composite Repositories
**Files:**
- Create: `src/dao/config/monitor_settings.py`
- Create: `src/dao/config/internal_settings.py`
- Remove: `src/dao/config/sqlite_repository.py`, `src/dao/config/yaml_repository.py`

- [ ] **Step 1: Implement `monitor_settings.py`**
    - Include `SqliteMonitorSettingsRepository`, `YamlMonitorSettingsRepository` (reads file, raises error if missing), and `CompositeMonitorSettingsRepository` (logic: get sqlite, if None get yaml, if yaml missing raise ConfigError).
- [ ] **Step 2: Implement `internal_settings.py`**
    - Include `YamlInternalSettingsRepository`.
- [ ] **Step 3: Commit**

### Task 3: Update Wiring
**Files:**
- Modify: `src/config/__init__.py`

- [ ] **Step 1: Update `get_config_repository` to use new Composite Repository**
- [ ] **Step 2: Update Migration logic to ensure default file exists**
- [ ] **Step 3: Commit**

### Task 4: Fix Tests
**Files:**
- Modify: `tests/config/test_config.py`

- [ ] **Step 1: Update tests for the new Composite Repository**
- [ ] **Step 2: Run tests and verify**
- [ ] **Step 3: Commit**
