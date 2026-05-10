from sqlmodel import SQLModel, Field, Session
from src.config.models import MonitorSettings as MonitorSettingsModel
from src.config.dao import IMonitorSettingsRepository


class MonitorSettingsDB(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    patterns_str: str  # Storing as comma-separated
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

    def get(self) -> MonitorSettingsModel:
        with Session(self.engine) as session:
            db_model = session.get(MonitorSettingsDB, 1)
            if db_model:
                return db_model.to_model()
            # Return a default settings object if not present
            return MonitorSettingsModel(
                patterns=["re:.*(出|整出).*(车位|停车位|首赞).*"],
                reaction_emoji="赞",
                check_interval=2.0,
                max_messages_per_check=3,
            )

    def save(self, settings: MonitorSettingsModel):
        with Session(self.engine) as session:
            db_model = MonitorSettingsDB.from_model(settings)
            session.merge(db_model)
            session.commit()
