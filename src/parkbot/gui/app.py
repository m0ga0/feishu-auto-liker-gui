# python libs
from typing import cast
import threading
import time

# 3rd-party libs
import customtkinter as ctk

# internal packages
from ..core.exceptions import AppError
from ..config.models import MonitorSettings
from ..core import RPABotCore
from ..installer import EnvChecker
from ..dao_impl.chat.dao import IFeishuMessageRepository

# package modules
from .tabs import ConsoleTab, InstallTab, SettingsTab


class App(ctk.CTk):
    def __init__(self, app_settings_repo, message_repo: IFeishuMessageRepository):
        super().__init__()

        if app_settings_repo is None:
            raise AppError("app_settings_repo is missing")
        if message_repo is None:
            raise AppError("message_repo is missing")

        self.app_settings_repo = app_settings_repo
        self.message_repo = message_repo
        self.monitor_settings = self.app_settings_repo.monitor.get()
        self.internal_settings = self.app_settings_repo.internal.get()

        # Apply UI settings from internal config
        self.title(self.internal_settings.win_title)
        self.geometry(
            f"{self.internal_settings.win_width}x{self.internal_settings.win_height}"
        )
        self.minsize(
            self.internal_settings.win_min_width, self.internal_settings.win_min_height
        )
        ctk.set_appearance_mode(self.internal_settings.appearance_mode)
        ctk.set_default_color_theme(self.internal_settings.color_theme)

        self.bot = None
        self.bot_start_time: float = 0
        self.install_checker = None

        self._build_ui()
        self._log_to_ui("欢迎使用飞书车位助手！")

    def _build_ui(self):
        self.tabview = ctk.CTkTabview(
            self,
            width=self.internal_settings.win_width,
            height=self.internal_settings.win_height,
        )
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabview.add("安装")
        self.tabview.add("控制台")
        self.tabview.add("设置")

        self._build_install_tab()
        self._build_console_tab()
        self._build_settings_tab()
        self._start_stats_loop()

    def _start_stats_loop(self):
        if hasattr(self, "bot") and self.bot and self.bot.is_running:
            uptime = self._calculate_uptime()
            self.console_tab.update_stats(
                self.bot.match_count,
                self.bot.reaction_count,
                self.bot.fail_count,
                uptime,
            )
            self.after(1000, self._start_stats_loop)

    def _calculate_uptime(self) -> str:
        """Calculate uptime from bot start time."""
        if not self.bot or not self.bot.start_time:
            return "0秒"
        total = int(time.time() - self.bot.start_time)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}小时{m}分{s}秒"
        elif m > 0:
            return f"{m}分{s}秒"
        return f"{s}秒"

    def _build_install_tab(self):
        tab = self.tabview.tab("安装")
        self.install_tab = InstallTab(
            tab,
            on_check_env=self._on_check_env,
            on_open_folder=self._open_data_folder,
            app_settings=self.monitor_settings.model_dump(),
        )
        self.install_tab.set_install_callback(self._run_installation)

    def _build_console_tab(self):
        tab = self.tabview.tab("控制台")
        self.console_tab = ConsoleTab(
            tab,
            on_start=self._start_bot,
            on_stop=self._stop_bot,
            on_reset=self._reset_stats,
        )

    def _build_settings_tab(self):
        tab = self.tabview.tab("设置")
        self.settings_tab = SettingsTab(tab, on_save=self._save_settings)
        self.settings_tab.load_config(self.monitor_settings.model_dump())

    def _log_to_ui(self, msg: str):
        if hasattr(self, "console_tab"):
            self.console_tab.log_message(msg)

    def _on_check_env(self, install_tab):
        checker = EnvChecker(log_callback=lambda msg: install_tab.log_message(msg))
        results = checker.check_all()

        key_map = {
            "python": "python",
            "pip": "pip",
            "playwright_pkg": "playwright_pkg",
            "playwright": "playwright_browser",
        }
        for key, data in results.items():
            display_key = key_map.get(key, key)
            status = "✅ 已安装" if data["installed"] else "❌ 未安装"
            install_tab.update_status(display_key, status)

    def _open_data_folder(self):
        from pathlib import Path

        browser_data = Path(__file__).parent.parent.parent / "feishu_browser_data"
        if browser_data.exists():
            import subprocess

            subprocess.Popen(["xdg-open", str(browser_data)])
        else:
            browser_data.mkdir(parents=True, exist_ok=True)
            import subprocess

            subprocess.Popen(["xdg-open", str(browser_data)])

    def _run_installation(self):
        self.install_tab.set_button_state(False)
        self._log_to_ui("开始安装依赖...")

        def install_thread():
            checker = EnvChecker(log_callback=lambda msg: self._log_to_ui(msg))
            checker.check_all()
            success = checker.install_all(
                progress_callback=lambda name: self._log_to_ui(f"正在安装 {name}...")
            )

            self.after(0, lambda: self.install_tab.set_button_state(True))
            if success:
                self.after(0, lambda: self._on_check_env(self.install_tab))

        threading.Thread(target=install_thread, daemon=True).start()

    def _start_bot(self):
        self._save_settings()
        self.monitor_settings = cast(
            MonitorSettings, self.app_settings_repo.monitor.get()
        )
        assert self.monitor_settings is not None
        self.internal_settings = self.app_settings_repo.internal.get()

        self.bot = RPABotCore(
            monitor_settings=self.monitor_settings,
            internal_settings=self.internal_settings,
            message_repo=self.message_repo,
            log_callback=lambda msg: self._log_to_ui(msg),
            stop_callback=self._on_bot_stopped,
        )
        self.bot.start()
        self.console_tab.on_bot_started()
        self._start_stats_loop()

    def _on_bot_stopped(self):
        self._log_to_ui("⏹ 监控已停止")
        if hasattr(self, "bot") and self.bot:
            self.after(0, self._log_final_stats)
        self.after(0, self.console_tab.on_bot_stopped)

    def _log_final_stats(self):
        uptime = self._calculate_uptime()
        self._log_to_ui(
            f"📊 本次运行统计 - 匹配: {self.bot.match_count} | "
            f"点赞: {self.bot.reaction_count} | "
            f"失败: {self.bot.fail_count} | "
            f"时长: {uptime}"
        )

    def _stop_bot(self):
        if self.bot:
            bot = self.bot
            bot.stop()
            if hasattr(bot, "_thread"):
                bot._thread.join(timeout=5)
            self.bot = None

    def _reset_stats(self):
        self.console_tab.reset()
        self._log_to_ui("🔄 统计已重置")

    def _save_settings(self):
        settings = self.settings_tab.get_config_data()

        self.monitor_settings.patterns = settings["patterns"]
        self.monitor_settings.reaction_emoji = settings["reaction_emoji"]
        self.monitor_settings.check_interval = settings["check_interval"]
        self.monitor_settings.max_messages_per_check = settings[
            "max_messages_per_check"
        ]

        self.app_settings_repo.monitor.save(self.monitor_settings)
        self._log_to_ui("💾 设置已保存")
