import threading
from typing import Optional

import customtkinter as ctk

from ..config import load_config
from ..core import RPABotCore
from ..state import BotState
from .tabs import build_install_tab, build_console_tab, build_settings_tab


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
        self.bot: Optional[RPABotCore] = None

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

    def _build_install_tab(self):
        tab = self.tabview.tab("安装")

        self.install_items = {}
        self.install_btn = ctk.CTkButton(tab, command=self._run_installation)
        self.install_log = ctk.CTkTextbox(tab)

        build_install_tab(
            tab,
            self.install_items,
            self.install_btn,
            self.install_log,
            self.config_data,
        )
        self.after(500, self._auto_check_env)

    def _build_console_tab(self):
        tab = self.tabview.tab("控制台")

        self.status_indicator = ctk.CTkLabel(tab)
        self.stat_labels = {}
        self.start_btn = ctk.CTkButton(tab, command=self._start_bot)
        self.stop_btn = ctk.CTkButton(tab, command=self._stop_bot)
        self.reset_btn = ctk.CTkButton(tab, command=self._reset_stats)
        self.console_log = ctk.CTkTextbox(tab)

        build_console_tab(
            tab,
            self.status_indicator,
            self.stat_labels,
            self.start_btn,
            self.stop_btn,
            self.reset_btn,
            self.console_log,
            self.config_data,
        )
        self._update_stats_loop()

    def _build_settings_tab(self):
        tab = self.tabview.tab("设置")

        self.keywords_text = ctk.CTkTextbox(tab)
        self.emoji_var = ctk.StringVar()
        self.groups_text = ctk.CTkTextbox(tab)
        self.interval_slider = ctk.CTkSlider(tab, from_=1, to=10, number_of_steps=19)
        self.interval_label = ctk.CTkLabel(tab)
        self.delay_min_slider = ctk.CTkSlider(tab, from_=1, to=3, number_of_steps=29)
        self.delay_min_label = ctk.CTkLabel(tab)
        self.delay_max_slider = ctk.CTkSlider(tab, from_=1, to=5, number_of_steps=45)
        self.delay_max_label = ctk.CTkLabel(tab)
        self.desktop_notify_var = ctk.BooleanVar()
        self.self_chat_var = ctk.BooleanVar()

        build_settings_tab(
            tab,
            self.keywords_text,
            self.emoji_var,
            self.groups_text,
            self.interval_slider,
            self.interval_label,
            self.delay_min_slider,
            self.delay_min_label,
            self.delay_max_slider,
            self.delay_max_label,
            self.desktop_notify_var,
            self.self_chat_var,
            self.config_data,
        )

    def _log_to_ui(self, msg: str, widget=None):
        w = widget or self.console_log
        w.configure(state="normal")
        w.insert("end", f"{msg}\n")
        w.see("end")
        w.configure(state="disabled")

    def _auto_check_env(self):
        from ..installer import EnvChecker

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
            from ..installer import EnvChecker

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
        self.bot_state.reset()
        self.bot_state.is_running = True
        self.bot = RPABotCore(
            self.config_data,
            self.bot_state,
            log_callback=lambda msg: self._log_to_ui(msg),
            stop_callback=self._on_bot_stopped,
        )
        self.bot.start()
        self._update_stats_loop()

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_indicator.configure(text="🟢 运行中", text_color="green")

    def _on_bot_stopped(self):
        self._log_to_ui("⏹ 监控已停止")
        if hasattr(self, "bot_state") and self.bot_state:
            self.after(0, self._log_final_stats)
            self.after(0, self._do_reset)
        self.after(0, self._update_ui_stopped)

    def _log_final_stats(self):
        self._log_to_ui(
            f"📊 本次运行统计 - 匹配: {self.bot_state.match_count} | "
            f"点赞: {self.bot_state.reaction_count} | "
            f"失败: {self.bot_state.fail_count} | "
            f"时长: {self.bot_state.uptime}"
        )

    def _do_reset(self):
        self.bot_state.reset()

    def _update_ui_stopped(self):
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_indicator.configure(text="⏹ 已停止", text_color="red")

    def _stop_monitoring(self):
        self._update_ui_stopped()

    def _update_ui_after_stop(self):
        self._update_ui_stopped()

    def _stop_bot(self):
        if self.bot:
            self.bot.stop()
            self.bot = None
        self._stop_monitoring()

    def _reset_stats(self):
        self.bot_state.reset()
        self._log_to_ui("🔄 统计已重置")

    def _update_stats_loop(self):
        self.stat_labels["match_count"].configure(text=str(self.bot_state.match_count))
        self.stat_labels["reaction_count"].configure(
            text=str(self.bot_state.reaction_count)
        )
        self.stat_labels["fail_count"].configure(text=str(self.bot_state.fail_count))
        self.stat_labels["uptime"].configure(text=self.bot_state.uptime)
        if self.bot_state.is_running:
            self.after(1000, self._update_stats_loop)

    def _save_settings(self):
        from ..config import save_config

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