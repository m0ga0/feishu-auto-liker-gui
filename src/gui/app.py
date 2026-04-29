import threading

import customtkinter as ctk

from ..config import load_config, save_config
from ..core import RPABotCore
from ..installer import EnvChecker
from ..state import BotState
from .tabs import ConsoleTab, InstallTab, SettingsTab


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("飞书自动点赞助手")
        self.geometry("900x700")
        self.minsize(800, 600)

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.config_data = load_config()
        self.bot_state = BotState()
        self.bot = None
        self.install_checker = None

        self._build_ui()
        self._log_to_ui("欢迎使用飞书自动点赞助手！")

    def _build_ui(self):
        self.tabview = ctk.CTkTabview(self, width=900, height=700)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabview.add("安装")
        self.tabview.add("控制台")
        self.tabview.add("设置")

        self._build_install_tab()
        self._build_console_tab()
        self._build_settings_tab()
        self._start_stats_loop()

    def _start_stats_loop(self):
        if hasattr(self, "bot_state") and self.bot_state.is_running:
            self.console_tab.update_stats(
                self.bot_state.match_count,
                self.bot_state.reaction_count,
                self.bot_state.fail_count,
                self.bot_state.uptime,
            )
            self.after(1000, self._start_stats_loop)

    def _build_install_tab(self):
        tab = self.tabview.tab("安装")
        self.install_tab = InstallTab(
            tab,
            on_check_env=self._on_check_env,
            on_open_folder=self._open_data_folder,
            app_settings=self.config_data,
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
        self.settings_tab.load_config(self.config_data.get("monitor", {}))
        self.settings_tab.load_anti_detect(self.config_data.get("anti_detect", {}))
        self.settings_tab.load_notification(self.config_data.get("notification", {}))

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
        self.config_data = load_config()
        self.bot_state.reset()
        self.bot_state.is_running = True
        self.bot = RPABotCore(
            self.config_data,
            self.bot_state,
            log_callback=lambda msg: self._log_to_ui(msg),
            stop_callback=self._on_bot_stopped,
        )
        self.bot.start()
        self.console_tab.on_bot_started()
        self._start_stats_loop()

    def _on_bot_stopped(self):
        self._log_to_ui("⏹ 监控已停止")
        if hasattr(self, "bot_state") and self.bot_state:
            self.after(0, self._log_final_stats)
            self.after(0, self._do_reset)
        self.after(0, self.console_tab.on_bot_stopped)

    def _log_final_stats(self):
        self._log_to_ui(
            f"📊 本次运行统计 - 匹配: {self.bot_state.match_count} | "
            f"点赞: {self.bot_state.reaction_count} | "
            f"失败: {self.bot_state.fail_count} | "
            f"时长: {self.bot_state.uptime}"
        )

    def _do_reset(self):
        self.bot_state.reset()

    def _stop_bot(self):
        if self.bot:
            bot = self.bot
            bot.stop()
            if hasattr(bot, "_thread"):
                bot._thread.join(timeout=5)
            self.bot = None

    def _reset_stats(self):
        self.bot_state.reset()
        self.console_tab.reset()
        self._log_to_ui("🔄 统计已重置")

    def _save_settings(self):
        settings = self.settings_tab.get_config_data()
        self.config_data["monitor"]["patterns"] = settings["patterns"]
        self.config_data["monitor"]["reaction_emoji"] = settings["reaction_emoji"]
        self.config_data["monitor"]["monitored_groups"] = settings["monitored_groups"]
        self.config_data["monitor"]["check_interval"] = settings["check_interval"]
        self.config_data["anti_detect"]["min_delay"] = settings["min_delay"]
        self.config_data["anti_detect"]["max_delay"] = settings["max_delay"]
        self.config_data["notification"]["desktop_notification"] = settings.get(
            "desktop_notification", False
        )
        self.config_data["notification"]["self_chat_notify"] = settings.get(
            "self_chat_notify", False
        )

        save_config(self.config_data)
        self._log_to_ui("💾 设置已保存")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
