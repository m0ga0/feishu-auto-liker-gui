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
    def __init__(
        self, monitor: IMonitorSettingsRepository, internal: IInternalSettingsRepository
    ):
        self.monitor = monitor
        self.internal = internal
