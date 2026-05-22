"""Additional tests for bot.py to increase coverage"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from parkbot.core.bot import RPABotCore
from parkbot.config.models import MonitorSettings, InternalSettings
from parkbot.chat.models import FeishuMessage


class TestRPABotCoreErrorHandling:
    """Test error handling paths in RPABotCore"""

    @pytest.fixture
    def bot(self):
        monitor_settings = MonitorSettings(
            patterns=["test"],
            reaction_emoji="👍",
            check_interval=1.0,
            max_messages_per_check=10,
        )
        internal_settings = InternalSettings(
            browser_user_data_dir="test_data",
            browser_win_width=800,
            browser_win_height=600,
            logging_level="INFO",
            logging_dir="logs",
            win_title="Test",
            win_width=800,
            win_height=600,
            win_min_width=400,
            win_min_height=300,
            appearance_mode="System",
            color_theme="blue",
        )
        message_repo = MagicMock()
        log_callback = MagicMock()

        bot = RPABotCore(
            monitor_settings=monitor_settings,
            internal_settings=internal_settings,
            message_repo=message_repo,
            log_callback=log_callback,
        )
        return bot

    @pytest.mark.asyncio
    async def test_navigate_to_feishu_browser_closed_error(self, bot):
        """Test _navigate_to_feishu handles browser closed error"""
        bot._page = MagicMock()
        bot._page.goto = AsyncMock(
            side_effect=Exception("Target page, context or browser has been closed")
        )

        await bot._navigate_to_feishu()

        assert bot._is_running is False

    @pytest.mark.asyncio
    async def test_navigate_to_feishu_net_err_aborted(self, bot):
        """Test _navigate_to_feishu handles net::ERR_ABORTED"""
        bot._page = MagicMock()
        bot._page.goto = AsyncMock(side_effect=Exception("net::ERR_ABORTED"))

        await bot._navigate_to_feishu()

        assert bot._is_running is False

    @pytest.mark.asyncio
    async def test_navigate_to_feishu_login_browser_closed(self, bot):
        """Test login wait handles browser closed"""
        bot._page = MagicMock()
        bot._page.goto = AsyncMock()
        bot._page.wait_for_selector = AsyncMock(
            side_effect=Exception("Target page, context or browser has been closed")
        )

        await bot._navigate_to_feishu()

        assert bot._is_running is False

    @pytest.mark.asyncio
    async def test_navigate_to_feishu_login_target_closed(self, bot):
        """Test login wait handles target closed"""
        bot._page = MagicMock()
        bot._page.goto = AsyncMock()
        bot._page.wait_for_selector = AsyncMock(side_effect=Exception("Target closed"))

        await bot._navigate_to_feishu()

        assert bot._is_running is False

    @pytest.mark.asyncio
    async def test_navigate_to_group_browser_closed(self, bot):
        """Test _navigate_to_group handles browser closed"""
        bot._page = MagicMock()
        bot._page.wait_for_selector = AsyncMock(
            side_effect=Exception("Target page, context or browser has been closed")
        )

        result = await bot._navigate_to_group("test_group")

        assert result is False
        assert bot._is_running is False

    @pytest.mark.asyncio
    async def test_get_messages_no_text_element(self, bot):
        """Test _get_messages skips messages without text element"""
        bot._page = MagicMock()
        mock_wrapper = MagicMock()
        mock_wrapper.query_selector = AsyncMock(return_value=None)
        bot._page.query_selector_all = AsyncMock(return_value=[mock_wrapper])

        messages = await bot._get_messages()

        assert messages == []

    @pytest.mark.asyncio
    async def test_get_messages_empty_text(self, bot):
        """Test _get_messages skips messages with empty text"""
        bot._page = MagicMock()
        mock_wrapper = MagicMock()
        mock_text_el = MagicMock()
        mock_text_el.inner_text = AsyncMock(return_value="   ")
        mock_wrapper.query_selector = AsyncMock(return_value=mock_text_el)
        bot._page.query_selector_all = AsyncMock(return_value=[mock_wrapper])

        messages = await bot._get_messages()

        assert messages == []

    @pytest.mark.asyncio
    async def test_get_messages_wrapper_exception(self, bot):
        """Test _get_messages handles wrapper exception"""
        bot._page = MagicMock()
        mock_wrapper = MagicMock()
        mock_wrapper.query_selector = AsyncMock(side_effect=Exception("Test error"))
        bot._page.query_selector_all = AsyncMock(return_value=[mock_wrapper])

        messages = await bot._get_messages()

        assert messages == []

    @pytest.mark.asyncio
    async def test_get_messages_outer_exception_browser_closed(self, bot):
        """Test _get_messages handles outer browser closed exception"""
        bot._page = MagicMock()
        bot._page.query_selector_all = AsyncMock(
            side_effect=Exception("Target page, context or browser has been closed")
        )

        messages = await bot._get_messages()

        assert bot._is_running is False
        assert messages == []

    @pytest.mark.asyncio
    async def test_get_messages_outer_exception_target_closed(self, bot):
        """Test _get_messages handles outer target closed exception"""
        bot._page = MagicMock()
        bot._page.query_selector_all = AsyncMock(side_effect=Exception("Target closed"))

        messages = await bot._get_messages()

        assert bot._is_running is False
        assert messages == []

    @pytest.mark.asyncio
    async def test_get_messages_outer_exception_other(self, bot):
        """Test _get_messages handles other outer exceptions"""
        bot._page = MagicMock()
        bot._page.query_selector_all = AsyncMock(side_effect=Exception("Other error"))

        messages = await bot._get_messages()

        assert messages == []


class TestRPABotCoreExtractMessageId:
    """Test _extract_message_id method"""

    @pytest.fixture
    def bot(self):
        monitor_settings = MonitorSettings(
            patterns=["test"],
            reaction_emoji="👍",
            check_interval=1.0,
            max_messages_per_check=10,
        )
        internal_settings = MagicMock()
        message_repo = MagicMock()

        bot = RPABotCore(
            monitor_settings=monitor_settings,
            internal_settings=internal_settings,
            message_repo=message_repo,
        )
        return bot

    @pytest.mark.asyncio
    async def test_extract_message_id_nested_element(self, bot):
        """Test extracting ID from nested element"""
        mock_element = MagicMock()
        mock_element.get_attribute = AsyncMock(
            side_effect=[None, None, None, None, None]
        )

        mock_nested = MagicMock()
        mock_nested.get_attribute = AsyncMock(return_value="nested_id_123")
        mock_element.query_selector = AsyncMock(return_value=mock_nested)

        result = await bot._extract_message_id(mock_element, "test text")

        assert result == "nested_id_123"

    @pytest.mark.asyncio
    async def test_extract_message_id_nested_exception(self, bot):
        """Test handling exception in nested element lookup"""
        mock_element = MagicMock()
        mock_element.get_attribute = AsyncMock(
            side_effect=[None, None, None, None, None]
        )
        mock_element.query_selector = AsyncMock(side_effect=Exception("Query failed"))

        result = await bot._extract_message_id(mock_element, "test text")

        # Should fall back to timestamp_hash format
        assert "_" in result

    @pytest.mark.asyncio
    async def test_extract_message_id_fallback_to_hash(self, bot):
        """Test fallback to timestamp_hash when no ID found"""
        mock_element = MagicMock()
        mock_element.get_attribute = AsyncMock(return_value=None)
        mock_element.query_selector = AsyncMock(return_value=None)

        result = await bot._extract_message_id(mock_element, "test text")

        # Should be in format: timestamp_hash
        parts = result.split("_")
        assert len(parts) == 2
        assert parts[0].isdigit()


class TestRPABotCoreReact:
    """Test _react method"""

    @pytest.fixture
    def bot(self):
        monitor_settings = MonitorSettings(
            patterns=["test"],
            reaction_emoji="👍",
            check_interval=1.0,
            max_messages_per_check=10,
        )
        internal_settings = MagicMock()
        message_repo = MagicMock()

        bot = RPABotCore(
            monitor_settings=monitor_settings,
            internal_settings=internal_settings,
            message_repo=message_repo,
        )
        return bot

    @pytest.mark.asyncio
    async def test_react_exception(self, bot):
        """Test _react handles exceptions"""
        mock_element = MagicMock()
        mock_element.hover = AsyncMock(side_effect=Exception("Hover failed"))

        result = await bot._react(mock_element)

        assert result is False


class TestRPABotCoreProcessMessageBatch:
    """Test _process_message_batch method"""

    @pytest.fixture
    def bot(self):
        monitor_settings = MonitorSettings(
            patterns=["test", "re:pattern.*"],
            reaction_emoji="👍",
            check_interval=1.0,
            max_messages_per_check=10,
        )
        internal_settings = MagicMock()
        message_repo = MagicMock()
        message_repo.get_by_ids.return_value = {}
        message_repo.exists_batch.return_value = {}

        bot = RPABotCore(
            monitor_settings=monitor_settings,
            internal_settings=internal_settings,
            message_repo=message_repo,
        )
        return bot

    @pytest.mark.asyncio
    async def test_process_batch_no_matches(self, bot):
        """Test processing batch with no pattern matches"""
        messages = [
            {"id": "msg1", "text": "no match here", "element": MagicMock()},
            {"id": "msg2", "text": "also no match", "element": MagicMock()},
        ]

        await bot._process_message_batch(messages, "test_group")

        # All messages should be saved as checked (no match)
        assert bot.message_repo.save_batch.called
        saved_messages = bot.message_repo.save_batch.call_args[0][0]
        assert len(saved_messages) == 2

    @pytest.mark.asyncio
    async def test_process_batch_with_matches(self, bot):
        """Test processing batch with pattern matches"""
        messages = [
            {"id": "msg1", "text": "test message", "element": MagicMock()},
            {"id": "msg2", "text": "no match", "element": MagicMock()},
        ]

        bot._react = AsyncMock(return_value=True)

        await bot._process_message_batch(messages, "test_group")

        # Should have reacted to matched message
        assert bot._react.called

    @pytest.mark.asyncio
    async def test_process_batch_already_reacted_exists(self, bot):
        """Test skipping messages that already exist and are reacted"""
        existing = FeishuMessage(id="msg1", text="test")
        existing.mark_processed(is_reacted=True, target_pattern="matched")
        bot.message_repo.exists_batch.return_value = {"msg1": True}
        bot.message_repo.get_by_ids.return_value = {"msg1": existing}

        messages = [
            {"id": "msg1", "text": "test message", "element": MagicMock()},
        ]

        bot._react = AsyncMock()

        await bot._process_message_batch(messages, "test_group")

        # Should skip already reacted
        bot._react.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_batch_reaction_failure(self, bot):
        """Test handling reaction failure"""
        messages = [
            {"id": "msg1", "text": "test message", "element": MagicMock()},
        ]

        bot._react = AsyncMock(side_effect=Exception("Reaction failed"))

        await bot._process_message_batch(messages, "test_group")

        # Should log failure and continue
        assert bot.fail_count == 1

    @pytest.mark.asyncio
    async def test_process_batch_save_error(self, bot):
        """Test handling save error"""
        messages = [
            {"id": "msg1", "text": "no match", "element": MagicMock()},
        ]

        bot.message_repo.save_batch.side_effect = Exception("Save failed")

        await bot._process_message_batch(messages, "test_group")

        # Should not raise

    @pytest.mark.asyncio
    async def test_process_batch_update_existing_no_match(self, bot):
        """Test updating existing message that now doesn't match"""
        existing = FeishuMessage(id="msg1", text="test message")
        existing.mark_processed(is_reacted=True, target_pattern="matched")
        bot.message_repo.get_by_ids.return_value = {"msg1": existing}

        messages = [
            {"id": "msg1", "text": "completely different text", "element": MagicMock()},
        ]

        await bot._process_message_batch(messages, "test_group")

        # Should update the existing message
        assert bot.message_repo.save_batch.called


class TestRPABotCoreStartStop:
    """Test start and stop methods"""

    @pytest.fixture
    def bot(self):
        monitor_settings = MonitorSettings(
            patterns=["test"],
            reaction_emoji="👍",
            check_interval=1.0,
            max_messages_per_check=10,
        )
        internal_settings = MagicMock()
        message_repo = MagicMock()
        stop_callback = MagicMock()

        bot = RPABotCore(
            monitor_settings=monitor_settings,
            internal_settings=internal_settings,
            message_repo=message_repo,
            stop_callback=stop_callback,
        )
        return bot

    def test_stop_sets_is_running_false(self, bot):
        """Test stop method"""
        bot._is_running = True
        bot.stop()
        assert bot._is_running is False

    @pytest.mark.asyncio
    async def test_cleanup_context_close_error(self, bot):
        """Test cleanup handles context close error"""
        bot._context = MagicMock()
        bot._context.close = AsyncMock(side_effect=Exception("Close error"))

        await bot._cleanup()

        # Should not raise

    @pytest.mark.asyncio
    async def test_cleanup_playwright_stop_error(self, bot):
        """Test cleanup handles playwright stop error"""
        bot._context = MagicMock()
        bot._context.close = AsyncMock()
        bot._playwright = MagicMock()
        bot._playwright.stop = AsyncMock(side_effect=Exception("Stop error"))

        await bot._cleanup()

        # Should not raise

    def test_start_fatal_error(self, bot):
        """Test start handles fatal error in run_async"""
        import threading

        def mock_run_async():
            raise Exception("Fatal browser error")

        # Patch threading.Thread to capture the target
        original_thread_init = threading.Thread.__init__

        def patched_thread_init(self, *args, **kwargs):
            if "target" in kwargs:
                # Replace the target with our mock
                kwargs["target"] = mock_run_async
            original_thread_init(self, *args, **kwargs)

        with patch.object(threading.Thread, "__init__", patched_thread_init):
            bot.start()
            # Wait briefly for thread
            import time

            time.sleep(0.1)

        # Thread should have been started
        assert hasattr(bot, "_thread")
