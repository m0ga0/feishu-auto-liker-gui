import customtkinter as ctk


class SettingsTab:
    """Settings tab control class."""

    def __init__(self, tab, on_save):
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

        self.keywords_text = ctk.CTkTextbox(scroll_frame, height=120)
        self.keywords_text.pack(fill="x", pady=5)

        ctk.CTkLabel(
            scroll_frame, text="😀 点赞表情", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(20, 5))

        self.emoji_var = ctk.StringVar(value="赞")

        emoji_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        emoji_frame.pack(fill="x", pady=5)

        emojis = ["赞", "爱心", "鼓掌", "微笑", "大笑", "感谢", "玫瑰", "加油"]
        for emoji in emojis:
            btn = ctk.CTkRadioButton(
                emoji_frame, text=emoji, variable=self.emoji_var, value=emoji
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

        self.groups_text = ctk.CTkTextbox(scroll_frame, height=80)
        self.groups_text.pack(fill="x", pady=5)

        ctk.CTkLabel(
            scroll_frame,
            text="⏱ 检查间隔（秒）",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", pady=(20, 5))

        self.interval_slider = ctk.CTkSlider(
            scroll_frame, from_=1, to=10, number_of_steps=19
        )
        self.interval_slider.pack(fill="x", pady=5)
        self.interval_slider.set(2)

        self.interval_label = ctk.CTkLabel(scroll_frame, text="2.0 秒")
        self.interval_label.pack()

        self.interval_slider.configure(
            command=lambda v: self.interval_label.configure(text=f"{v:.1f} 秒")
        )

        ctk.CTkLabel(
            scroll_frame,
            text="🛡️ 反检测延迟（秒）",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", pady=(20, 5))

        self.delay_min_slider = ctk.CTkSlider(
            scroll_frame, from_=1, to=3, number_of_steps=29
        )
        self.delay_min_slider.pack(fill="x", pady=5)
        self.delay_min_slider.set(0.5)

        self.delay_max_slider = ctk.CTkSlider(
            scroll_frame, from_=1, to=5, number_of_steps=45
        )
        self.delay_max_slider.pack(fill="x", pady=5)
        self.delay_max_slider.set(2.0)

        delay_label_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        delay_label_frame.pack(fill="x")
        ctk.CTkLabel(delay_label_frame, text="最小:").pack(side="left")
        self.delay_min_label = ctk.CTkLabel(delay_label_frame, text="0.5s")
        self.delay_min_label.pack(side="left", padx=5)
        ctk.CTkLabel(delay_label_frame, text="最大:").pack(side="left", padx=(20, 0))
        self.delay_max_label = ctk.CTkLabel(delay_label_frame, text="2.0s")
        self.delay_max_label.pack(side="left", padx=5)

        self.delay_min_slider.configure(
            command=lambda v: self.delay_min_label.configure(text=f"{v:.1f}s")
        )
        self.delay_max_slider.configure(
            command=lambda v: self.delay_max_label.configure(text=f"{v:.1f}s")
        )

        ctk.CTkLabel(
            scroll_frame,
            text="🔔 通知设置",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", pady=(20, 5))

        self.desktop_notify_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            scroll_frame,
            text="桌面通知",
            variable=self.desktop_notify_var,
        ).pack(anchor="w", pady=5)

        self.self_chat_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            scroll_frame,
            text="发送通知到我的飞书",
            variable=self.self_chat_var,
        ).pack(anchor="w", pady=5)

        ctk.CTkButton(
            scroll_frame,
            text="💾 保存设置",
            fg_color="#5865F2",
            hover_color="#4752C4",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=on_save,
            height=40,
        ).pack(pady=20)

    def load_config(self, config_data: dict):
        keywords = config_data.get("patterns", [])
        self.keywords_text.insert("1.0", "\n".join(keywords))

        self.emoji_var.set(config_data.get("reaction_emoji", "赞"))

        groups = config_data.get("monitored_groups", [])
        self.groups_text.insert("1.0", "\n".join(groups))

        self.interval_slider.set(config_data.get("check_interval", 2))
        self.interval_label.configure(
            text=f"{config_data.get('check_interval', 2):.1f} 秒"
        )

    def load_anti_detect(self, anti_data: dict):
        self.delay_min_slider.set(anti_data.get("min_delay", 0.5))
        self.delay_min_label.configure(text=f"{anti_data.get('min_delay', 0.5):.1f}s")

        self.delay_max_slider.set(anti_data.get("max_delay", 2.0))
        self.delay_max_label.configure(text=f"{anti_data.get('max_delay', 2.0):.1f}s")

    def load_notification(self, notify_data: dict):
        self.desktop_notify_var.set(notify_data.get("desktop_notification", False))
        self.self_chat_var.set(notify_data.get("self_chat_notify", False))

    def get_config_data(self) -> dict:
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

        return {
            "patterns": keywords,
            "reaction_emoji": self.emoji_var.get(),
            "monitored_groups": groups,
            "check_interval": self.interval_slider.get(),
            "min_delay": self.delay_min_slider.get(),
            "max_delay": self.delay_max_slider.get(),
            "desktop_notification": self.desktop_notify_var.get(),
            "self_chat_notify": self.self_chat_var.get(),
        }
