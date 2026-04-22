DEFAULT_CONFIG = {
    "monitor": {
        "patterns": ["re:.*(出|整出).*(车位|停车位|首赞).*"],
        "reaction_emoji": "赞",
        "monitored_groups": [],
        "check_interval": 2,
        "max_messages_per_check": 3,
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