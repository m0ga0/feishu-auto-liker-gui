"""Browser Exception Handling Tests"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.state import BotState
from src.core.bot import RPABotCore


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

        bot = RPABotCore({}, BotState(), log_callback=mock_log)
        bot._page = MockPage(
            error_on_goto="Target page, context or browser has been closed"
        )

        await bot._navigate_to_feishu()

        assert bot._running is False
        assert "⚠️ 浏览器已关闭" in log_messages

    @pytest.mark.asyncio
    async def test_navigate_handles_err_aborted(self):
        """Test _navigate_to_feishu handles net::ERR_ABORTED"""
        log_messages = []

        def mock_log(msg):
            log_messages.append(msg)

        bot = RPABotCore({}, BotState(), log_callback=mock_log)
        bot._page = MockPage(error_on_goto="Page.goto: net::ERR_ABORTED")

        await bot._navigate_to_feishu()

        assert bot._running is False
        assert "⚠️ 页面导航中断" in log_messages

    @pytest.mark.asyncio
    async def test_navigate_group_handles_browser_closed(self):
        """Test _navigate_to_group handles browser closed"""
        log_messages = []

        def mock_log(msg):
            log_messages.append(msg)

        bot = RPABotCore({}, BotState(), log_callback=mock_log)
        bot._page = MockPage(
            error_on_wait="Target page, context or browser has been closed"
        )

        result = await bot._navigate_to_group("test_group")

        assert result is False
        assert bot._running is False
        assert "浏览器已关闭" in log_messages[0]

    @pytest.mark.asyncio
    async def test_navigate_group_handles_err_aborted(self):
        """Test _navigate_to_group handles ERR_ABORTED"""
        log_messages = []

        def mock_log(msg):
            log_messages.append(msg)

        bot = RPABotCore({}, BotState(), log_callback=mock_log)
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

        bot = RPABotCore({}, BotState(), log_callback=mock_log)
        bot._page = MagicMock()
        bot._page.query_selector_all = AsyncMock(
            side_effect=Exception("Target page, context or browser has been closed")
        )

        messages = await bot._get_messages("test_group")

        assert messages == []
        assert bot._running is False
        assert "浏览器已关闭" in log_messages[0]

    @pytest.mark.asyncio
    async def test_login_timeout_still_continues(self):
        """Test login timeout doesn't stop the bot when timeout is generic"""
        log_messages = []

        def mock_log(msg):
            log_messages.append(msg)

        bot = RPABotCore({}, BotState(), log_callback=mock_log)
        bot._page = MockPage(
            error_on_wait="TimeoutError: waiting for selector timed out"
        )

        await bot._navigate_to_feishu()

        # For TimeoutError, it should still print timeout message but keep running
        assert any("登录超时" in msg for msg in log_messages)

    def test_stop_sets_running_false(self):
        """Test stop() sets _running to False"""
        bot = RPABotCore({}, BotState())
        bot._running = True

        bot.stop()

        assert bot._running is False

    def test_initial_running_state(self):
        """Test initial _running state is False"""
        bot = RPABotCore({}, BotState())
        assert bot._running is False
