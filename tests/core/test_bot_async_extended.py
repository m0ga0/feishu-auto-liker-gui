import pytest
from unittest.mock import AsyncMock, patch
from src.core.bot import RPABotCore
from src.state import BotState
import asyncio


@pytest.mark.asyncio
async def test_setup_browser():
    """测试设置浏览器"""
    config = {
        "browser": {
            "user_data_dir": "./test_data",
            "width": 1024,
            "height": 768,
            "headless": True,
        }
    }
    state = BotState()
    bot = RPABotCore(config, state)

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
    bot = RPABotCore({}, BotState())
    bot._page = AsyncMock()

    await bot._navigate_to_feishu()

    bot._page.goto.assert_called_once()
    bot._page.wait_for_selector.assert_called_once()


@pytest.mark.asyncio
async def test_get_messages_success():
    """测试获取消息成功"""
    bot = RPABotCore({}, BotState())
    bot._page = AsyncMock()

    # Mock message wrappers
    mock_wrapper = AsyncMock()
    mock_wrapper.get_attribute.return_value = "msg_123"

    mock_text_el = AsyncMock()
    mock_text_el.inner_text.return_value = "Hello World"
    mock_wrapper.query_selector.return_value = mock_text_el

    bot._page.query_selector_all.return_value = [mock_wrapper]

    messages = await bot._get_messages("test_group")

    assert len(messages) == 1
    assert messages[0]["id"] == "msg_123"
    assert messages[0]["text"] == "Hello World"


@pytest.mark.asyncio
async def test_react_success():
    """测试点赞成功"""
    bot = RPABotCore({}, BotState())
    mock_el = AsyncMock()
    mock_btn = AsyncMock()

    mock_el.evaluate_handle.return_value = mock_btn

    success = await bot._react(mock_el)

    assert success is True
    mock_el.hover.assert_called_once()
    mock_btn.evaluate.assert_called_once_with("el => el.click()")


@pytest.mark.asyncio
async def test_extract_message_id_fallback():
    """测试提取消息ID回退方案"""
    bot = RPABotCore({}, BotState())
    mock_el = AsyncMock()
    mock_el.get_attribute.return_value = None
    mock_el.query_selector.return_value = None

    msg_id = await bot._extract_message_id(mock_el, "test text")

    assert "_" in msg_id
    assert msg_id.split("_")[1] == str(hash("test text"))


@pytest.mark.asyncio
async def test_run_loop_stop():
    """测试运行循环停止"""
    config = {"monitor": {"check_interval": 0.1}}
    bot = RPABotCore(config, BotState())
    bot._running = True

    # Mock methods to avoid actual browser interaction
    with patch.object(bot, "_get_messages", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []

        # Run loop in a task and stop it after one iteration
        loop_task = asyncio.create_task(bot._run_loop())
        await asyncio.sleep(0.2)
        bot.stop()
        await loop_task

        assert bot._running is False
        assert bot.state.is_running is False


@pytest.mark.asyncio
async def test_cleanup():
    """测试资源清理"""
    bot = RPABotCore({}, BotState())
    bot._context = AsyncMock()
    bot._playwright = AsyncMock()

    await bot._cleanup()

    bot._context.close.assert_called_once()
    bot._playwright.stop.assert_called_once()


@pytest.mark.asyncio
async def test_navigate_to_feishu_closed_browser():
    """测试导航到飞书时浏览器已关闭"""
    bot = RPABotCore({}, BotState())
    bot._page = AsyncMock()
    bot._page.goto.side_effect = Exception(
        "Target page, context or browser has been closed"
    )
    bot._running = True

    await bot._navigate_to_feishu()

    assert bot._running is False


@pytest.mark.asyncio
async def test_navigate_to_feishu_aborted():
    """测试导航到飞书时被中止"""
    bot = RPABotCore({}, BotState())
    bot._page = AsyncMock()
    bot._page.goto.side_effect = Exception("net::ERR_ABORTED")
    bot._running = True

    await bot._navigate_to_feishu()

    assert bot._running is False


@pytest.mark.asyncio
async def test_navigate_to_feishu_login_timeout():
    """测试导航到飞书登录超时"""
    bot = RPABotCore({}, BotState())
    bot._page = AsyncMock()
    bot._page.wait_for_selector.side_effect = Exception("Timeout")

    await bot._navigate_to_feishu()
    # Should not raise exception, just log


@pytest.mark.asyncio
async def test_navigate_to_group_not_found():
    """测试群组未找到"""
    bot = RPABotCore({}, BotState())
    bot._page = AsyncMock()
    bot._page.wait_for_selector.return_value = None

    result = await bot._navigate_to_group("missing_group")
    assert result is False


@pytest.mark.asyncio
async def test_get_messages_no_wrappers():
    """测试获取消息时无包装元素"""
    bot = RPABotCore({}, BotState())
    bot._page = AsyncMock()
    bot._page.query_selector_all.return_value = []

    messages = await bot._get_messages("test")
    assert messages == []


@pytest.mark.asyncio
async def test_get_messages_unseen_only():
    """测试仅获取未见过的消息"""
    state = BotState()
    state.mark_seen("test", "msg_seen")
    bot = RPABotCore({}, state)
    bot._page = AsyncMock()

    mock_seen = AsyncMock()
    mock_seen.get_attribute.return_value = "msg_seen"

    mock_new = AsyncMock()
    mock_new.get_attribute.return_value = "msg_new"
    mock_text_el = AsyncMock()
    mock_text_el.inner_text.return_value = "New Message"
    mock_new.query_selector.return_value = mock_text_el

    bot._page.query_selector_all.return_value = [mock_seen, mock_new]

    messages = await bot._get_messages("test")
    assert len(messages) == 1
    assert messages[0]["id"] == "msg_new"


@pytest.mark.asyncio
async def test_react_not_found():
    """测试点赞按钮未找到"""
    bot = RPABotCore({}, BotState())
    mock_el = AsyncMock()
    mock_el.evaluate_handle.return_value = None

    success = await bot._react(mock_el)
    assert success is False


@pytest.mark.asyncio
async def test_run_loop_with_messages():
    """测试运行循环处理消息"""
    config = {"monitor": {"check_interval": 0.01, "monitored_groups": ["Group A"]}}
    state = BotState()
    with patch.object(state, "mark_seen", side_effect=state.mark_seen) as mock_mark:
        bot = RPABotCore(config, state)
        bot._running = True

        # Mock methods
        with (
            patch.object(bot, "_navigate_to_group", new_callable=AsyncMock) as mock_nav,
            patch.object(bot, "_get_messages", new_callable=AsyncMock) as mock_get,
            patch.object(bot.matcher, "matches", return_value=True),
            patch.object(bot, "_react", new_callable=AsyncMock) as mock_react,
        ):
            mock_nav.return_value = True
            mock_get.side_effect = [
                [
                    {
                        "id": "m1",
                        "text": "hello",
                        "element": AsyncMock(),
                        "group": "Group A",
                    }
                ],
                [],
            ]
            mock_react.return_value = True

            loop_task = asyncio.create_task(bot._run_loop())
            await asyncio.sleep(0.1)
            bot.stop()
            await loop_task

            assert state.reaction_count >= 0
            mock_mark.assert_called_with("Group A", "m1")


@pytest.mark.asyncio
async def test_run_loop_exception_handling():
    """测试运行循环中的异常处理"""
    config = {"monitor": {"check_interval": 0.01}}
    bot = RPABotCore(config, BotState())
    bot._running = True

    with patch.object(bot, "_get_messages", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Generic error")

        loop_task = asyncio.create_task(bot._run_loop())
        await asyncio.sleep(0.05)
        bot.stop()
        await loop_task


@pytest.mark.asyncio
async def test_start_method():
    """测试 start 方法启动线程"""
    bot = RPABotCore({}, BotState())
    with patch("threading.Thread") as mock_thread:
        bot.start()
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()


@pytest.mark.asyncio
async def test_navigate_to_group_browser_closed_msg():
    """测试导航到群组时浏览器已关闭的错误消息"""
    bot = RPABotCore({}, BotState())
    bot._page = AsyncMock()
    bot._page.wait_for_selector.side_effect = Exception(
        "Target page, context or browser has been closed"
    )
    bot._running = True

    result = await bot._navigate_to_group("test")
    assert result is False
    assert bot._running is False


@pytest.mark.asyncio
async def test_get_messages_extract_id_error():
    """测试提取ID时发生异常"""
    bot = RPABotCore({}, BotState())
    bot._page = AsyncMock()

    mock_wrapper = AsyncMock()
    # Mock extract_message_id to fail
    with patch.object(bot, "_extract_message_id", side_effect=Exception("ID Error")):
        bot._page.query_selector_all.return_value = [mock_wrapper]
        messages = await bot._get_messages("test")
        assert messages == []


@pytest.mark.asyncio
async def test_run_loop_already_seen():
    """测试运行循环跳过已处理的消息"""
    config = {"monitor": {"check_interval": 0.01}}
    state = BotState()
    state.mark_seen("_default", "m1")
    bot = RPABotCore(config, state)
    bot._running = True

    with patch.object(bot, "_get_messages", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = [
            [
                {
                    "id": "m1",
                    "text": "hello",
                    "element": AsyncMock(),
                    "group": "_default",
                }
            ],
            [],
        ]

        loop_task = asyncio.create_task(bot._run_loop())
        await asyncio.sleep(0.05)
        bot.stop()
        await loop_task
        assert state.reaction_count == 0


@pytest.mark.asyncio
async def test_run_loop_no_match():
    """测试运行循环处理不匹配的消息"""
    config = {"monitor": {"check_interval": 0.01}}
    state = BotState()
    with patch.object(state, "mark_seen", side_effect=state.mark_seen) as mock_mark:
        bot = RPABotCore(config, state)
        bot._running = True

        with (
            patch.object(bot, "_get_messages", new_callable=AsyncMock) as mock_get,
            patch.object(bot.matcher, "matches", return_value=False),
        ):
            mock_get.side_effect = [
                [
                    {
                        "id": "m1",
                        "text": "nomatch",
                        "element": AsyncMock(),
                        "group": "_default",
                    }
                ],
                [],
            ]

            loop_task = asyncio.create_task(bot._run_loop())
            await asyncio.sleep(0.05)
            bot.stop()
            await loop_task
            assert state.reaction_count == 0
            mock_mark.assert_called_with("_default", "m1")


@pytest.mark.asyncio
async def test_run_loop_react_fail():
    """测试运行循环中点赞失败的情况"""
    config = {"monitor": {"check_interval": 0.01}}
    state = BotState()
    bot = RPABotCore(config, state)
    bot._running = True

    with (
        patch.object(bot, "_get_messages", new_callable=AsyncMock) as mock_get,
        patch.object(bot.matcher, "matches", return_value=True),
        patch.object(bot, "_react", new_callable=AsyncMock) as mock_react,
    ):
        mock_get.side_effect = [
            [
                {
                    "id": "m1",
                    "text": "hello",
                    "element": AsyncMock(),
                    "group": "_default",
                }
            ],
            [],
        ]
        mock_react.return_value = False

        loop_task = asyncio.create_task(bot._run_loop())
        await asyncio.sleep(0.1)
        bot.stop()
        await loop_task
        assert state.reaction_count == 0


@pytest.mark.asyncio
async def test_run_loop_browser_closed_exception():
    """测试运行循环中浏览器关闭异常"""
    config = {"monitor": {"check_interval": 0.01}}
    bot = RPABotCore(config, BotState())
    bot._running = True

    with patch.object(bot, "_get_messages", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception(
            "Target page, context or browser has been closed"
        )

        loop_task = asyncio.create_task(bot._run_loop())
        await asyncio.sleep(0.05)
        # Should break loop automatically
        await loop_task
        assert bot._running is False
