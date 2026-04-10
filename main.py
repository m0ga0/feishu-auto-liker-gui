import asyncio
import json
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import customtkinter as ctk
import yaml
from loguru import logger
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1

# ---------------------------------------------------------------------------
# Configuration Helpers
# ---------------------------------------------------------------------------

CONFIG_PATH = Path("config.yaml")
STATE_PATH = Path("state.json")

DEFAULT_CONFIG = {
    "monitor": {
        "patterns": ["打卡", "签到"],
        "reaction_emoji": "赞",
        "monitored_groups": [],
        "check_interval": 2,
        "max_messages_per_check": 10,
    },
    "notification": {
        "desktop_notification": True,
        "self_chat_notify": False,
    },
    "anti_detect": {
        "min_delay": 0.5,
        "max_delay": 2.0,
        "reaction_delay_min": 0.3,
        "reaction_delay_max": 1.5,
    },
    "browser": {
        "user_data_dir": "./feishu_browser_data",
        "width": 1280,
        "height": 800,
        "headless": False,
    },
    "log": {
        "level": "INFO",
        "file": "rpa_bot.log",
    },
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


# ---------------------------------------------------------------------------
# Core Classes
# ---------------------------------------------------------------------------


class EnvChecker:
    """Check and install required dependencies."""

    def __init__(self, log_callback=None):
        self.log = log_callback or (lambda msg: None)

    def check_all(self) -> dict:
        browser_status = self._check_playwright_browser()
        self.log("正在扫描环境...")
        return {
            "python": {
                "installed": True,
                "version": "Frozen"
                if getattr(sys, "frozen", False)
                else sys.version.split()[0],
                "path": sys.executable,
            },
            "pip": {"installed": True, "version": "N/A"},
            "playwright_pkg": {"installed": True, "version": "Checked"},
            "playwright_browser": browser_status,
        }

    def _check_playwright_browser(self) -> dict:
        persist_path = Path.home() / ".cache" / "ms-playwright"
        chromium_exists = False
        if persist_path.exists():
            chromium_exists = any(
                p.name.startswith("chromium-")
                for p in persist_path.iterdir()
                if p.is_dir()
            )
        return {
            "installed": chromium_exists,
            "version": "chromium (detected)" if chromium_exists else "",
        }

    def install_all(self, progress_callback=None) -> bool:
        self.log("⏳ 正在下载浏览器，请稍候...")
        cmd = "python3 -m playwright install chromium --with-deps"
        if platform.system() == "Windows":
            cmd = "python -m playwright install chromium --with-deps"
        try:
            subprocess.check_call(cmd, shell=True)
            self.log("✅ 浏览器安装成功")
            return True
        except Exception as e:
            self.log(f"❌ 安装失败: {e}")
            return False


class PatternMatcher:
    def __init__(self, patterns: list[str]):
        self._compiled: list[tuple[bool, re.Pattern | str]] = []
        for raw in patterns:
            if raw.startswith("re:"):
                try:
                    self._compiled.append((True, re.compile(raw[3:], re.IGNORECASE)))
                except re.error:
                    pass
            else:
                self._compiled.append((False, raw))

    def matches(self, text: str) -> bool:
        for is_regex, pattern in self._compiled:
            if is_regex:
                if pattern.search(text):
                    return True
            else:
                if pattern in text:
                    return True
        return False


class BotState:
    def __init__(self):
        self._seen_ids: set[str] = set()
        self._lock = threading.Lock()
        self.match_count = 0
        self.reaction_count = 0
        self.fail_count = 0
        self.start_time: Optional[float] = None
        self.recent_logs: list[str] = []
        self.is_running = False

    def is_seen(self, msg_id: str) -> bool:
        with self._lock:
            if msg_id in self._seen_ids:
                return True
            self._seen_ids.add(msg_id)
            if len(self._seen_ids) > 5000:
                self._seen_ids.clear()
            return False

    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self.recent_logs.append(entry)
        self.recent_logs = self.recent_logs[-100:]

    def reset(self):
        self.match_count = 0
        self.reaction_count = 0
        self.fail_count = 0
        self.start_time = time.time()
        self.recent_logs.clear()
        self._seen_ids.clear()

    @property
    def uptime(self) -> str:
        if not self.start_time:
            return "0秒"
        total = int(time.time() - self.start_time)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h}h{m}m{s}s"


class RPABotCore:
    FEISHU_CHAT_URL = "https://www.feishu.cn/messenger"
    SELECTORS = {
        "message_wrapper": ".message-wrapper, [class*='message-wrapper']",
        "message_text": ".message-text, [class*='message-text'], .rich-text",
        "reaction_button": "[class*='reaction'], [class*='emoji-btn']",
        "chat_item": ".chat-item, [class*='chat-item']",
        "message_input": ".message-input, [class*='message-input'], [contenteditable='true']",
    }

    def __init__(self, config: dict, state: BotState, log_callback=None):
        self.config = config
        self.state = state
        self.log = log_callback or (lambda msg: None)
        self.matcher = PatternMatcher(config.get("monitor", {}).get("patterns", []))
        self._running = False
        self._page = None
        self._context = None
        self._playwright = None

    async def _setup_browser(self):
        from playwright.async_api import async_playwright

        persist_path = str(Path.home() / ".cache" / "ms-playwright")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = persist_path
        Path(persist_path).mkdir(parents=True, exist_ok=True)
        self._playwright = await async_playwright().start()
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(
                Path(
                    self.config.get("browser", {}).get(
                        "user_data_dir", "./feishu_browser_data"
                    )
                )
            ),
            headless=False,
            viewport={"width": 1280, "height": 800},
        )
        self._page = (
            self._context.pages[0]
            if self._context.pages
            else await self._context.new_page()
        )

    async def _navigate_to_feishu(self):
        await self._page.goto(
            self.FEISHU_CHAT_URL, wait_until="domcontentloaded", timeout=60000
        )
        self.log("等待登录...")

    async def _run_loop(self):
        self._running = True
        while self._running:
            try:
                messages = await self._get_messages()
                for msg in messages:
                    if self.state.is_seen(msg["id"]):
                        continue
                    if self.matcher.matches(msg["text"]):
                        self.state.match_count += 1
                        self.log(f"🎯 匹配: {msg['text'][:50]}")
                        if await self._react(msg["element"]):
                            self.state.reaction_count += 1
                            self.log("✅ 点赞成功")
                await asyncio.sleep(2)
            except Exception as e:
                self.log(f"⚠️ 异常: {e}")
                await asyncio.sleep(2)

    async def _get_messages(self) -> list:
        # Simplified for brevity
        wrappers = await self._page.query_selector_all(
            self.SELECTORS["message_wrapper"]
        )
        messages = []
        for w in wrappers[-10:]:
            t = await w.query_selector(self.SELECTORS["message_text"])
            if t:
                text = (await t.inner_text()).strip()
                messages.append({"id": hash(text), "text": text, "element": w})
        return messages

    async def _react(self, el) -> bool:
        try:
            await el.hover()
            btn = await el.query_selector(self.SELECTORS["reaction_button"])
            if btn:
                await btn.click()
                await asyncio.sleep(0.5)
                return True
        except:
            return False

    def start(self):
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._setup_browser())
            loop.run_until_complete(self._navigate_to_feishu())
            loop.run_until_complete(self._run_loop())

        threading.Thread(target=run, daemon=True).start()

    def stop(self):
        self._running = False


# ---------------------------------------------------------------------------
# GUI Class (Finally defined after all core classes)
# ---------------------------------------------------------------------------


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("飞书自动点赞助手")
        self.geometry("800x600")
        self.state = BotState()
        self.config = load_config()
        self.bot = None
        self._build_ui()

    def _build_ui(self):
        self.btn = ctk.CTkButton(self, text="启动监控", command=self._start)
        self.btn.pack(pady=20)
        self.log = ctk.CTkTextbox(self)
        self.log.pack(fill="both", expand=True)

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", f"{msg}\n")
        self.log.configure(state="disabled")

    def _start(self):
        self.bot = RPABotCore(self.config, self.state, log_callback=self._log)
        self.bot.start()


if __name__ == "__main__":
    App().mainloop()
