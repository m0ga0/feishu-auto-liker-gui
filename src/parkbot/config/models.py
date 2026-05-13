from pydantic import BaseModel
from typing import List


class MonitorSettings(BaseModel):
    patterns: List[str]
    reaction_emoji: str
    check_interval: float
    max_messages_per_check: int


class InternalSettings(BaseModel):
    browser_user_data_dir: str
    browser_win_width: int
    browser_win_height: int
    logging_level: str
    logging_dir: str
    win_title: str
    win_width: int
    win_height: int
    win_min_width: int
    win_min_height: int
    appearance_mode: str
    color_theme: str
