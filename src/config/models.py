from pydantic import BaseModel
from typing import List


class MonitorSettings(BaseModel):
    patterns: List[str]
    reaction_emoji: str
    check_interval: float
    max_messages_per_check: int


class InternalSettings(BaseModel):
    browser_user_data_dir: str = "./feishu_browser_data"
    browser_win_width: int = 1280
    browser_win_height: int = 800
    logging_level: str = "INFO"
    logging_dir: str = "rpa_bot.log"


class AppConfig(BaseModel):
    monitor: MonitorSettings
    internal: InternalSettings
