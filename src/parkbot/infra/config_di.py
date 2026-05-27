from sqlalchemy import Engine
from sqlmodel import create_engine, SQLModel
from ..config.dao import AppSettingsRepository
from ..dao_impl.config.monitor_settings_impl import (
    SqliteMonitorSettingsRepository,
    YamlMonitorSettingsRepository,
    CompositeMonitorSettingsRepository,
)
from ..dao_impl.config.internal_settings_impl import YamlInternalSettingsRepository
from ..dao_impl.chat.repo_impls import SqliteFeishuMessageRepository
from ..dao_impl.chat.dao import IFeishuMessageRepository


# each package should have a default  settings yaml file in the app dir
MONITOR_DEFAULT_SETTINGS_PATH = "monitor_default_settings.yaml"
# system internal settings yaml
SYS_INTERNAL_SETTINGS_PATH = "sys_internal_settings.yaml"
# sqlite db file name
DB_PATH = "app.db"

_repo: AppSettingsRepository | None = None
_message_repo: IFeishuMessageRepository | None = None
_engine: Engine | None = None


def _get_engine() -> Engine:
    """Get or create the shared database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(f"sqlite:///{DB_PATH}")
    return _engine


def get_settings_repository() -> AppSettingsRepository:
    global _repo
    if _repo:
        return _repo
    engine = _get_engine()
    sqlite_monitor_repo = SqliteMonitorSettingsRepository(engine)
    yaml_monitor_repo = YamlMonitorSettingsRepository(MONITOR_DEFAULT_SETTINGS_PATH)
    monitor_repo = CompositeMonitorSettingsRepository(
        sqlite_monitor_repo, yaml_monitor_repo
    )
    internal_repo = YamlInternalSettingsRepository(SYS_INTERNAL_SETTINGS_PATH)
    _repo = AppSettingsRepository(monitor_repo, internal_repo)
    return _repo


def get_message_repository() -> IFeishuMessageRepository:
    """Get the message repository singleton."""
    global _message_repo
    if _message_repo:
        return _message_repo

    # Use the shared engine
    engine = _get_engine()

    # Create tables automatically (only creates if not exist)
    SQLModel.metadata.create_all(engine)

    _message_repo = SqliteFeishuMessageRepository(engine)
    return _message_repo
