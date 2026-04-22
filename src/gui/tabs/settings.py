import customtkinter as ctk


def build_settings_tab(
    tab,
    keywords_text,
    emoji_var,
    groups_text,
    interval_slider,
    interval_label,
    delay_min_slider,
    delay_min_label,
    delay_max_slider,
    delay_max_label,
    desktop_notify_var,
    self_chat_var,
    config_data,
):
    scroll_frame = ctk.CTkScrollableFrame(tab)
    scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

    ctk.CTkLabel(
        scroll_frame, text="🎯 监控关键词", font=ctk.CTkFont(size=16, weight="bold")
    ).pack(anchor="w", pady=(10, 5))

    ctk.CTkLabel(
        scroll_frame,
        text="每行一个关键词，支持正则表达式（以 re: 开头）",
        text_color="gray",
    ).pack(anchor="w")

    keywords_text.configure(height=120)
    keywords_text.pack(fill="x", pady=5)
    keywords_text.insert(
        "1.0", "\n".join(config_data.get("monitor", {}).get("patterns", []))
    )

    ctk.CTkLabel(
        scroll_frame, text="😀 点赞表情", font=ctk.CTkFont(size=16, weight="bold")
    ).pack(anchor="w", pady=(20, 5))

    emoji_var.set(config_data.get("monitor", {}).get("reaction_emoji", "赞"))

    emojis = ["赞", "爱心", "鼓掌", "微笑", "大笑", "感谢", "玫瑰", "加油"]
    emoji_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
    emoji_frame.pack(fill="x", pady=5)

    for emoji in emojis:
        btn = ctk.CTkRadioButton(
            emoji_frame, text=emoji, variable=emoji_var, value=emoji
        )
        btn.pack(side="left", padx=10)

    ctk.CTkLabel(
        scroll_frame, text="💬 监控群组", font=ctk.CTkFont(size=16, weight="bold")
    ).pack(anchor="w", pady=(20, 5))

    ctk.CTkLabel(
        scroll_frame,
        text="每行一个群名（留空表示监控当前活跃聊天）",
        text_color="gray",
    ).pack(anchor="w")

    groups_text.configure(height=80)
    groups_text.pack(fill="x", pady=5)
    groups_text.insert(
        "1.0",
        "\n".join(config_data.get("monitor", {}).get("monitored_groups", [])),
    )

    ctk.CTkLabel(
        scroll_frame,
        text="⏱ 检查间隔（秒）",
        font=ctk.CTkFont(size=16, weight="bold"),
    ).pack(anchor="w", pady=(20, 5))

    interval_slider.configure(from_=0.5, to=10, number_of_steps=19)
    interval_slider.pack(fill="x", pady=5)
    interval_slider.set(config_data.get("monitor", {}).get("check_interval", 2))

    interval_label.configure(text=f"{interval_slider.get():.1f} 秒")
    interval_label.pack()
    interval_slider.configure(
        command=lambda v: interval_label.configure(text=f"{v:.1f} 秒")
    )

    ctk.CTkLabel(
        scroll_frame,
        text="🛡️ 反检测延迟（秒）",
        font=ctk.CTkFont(size=16, weight="bold"),
    ).pack(anchor="w", pady=(20, 5))

    anti = config_data.get("anti_detect", {})
    delay_min_slider.configure(from_=0.1, to=3, number_of_steps=29)
    delay_min_slider.pack(fill="x", pady=5)
    delay_min_slider.set(anti.get("min_delay", 0.5))

    delay_max_slider.configure(from_=0.5, to=5, number_of_steps=45)
    delay_max_slider.pack(fill="x", pady=5)
    delay_max_slider.set(anti.get("max_delay", 2.0))

    delay_label_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
    delay_label_frame.pack(fill="x")
    ctk.CTkLabel(delay_label_frame, text="最小:").pack(side="left")
    delay_min_label.configure(text=f"{anti.get('min_delay', 0.5):.1f}s")
    delay_min_label.pack(side="left", padx=5)
    ctk.CTkLabel(delay_label_frame, text="最大:").pack(side="left", padx=(20, 0))
    delay_max_label.configure(text=f"{anti.get('max_delay', 2.0):.1f}s")
    delay_max_label.pack(side="left", padx=5)

    delay_min_slider.configure(
        command=lambda v: delay_min_label.configure(text=f"{v:.1f}s")
    )
    delay_max_slider.configure(
        command=lambda v: delay_max_label.configure(text=f"{v:.1f}s")
    )

    ctk.CTkLabel(
        scroll_frame,
        text="🔔 通知设置",
        font=ctk.CTkFont(size=16, weight="bold"),
    ).pack(anchor="w", pady=(20, 5))

    desktop_notify_var.set(config_data.get("notification", {}).get("desktop_notification", True))
    ctk.CTkCheckBox(
        scroll_frame, text="桌面弹窗通知", variable=desktop_notify_var
    ).pack(anchor="w", pady=5)

    self_chat_var.set(config_data.get("notification", {}).get("self_chat_notify", False))
    ctk.CTkCheckBox(
        scroll_frame, text="发送消息到文件助手", variable=self_chat_var
    ).pack(anchor="w", pady=5)

    return scroll_frame