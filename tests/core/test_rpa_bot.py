"""RPABotCore 同步接口测试"""

import pytest

from parkbot.core.bot import RPABotCore
from parkbot.core.matcher import PatternMatcher
from parkbot.config.models import MonitorSettings, InternalSettings
from parkbot.dao_impl.chat.repo_impls import InMemoryFeishuMessageRepository


def create_monitor_settings(patterns=None, **kwargs):
    """Helper to create MonitorSettings with defaults."""
    defaults = {
        "patterns": patterns or ["test"],
        "reaction_emoji": "👍",
        "check_interval": 2.0,
        "max_messages_per_check": 10,
    }
    defaults.update(kwargs)
    return MonitorSettings(**defaults)


def create_internal_settings(**kwargs):
    """Helper to create InternalSettings with defaults."""
    defaults = {
        "browser_user_data_dir": "./feishu_browser_data",
        "browser_win_width": 1280,
        "browser_win_height": 800,
        "logging_level": "INFO",
        "logging_dir": "rpa_bot.log",
        "win_title": "飞书自动点赞助手",
        "win_width": 900,
        "win_height": 700,
        "win_min_width": 800,
        "win_min_height": 600,
        "appearance_mode": "system",
        "color_theme": "blue",
    }
    defaults.update(kwargs)
    return InternalSettings(**defaults)


class TestRPABotCoreSyncInterface:
    """RPABotCore 同步接口测试"""

    def test_init_creates_matcher_with_patterns(self):
        """初始化时使用配置创建 PatternMatcher"""
        monitor_settings = create_monitor_settings(patterns=["hello", "world\\d+"])
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(monitor_settings, internal_settings, message_repo)

        assert isinstance(bot.matcher, PatternMatcher)

    def test_init_uses_empty_patterns(self):
        """配置中没有 patterns 时使用空列表"""
        monitor_settings = create_monitor_settings(patterns=[])
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(monitor_settings, internal_settings, message_repo)

        assert isinstance(bot.matcher, PatternMatcher)

    def test_matcher_is_used_for_message_matching(self):
        """PatternMatcher 用于消息匹配"""
        monitor_settings = create_monitor_settings(patterns=["车位"])
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(monitor_settings, internal_settings, message_repo)

        assert bot.matcher.matches("有车位 请联系") is True
        assert bot.matcher.matches("没有匹配") is False

    def test_regex_patterns_work(self):
        """正则表达式模式可用"""
        monitor_settings = create_monitor_settings(patterns=["车位\\d+"])
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(monitor_settings, internal_settings, message_repo)

        assert bot.matcher.matches("车位123") is True
        assert bot.matcher.matches("车位") is False

    def test_monitor_settings_stored(self):
        """监控设置被正确存储"""
        monitor_settings = create_monitor_settings(
            patterns=["test"],
            check_interval=5.0,
            max_messages_per_check=20,
        )
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(monitor_settings, internal_settings, message_repo)

        assert bot.monitor_settings.check_interval == 5.0
        assert bot.monitor_settings.max_messages_per_check == 20

    def test_internal_settings_stored(self):
        """内部设置被正确存储"""
        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings(
            browser_user_data_dir="./test_browser_data",
            browser_win_width=1920,
            browser_win_height=1080,
        )
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(monitor_settings, internal_settings, message_repo)

        assert bot.internal_settings.browser_user_data_dir == "./test_browser_data"
        assert bot.internal_settings.browser_win_width == 1920
        assert bot.internal_settings.browser_win_height == 1080

    def test_runtime_stats_initially_zero(self):
        """运行时统计初始为0"""
        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(monitor_settings, internal_settings, message_repo)

        assert bot.match_count == 0
        assert bot.reaction_count == 0
        assert bot.fail_count == 0
        assert bot.start_time is None

    def test_log_callback_is_stored(self):
        """日志回调被存储"""
        log_msgs = []

        def mock_log(msg):
            log_msgs.append(msg)

        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(
            monitor_settings, internal_settings, message_repo, log_callback=mock_log
        )

        bot.log("test message")
        assert log_msgs[0] == "test message"

    def test_stop_callback_is_stored(self):
        """停止回调被存储"""

        def mock_stop():
            pass

        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(
            monitor_settings, internal_settings, message_repo, stop_callback=mock_stop
        )

        assert callable(bot.stop_callback)

    def test_initial_running_state_false(self):
        """初始运行状态为 False"""
        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(monitor_settings, internal_settings, message_repo)

        assert bot.is_running is False

    def test_is_running_property_readonly(self):
        """is_running 属性是只读的"""
        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(monitor_settings, internal_settings, message_repo)

        # Should not be able to set directly (property is read-only)
        with pytest.raises(AttributeError):
            bot.is_running = True  # ty: ignore[invalid-assignment]

    def test_message_repo_stored(self):
        """消息仓库被正确存储"""
        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(monitor_settings, internal_settings, message_repo)

        assert bot.message_repo is message_repo
