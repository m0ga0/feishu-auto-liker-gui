"""
Feishu Auto-Liker GUI Application
A user-friendly desktop app for monitoring Feishu group messages and auto-reacting.
"""

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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG_PATH = Path("config.yaml")

DEFAULT_CONFIG = {
    "monitor": {
        "patterns": ["re:.*(出|整出).*(车位|停车位|首赞).*"],
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
# Environment Checker & Installer
# ---------------------------------------------------------------------------


class EnvChecker:
    """Check and install required dependencies."""

    def __init__(self, log_callback=None):
        self.log = log_callback or (lambda msg: None)
        self._results = {}

    def check_all(self) -> dict:
        """Check all dependencies."""
        # 即使是打包环境，浏览器也必须实际核实
        browser_status = self._check_playwright_browser()

        # 如果是打包环境，仅忽略 Python/Pip/Playwright 库的检查
        if getattr(sys, "frozen", False):
            self.log("检测到已打包环境...")
            self._results = {
                "python": {
                    "installed": True,
                    "version": "Frozen",
                    "path": sys.executable,
                },
                "pip": {"installed": True, "version": "Frozen"},
                "playwright_pkg": {"installed": True, "version": "Frozen"},
                "playwright_browser": browser_status,
            }
        else:
            self.log("检查环境依赖...")
            self._results = {
                "python": self._check_python(),
                "pip": self._check_pip(),
                "playwright_pkg": self._check_playwright_pkg(),
                "playwright_browser": browser_status,
            }
        return self._results

    def _run(self, cmd: str, timeout: int = 10) -> tuple[bool, str]:
        # 如果是打包后的二进制文件，防止循环启动自身
        if getattr(sys, "frozen", False):
            return True, "Frozen"
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            return False, str(e)

    def _check_python(self) -> dict:
        ok, version = self._run(f'"{sys.executable}" --version')
        if ok:
            return {"installed": True, "version": version, "path": sys.executable}
        return {"installed": False, "version": "", "path": ""}

    def _check_pip(self) -> dict:
        ok, version = self._run(f'"{sys.executable}" -m pip --version')
        return {"installed": ok, "version": version.split()[1] if ok else ""}

    def _check_playwright_pkg(self) -> dict:
        ok, _ = self._run(f'"{sys.executable}" -c "import playwright"')
        if ok:
            ok2, ver = self._run(
                f'"{sys.executable}" -c "import playwright; print(playwright.__version__)"'
            )
            return {"installed": True, "version": ver if ok2 else "unknown"}
        return {"installed": False, "version": ""}

    def _check_playwright_browser(self) -> dict:
        data_dir = Path(__file__).parent / "browser_data_check"
        ok, _ = self._run(
            f'"{sys.executable}" -m playwright install --dry-run chromium 2>&1'
        )
        # Check if chromium is already installed
        pw_base = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""))
        if not pw_base.exists():
            # Default location
            if platform.system() == "Windows":
                pw_base = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright"
            elif platform.system() == "Darwin":
                pw_base = Path.home() / "Library" / "Caches" / "ms-playwright"
            else:
                pw_base = Path.home() / ".cache" / "ms-playwright"

        chromium_exists = (
            (pw_base / "chromium-*").exists()
            or any(p.is_dir() for p in pw_base.parent.glob("ms-playwright/chromium-*"))
            if pw_base.exists()
            else False
        )

        # Simpler check: try to import and see if browser is available
        ok_import, _ = self._run(
            f'"{sys.executable}" -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); p.chromium.launch(); p.stop()"'
        )
        return {"installed": ok_import, "version": "chromium" if ok_import else ""}

    def install_all(self, progress_callback=None) -> bool:
        """Install all missing dependencies."""
        steps = [
            ("pip", self._install_pip),
            ("playwright_pkg", self._install_playwright_pkg),
            ("playwright_browser", self._install_playwright_browser),
        ]

        for name, install_func in steps:
            status = self._results.get(name, {})
            if status.get("installed"):
                self.log(f"✅ {name} 已安装")
                continue

            self.log(f"⏳ 正在安装 {name}...")
            if progress_callback:
                progress_callback(name)
            success = install_func()
            if not success:
                self.log(f"❌ {name} 安装失败")
                return False
            self.log(f"✅ {name} 安装成功")

        self.log("🎉 所有依赖安装完成！")
        return True

    def _install_pip(self) -> bool:
        ok, _ = self._run(f'"{sys.executable}" -m ensurepip --upgrade')
        return ok

    def _install_playwright_pkg(self) -> bool:
        ok, _ = self._run(
            f'"{sys.executable}" -m pip install playwright --quiet',
            timeout=120,
        )
        return ok

    def _install_playwright_browser(self) -> bool:
        ok, _ = self._run(
            f'"{sys.executable}" -m playwright install chromium --with-deps',
            timeout=300,
        )
        return ok


# ---------------------------------------------------------------------------
# Pattern Matcher
# ---------------------------------------------------------------------------


class PatternMatcher:
    def __init__(self, patterns: list[str], log_callback=None):
        self._compiled: list[tuple[bool, re.Pattern | str]] = []
        self.log = log_callback or (lambda msg: None)
        for raw in patterns:
            if raw.startswith("re:"):
                try:
                    self._compiled.append((True, re.compile(raw[3:], re.IGNORECASE)))
                except re.error:
                    pass
            else:
                self._compiled.append((False, raw))

    def matches(self, text: str) -> bool:
        self.log(f"🔍 正在检查消息: '{text[:20]}...'")
        for is_regex, pattern in self._compiled:
            is_match = False
            if is_regex:
                if pattern.search(text):
                    is_match = True
            else:
                if pattern in text:
                    is_match = True

            p_str = pattern.pattern if is_regex else pattern
            self.log(f"   > 规则 '{p_str}': {'✅ 符合' if is_match else '❌ 不符'}")
            if is_match:
                return True
        return False


# ---------------------------------------------------------------------------
# State Tracker
# ---------------------------------------------------------------------------


class _BotState:
    def __init__(self):
        self._seen_ids: set[str] = set()
        self._group_states: dict[str, dict] = {}
        self._lock = threading.Lock()
        self.match_count = 0
        self.reaction_count = 0
        self.fail_count = 0
        self.start_time: Optional[float] = None
        self.recent_logs: list[str] = []
        self.is_running = False
        self._load_state()

    def get_group_state(self, group_name: str) -> dict:
        if group_name not in self._group_states:
            self._group_states[group_name] = {
                "seen_ids": set(),
                "last_checked_ids": [],
                "last_check_time": 0,
            }
        return self._group_states[group_name]

    def mark_seen(self, group_name: str, msg_id: str):
        gs = self.get_group_state(group_name)
        gs["seen_ids"].add(msg_id)

    def is_seen(self, group_name: str, msg_id: str) -> bool:
        gs = self.get_group_state(group_name)
        return msg_id in gs["seen_ids"]

    def update_last_checked_ids(self, group_name: str, ids: list[str]):
        gs = self.get_group_state(group_name)
        gs["last_checked_ids"] = ids
        gs["last_check_time"] = time.time()
        self._save_state()

    def get_last_checked_ids(self, group_name: str) -> list[str]:
        gs = self.get_group_state(group_name)
        return gs.get("last_checked_ids", [])

    def _load_state(self):
        if STATE_PATH.exists():
            try:
                data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
                groups_data = data.get("groups", {})
                for name, state in groups_data.items():
                    self._group_states[name] = {
                        "seen_ids": set(state.get("seen_ids", [])),
                        "last_checked_ids": state.get("last_checked_ids", []),
                        "last_check_time": state.get("last_check_time", 0),
                    }
                logger.info(f"已加载 {len(self._group_states)} 个群组的状态")
            except Exception as e:
                logger.warning(f"加载状态文件失败: {e}")

    def _save_state(self):
        try:
            data = {
                "groups": {
                    name: {
                        "seen_ids": list(state["seen_ids"]),
                        "last_checked_ids": state["last_checked_ids"],
                        "last_check_time": state["last_check_time"],
                    }
                    for name, state in self._group_states.items()
                }
            }
            STATE_PATH.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"保存状态文件失败: {e}")

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
        self._group_states.clear()
        if STATE_PATH.exists():
            STATE_PATH.unlink()
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
        if h > 0:
            return f"{h}小时{m}分{s}秒"
        elif m > 0:
            return f"{m}分{s}秒"
        return f"{s}秒"


# ---------------------------------------------------------------------------
# RPA Bot Core (async, runs in background thread)
# ---------------------------------------------------------------------------


class RPABotCore:
    """
    The actual RPA bot logic. Runs in a separate thread with its own event loop.
    """

    FEISHU_CHAT_URL = "https://www.feishu.cn/messenger"

    SELECTORS = {
        "message_wrapper": "[data-element='message-section-left'], [data-element='message-section-right'], .message-section-left, .message-section-right",
        "message_text": ".message-text .text-only, .richTextContainer .text-only, .text-only",
        "reaction_button": ".messageAction__toolbar .toolbar-item.praise",
        "chat_item": ".chat-item, [class*='chat-item'], [class*='session-item']",
        "message_input": ".message-input, [class*='message-input'], [contenteditable='true']",
        "search_input": ".search-input, [class*='search'], [placeholder*='搜索']",
    }

    def __init__(self, config: dict, state: _BotState, log_callback=None):
        self.config = config
        self.state = state
        self.log = log_callback or (lambda msg: None)
        self.matcher = PatternMatcher(
            config.get("monitor", {}).get("patterns", []), log_callback=self.log
        )
        self._running = False
        self._page = None
        self._context = None
        self._playwright = None

    async def _setup_browser(self):
        # 1. 极早设置路径，必须在 import 前
        persist_path = str(Path.home() / ".cache" / "ms-playwright")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = persist_path

        # 2. 确保目录一定存在
        Path(persist_path).mkdir(parents=True, exist_ok=True)

        # 3. 延迟 import，确保设置已生效
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
        await self._page.goto(
            self.FEISHU_CHAT_URL, wait_until="domcontentloaded", timeout=60000
        )

        self.log("等待登录...请在浏览器中完成登录")
        try:
            await self._page.wait_for_selector(
                self.SELECTORS["message_input"],
                timeout=300000,
            )
            self.log("✅ 登录成功！")
        except Exception:
            self.log("⚠️ 登录超时，但仍可继续操作")

    async def _navigate_to_group(self, group_name: str) -> bool:
        try:
            chat_item = await self._page.wait_for_selector(
                f"{self.SELECTORS['chat_item']} >> text='{group_name}'",
                timeout=5000,
            )
            await chat_item.click()
            await self._delay(1, 2)
            return True
        except Exception:
            return False

    async def _get_messages(self, group_name: str = "") -> list[dict]:
        messages = []
        max_msgs = self.config.get("monitor", {}).get("max_messages_per_check", 10)
        current_time = datetime.now().strftime("%H:%M:%S")

        try:
            wrappers = await self._page.query_selector_all(
                self.SELECTORS["message_wrapper"]
            )
            if not wrappers:
                self.log(
                    f"没有定位到消息渲染单元{self.SELECTORS['message_wrapper']}，继续监测。"
                )
                return messages

            for wrapper in wrappers[-max_msgs:]:
                try:
                    wrapper_class = await wrapper.get_attribute("class") or ""
                    if "message-section" not in wrapper_class:
                        continue

                    text_el = await wrapper.query_selector(
                        self.SELECTORS["message_text"]
                    )
                    if not text_el:
                        continue
                    text = (await text_el.inner_text()).strip()
                    if not text:
                        continue

                    msg_id = self._generate_message_id(wrapper, text)
                    self.log(f"[{current_time}] 抓取消息 ID={msg_id}")
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
            self.log(f"异常：{str(e)}")

        return messages

    def _generate_message_id(self, element, text: str) -> str:
        import time

        current_timestamp = int(time.time() * 1000)

        attrs_to_try = [
            "data-message-id",
            "data-id",
            "id",
            "data-msg-id",
            "message-id",
        ]

        for attr in attrs_to_try:
            msg_id = element.get_attribute(attr)
            if msg_id:
                return msg_id

        try:
            msg_content = element.query_selector("[data-message-id]")
            if msg_content:
                msg_id = msg_content.get_attribute("data-message-id")
                if msg_id:
                    return msg_id
        except:
            pass

        text_hash = hash(text)
        return f"{current_timestamp}_{text_hash}"

    async def _react(self, message_element) -> bool:
        try:
            # 1. 触发 Hover
            await message_element.hover()
            # 增加一个微小的延迟，给飞书渲染工具栏的时间
            await self._delay(0.3, 0.5)

            # 2. 在消息容器内部进行“相对查找”
            # 使用 wait_for_selector 限制范围在 message_element 内部
            try:
                toolbar = await message_element.wait_for_selector(
                    ".messageAction__toolbar", timeout=1000
                )
            except:
                self.log("未在消息容器内找到工具栏")
                return False

            # 3. 在工具栏内找点赞按钮
            reaction_btn = await toolbar.query_selector(".toolbar-item.praise")
            if reaction_btn:
                await reaction_btn.click()
                await self._delay(0.5, 1.0)
                return True

            self.log("未在工具栏中找到点赞按钮")
            return False
        except Exception as e:
            self.log(f"点赞操作异常: {e}")
            return False

            # 4. 点击点赞按钮
            reaction_btn = await toolbar.query_selector(".toolbar-item.praise")
            if reaction_btn:
                await reaction_btn.click()
                await self._delay(0.5, 1.0)
                return True

            self.log("未找到点赞按钮")
            return False
        except Exception as e:
            self.log(f"点赞操作异常: {e}")
            return False
        except Exception as e:
            self.log(f"点赞失败: {e}")
            return False

    async def _delay(self, min_s: float = None, max_s: float = None):
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

        while self._running:
            try:
                # Navigate to groups if specified
                if monitored_groups:
                    for group in monitored_groups:
                        if not self._running:
                            break
                        await self._navigate_to_group(group)

                messages = await self._get_messages()

                for msg in messages:
                    if not self._running:
                        break
                    if self.state.is_seen(msg["id"]):
                        continue
                    if self.matcher.matches(msg["text"]):
                        self.state.match_count += 1
                        self.log(f"🎯 匹配: {msg['text'][:80]}")

                        success = await self._react(msg["element"])
                        if success:
                            self.state.reaction_count += 1
                            self.log("✅ 点赞成功")
                        else:
                            self.state.fail_count += 1
                            self.log("❌ 点赞失败")

                        await self._delay()
                    else:
                        self.log(f"消息{msg['text'][:80]}没有匹配")

                await asyncio.sleep(check_interval)

            except Exception as e:
                self.log(f"⚠️ 监控异常: {e}")
                await asyncio.sleep(check_interval)

        self.state.is_running = False
        self.log("⏹ 监控已停止")

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
        """Stop the bot."""
        self._running = False

    async def _cleanup(self):
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()


# ---------------------------------------------------------------------------
# GUI Application
# ---------------------------------------------------------------------------


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("飞书自动点赞助手")
        self.geometry("900x700")
        self.minsize(800, 600)

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.config_data = load_config()
        self.state = _BotState()
        self.bot: Optional[RPABotCore] = None

        self._build_ui()
        self._log_to_ui("欢迎使用飞书自动点赞助手！")

    # -----------------------------------------------------------------------
    # UI Building
    # -----------------------------------------------------------------------

    def _build_ui(self):
        # Tab view
        self.tabview = ctk.CTkTabview(self, width=900, height=700)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabview.add("安装")
        self.tabview.add("控制台")
        self.tabview.add("设置")

        self._build_install_tab()
        self._build_console_tab()
        self._build_settings_tab()

    def _build_install_tab(self):
        tab = self.tabview.tab("安装")

        title = ctk.CTkLabel(
            tab, text="🔧 环境安装", font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(30, 10))

        desc = ctk.CTkLabel(
            tab,
            text="首次使用需要安装必要的依赖。点击下方按钮自动完成安装。\n"
            "安装过程可能需要几分钟，请耐心等待。",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        desc.pack(pady=(0, 20))

        # Status frame
        self.install_frame = ctk.CTkFrame(tab)
        self.install_frame.pack(fill="x", padx=40, pady=10)

        self.install_items = {}
        items = [
            ("python", "Python 运行环境"),
            ("pip", "pip 包管理器"),
            ("playwright_pkg", "Playwright 自动化库"),
            ("playwright_browser", "Chromium 浏览器"),
        ]

        for key, label in items:
            row = ctk.CTkFrame(self.install_frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=8)

            ctk.CTkLabel(row, text=label, width=200, anchor="w").pack(side="left")
            status = ctk.CTkLabel(row, text="⏳ 检查中...", width=100, anchor="center")
            status.pack(side="left")
            self.install_items[key] = status

        # Install button
        self.install_btn = ctk.CTkButton(
            tab,
            text="🚀 一键安装",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self._run_installation,
        )
        self.install_btn.pack(pady=30)

        # Log area
        self.install_log = ctk.CTkTextbox(tab, height=150, font=ctk.CTkFont(size=12))
        self.install_log.pack(fill="x", padx=40, pady=10)
        self.install_log.configure(state="disabled")

        # Auto-check on startup
        self.after(500, self._auto_check_env)

    def _build_console_tab(self):
        tab = self.tabview.tab("控制台")

        # Status bar
        status_frame = ctk.CTkFrame(tab)
        status_frame.pack(fill="x", padx=20, pady=15)

        self.status_indicator = ctk.CTkLabel(
            status_frame, text="⏹ 未运行", font=ctk.CTkFont(size=16, weight="bold")
        )
        self.status_indicator.pack(side="left", padx=20, pady=10)

        # Stats
        self.stats_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        self.stats_frame.pack(side="right", padx=20, pady=10)

        stats = [
            ("match_count", "匹配次数"),
            ("reaction_count", "点赞成功"),
            ("fail_count", "失败次数"),
            ("uptime", "运行时长"),
        ]

        self.stat_labels = {}
        for key, label in stats:
            row = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
            row.pack(side="left", padx=10)
            ctk.CTkLabel(
                row, text=label, font=ctk.CTkFont(size=11), text_color="gray"
            ).pack()
            val = ctk.CTkLabel(row, text="0", font=ctk.CTkFont(size=16, weight="bold"))
            val.pack()
            self.stat_labels[key] = val

        # Control buttons
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="▶ 启动监控",
            fg_color="green",
            hover_color="darkgreen",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_bot,
        )
        self.start_btn.pack(side="left", padx=10)

        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹ 停止",
            fg_color="red",
            hover_color="darkred",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._stop_bot,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=10)

        self.reset_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 重置统计",
            font=ctk.CTkFont(size=14),
            command=self._reset_stats,
        )
        self.reset_btn.pack(side="left", padx=10)

        # Log area
        ctk.CTkLabel(
            tab, text="运行日志", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 0))

        self.console_log = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=12))
        self.console_log.pack(fill="both", expand=True, padx=20, pady=10)
        self.console_log.configure(state="disabled")

        # Start stats update loop
        self._update_stats_loop()

    def _build_settings_tab(self):
        tab = self.tabview.tab("设置")

        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Keywords
        ctk.CTkLabel(
            scroll_frame, text="🎯 监控关键词", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(10, 5))

        ctk.CTkLabel(
            scroll_frame,
            text="每行一个关键词，支持正则表达式（以 re: 开头）",
            text_color="gray",
        ).pack(anchor="w")

        self.keywords_text = ctk.CTkTextbox(scroll_frame, height=120)
        self.keywords_text.pack(fill="x", pady=5)
        self.keywords_text.insert(
            "1.0", "\n".join(self.config_data.get("monitor", {}).get("patterns", []))
        )

        # Emoji
        ctk.CTkLabel(
            scroll_frame, text="😀 点赞表情", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(20, 5))

        emoji_var = ctk.StringVar(
            value=self.config_data.get("monitor", {}).get("reaction_emoji", "赞")
        )
        self.emoji_var = emoji_var

        emojis = ["赞", "爱心", "鼓掌", "微笑", "大笑", "感谢", "玫瑰", "加油"]
        emoji_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        emoji_frame.pack(fill="x", pady=5)

        for emoji in emojis:
            btn = ctk.CTkRadioButton(
                emoji_frame, text=emoji, variable=emoji_var, value=emoji
            )
            btn.pack(side="left", padx=10)

        # Groups
        ctk.CTkLabel(
            scroll_frame, text="💬 监控群组", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(20, 5))

        ctk.CTkLabel(
            scroll_frame,
            text="每行一个群名（留空表示监控当前活跃聊天）",
            text_color="gray",
        ).pack(anchor="w")

        self.groups_text = ctk.CTkTextbox(scroll_frame, height=80)
        self.groups_text.pack(fill="x", pady=5)
        self.groups_text.insert(
            "1.0",
            "\n".join(self.config_data.get("monitor", {}).get("monitored_groups", [])),
        )

        # Check interval
        ctk.CTkLabel(
            scroll_frame,
            text="⏱ 检查间隔（秒）",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", pady=(20, 5))

        self.interval_slider = ctk.CTkSlider(
            scroll_frame, from_=0.5, to=10, number_of_steps=19
        )
        self.interval_slider.pack(fill="x", pady=5)
        self.interval_slider.set(
            self.config_data.get("monitor", {}).get("check_interval", 2)
        )

        self.interval_label = ctk.CTkLabel(
            scroll_frame, text=f"{self.interval_slider.get():.1f} 秒"
        )
        self.interval_label.pack()
        self.interval_slider.configure(
            command=lambda v: self.interval_label.configure(text=f"{v:.1f} 秒")
        )

        # Anti-detect
        ctk.CTkLabel(
            scroll_frame,
            text="🛡️ 反检测延迟（秒）",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", pady=(20, 5))

        anti = self.config_data.get("anti_detect", {})
        self.delay_min_slider = ctk.CTkSlider(
            scroll_frame, from_=0.1, to=3, number_of_steps=29
        )
        self.delay_min_slider.pack(fill="x", pady=5)
        self.delay_min_slider.set(anti.get("min_delay", 0.5))

        self.delay_max_slider = ctk.CTkSlider(
            scroll_frame, from_=0.5, to=5, number_of_steps=45
        )
        self.delay_max_slider.pack(fill="x", pady=5)
        self.delay_max_slider.set(anti.get("max_delay", 2.0))

        delay_label_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        delay_label_frame.pack(fill="x")
        ctk.CTkLabel(delay_label_frame, text="最小:").pack(side="left")
        self.delay_min_label = ctk.CTkLabel(
            delay_label_frame, text=f"{anti.get('min_delay', 0.5):.1f}s"
        )
        self.delay_min_label.pack(side="left", padx=5)
        ctk.CTkLabel(delay_label_frame, text="最大:").pack(side="left", padx=(20, 0))
        self.delay_max_label = ctk.CTkLabel(
            delay_label_frame, text=f"{anti.get('max_delay', 2.0):.1f}s"
        )
        self.delay_max_label.pack(side="left", padx=5)

        self.delay_min_slider.configure(
            command=lambda v: self.delay_min_label.configure(text=f"{v:.1f}s")
        )
        self.delay_max_slider.configure(
            command=lambda v: self.delay_max_label.configure(text=f"{v:.1f}s")
        )

        # Notifications
        ctk.CTkLabel(
            scroll_frame,
            text="🔔 通知设置",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", pady=(20, 5))

        self.desktop_notify_var = ctk.BooleanVar(
            value=self.config_data.get("notification", {}).get(
                "desktop_notification", True
            )
        )
        ctk.CTkCheckBox(
            scroll_frame, text="桌面弹窗通知", variable=self.desktop_notify_var
        ).pack(anchor="w", pady=5)

        self.self_chat_var = ctk.BooleanVar(
            value=self.config_data.get("notification", {}).get(
                "self_chat_notify", False
            )
        )
        ctk.CTkCheckBox(
            scroll_frame, text="发送消息到文件助手", variable=self.self_chat_var
        ).pack(anchor="w", pady=5)

        # Save button
        save_btn = ctk.CTkButton(
            scroll_frame,
            text="💾 保存设置",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            command=self._save_settings,
        )
        save_btn.pack(pady=30)

    # -----------------------------------------------------------------------
    # Handlers
    # -----------------------------------------------------------------------

    def _log_to_ui(self, msg: str, widget=None):
        w = widget or self.console_log
        w.configure(state="normal")
        w.insert("end", f"{msg}\n")
        w.see("end")
        w.configure(state="disabled")
        logger.info(msg)

    def _auto_check_env(self):
        checker = EnvChecker(
            log_callback=lambda msg: self._log_to_ui(msg, self.install_log)
        )
        results = checker.check_all()

        for key, status in results.items():
            label = self.install_items.get(key)
            if label:
                if status["installed"]:
                    label.configure(text="✅ 已安装", text_color="green")
                else:
                    label.configure(text="❌ 未安装", text_color="red")

    def _run_installation(self):
        self.install_btn.configure(state="disabled", text="⏳ 安装中...")
        self._log_to_ui("开始安装依赖...", self.install_log)

        def install_thread():
            checker = EnvChecker(
                log_callback=lambda msg: self._log_to_ui(msg, self.install_log)
            )
            checker.check_all()
            success = checker.install_all(
                progress_callback=lambda name: self._log_to_ui(
                    f"正在安装 {name}...", self.install_log
                )
            )

            self.after(
                0,
                lambda: self.install_btn.configure(
                    state="normal",
                    text="✅ 安装完成" if success else "❌ 安装失败，重试",
                ),
            )
            if success:
                self.after(0, lambda: self._auto_check_env())

        threading.Thread(target=install_thread, daemon=True).start()

    def _start_bot(self):
        self._save_settings()
        self.config_data = load_config()

        self.state.reset()
        self.bot = RPABotCore(
            self.config_data,
            self.state,
            log_callback=lambda msg: self._log_to_ui(msg),
        )
        self.bot.start()

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_indicator.configure(text="🟢 运行中", text_color="green")

    def _stop_bot(self):
        if self.bot:
            self.bot.stop()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_indicator.configure(text="⏹ 已停止", text_color="red")

    def _reset_stats(self):
        self.state.reset()
        self._log_to_ui("🔄 统计已重置")

    def _update_stats_loop(self):
        self.stat_labels["match_count"].configure(text=str(self.state.match_count))
        self.stat_labels["reaction_count"].configure(
            text=str(self.state.reaction_count)
        )
        self.stat_labels["fail_count"].configure(text=str(self.state.fail_count))
        self.stat_labels["uptime"].configure(text=self.state.uptime)
        self.after(1000, self._update_stats_loop)

    def _save_settings(self):
        keywords = [
            line.strip()
            for line in self.keywords_text.get("1.0", "end").split("\n")
            if line.strip()
        ]
        groups = [
            line.strip()
            for line in self.groups_text.get("1.0", "end").split("\n")
            if line.strip()
        ]

        self.config_data["monitor"]["patterns"] = keywords
        self.config_data["monitor"]["reaction_emoji"] = self.emoji_var.get()
        self.config_data["monitor"]["monitored_groups"] = groups
        self.config_data["monitor"]["check_interval"] = self.interval_slider.get()
        self.config_data["anti_detect"]["min_delay"] = self.delay_min_slider.get()
        self.config_data["anti_detect"]["max_delay"] = self.delay_max_slider.get()
        self.config_data["notification"]["desktop_notification"] = (
            self.desktop_notify_var.get()
        )
        self.config_data["notification"]["self_chat_notify"] = self.self_chat_var.get()

        save_config(self.config_data)
        self._log_to_ui("💾 设置已保存")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    # Setup logging
    logger.remove()
    logger.add("rpa_bot.log", rotation="10 MB", level="INFO")

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
