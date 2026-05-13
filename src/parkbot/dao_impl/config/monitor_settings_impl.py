import yaml
from pathlib import Path
from typing import Optional
from sqlmodel import SQLModel, Field, Session
from ...core.exceptions import ConfigError
from ...config.models import MonitorSettings as MonitorSettingsModel
from ...config.dao import IMonitorSettingsRepository


class MonitorSettingsDB(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    patterns_str: str
    reaction_emoji: str
    check_interval: float
    max_messages_per_check: int

    def to_model(self) -> MonitorSettingsModel:
        return MonitorSettingsModel(
            patterns=self.patterns_str.split(",") if self.patterns_str else [],
            reaction_emoji=self.reaction_emoji,
            check_interval=self.check_interval,
            max_messages_per_check=self.max_messages_per_check,
        )

    @classmethod
    def from_model(cls, model: MonitorSettingsModel) -> "MonitorSettingsDB":
        return cls(
            id=1,
            patterns_str=",".join(model.patterns),
            reaction_emoji=model.reaction_emoji,
            check_interval=model.check_interval,
            max_messages_per_check=model.max_messages_per_check,
        )


class SqliteMonitorSettingsRepository(IMonitorSettingsRepository):
    def __init__(self, engine):
        self.engine = engine
        SQLModel.metadata.create_all(self.engine)

    def get(self) -> Optional[MonitorSettingsModel]:
        with Session(self.engine) as session:
            db_model = session.get(MonitorSettingsDB, 1)
            return None if not db_model else db_model.to_model()

    def save(self, settings: MonitorSettingsModel):
        with Session(self.engine) as session:
            db_model = MonitorSettingsDB.from_model(settings)
            session.merge(db_model)
            session.commit()


class YamlMonitorSettingsRepository(IMonitorSettingsRepository):
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    def get(self) -> Optional[MonitorSettingsModel]:
        if not self.file_path.exists():
            raise ConfigError("YAML setting file for monitor is missing")
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return None if not data else MonitorSettingsModel(**data)

    def save(self, settings: MonitorSettingsModel):
        with open(self.file_path, "w", encoding="utf-8") as f:
            yaml.dump(settings.model_dump(), f, default_flow_style=False)


class InMemoryMonitorSettingsRepository(IMonitorSettingsRepository):
    def __init__(self):
        self.__settings = {}

    def get(self) -> Optional[MonitorSettingsModel]:
        return MonitorSettingsModel(**self.__settings)

    def save(self, settings: MonitorSettingsModel):
        self.__settings.update(settings.model_dump())


class CompositeMonitorSettingsRepository(IMonitorSettingsRepository):
    def __init__(
        self,
        sqlite_repo: SqliteMonitorSettingsRepository,
        yaml_repo: YamlMonitorSettingsRepository,
    ):
        self.sqlite_repo = sqlite_repo
        self.yaml_repo = yaml_repo

    def get(self) -> Optional[MonitorSettingsModel]:
        settings = self.sqlite_repo.get()
        return settings if settings else self.yaml_repo.get()

    def save(self, settings: MonitorSettingsModel):
        self.sqlite_repo.save(settings)
