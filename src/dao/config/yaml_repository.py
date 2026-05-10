import yaml
import os
from src.config.models import MonitorSettings, InternalSettings
from src.config.dao import IMonitorSettingsRepository, IInternalSettingsRepository


class YamlMonitorSettingsRepository(IMonitorSettingsRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get(self) -> MonitorSettings:
        if not os.path.exists(self.file_path):
            return MonitorSettings(
                patterns=["re:.*(出|整出).*(车位|停车位|首赞).*"],
                reaction_emoji="赞",
                check_interval=2.0,
                max_messages_per_check=3,
            )
        with open(self.file_path, "r") as f:
            data = yaml.safe_load(f)
            if data and "monitor" in data:
                return MonitorSettings(**data["monitor"])
        return MonitorSettings(
            patterns=["re:.*(出|整出).*(车位|停车位|首赞).*"],
            reaction_emoji="赞",
            check_interval=2.0,
            max_messages_per_check=3,
        )

    def save(self, settings: MonitorSettings):
        data = {}
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                data = yaml.safe_load(f) or {}

        data["monitor"] = settings.model_dump()

        with open(self.file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)


class YamlInternalSettingsRepository(IInternalSettingsRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get(self) -> InternalSettings:
        if not os.path.exists(self.file_path):
            return InternalSettings()
        with open(self.file_path, "r") as f:
            data = yaml.safe_load(f)
            if data and "internal" in data:
                return InternalSettings(**data["internal"])
        return InternalSettings()

    def save(self, settings: InternalSettings):
        data = {}
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                data = yaml.safe_load(f) or {}

        data["internal"] = settings.model_dump()

        with open(self.file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
