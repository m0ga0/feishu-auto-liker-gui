"""Feishu Auto-Liker package."""

from .config import DEFAULT_CONFIG, load_config, save_config
from .config.constants import CONFIG_PATH, STATE_PATH
from .core import RPABotCore
from .core.matcher import PatternMatcher
from .core.constants import FEISHU_CHAT_URL, SELECTORS
from .installer import EnvChecker
from .state import BotState
from .gui import App

__all__ = [
    "DEFAULT_CONFIG",
    "load_config",
    "save_config",
    "CONFIG_PATH",
    "STATE_PATH",
    "RPABotCore",
    "PatternMatcher",
    "FEISHU_CHAT_URL",
    "SELECTORS",
    "EnvChecker",
    "BotState",
    "App",
]
