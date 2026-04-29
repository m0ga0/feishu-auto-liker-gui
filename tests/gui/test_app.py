"""GUI App 逻辑测试"""

from unittest.mock import MagicMock, patch

# Import App - the conftest provides mocked customtkinter
from src.gui.app import App


class TestApp:
    """App 核心逻辑测试"""

    @patch(
        "src.gui.app.load_config",
        return_value={"monitor": {}, "anti_detect": {}, "notification": {}},
    )
    @patch("src.gui.app.BotState")
    @patch("src.gui.app.ConsoleTab")
    @patch("src.gui.app.InstallTab")
    @patch("src.gui.app.SettingsTab")
    def test_app_init(
        self,
        mock_settings,
        mock_install,
        mock_console,
        mock_bot_state,
        mock_load_config,
    ):
        """测试应用初始化"""

        app = App()

        assert app.config_data == {"monitor": {}, "anti_detect": {}, "notification": {}}
        assert mock_bot_state.called
        assert mock_console.called
        assert mock_install.called
        assert mock_settings.called

    @patch(
        "src.gui.app.load_config",
        return_value={"monitor": {}, "anti_detect": {}, "notification": {}},
    )
    @patch("src.gui.app.BotState")
    @patch("src.gui.app.ConsoleTab")
    @patch("src.gui.app.InstallTab")
    @patch("src.gui.app.SettingsTab")
    @patch("src.gui.app.save_config")
    def test_save_settings(
        self,
        mock_save_config,
        mock_settings_class,
        mock_install,
        mock_console,
        mock_bot_state,
        mock_load_config,
    ):
        """测试保存设置逻辑"""
        app = App()

        mock_settings = mock_settings_class.return_value
        mock_settings.get_config_data.return_value = {
            "patterns": ["test"],
            "reaction_emoji": "👍",
            "monitored_groups": ["group1"],
            "check_interval": 2.0,
            "min_delay": 0.5,
            "max_delay": 1.0,
            "desktop_notification": True,
            "self_chat_notify": False,
        }
        app.settings_tab = mock_settings

        app._log_to_ui = MagicMock()  # ty: ignore[invalid-assignment]

        app._save_settings()

        assert mock_save_config.called
        assert app.config_data["monitor"]["patterns"] == ["test"]
        assert app.config_data["notification"]["desktop_notification"] is True

    @patch(
        "src.gui.app.load_config",
        return_value={"monitor": {}, "anti_detect": {}, "notification": {}},
    )
    @patch("src.gui.app.BotState")
    @patch("src.gui.app.ConsoleTab")
    @patch("src.gui.app.InstallTab")
    @patch("src.gui.app.SettingsTab")
    def test_log_to_ui_with_console_tab(
        self,
        mock_settings,
        mock_install,
        mock_console,
        mock_bot_state,
        mock_load_config,
    ):
        """测试日志输出到控制台"""
        app = App()

        app.console_tab = MagicMock()
        app._log_to_ui("test message")

        app.console_tab.log_message.assert_called_once_with("test message")

    @patch(
        "src.gui.app.load_config",
        return_value={"monitor": {}, "anti_detect": {}, "notification": {}},
    )
    @patch("src.gui.app.BotState")
    @patch("src.gui.app.ConsoleTab")
    @patch("src.gui.app.InstallTab")
    @patch("src.gui.app.SettingsTab")
    def test_log_to_ui_without_console_tab(
        self,
        mock_settings,
        mock_install,
        mock_console,
        mock_bot_state,
        mock_load_config,
    ):
        """测试无控制台时不报错"""
        app = App()

        app._log_to_ui("test message")

    @patch(
        "src.gui.app.load_config",
        return_value={"monitor": {}, "anti_detect": {}, "notification": {}},
    )
    @patch("src.gui.app.BotState")
    @patch("src.gui.app.ConsoleTab")
    @patch("src.gui.app.InstallTab")
    @patch("src.gui.app.SettingsTab")
    @patch("src.gui.app.EnvChecker")
    def test_on_check_env(
        self,
        mock_checker_class,
        mock_settings,
        mock_install,
        mock_console,
        mock_bot_state,
        mock_load_config,
    ):
        """测试环境检查"""
        app = App()

        mock_checker = MagicMock()
        mock_checker.check_all.return_value = {
            "python": {"installed": True},
            "pip": {"installed": True},
            "playwright_pkg": {"installed": True},
            "playwright": {"installed": True},
        }
        mock_checker_class.return_value = mock_checker

        mock_install_tab = MagicMock()
        app._on_check_env(mock_install_tab)

        assert mock_checker.check_all.called

    @patch(
        "src.gui.app.load_config",
        return_value={"monitor": {}, "anti_detect": {}, "notification": {}},
    )
    @patch("src.gui.app.BotState")
    @patch("src.gui.app.ConsoleTab")
    @patch("src.gui.app.InstallTab")
    @patch("src.gui.app.SettingsTab")
    @patch("subprocess.Popen")
    def test_open_data_folder_exists(
        self,
        mock_popen,
        mock_settings,
        mock_install,
        mock_console,
        mock_bot_state,
        mock_load_config,
    ):
        """测试打开数据文件夹(已存在)"""
        with patch("pathlib.Path.exists", return_value=True):
            app = App()
            app._open_data_folder()

            mock_popen.assert_called()

    @patch("threading.Thread")
    @patch(
        "src.gui.app.load_config",
        return_value={"monitor": {}, "anti_detect": {}, "notification": {}},
    )
    @patch("src.gui.app.BotState")
    @patch("src.gui.app.ConsoleTab")
    @patch("src.gui.app.InstallTab")
    @patch("src.gui.app.SettingsTab")
    @patch("src.gui.app.EnvChecker")
    def test_run_installation(
        self,
        mock_checker_class,
        mock_settings,
        mock_install,
        mock_console,
        mock_bot_state,
        mock_load_config,
        mock_thread,
    ):
        """测试运行安装"""
        app = App()
        app.install_tab = MagicMock()
        app.console_tab = MagicMock()

        mock_checker = MagicMock()
        mock_checker.install_all.return_value = True
        mock_checker.check_all.return_value = {}
        mock_checker_class.return_value = mock_checker

        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        app._run_installation()

        mock_thread.assert_called()
        mock_thread_instance.start.assert_called()

    @patch(
        "src.gui.app.load_config",
        return_value={"monitor": {}, "anti_detect": {}, "notification": {}},
    )
    @patch("src.gui.app.BotState")
    @patch("src.gui.app.ConsoleTab")
    @patch("src.gui.app.InstallTab")
    @patch("src.gui.app.SettingsTab")
    @patch("src.gui.app.RPABotCore")
    def test_start_bot(
        self,
        mock_bot_core,
        mock_settings,
        mock_install,
        mock_console,
        mock_bot_state,
        mock_load_config,
    ):
        """测试启动机器人"""
        app = App()
        app.settings_tab = MagicMock()
        app.settings_tab.get_config_data.return_value = {
            "patterns": [],
            "reaction_emoji": "👍",
            "monitored_groups": [],
            "check_interval": 2.0,
            "min_delay": 0.5,
            "max_delay": 1.0,
            "desktop_notification": False,
            "self_chat_notify": False,
        }

        app.console_tab = MagicMock()
        app._log_to_ui = MagicMock()  # ty: ignore[invalid-assignment]

        app._start_bot()

        assert mock_bot_core.called

    @patch(
        "src.gui.app.load_config",
        return_value={"monitor": {}, "anti_detect": {}, "notification": {}},
    )
    @patch("src.gui.app.BotState")
    @patch("src.gui.app.ConsoleTab")
    @patch("src.gui.app.InstallTab")
    @patch("src.gui.app.SettingsTab")
    def test_on_bot_stopped(
        self,
        mock_settings,
        mock_install,
        mock_console,
        mock_bot_state,
        mock_load_config,
    ):
        """测试机器人停止回调不报错"""
        app = App()
        app.bot_state = MagicMock()
        app.console_tab = MagicMock()

        app._on_bot_stopped()

    @patch(
        "src.gui.app.load_config",
        return_value={"monitor": {}, "anti_detect": {}, "notification": {}},
    )
    @patch("src.gui.app.BotState")
    @patch("src.gui.app.ConsoleTab")
    @patch("src.gui.app.InstallTab")
    @patch("src.gui.app.SettingsTab")
    def test_log_final_stats(
        self,
        mock_settings,
        mock_install,
        mock_console,
        mock_bot_state,
        mock_load_config,
    ):
        """测试输出最终统计"""
        app = App()
        app.bot_state.match_count = 10
        app.bot_state.reaction_count = 8
        app.bot_state.fail_count = 2

        app._log_to_ui = MagicMock()  # ty: ignore[invalid-assignment]

        app._log_final_stats()

        app._log_to_ui.assert_called()  # ty: ignore[unresolved-attribute]

    @patch(
        "src.gui.app.load_config",
        return_value={"monitor": {}, "anti_detect": {}, "notification": {}},
    )
    @patch("src.gui.app.BotState")
    @patch("src.gui.app.ConsoleTab")
    @patch("src.gui.app.InstallTab")
    @patch("src.gui.app.SettingsTab")
    def test_do_reset(
        self,
        mock_settings,
        mock_install,
        mock_console,
        mock_bot_state,
        mock_load_config,
    ):
        """测试重置状态"""
        app = App()
        app.bot_state = MagicMock()

        app._do_reset()

        app.bot_state.reset.assert_called_once()

    @patch(
        "src.gui.app.load_config",
        return_value={"monitor": {}, "anti_detect": {}, "notification": {}},
    )
    @patch("src.gui.app.BotState")
    @patch("src.gui.app.ConsoleTab")
    @patch("src.gui.app.InstallTab")
    @patch("src.gui.app.SettingsTab")
    def test_reset_stats(
        self,
        mock_settings,
        mock_install,
        mock_console,
        mock_bot_state,
        mock_load_config,
    ):
        """测试重置统计"""
        app = App()
        app.bot_state = MagicMock()
        app.console_tab = MagicMock()

        app._log_to_ui = MagicMock()  # ty: ignore[invalid-assignment]

        app._reset_stats()

        app.bot_state.reset.assert_called_once()
        app.console_tab.reset.assert_called_once()
        app._log_to_ui.assert_called()  # ty: ignore[unresolved-attribute]
