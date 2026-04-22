import customtkinter as ctk


def build_install_tab(tab, install_items, install_btn, install_log, config_data):
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

    install_frame = ctk.CTkFrame(tab)
    install_frame.pack(fill="x", padx=40, pady=10)

    items = [
        ("python", "Python 运行环境"),
        ("pip", "pip 包管理器"),
        ("playwright_pkg", "Playwright 自动化库"),
        ("playwright_browser", "Chromium 浏览器"),
    ]

    for key, label in items:
        row = ctk.CTkFrame(install_frame, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(row, text=label, width=200, anchor="w").pack(side="left")
        status = ctk.CTkLabel(row, text="⏳ 检查中...", width=100, anchor="center")
        status.pack(side="left")
        install_items[key] = status

    install_btn.configure(text="🚀 一键安装", font=ctk.CTkFont(size=16, weight="bold"), height=50)
    install_btn.pack(pady=30)

    install_log.configure(height=150, font=ctk.CTkFont(size=12), state="disabled")
    install_log.pack(fill="x", padx=40, pady=10)

    return install_frame