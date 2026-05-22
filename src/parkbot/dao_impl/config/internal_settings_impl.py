import yaml
from pathlib import Path
from ...core.exceptions import ConfigError
from ...config.models import InternalSettings
from ...config.dao import IInternalSettingsRepository


class YamlInternalSettingsRepository(IInternalSettingsRepository):
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def get(self) -> InternalSettings:
        if not self.file_path.exists():
            raise ConfigError(
                f"YAML file for internal system setting is missing: {self.file_path}"
            )
        with open(self.file_path, "r") as f:
            data = yaml.safe_load(f)
            if not data:
                raise ConfigError(f"YAML file {self.file_path} data is empty")
            return InternalSettings(**data)

    def save(self, settings: InternalSettings):
        with open(self.file_path, "w", encoding="utf-8") as f:
            yaml.dump(settings.model_dump(), f, default_flow_style=False)


class InMemoryInternalSettingsRepository(IInternalSettingsRepository):
    def __init__(self, file_path: str):
        if not file_path:
            raise ConfigError("initial yaml setting file missing")

        self.__initial_file_repo = YamlInternalSettingsRepository(file_path)
        self.__settings: InternalSettings = self.__initial_file_repo.get()

    def get(self) -> InternalSettings:
        return self.__settings

    def save(self, settings: InternalSettings):
        self.__settings = settings
