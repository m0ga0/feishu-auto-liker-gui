import pytest
from unittest.mock import AsyncMock
from src.core.bot import RPABotCore
from src.state import BotState


@pytest.mark.asyncio
async def test_navigate_to_group_success():
    """测试导航到群组成功"""
    config = {"monitor": {"patterns": ["test"]}}
    state = BotState()
    bot = RPABotCore(config, state)

    # Mock page
    bot._page = AsyncMock()

    # Mock chat_item
    chat_item = AsyncMock()
    bot._page.wait_for_selector.return_value = chat_item

    result = await bot._navigate_to_group("test_group")

    assert result is True
    bot._page.wait_for_selector.assert_called_once()
    chat_item.click.assert_called_once()


@pytest.mark.asyncio
async def test_navigate_to_group_failure():
    """测试导航到群组失败"""
    config = {"monitor": {"patterns": ["test"]}}
    state = BotState()
    bot = RPABotCore(config, state)

    # Mock page
    bot._page = AsyncMock()
    bot._page.wait_for_selector.side_effect = Exception("Not found")

    result = await bot._navigate_to_group("test_group")

    assert result is False
    assert bot._running is False  # Expecting False


@pytest.mark.asyncio
async def test_navigate_to_group_browser_closed():
    """测试导航到群组浏览器关闭"""
    config = {"monitor": {"patterns": ["test"]}}
    state = BotState()
    bot = RPABotCore(config, state)
    bot._running = True

    # Mock page
    bot._page = AsyncMock()
    bot._page.wait_for_selector.side_effect = Exception(
        "Target page, context or browser has been closed"
    )

    result = await bot._navigate_to_group("test_group")

    assert result is False
    assert bot._running is False
