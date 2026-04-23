import customtkinter as ctk
import threading


class InstallTab:
    """Install tab control class."""

    def __init__(self, tab, on_check_env, on_open_folder, app_settings):
        self._on_check_env = on_check_env
        self._on_open_folder = on_open_folder

        ctk.CTkLabel(
            tab,
            text="环境检测",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=40, pady=(20, 5))

        ctk.CTkLabel(
            tab,
            text="检测飞书RPA运行所需的环境依赖",
            text_color="gray",
        ).pack(anchor="w", padx=40, pady=(0, 20))

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

        self.install_btn = ctk.CTkButton(
            tab,
            text="🚀 一键安装",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self._on_install_clicked
        )
        self.install_btn.pack(pady=30)

        self.install_log = ctk.CTkTextbox(tab, height=150, font=ctk.CTkFont(size=12))
        self.install_log.pack(fill="x", padx=40, pady=10)
        self.install_log.configure(state="disabled")

        self._start_env_check()

    def _start_env_check(self):
        def check():
            self._on_check_env(self)

        threading.Thread(target=check, daemon=True).start()

    def _on_install_clicked(self):
        if hasattr(self, "_install_callback"):
            self._install_callback()

    def update_status(self, key, status):
        if key in self.install_items:
            self.install_items[key].configure(text=status)

    def set_install_callback(self, callback):
        self._install_callback = callback

    def log_message(self, msg):
        self.install_log.configure(state="normal")
        self.install_log.insert("end", f"{msg}\n")
        self.install_log.see("end")
        self.install_log.configure(state="disabled")

    def set_button_state(self, enabled, text=None):
        if enabled:
            self.install_btn.configure(state="normal")
        else:
            self.install_btn.configure(state="disabled")
        if text:
            self.install_btn.configure(text=text)
