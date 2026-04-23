import customtkinter as ctk


class ConsoleTab:
    """Console tab control class."""

    def __init__(self, tab, on_start, on_stop, on_reset):
        status_frame = ctk.CTkFrame(tab)
        status_frame.pack(fill="x", padx=20, pady=15)

        self.status_indicator = ctk.CTkLabel(
            status_frame, text="⏹ 未运行", font=ctk.CTkFont(size=16, weight="bold")
        )
        self.status_indicator.pack(side="left", padx=20, pady=10)

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

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="▶ 启动监控",
            fg_color="green",
            hover_color="darkgreen",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=on_start
        )
        self.start_btn.pack(side="left", padx=10)

        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹ 停止",
            fg_color="red",
            hover_color="darkred",
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
            command=on_stop
        )
        self.stop_btn.pack(side="left", padx=10)

        self.reset_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 重置统计",
            font=ctk.CTkFont(size=14),
            command=on_reset
        )
        self.reset_btn.pack(side="left", padx=10)

        ctk.CTkLabel(
            tab, text="运行日志", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 0))

        self.console_log = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=12))
        self.console_log.pack(fill="both", expand=True, padx=20, pady=10)
        self.console_log.configure(state="disabled")

    def log_message(self, msg):
        self.console_log.configure(state="normal")
        self.console_log.insert("end", f"{msg}\n")
        self.console_log.see("end")
        self.console_log.configure(state="disabled")

    def update_stats(self, match, reaction, fail, uptime):
        self.stat_labels["match_count"].configure(text=str(match))
        self.stat_labels["reaction_count"].configure(text=str(reaction))
        self.stat_labels["fail_count"].configure(text=str(fail))
        self.stat_labels["uptime"].configure(text=uptime)

    def on_bot_started(self):
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_indicator.configure(text="🟢 运行中", text_color="green")

    def on_bot_stopped(self):
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_indicator.configure(text="⏹ 已停止", text_color="red")

    def reset(self):
        self.stat_labels["match_count"].configure(text="0")
        self.stat_labels["reaction_count"].configure(text="0")
        self.stat_labels["fail_count"].configure(text="0")
        self.stat_labels["uptime"].configure(text="0")