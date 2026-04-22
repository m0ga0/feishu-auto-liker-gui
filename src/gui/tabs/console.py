import customtkinter as ctk


def build_console_tab(tab, status_indicator, stat_labels, start_btn, stop_btn, reset_btn, console_log, config_data):
    status_frame = ctk.CTkFrame(tab)
    status_frame.pack(fill="x", padx=20, pady=15)

    status_indicator.configure(text="⏹ 未运行", font=ctk.CTkFont(size=16, weight="bold"))
    status_indicator.pack(side="left", padx=20, pady=10)

    stats_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
    stats_frame.pack(side="right", padx=20, pady=10)

    stats = [
        ("match_count", "匹配次数"),
        ("reaction_count", "点赞成功"),
        ("fail_count", "失败次数"),
        ("uptime", "运行时长"),
    ]

    for key, label in stats:
        row = ctk.CTkFrame(stats_frame, fg_color="transparent")
        row.pack(side="left", padx=10)
        ctk.CTkLabel(
            row, text=label, font=ctk.CTkFont(size=11), text_color="gray"
        ).pack()
        val = ctk.CTkLabel(row, text="0", font=ctk.CTkFont(size=16, weight="bold"))
        val.pack()
        stat_labels[key] = val

    btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=10)

    start_btn.configure(
        text="▶ 启动监控",
        fg_color="green",
        hover_color="darkgreen",
        font=ctk.CTkFont(size=14, weight="bold"),
    )
    start_btn.pack(side="left", padx=10)

    stop_btn.configure(
        text="⏹ 停止",
        fg_color="red",
        hover_color="darkred",
        font=ctk.CTkFont(size=14, weight="bold"),
        state="disabled",
    )
    stop_btn.pack(side="left", padx=10)

    reset_btn.configure(text="🔄 重置统计", font=ctk.CTkFont(size=14))
    reset_btn.pack(side="left", padx=10)

    ctk.CTkLabel(
        tab, text="运行日志", font=ctk.CTkFont(size=14, weight="bold")
    ).pack(anchor="w", padx=20, pady=(10, 0))

    console_log.configure(font=ctk.CTkFont(size=12), state="disabled")
    console_log.pack(fill="both", expand=True, padx=20, pady=10)

    return btn_frame