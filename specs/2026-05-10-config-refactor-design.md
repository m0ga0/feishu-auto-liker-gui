# Design: Configuration Refactoring

## Overview
Replace the current file-based configuration (yaml/json) with a hybrid storage system:
- **Internal Settings (Technical)**: YAML file.
- **Monitor Settings (Business)**: SQLite database.
- **DAO Architecture**: Interface-driven data access, with implementations in `src/dao/`.

## Architecture

### Configuration Model
- `AppConfig`: Pydantic model.
- `InternalSettings`: Loaded from `settings.yaml`.
- `MonitorSettings`: Loaded from SQLite, with `monitor-default-settings.yaml` as the initial fallback.

### DAO Layer
- **Interfaces (`src/config/dao.py`)**: `AppConfigRepository` (ABCs). Only methods for `AppConfig` related data.
- **Implementations (`src/dao/config/`)**:
    - `SqliteAppConfigRepository`: For database operations.
    - `YamlAppConfigRepository`: For YAML file operations.

## Migration Strategy
- Migrate existing `config.yaml` to the new structure.
- `state.json` is preserved as-is.

## Error Handling
- Custom `AppError` exception hierarchy for robust error handling.
