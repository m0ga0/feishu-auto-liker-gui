"""GUI SettingsTab 逻辑测试"""

from unittest.mock import MagicMock
from src.gui.tabs.settings_tab import SettingsTab


class TestSettingsTab:
    """SettingsTab 界面逻辑测试"""

    def test_init_creates_widgets(self):
        """测试控件创建"""
        tab = MagicMock()
        on_save = MagicMock()

        settings = SettingsTab(tab, on_save)

        assert hasattr(settings, "keywords_text")
        assert hasattr(settings, "emoji_var")
        assert hasattr(settings, "groups_text")
        assert hasattr(settings, "interval_slider")
        assert hasattr(settings, "delay_min_slider")
        assert hasattr(settings, "delay_max_slider")

    def test_load_config(self):
        """测试加载配置"""
        tab = MagicMock()
        on_save = MagicMock()

        settings = SettingsTab(tab, on_save)

        # Mock textboxes
        settings.keywords_text = MagicMock()
        settings.keywords_text.insert = MagicMock()
        settings.groups_text = MagicMock()
        settings.groups_text.insert = MagicMock()
        settings.interval_slider = MagicMock()
        settings.interval_label = MagicMock()
        settings.emoji_var = MagicMock()

        config_data = {
            "patterns": ["车位", "租房"],
            "reaction_emoji": "爱心",
            "monitored_groups": ["群1", "群2"],
            "check_interval": 5,
        }

        settings.load_config(config_data)

        settings.keywords_text.insert.assert_called_with("1.0", "车位\n租房")
        settings.groups_text.insert.assert_called_with("1.0", "群1\n群2")
        settings.interval_slider.set.assert_called_with(5)
        settings.emoji_var.set.assert_called_with("爱心")

    def test_load_anti_detect(self):
        """测试加载反检测设置"""
        tab = MagicMock()
        on_save = MagicMock()

        settings = SettingsTab(tab, on_save)

        # Mock sliders and labels
        settings.delay_min_slider = MagicMock()
        settings.delay_max_slider = MagicMock()
        settings.delay_min_label = MagicMock()
        settings.delay_max_label = MagicMock()

        anti_data = {
            "min_delay": 1.0,
            "max_delay": 3.0,
        }

        settings.load_anti_detect(anti_data)

        settings.delay_min_slider.set.assert_called_with(1.0)
        settings.delay_min_label.configure.assert_called_with(text="1.0s")
        settings.delay_max_slider.set.assert_called_with(3.0)
        settings.delay_max_label.configure.assert_called_with(text="3.0s")

    def test_load_notification(self):
        """测试加载通知设置"""
        tab = MagicMock()
        on_save = MagicMock()

        settings = SettingsTab(tab, on_save)

        # Mock vars
        settings.desktop_notify_var = MagicMock()
        settings.self_chat_var = MagicMock()

        notify_data = {
            "desktop_notification": True,
            "self_chat_notify": False,
        }

        settings.load_notification(notify_data)

        settings.desktop_notify_var.set.assert_called_with(True)
        settings.self_chat_var.set.assert_called_with(False)

    def test_get_config_data(self):
        """测试获取配置数据"""
        tab = MagicMock()
        on_save = MagicMock()

        settings = SettingsTab(tab, on_save)

        # Mock widgets
        settings.keywords_text = MagicMock()
        settings.keywords_text.get.return_value = "车位\n租房"

        settings.groups_text = MagicMock()
        settings.groups_text.get.return_value = "群1\n群2"

        settings.emoji_var = MagicMock()
        settings.emoji_var.get.return_value = "爱心"

        settings.interval_slider = MagicMock()
        settings.interval_slider.get.return_value = 5

        settings.delay_min_slider = MagicMock()
        settings.delay_min_slider.get.return_value = 1.0

        settings.delay_max_slider = MagicMock()
        settings.delay_max_slider.get.return_value = 2.0

        settings.desktop_notify_var = MagicMock()
        settings.desktop_notify_var.get.return_value = True

        settings.self_chat_var = MagicMock()
        settings.self_chat_var.get.return_value = False

        config = settings.get_config_data()

        assert config["patterns"] == ["车位", "租房"]
        assert config["reaction_emoji"] == "爱心"
        assert config["monitored_groups"] == ["群1", "群2"]
        assert config["check_interval"] == 5
        assert config["min_delay"] == 1.0
        assert config["max_delay"] == 2.0
        assert config["desktop_notification"] is True
        assert config["self_chat_notify"] is False

    def test_get_config_data_filters_empty_lines(self):
        """测试获取配置时过滤空行"""
        tab = MagicMock()
        on_save = MagicMock()

        settings = SettingsTab(tab, on_save)

        # Mock with empty lines
        settings.keywords_text = MagicMock()
        settings.keywords_text.get.return_value = "车位\n\n  \n租房"

        settings.groups_text = MagicMock()
        settings.groups_text.get.return_value = "群1"

        settings.emoji_var = MagicMock()
        settings.emoji_var.get.return_value = "赞"

        settings.interval_slider = MagicMock()
        settings.interval_slider.get.return_value = 2

        settings.delay_min_slider = MagicMock()
        settings.delay_min_slider.get.return_value = 0.5

        settings.delay_max_slider = MagicMock()
        settings.delay_max_slider.get.return_value = 2.0

        settings.desktop_notify_var = MagicMock()
        settings.desktop_notify_var.get.return_value = False

        settings.self_chat_var = MagicMock()
        settings.self_chat_var.get.return_value = False

        config = settings.get_config_data()

        # Empty lines should be filtered
        assert config["patterns"] == ["车位", "租房"]
