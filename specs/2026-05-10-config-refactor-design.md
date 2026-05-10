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
- **Interfaces (`src/config/dao.py`)**:
    - `IMonitorSettingsRepository`: ABC for monitor settings.
    - `IInternalSettingsRepository`: ABC for internal settings.
    - `AppConfigRepository`: Facade exposing both repositories.
- **Implementations (`src/dao/config/`)**:
    - `SqliteMonitorSettingsRepository`: SQLite impl for `IMonitorSettingsRepository`.
    - `YamlMonitorSettingsRepository`: YAML impl for `IMonitorSettingsRepository`.
    - `YamlInternalSettingsRepository`: YAML impl for `IInternalSettingsRepository`.

## Migration Strategy
- Migrate existing `config.yaml` to the new structure.
- `state.json` is preserved as-is.

## Error Handling
- Custom `AppError` exception hierarchy for robust error handling.
