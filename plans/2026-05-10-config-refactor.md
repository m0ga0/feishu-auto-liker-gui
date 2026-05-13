# Config Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace file-based config with SQLite/YAML hybrid storage using DAO pattern and Pydantic models.

**Architecture:**
- **Pydantic Models** for config data.
- **DAO Pattern**: Interfaces in `src/config/dao.py`, Implementations in `src/dao/config/`.
- **Hybrid Storage**: SQLite for dynamic monitor settings, YAML for static internal settings.
- **Migration**: On startup, migrate existing `config.yaml` to new structure.

**Tech Stack:** `SQLModel` (for SQLite), `Pydantic` (for models), `PyYAML` (for YAML).

---

### Task 1: Setup Error Handling and Base Models
**Files:**
- Create: `src/core/exceptions.py`
- Create: `src/config/models.py`

- [ ] **Step 1: Create `AppError` base class**
```python
class AppError(Exception):
    """Base class for application errors."""
    pass

class ConfigError(AppError):
    """Configuration related errors."""
    pass
```

- [ ] **Step 2: Define `AppConfig` models**
```python
from pydantic import BaseModel, Field
from typing import List

class MonitorSettings(BaseModel):
    patterns: List[str]
    reaction_emoji: str
    check_interval: float
    max_messages_per_check: int

class InternalSettings(BaseModel):
    browser_user_data_dir: str = "./feishu_browser_data"
    browser_win_width: int = 1280
    browser_win_height: int = 800
    logging_level: str = "INFO"
    logging_dir: str = "rpa_bot.log"

class AppConfig(BaseModel):
    monitor: MonitorSettings
    internal: InternalSettings
```

- [ ] **Step 3: Commit**
```bash
git add src/core/exceptions.py src/config/models.py
git commit -m "feat: add AppError and AppConfig models"
```

### Task 2: Define DAO Interfaces
**Files:**
- Create: `src/config/dao.py`

- [ ] **Step 1: Define `IMonitorSettingsRepository` and `IInternalSettingsRepository`**
```python
from abc import ABC, abstractmethod
from .models import MonitorSettings, InternalSettings

class IMonitorSettingsRepository(ABC):
    @abstractmethod
    def get(self) -> MonitorSettings: ...
    @abstractmethod
    def save(self, settings: MonitorSettings): ...

class IInternalSettingsRepository(ABC):
    @abstractmethod
    def get(self) -> InternalSettings: ...
    @abstractmethod
    def save(self, settings: InternalSettings): ...

class AppConfigRepository:
    def __init__(self, monitor: IMonitorSettingsRepository, internal: IInternalSettingsRepository):
        self.monitor = monitor
        self.internal = internal
```

- [ ] **Step 2: Commit**
```bash
git add src/config/dao.py
git commit -m "feat: define config DAO interfaces"
```

### Task 3: Implement Repositories
**Files:**
- Create: `src/dao/config/sqlite_repository.py`
- Create: `src/dao/config/yaml_repository.py`
- Create: `src/dao/config/__init__.py`

- [ ] **Step 1: Implement `SqliteMonitorSettingsRepository`** (using SQLModel)
- [ ] **Step 2: Implement `YamlMonitorSettingsRepository`** (using PyYAML)
- [ ] **Step 3: Implement `YamlInternalSettingsRepository`** (using PyYAML)
- [ ] **Step 4: Commit**

### Task 4: Implement Wiring and Migration
**Files:**
- Modify: `src/config/__init__.py`
- Remove: `src/config/defaults.py`

- [ ] **Step 1: Implement config initialization logic**
- [ ] **Step 2: Migration from old config.yaml to new structure**
- [ ] **Step 3: Remove `defaults.py` and usages**
- [ ] **Step 4: Commit**

### Task 5: Integration and Cleanup
**Files:**
- Modify: All files referencing `src.config.defaults` or `config.yaml`.
- Test: `tests/config/test_config.py`

- [ ] **Step 1: Update code usage to new `AppConfig`**
- [ ] **Step 2: Update tests**
- [ ] **Step 3: Commit**
