import pytest
from unittest.mock import MagicMock, patch

# Import App - the conftest provides mocked customtkinter
from parkbot.gui.app import App
from parkbot.config.models import MonitorSettings, InternalSettings
from parkbot.dao_impl.chat.repo_impls import InMemoryFeishuMessageRepository


@pytest.fixture
def mock_config_repo():
    """Create a mock config repository."""
    repo = MagicMock()

    # Setup monitor settings
    monitor_settings = MonitorSettings(
        patterns=[], reaction_emoji="👍", check_interval=2.0, max_messages_per_check=3
    )
    repo.monitor.get.return_value = monitor_settings

    # Setup internal settings
    internal_settings = InternalSettings(
        browser_user_data_dir="./feishu_browser_data",
        browser_win_width=1280,
        browser_win_height=800,
        logging_level="INFO",
        logging_dir="rpa_bot.log",
        win_title="飞书自动点赞助手",
        win_width=900,
        win_height=700,
        win_min_width=800,
        win_min_height=600,
        appearance_mode="system",
        color_theme="blue",
    )
    repo.internal.get.return_value = internal_settings

    return repo


@pytest.fixture
def mock_message_repo():
    """Create a mock message repository."""
    return InMemoryFeishuMessageRepository()


class TestApp:
    @patch("parkbot.gui.app.ConsoleTab")
    @patch("parkbot.gui.app.InstallTab")
    @patch("parkbot.gui.app.SettingsTab")
    def test_app_init(
        self,
        mock_settings,
        mock_install,
        mock_console,
        mock_config_repo,
        mock_message_repo,
    ):
        App(app_settings_repo=mock_config_repo, message_repo=mock_message_repo)

        assert mock_console.called
        assert mock_install.called
        assert mock_settings.called

    @patch("parkbot.gui.app.ConsoleTab")
    @patch("parkbot.gui.app.InstallTab")
    @patch("parkbot.gui.app.SettingsTab")
    def test_save_settings(
        self,
        mock_settings_class,
        mock_install,
        mock_console,
        mock_config_repo,
        mock_message_repo,
    ):
        app = App(app_settings_repo=mock_config_repo, message_repo=mock_message_repo)

        mock_settings = mock_settings_class.return_value
        mock_settings.get_config_data.return_value = {
            "patterns": ["test"],
            "reaction_emoji": "👍",
            "check_interval": 2.0,
            "max_messages_per_check": 3,
        }
        app.settings_tab = mock_settings

        with patch.object(app, "_log_to_ui", MagicMock()):
            app._save_settings()
            assert app.monitor_settings.patterns == ["test"]
            mock_config_repo.monitor.save.assert_called()

    @patch("parkbot.gui.app.ConsoleTab")
    @patch("parkbot.gui.app.InstallTab")
    @patch("parkbot.gui.app.SettingsTab")
    def test_log_to_ui_with_console_tab(
        self,
        mock_settings,
        mock_install,
        mock_console,
        mock_config_repo,
        mock_message_repo,
    ):
        app = App(app_settings_repo=mock_config_repo, message_repo=mock_message_repo)

        app.console_tab = MagicMock()
        app._log_to_ui("test message")

        app.console_tab.log_message.assert_called_once_with("test message")

    @patch("parkbot.gui.app.ConsoleTab")
    @patch("parkbot.gui.app.InstallTab")
    @patch("parkbot.gui.app.SettingsTab")
    def test_log_to_ui_without_console_tab(
        self,
        mock_settings,
        mock_install,
        mock_console,
        mock_config_repo,
        mock_message_repo,
    ):
        app = App(app_settings_repo=mock_config_repo, message_repo=mock_message_repo)

        app._log_to_ui("test message")

    @patch("parkbot.gui.app.ConsoleTab")
    @patch("parkbot.gui.app.InstallTab")
    @patch("parkbot.gui.app.SettingsTab")
    @patch("parkbot.gui.app.EnvChecker")
    def test_on_check_env(
        self,
        mock_checker_class,
        mock_settings,
        mock_install,
        mock_console,
        mock_config_repo,
        mock_message_repo,
    ):
        app = App(app_settings_repo=mock_config_repo, message_repo=mock_message_repo)

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

    @patch("parkbot.gui.app.ConsoleTab")
    @patch("parkbot.gui.app.InstallTab")
    @patch("parkbot.gui.app.SettingsTab")
    @patch("subprocess.Popen")
    def test_open_data_folder_exists(
        self,
        mock_popen,
        mock_settings,
        mock_install,
        mock_console,
        mock_config_repo,
        mock_message_repo,
    ):
        app = App(app_settings_repo=mock_config_repo, message_repo=mock_message_repo)

        with patch("pathlib.Path.exists", return_value=True):
            app._open_data_folder()

            mock_popen.assert_called()

    @patch("threading.Thread")
    @patch("parkbot.gui.app.ConsoleTab")
    @patch("parkbot.gui.app.InstallTab")
    @patch("parkbot.gui.app.SettingsTab")
    @patch("parkbot.gui.app.EnvChecker")
    def test_run_installation(
        self,
        mock_checker_class,
        mock_settings,
        mock_install,
        mock_console,
        mock_thread,
        mock_config_repo,
        mock_message_repo,
    ):
        app = App(app_settings_repo=mock_config_repo, message_repo=mock_message_repo)
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

    @patch("parkbot.gui.app.ConsoleTab")
    @patch("parkbot.gui.app.InstallTab")
    @patch("parkbot.gui.app.SettingsTab")
    @patch("parkbot.gui.app.RPABotCore")
    def test_start_bot(
        self,
        mock_bot_core,
        mock_settings,
        mock_install,
        mock_console,
        mock_config_repo,
        mock_message_repo,
    ):
        app = App(app_settings_repo=mock_config_repo, message_repo=mock_message_repo)
        app.settings_tab = MagicMock()
        app.settings_tab.get_config_data.return_value = {
            "patterns": [],
            "reaction_emoji": "👍",
            "check_interval": 2.0,
            "max_messages_per_check": 3,
        }

        app.console_tab = MagicMock()
        with patch.object(app, "_log_to_ui", MagicMock()):
            app._start_bot()
            assert app.bot is not None
            mock_bot_core.assert_called()

        assert mock_bot_core.called

    @patch("parkbot.gui.app.ConsoleTab")
    @patch("parkbot.gui.app.InstallTab")
    @patch("parkbot.gui.app.SettingsTab")
    def test_on_bot_stopped(
        self,
        mock_settings,
        mock_install,
        mock_console,
        mock_config_repo,
        mock_message_repo,
    ):
        app = App(app_settings_repo=mock_config_repo, message_repo=mock_message_repo)
        app.bot = MagicMock()
        app.bot.start_time = MagicMock()
        app.console_tab = MagicMock()

        app._on_bot_stopped()

    @patch("parkbot.gui.app.SettingsTab")
    @patch("parkbot.gui.app.InstallTab")
    @patch("parkbot.gui.app.ConsoleTab")
    @patch.object(App, "_log_to_ui")
    def test_log_final_stats(
        self,
        mock_log_to_ui,
        mock_console,
        mock_install,
        mock_settings,
        mock_config_repo,
        mock_message_repo,
    ):
        app = App(app_settings_repo=mock_config_repo, message_repo=mock_message_repo)
        app.bot = MagicMock()
        app.bot.match_count = 10
        app.bot.reaction_count = 8
        app.bot.fail_count = 2
        app.bot.start_time = MagicMock()

        app._log_final_stats()

        mock_log_to_ui.assert_called()

    @patch("parkbot.gui.app.SettingsTab")
    @patch("parkbot.gui.app.InstallTab")
    @patch("parkbot.gui.app.ConsoleTab")
    def test_do_reset(
        self,
        mock_settings,
        mock_install,
        mock_console,
        mock_config_repo,
        mock_message_repo,
    ):
        app = App(app_settings_repo=mock_config_repo, message_repo=mock_message_repo)
        # No bot_state to reset anymore, just verify it doesn't crash
        app._log_to_ui = MagicMock()  # ty: ignore[invalid-assignment]

        app._reset_stats()

        # Should log a message
        app._log_to_ui.assert_called_once()  # ty: ignore[unresolved-attribute]

    @patch("parkbot.gui.app.SettingsTab")
    @patch("parkbot.gui.app.InstallTab")
    @patch("parkbot.gui.app.ConsoleTab")
    @patch.object(App, "_log_to_ui")
    def test_reset_stats(
        self,
        mock_log_to_ui,
        mock_console,
        mock_install,
        mock_settings,
        mock_config_repo,
        mock_message_repo,
    ):
        app = App(app_settings_repo=mock_config_repo, message_repo=mock_message_repo)
        app.console_tab = MagicMock()

        app._reset_stats()

        app.console_tab.reset.assert_called_once()
        mock_log_to_ui.assert_called()
