import pytest
from unittest.mock import AsyncMock
from parkbot.core.bot import RPABotCore
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


@pytest.mark.asyncio
async def test_navigate_to_group_success():
    """测试导航到群组成功"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)

    # Mock page with proper async behavior
    from unittest.mock import AsyncMock

    bot._page = AsyncMock()

    # Mock chat_item that supports async click
    chat_item = AsyncMock()
    chat_item.click = AsyncMock()
    bot._page.wait_for_selector = AsyncMock(return_value=chat_item)

    result = await bot._navigate_to_group("test_group")

    assert result is True
    bot._page.wait_for_selector.assert_called_once()
    chat_item.click.assert_called_once()


@pytest.mark.asyncio
async def test_navigate_to_group_failure():
    """测试导航到群组失败"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)

    # Mock page
    bot._page = AsyncMock()
    bot._page.wait_for_selector.side_effect = Exception("Not found")

    result = await bot._navigate_to_group("test_group")

    assert result is False


@pytest.mark.asyncio
async def test_navigate_to_group_browser_closed():
    """测试导航到群组浏览器关闭"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    bot._is_running = True

    # Mock page
    bot._page = AsyncMock()
    bot._page.wait_for_selector.side_effect = Exception(
        "Target page, context or browser has been closed"
    )

    result = await bot._navigate_to_group("test_group")

    assert result is False
    assert bot.is_running is False
