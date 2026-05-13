"""GUI SettingsTab 逻辑测试"""

from unittest.mock import MagicMock
from parkbot.gui.tabs.settings_tab import SettingsTab


class TestSettingsTab:
    """SettingsTab 界面逻辑测试"""

    def test_init_creates_widgets(self):
        """测试控件创建"""
        tab = MagicMock()
        on_save = MagicMock()

        settings = SettingsTab(tab, on_save)

        assert hasattr(settings, "keywords_text")
        assert hasattr(settings, "emoji_var")
        assert hasattr(settings, "interval_slider")

    def test_load_config(self):
        """测试加载配置"""
        tab = MagicMock()
        on_save = MagicMock()

        settings = SettingsTab(tab, on_save)

        # Mock widgets
        settings.keywords_text = MagicMock()
        settings.keywords_text.insert = MagicMock()
        settings.interval_slider = MagicMock()
        settings.interval_label = MagicMock()
        settings.emoji_var = MagicMock()

        config_data = {
            "patterns": ["车位", "租房"],
            "reaction_emoji": "爱心",
            "check_interval": 5,
        }

        settings.load_config(config_data)

        settings.keywords_text.insert.assert_called_with("1.0", "车位\n租房")
        settings.interval_slider.set.assert_called_with(5)
        settings.emoji_var.set.assert_called_with("爱心")

    def test_get_config_data(self):
        """测试获取配置数据"""
        tab = MagicMock()
        on_save = MagicMock()

        settings = SettingsTab(tab, on_save)

        # Mock widgets
        settings.keywords_text = MagicMock()
        settings.keywords_text.get.return_value = "车位\n租房"

        settings.emoji_var = MagicMock()
        settings.emoji_var.get.return_value = "爱心"

        settings.interval_slider = MagicMock()
        settings.interval_slider.get.return_value = 5

        config = settings.get_config_data()

        assert config["patterns"] == ["车位", "租房"]
        assert config["reaction_emoji"] == "爱心"
        assert config["check_interval"] == 5

    def test_get_config_data_filters_empty_lines(self):
        """测试获取配置时过滤空行"""
        tab = MagicMock()
        on_save = MagicMock()

        settings = SettingsTab(tab, on_save)

        # Mock with empty lines
        settings.keywords_text = MagicMock()
        settings.keywords_text.get.return_value = "车位\n\n  \n租房"

        settings.emoji_var = MagicMock()
        settings.emoji_var.get.return_value = "赞"

        settings.interval_slider = MagicMock()
        settings.interval_slider.get.return_value = 2

        config = settings.get_config_data()

        # Empty lines should be filtered
        assert config["patterns"] == ["车位", "租房"]
