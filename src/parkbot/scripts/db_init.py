"""Database initialization module."""

from sqlmodel import create_engine
from ..infra import DB_PATH
from ..dao_impl.config.monitor_settings_impl import MonitorSettingsDB


def init_database():
    """Initialize the database and create all tables."""
    engine = create_engine(f"sqlite:///{DB_PATH}")
    MonitorSettingsDB.metadata.create_all(engine)
    print(f"Database initialized at {DB_PATH}")


if __name__ == "__main__":
    init_database()
