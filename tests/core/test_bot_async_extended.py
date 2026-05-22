import pytest
from unittest.mock import AsyncMock, patch
from parkbot.core.bot import RPABotCore
from parkbot.config.models import MonitorSettings, InternalSettings
from parkbot.dao_impl.chat.repo_impls import InMemoryFeishuMessageRepository
import asyncio


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
async def test_setup_browser():
    """测试设置浏览器"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)

    with patch("playwright.async_api.async_playwright") as mock_pw:
        mock_instance = AsyncMock()
        mock_pw.return_value.start = AsyncMock(return_value=mock_instance)

        mock_context = AsyncMock()
        mock_instance.chromium.launch_persistent_context = AsyncMock(
            return_value=mock_context
        )

        mock_page = AsyncMock()
        mock_context.pages = [mock_page]

        await bot._setup_browser()

        assert bot._playwright == mock_instance
        assert bot._context == mock_context
        assert bot._page == mock_page
        mock_instance.chromium.launch_persistent_context.assert_called_once()


@pytest.mark.asyncio
async def test_navigate_to_feishu_success():
    """测试导航到飞书成功"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    bot._page = AsyncMock()

    await bot._navigate_to_feishu()

    bot._page.goto.assert_called_once()
    bot._page.wait_for_selector.assert_called_once()


@pytest.mark.asyncio
async def test_navigate_to_feishu_closed_browser():
    """测试导航到飞书时浏览器已关闭"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    bot._page = AsyncMock()
    bot._page.goto.side_effect = Exception(
        "Target page, context or browser has been closed"
    )
    bot._is_running = True

    await bot._navigate_to_feishu()

    assert bot.is_running is False


@pytest.mark.asyncio
async def test_navigate_to_feishu_aborted():
    """测试导航到飞书时被中止"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    bot._page = AsyncMock()
    bot._page.goto.side_effect = Exception("net::ERR_ABORTED")
    bot._is_running = True

    await bot._navigate_to_feishu()

    assert bot.is_running is False


@pytest.mark.asyncio
async def test_navigate_to_feishu_login_timeout():
    """测试导航到飞书登录超时"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    bot._page = AsyncMock()
    bot._page.wait_for_selector.side_effect = Exception("Timeout")

    await bot._navigate_to_feishu()
    # Should not raise exception, just log


@pytest.mark.asyncio
async def test_navigate_to_group_not_found():
    """测试群组未找到"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    bot._page = AsyncMock()
    bot._page.wait_for_selector.return_value = None

    result = await bot._navigate_to_group("missing_group")
    assert result is False


@pytest.mark.asyncio
async def test_get_messages_no_wrappers():
    """测试获取消息时无包装元素"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    bot._page = AsyncMock()
    bot._page.query_selector_all.return_value = []

    messages = await bot._get_messages("test")
    assert messages == []


@pytest.mark.asyncio
async def test_get_messages_unseen_only():
    """测试仅获取未见过的消息"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    bot._page = AsyncMock()

    mock_new = AsyncMock()
    mock_new.get_attribute.return_value = "msg_new"
    mock_text_el = AsyncMock()
    mock_text_el.inner_text.return_value = "New Message"
    mock_new.query_selector.return_value = mock_text_el

    bot._page.query_selector_all.return_value = [mock_new]

    messages = await bot._get_messages("test")
    assert len(messages) == 1
    assert messages[0]["id"] == "msg_new"


@pytest.mark.asyncio
async def test_react_not_found():
    """测试点赞按钮未找到"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    mock_el = AsyncMock()
    mock_el.evaluate_handle.return_value = None

    success = await bot._react(mock_el)
    assert success is False


@pytest.mark.asyncio
async def test_run_loop_stop():
    """测试运行循环停止"""
    monitor_settings = create_monitor_settings(check_interval=0.1)
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    bot._is_running = True

    # Mock methods to avoid actual browser interaction
    with patch.object(bot, "_get_messages", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []

        # Run loop in a task and stop it after one iteration
        loop_task = asyncio.create_task(bot._run_loop())
        await asyncio.sleep(0.2)
        bot.stop()
        await loop_task

        assert bot.is_running is False


@pytest.mark.asyncio
async def test_cleanup():
    """测试资源清理"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    bot._context = AsyncMock()
    bot._playwright = AsyncMock()

    await bot._cleanup()

    bot._context.close.assert_called_once()
    bot._playwright.stop.assert_called_once()


@pytest.mark.asyncio
async def test_start_method():
    """测试 start 方法启动线程"""
    monitor_settings = create_monitor_settings()
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    with patch("threading.Thread") as mock_thread:
        bot.start()
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()


@pytest.mark.asyncio
async def test_run_loop_exception_handling():
    """测试运行循环中的异常处理"""
    monitor_settings = create_monitor_settings(check_interval=0.01)
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    bot._is_running = True

    with patch.object(bot, "_get_messages", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Generic error")

        loop_task = asyncio.create_task(bot._run_loop())
        await asyncio.sleep(0.05)
        bot.stop()
        await loop_task


@pytest.mark.asyncio
async def test_run_loop_browser_closed_exception():
    """测试运行循环中浏览器关闭异常"""
    monitor_settings = create_monitor_settings(check_interval=0.01)
    internal_settings = create_internal_settings()
    message_repo = InMemoryFeishuMessageRepository()
    bot = RPABotCore(monitor_settings, internal_settings, message_repo)
    bot._is_running = True

    with patch.object(bot, "_get_messages", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception(
            "Target page, context or browser has been closed"
        )

        loop_task = asyncio.create_task(bot._run_loop())
        await asyncio.sleep(0.05)
        # Should break loop automatically
        await loop_task
        assert bot.is_running is False
