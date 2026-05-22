"""Browser Exception Handling Tests"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from parkbot.config.models import MonitorSettings, InternalSettings
from parkbot.core.bot import RPABotCore
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


class MockPage:
    """Mock Playwright Page"""

    def __init__(self, error_on_goto=None, error_on_wait=None):
        self.error_on_goto = error_on_goto
        self.error_on_wait = error_on_wait
        self.goto_count = 0
        self.wait_count = 0

    async def goto(self, url, **kwargs):
        self.goto_count += 1
        if self.error_on_goto:
            raise Exception(self.error_on_goto)
        return MagicMock()

    async def wait_for_selector(self, selector, timeout=0):
        self.wait_count += 1
        if self.error_on_wait:
            raise Exception(self.error_on_wait)
        return MagicMock()


class TestBrowserExceptionHandling:
    """Browser exception handling tests"""

    @pytest.mark.asyncio
    async def test_navigate_handles_browser_closed(self):
        """Test _navigate_to_feishu handles browser closed exception"""
        log_messages = []

        def mock_log(msg):
            log_messages.append(msg)

        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(
            monitor_settings, internal_settings, message_repo, log_callback=mock_log
        )
        bot._page = MockPage(
            error_on_goto="Target page, context or browser has been closed"
        )

        await bot._navigate_to_feishu()

        assert bot.is_running is False
        assert "⚠️ 浏览器已关闭" in log_messages

    @pytest.mark.asyncio
    async def test_navigate_handles_err_aborted(self):
        """Test _navigate_to_feishu handles net::ERR_ABORTED"""
        log_messages = []

        def mock_log(msg):
            log_messages.append(msg)

        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(
            monitor_settings, internal_settings, message_repo, log_callback=mock_log
        )
        bot._page = MockPage(error_on_goto="Page.goto: net::ERR_ABORTED")

        await bot._navigate_to_feishu()

        assert bot.is_running is False
        assert "⚠️ 页面导航中断" in log_messages

    @pytest.mark.asyncio
    async def test_navigate_group_handles_browser_closed(self):
        """Test _navigate_to_group handles browser closed"""
        log_messages = []

        def mock_log(msg):
            log_messages.append(msg)

        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(
            monitor_settings, internal_settings, message_repo, log_callback=mock_log
        )
        bot._page = MockPage(
            error_on_wait="Target page, context or browser has been closed"
        )

        result = await bot._navigate_to_group("test_group")

        assert result is False
        assert bot.is_running is False
        assert "浏览器已关闭" in log_messages[0]

    @pytest.mark.asyncio
    async def test_navigate_group_handles_err_aborted(self):
        """Test _navigate_to_group handles ERR_ABORTED"""
        log_messages = []

        def mock_log(msg):
            log_messages.append(msg)

        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(
            monitor_settings, internal_settings, message_repo, log_callback=mock_log
        )
        bot._page = MockPage(error_on_wait="net::ERR_ABORTED")

        result = await bot._navigate_to_group("test_group")

        assert result is False
        assert "页面导航中断" in log_messages[0]

    @pytest.mark.asyncio
    async def test_get_messages_handles_browser_closed(self):
        """Test _get_messages handles browser closed"""
        log_messages = []

        def mock_log(msg):
            log_messages.append(msg)

        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(
            monitor_settings, internal_settings, message_repo, log_callback=mock_log
        )
        bot._page = MagicMock()
        bot._page.query_selector_all = AsyncMock(
            side_effect=Exception("Target page, context or browser has been closed")
        )

        messages = await bot._get_messages("test_group")

        assert messages == []
        assert bot.is_running is False
        assert "浏览器已关闭" in log_messages[0]

    @pytest.mark.asyncio
    async def test_login_timeout_still_continues(self):
        """Test login timeout doesn't stop the bot when timeout is generic"""
        log_messages = []

        def mock_log(msg):
            log_messages.append(msg)

        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(
            monitor_settings, internal_settings, message_repo, log_callback=mock_log
        )
        bot._page = MockPage(
            error_on_wait="TimeoutError: waiting for selector timed out"
        )

        await bot._navigate_to_feishu()

        # For TimeoutError, it should still print timeout message but keep running
        assert any("登录超时" in msg for msg in log_messages)

    def test_stop_sets_running_false(self):
        """Test stop() sets _is_running to False"""
        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(monitor_settings, internal_settings, message_repo)
        bot._is_running = True

        bot.stop()

        assert bot.is_running is False

    def test_initial_running_state(self):
        """Test initial _is_running state is False"""
        monitor_settings = create_monitor_settings()
        internal_settings = create_internal_settings()
        message_repo = InMemoryFeishuMessageRepository()
        bot = RPABotCore(monitor_settings, internal_settings, message_repo)
        assert bot.is_running is False
