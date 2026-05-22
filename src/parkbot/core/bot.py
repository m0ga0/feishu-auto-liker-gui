import asyncio
import os
import random
import threading
import time
from pathlib import Path
from typing import Any, Callable, List, Optional, cast


from ..config.models import MonitorSettings, InternalSettings
from ..chat.models import FeishuMessage
from ..dao_impl.chat.dao import IFeishuMessageRepository
from .constants import FEISHU_CHAT_URL, SELECTORS
from .matcher import PatternMatcher


class RPABotCore:
    """
    The actual RPA bot logic. Runs in a separate thread with its own event loop.
    """

    def __init__(
        self,
        monitor_settings: MonitorSettings,
        internal_settings: InternalSettings,
        message_repo: IFeishuMessageRepository,
        log_callback: Optional[Callable[[str], None]] = None,
        stop_callback: Optional[Callable[[], None]] = None,
    ):
        self.monitor_settings = monitor_settings
        self.internal_settings = internal_settings

        # Runtime statistics (moved from BotState)
        self.match_count = 0
        self.reaction_count = 0
        self.fail_count = 0
        self.start_time: Optional[float] = None

        # Unified running state (merged from BotState)
        self._is_running = False

        # Repository for message persistence
        self.message_repo = message_repo

        # Callbacks
        self.log = log_callback or (lambda msg: None)
        self.stop_callback = stop_callback or (lambda: None)

        # Matcher
        self.matcher = PatternMatcher(self.monitor_settings.patterns)

        # Browser resources
        self._page: object = None
        self._context = None
        self._playwright = None

    @property
    def is_running(self) -> bool:
        """Public read-only access to running state."""
        return self._is_running

    async def _setup_browser(self):
        persist_path = str(Path.home() / ".cache" / "ms-playwright")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = persist_path

        Path(persist_path).mkdir(parents=True, exist_ok=True)

        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()

        user_data_dir = self.internal_settings.browser_user_data_dir
        Path(user_data_dir).mkdir(parents=True, exist_ok=True)

        width = self.internal_settings.browser_win_width
        height = self.internal_settings.browser_win_height

        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
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
                self._is_running = False
                return
            elif "net::ERR_ABORTED" in error_msg:
                self.log("⚠️ 页面导航中断")
                self._is_running = False
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
                self.log("⚠️ 浏览器已关闭")
                self._is_running = False
            elif "Target closed" in error_msg:
                self.log("⚠️ 页面已关闭")
                self._is_running = False
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
            print(error_msg)
            if "Target page, context or browser has been closed" in error_msg:
                self.log("⚠️ 浏览器已关闭，停止监控")
                self._is_running = False
            elif "Target closed" in error_msg:
                self.log("⚠️ 页面已关闭，停止监控")
                self._is_running = False
            elif "net::ERR_ABORTED" in error_msg:
                self.log("⚠️ 页面导航中断，停止监控")
                self._is_running = False
            return False

    async def _get_messages(self, group_name: str = "") -> list[dict]:
        messages = []
        max_msgs = self.monitor_settings.max_messages_per_check

        try:
            wrappers = await cast(Any, self._page).query_selector_all(
                SELECTORS["message_wrapper"]
            )
            if not wrappers:
                return messages

            for wrapper in reversed(wrappers[-max_msgs:]):
                try:
                    msg_id = await self._extract_message_id(wrapper, "")

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
                self._is_running = False
            elif "Target closed" in error_msg:
                self.log("⚠️ 页面已关闭，停止监控")
                self._is_running = False
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
        mn = min_s if min_s is not None else 0.5
        mx = max_s if max_s is not None else 2.0
        await asyncio.sleep(random.uniform(mn, mx))

    async def _run_loop(self):
        """Main processing loop with batch operations."""
        self._is_running = True
        self.start_time = time.time()

        check_interval = self.monitor_settings.check_interval
        current_group = "_default"

        while self._is_running:
            try:
                # Get messages from browser
                messages = await self._get_messages(current_group)

                if not messages:
                    await asyncio.sleep(check_interval)
                    continue

                # Extract message IDs for batch query
                message_ids = [msg["id"] for msg in messages]

                # BATCH QUERY: Get existing messages from storage
                existing_messages = self.message_repo.get_by_ids(message_ids)

                # Classify messages into 3 groups
                to_process = []  # Scenario 1: Not in storage
                to_skip_checked = []  # Scenario 3: Checked, not matched
                to_skip_reacted = []  # Scenario 4: Already reacted

                for msg_data in messages:
                    msg_id = msg_data["id"]
                    existing = existing_messages.get(msg_id)

                    if existing is None:
                        # Scenario 1: Never seen
                        to_process.append(msg_data)
                    elif existing.is_reacted is None:
                        # Scenario 2: Seen but not processed (app killed)
                        to_process.append(msg_data)
                    elif existing.is_reacted is False:
                        # Scenario 3: Checked, no match
                        to_skip_checked.append(msg_id)
                    elif existing.is_reacted is True:
                        # Scenario 4: Already reacted
                        to_skip_reacted.append(msg_id)

                # Log skipped messages
                # if to_skip_checked:
                #    self.log(f"Skipping {len(to_skip_checked)} checked non-matching messages")
                # if to_skip_reacted:
                #    self.log(f"Skipping {len(to_skip_reacted)} already-reacted messages")

                # Process messages that need action
                if to_process:
                    await self._process_message_batch(to_process, current_group)

                await asyncio.sleep(check_interval)

            except Exception as e:
                self.log(f"⚠️ 监控异常: {e}")
                if not self._is_running:
                    break
                # Handle specific error types
                error_msg = str(e)
                if "Target page, context or browser has been closed" in error_msg:
                    self.log("⚠️ 浏览器已关闭，停止监控")
                    self._is_running = False
                    break
                elif "Target closed" in error_msg:
                    self.log("⚠️ 页面已关闭，停止监控")
                    self._is_running = False
                    break
                elif "net::ERR_ABORTED" in error_msg:
                    self.log("⚠️ 页面导航中断，停止监控")
                    self._is_running = False
                    break
                await asyncio.sleep(check_interval)

        self._is_running = False
        self.stop_callback()

    async def _process_message_batch(
        self, messages: List[dict], group_name: str
    ) -> None:
        """
        Process a batch of messages with pattern matching and reactions.

        Steps:
        1. Match all messages against patterns
        2. Filter out already-reacted messages
        3. Execute batch reactions
        4. Save results to storage
        """
        matched_messages = []
        no_match_messages = []

        # Step 1: Pattern matching for all messages
        for msg_data in messages:
            msg_id = msg_data["id"]
            msg_text = msg_data["text"]

            is_match = self.matcher.matches(msg_text)

            if is_match:
                self.match_count += 1
                matched_messages.append(msg_data)
            else:
                no_match_messages.append(msg_data)
            self.log(f"[{msg_id}]:{msg_text} -> {is_match}")

        # Step 2: Check which matched messages were already reacted
        if matched_messages:
            matched_ids = [m["id"] for m in matched_messages]
            reacted_status = self.message_repo.exists_batch(matched_ids)

            to_react = []
            already_reacted = []

            for msg_data in matched_messages:
                msg_id = msg_data["id"]
                if reacted_status.get(msg_id, False):
                    # Check if actually reacted (not just exists)
                    existing = self.message_repo.get_by_ids([msg_id]).get(msg_id)
                    if existing and existing.is_reacted is True:
                        already_reacted.append(msg_id)
                    else:
                        to_react.append(msg_data)
                else:
                    to_react.append(msg_data)

            # if already_reacted:
            #    self.log(f"Skipping {len(already_reacted)} already-reacted messages")
        else:
            to_react = []

        # Step 3: Execute batch reactions
        reaction_results = []
        if to_react:
            self.log(f"Reacting to {len(to_react)} matched messages...")
            for msg_data in to_react:
                msg_id = msg_data["id"]
                try:
                    success = await self._react(msg_data["element"])
                    reaction_results.append((msg_data, success))
                except Exception as e:
                    self.log(f"Reaction failed for msg {msg_id}: {e}")
                    reaction_results.append((msg_data, False))

        # Step 4: Prepare messages for saving
        messages_to_save = []

        # Add matched messages with reaction results
        for msg_data, success in reaction_results:
            msg_id = msg_data["id"]
            msg_text = msg_data["text"]

            # Get existing or create new
            existing = self.message_repo.get_by_ids([msg_id]).get(msg_id)
            if existing:
                msg = existing
            else:
                msg = FeishuMessage(
                    id=msg_id,
                    group_name=group_name,
                    text=msg_text,
                )

            # Update state using unified mark_processed method
            if success:
                msg.mark_processed(is_reacted=True, target_pattern="matched")
                self.reaction_count += 1
            else:
                msg.mark_processed(is_reacted=False, target_pattern="matched")
                self.fail_count += 1

            messages_to_save.append(msg)

        # Add non-matching messages (mark as checked)
        for msg_data in no_match_messages:
            msg_id = msg_data["id"]
            msg_text = msg_data["text"]

            existing = self.message_repo.get_by_ids([msg_id]).get(msg_id)
            if existing:
                msg = existing
            else:
                msg = FeishuMessage(
                    id=msg_id,
                    group_name=group_name,
                    text=msg_text,
                )

            # Mark as checked but no match - stores the pattern that was checked
            msg.mark_processed(is_reacted=False, target_pattern="checked")
            messages_to_save.append(msg)

        # BATCH SAVE: Save all messages at once
        if messages_to_save:
            try:
                self.message_repo.save_batch(messages_to_save)
                self.log(f"Saved {len(messages_to_save)} message states")
            except Exception as e:
                msg_ids = [m.id for m in messages_to_save]
                self.log(f"ERROR: Failed to save messages {msg_ids}: {e}")

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
        self._is_running = False

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
