import asyncio
import os
import random
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, cast


from ..state import BotState
from .constants import FEISHU_CHAT_URL, SELECTORS
from .matcher import PatternMatcher


class RPABotCore:
    """
    The actual RPA bot logic. Runs in a separate thread with its own event loop.
    """

    def __init__(
        self,
        config: dict,
        state: BotState,
        log_callback: Optional[Callable[[str], None]] = None,
        stop_callback: Optional[Callable[[], None]] = None,
    ):
        self.config = config
        self.state = state
        self.log = log_callback or (lambda msg: None)
        self.stop_callback = stop_callback or (lambda: None)
        self.matcher = PatternMatcher(
            config.get("monitor", {}).get("patterns", []), log_callback=self.log
        )
        self._running = False
        self._page: object = None
        self._context = None
        self._playwright = None

    async def _setup_browser(self):
        persist_path = str(Path.home() / ".cache" / "ms-playwright")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = persist_path

        Path(persist_path).mkdir(parents=True, exist_ok=True)

        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()

        user_data_dir = self.config.get("browser", {}).get(
            "user_data_dir", "./feishu_browser_data"
        )
        Path(user_data_dir).mkdir(parents=True, exist_ok=True)

        width = self.config.get("browser", {}).get("width", 1280)
        height = self.config.get("browser", {}).get("height", 800)
        headless = self.config.get("browser", {}).get("headless", False)

        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=headless,
            viewport={"width": width, "height": height},
            locale="zh-CN",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self._page = (
            self._context.pages[0]
            if self._context.pages
            else await self._context.new_page()
        )

    async def _navigate_to_feishu(self):
        self.log("正在打开飞书网页版...")
        try:
            await cast(Any, self._page).goto(
                FEISHU_CHAT_URL, wait_until="domcontentloaded", timeout=60000
            )
        except Exception as e:
            error_msg = str(e)
            if "Target page, context or browser has been closed" in error_msg:
                self.log("⚠️ 浏览器已关闭")
                self._running = False
                return
            elif "net::ERR_ABORTED" in error_msg:
                self.log("⚠️ 页面导航中断")
                self._running = False
                return
            raise

        self.log("等待登录...请在浏览器中完成登录")
        try:
            await cast(Any, self._page).wait_for_selector(
                SELECTORS["message_input"],
                timeout=300000,
            )
            self.log("✅ 登录成功！")
        except Exception as e:
            error_msg = str(e)
            if "Target page, context or browser has been closed" in error_msg:
                self.log("⚠️ 浏览器已���闭")
                self._running = False
            elif "Target closed" in error_msg:
                self.log("⚠️ 页面已关闭")
                self._running = False
            else:
                self.log("⚠️ 登录超时，但仍可继续操作")

    async def _navigate_to_group(self, group_name: str) -> bool:
        try:
            chat_item = await cast(Any, self._page).wait_for_selector(
                f"{SELECTORS['chat_item']} >> text='{group_name}'",
                timeout=5000,
            )
            if chat_item is None:
                raise RuntimeError(f"Chat item not found for group: {group_name}")
            await chat_item.click()
            await self._delay(1, 2)
            return True
        except Exception as e:
            error_msg = str(e)
            if "Target page, context or browser has been closed" in error_msg:
                self.log("⚠️ 浏览器已关闭，停止监控")
                self._running = False
            elif "Target closed" in error_msg:
                self.log("⚠️ 页面已关闭，停止监控")
                self._running = False
            elif "net::ERR_ABORTED" in error_msg:
                self.log("⚠️ 页面导航中断，停止监控")
                self._running = False
            return False

    async def _get_messages(self, group_name: str = "") -> list[dict]:
        messages = []
        max_msgs = self.config.get("monitor", {}).get("max_messages_per_check", 10)

        try:
            wrappers = await cast(Any, self._page).query_selector_all(
                SELECTORS["message_wrapper"]
            )
            if not wrappers:
                return messages

            for wrapper in reversed(wrappers[-max_msgs:]):
                try:
                    msg_id = await self._extract_message_id(wrapper, "")
                    if self.state.is_seen(group_name, msg_id):
                        continue

                    text_el = await wrapper.query_selector(SELECTORS["message_text"])
                    if not text_el:
                        continue
                    text = (await text_el.inner_text()).strip()
                    if not text:
                        continue
                    messages.append(
                        {
                            "id": msg_id,
                            "text": text,
                            "element": wrapper,
                            "group": group_name,
                        }
                    )
                except Exception as e:
                    self.log(f"异常：{str(e)}")
        except Exception as e:
            error_msg = str(e)
            if "Target page, context or browser has been closed" in error_msg:
                self.log("⚠️ 浏览器已关闭，停止监控")
                self._running = False
            elif "Target closed" in error_msg:
                self.log("⚠️ 页面已关闭，停止监控")
                self._running = False
            else:
                self.log(f"异常：{error_msg}")

        return messages

    async def _extract_message_id(self, element, text: str) -> str:
        current_timestamp = int(time.time() * 1000)

        attrs_to_try = [
            "data-message-id",
            "data-id",
            "id",
            "data-msg-id",
            "message-id",
        ]

        for attr in attrs_to_try:
            msg_id = await element.get_attribute(attr)
            if msg_id:
                return msg_id

        try:
            msg_content = await element.query_selector("[data-message-id]")
            if msg_content:
                msg_id = await msg_content.get_attribute("data-message-id")
                if msg_id:
                    return msg_id
        except Exception as e:
            self.log(f"Unexpected error: {str(e)}")

        text_hash = hash(text)
        return f"{current_timestamp}_{text_hash}"

    async def _react(self, message_element) -> bool:
        try:
            await message_element.hover()

            reaction_btn = None

            script = """
                (msgEl) => {
                    const msgRect = msgEl.getBoundingClientRect();
                    const msgCenterX = msgRect.left + msgRect.width / 2;
                    const msgCenterY = msgRect.top + msgRect.height / 2;

                    const allElements = document.querySelectorAll('*');
                    let closestBtn = null;
                    let closestDist = Infinity;

                    for (const el of allElements) {
                        if (!el.className || typeof el.className !== 'string') continue;
                        const classStr = el.className.toString().toLowerCase();
                        if (!classStr.includes('praise') && !classStr.includes('like')) continue;
                        if (el.tagName === 'BUTTON' || el.tagName === 'SPAN' || el.tagName === 'DIV') {
                            const rect = el.getBoundingClientRect();
                            const centerX = rect.left + rect.width / 2;
                            const centerY = rect.top + rect.height / 2;
                            const dist = Math.sqrt(Math.pow(centerX - msgCenterX, 2) + Math.pow(centerY - msgCenterY, 2));
                            if (dist < closestDist && dist < 200) {
                                closestDist = dist;
                                closestBtn = el;
                            }
                        }
                    }
                    return closestBtn;
                }
            """

            reaction_btn = await message_element.evaluate_handle(
                script, message_element
            )

            if not reaction_btn:
                self.log("未找到点赞按钮")
                return False

            await reaction_btn.evaluate("el => el.click()")
            return True
        except Exception as e:
            self.log(f"点赞操作异常: {e}")
            return False

    async def _delay(self, min_s: float | None = None, max_s: float | None = None):
        anti = self.config.get("anti_detect", {})
        mn = min_s if min_s is not None else anti.get("min_delay", 0.5)
        mx = max_s if max_s is not None else anti.get("max_delay", 2.0)
        await asyncio.sleep(random.uniform(mn, mx))

    async def _run_loop(self):
        self._running = True
        self.state.is_running = True
        self.state.start_time = time.time()
        self.log("🚀 开始监控群消息...")

        monitored_groups = self.config.get("monitor", {}).get("monitored_groups", [])
        check_interval = self.config.get("monitor", {}).get("check_interval", 2)
        current_group = ""

        while self._running:
            try:
                if monitored_groups:
                    for group in monitored_groups:
                        if not self._running:
                            break
                        current_group = group
                        await self._navigate_to_group(group)
                else:
                    current_group = "_default"

                messages = await self._get_messages(current_group)
                current_time = datetime.now().strftime("%H:%M:%S")

                for msg in messages:
                    if not self._running:
                        break

                    if self.state.is_seen(current_group, msg["id"]):
                        continue

                    self.state.mark_seen(current_group, msg["id"])
                    msg_id = msg["id"]
                    msg_text = msg["text"]

                    is_match = self.matcher.matches(msg_text)

                    if is_match:
                        if self.state.is_reacted(current_group, msg_id):
                            self.log(
                                f"[{current_time}] msg_id={msg_id} | {msg_text} | 已点赞"
                            )
                            continue
                        self.state.match_count += 1
                        success = await self._react(msg["element"])
                        if success:
                            self.state.reaction_count += 1
                            self.state.mark_reacted(current_group, msg_id)
                            self.log(
                                f"[{current_time}] msg_id={msg_id} | {msg_text} | 点赞成功"
                            )
                        else:
                            self.state.fail_count += 1
                            self.log(
                                f"[{current_time}] msg_id={msg_id} | {msg_text} | 点赞失败"
                            )
                        await self._delay()
                    else:
                        self.log(
                            f"[{current_time}] msg_id={msg_id} | {msg_text} | 匹配失败"
                        )

                if messages:
                    new_ids = [m["id"] for m in messages]
                    self.state.update_last_checked_ids(current_group, new_ids)

                await asyncio.sleep(check_interval)

            except Exception as e:
                self.log(f"⚠️ 监控异常: {e}")
                if not self._running:
                    break
                error_msg = str(e)
                if "Target page, context or browser has been closed" in error_msg:
                    self.log("⚠️ 浏览器已关闭，停止监控")
                    self._running = False
                    break
                elif "Target closed" in error_msg:
                    self.log("⚠️ 页面已关闭，停止监控")
                    self._running = False
                    break
                elif "net::ERR_ABORTED" in error_msg:
                    self.log("⚠️ 页面导航中断，停止监控")
                    self._running = False
                    break
                await asyncio.sleep(check_interval)

        self.state.is_running = False
        self.stop_callback()

    def start(self):
        """Start the bot in a background thread."""

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._setup_browser())
                loop.run_until_complete(self._navigate_to_feishu())
                loop.run_until_complete(self._run_loop())
            except Exception as e:
                self.log(f"💥 致命错误: {e}")
            finally:
                loop.run_until_complete(self._cleanup())
                loop.close()

        self._thread = threading.Thread(target=run_async, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    async def _cleanup(self):
        try:
            if self._context:
                await self._context.close()
        except Exception as e:
            self.log(f"关闭浏览器上下文时出错: {e}")
        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            self.log(f"关闭Playwright时出错: {e}")
