from abc import ABC, abstractmethod
from typing import Optional
from .models import MonitorSettings, InternalSettings


class IMonitorSettingsRepository(ABC):
    @abstractmethod
    def get(self) -> Optional[MonitorSettings]: ...
    @abstractmethod
    def save(self, settings: MonitorSettings): ...


class IInternalSettingsRepository(ABC):
    @abstractmethod
    def get(self) -> InternalSettings: ...
    @abstractmethod
    def save(self, settings: InternalSettings): ...


class AppSettingsRepository:
    def __init__(
        self, monitor: IMonitorSettingsRepository, internal: IInternalSettingsRepository
    ):
        self.monitor = monitor
        self.internal = internal
