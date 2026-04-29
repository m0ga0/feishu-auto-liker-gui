"""GUI InstallTab 逻辑测试"""

from unittest.mock import MagicMock, patch
from src.gui.tabs.install_tab import InstallTab


class TestInstallTab:
    """InstallTab 界面逻辑测试"""

    def test_init_creates_widgets(self):
        """测试控件创建"""
        tab = MagicMock()
        on_check_env = MagicMock()
        on_open_folder = MagicMock()
        app_settings = {}

        # Mock threading so _start_env_check doesn't actually start a thread
        with patch("threading.Thread"):
            install = InstallTab(tab, on_check_env, on_open_folder, app_settings)

        assert hasattr(install, "install_frame")
        assert hasattr(install, "install_items")
        assert hasattr(install, "install_btn")
        assert hasattr(install, "install_log")

    def test_update_status(self):
        """测试状态更新"""
        tab = MagicMock()
        on_check_env = MagicMock()
        on_open_folder = MagicMock()
        app_settings = {}

        with patch("threading.Thread"):
            install = InstallTab(tab, on_check_env, on_open_folder, app_settings)

        # Mock the label objects
        install.install_items = {}
        for key in ["python", "pip", "playwright_pkg", "playwright_browser"]:
            label = MagicMock()
            install.install_items[key] = label

        # Test update_status
        install.update_status("python", "✅ 已安装")

        install.install_items["python"].configure.assert_called_with(text="✅ 已安装")

    def test_update_status_unknown_key(self):
        """测试未知 key 不报错"""
        tab = MagicMock()
        on_check_env = MagicMock()
        on_open_folder = MagicMock()
        app_settings = {}

        with patch("threading.Thread"):
            install = InstallTab(tab, on_check_env, on_open_folder, app_settings)

        # Should not raise for unknown key
        install.update_status("unknown_key", "some status")

    def test_log_message(self):
        """测试日志消息"""
        tab = MagicMock()
        on_check_env = MagicMock()
        on_open_folder = MagicMock()
        app_settings = {}

        with patch("threading.Thread"):
            install = InstallTab(tab, on_check_env, on_open_folder, app_settings)

        install.install_log = MagicMock()

        install.log_message("测试日志")

        install.install_log.insert.assert_called_with("end", "测试日志\n")
        install.install_log.see.assert_called_with("end")

    def test_set_install_callback(self):
        """测试安装回调设置"""
        tab = MagicMock()
        on_check_env = MagicMock()
        on_open_folder = MagicMock()
        app_settings = {}

        with patch("threading.Thread"):
            install = InstallTab(tab, on_check_env, on_open_folder, app_settings)

        callback = MagicMock()
        install.set_install_callback(callback)

        assert hasattr(install, "_install_callback")
        assert install._install_callback == callback

    def test_on_install_clicked_with_callback(self):
        """测试点击安装按钮调用回调"""
        tab = MagicMock()
        on_check_env = MagicMock()
        on_open_folder = MagicMock()
        app_settings = {}

        with patch("threading.Thread"):
            install = InstallTab(tab, on_check_env, on_open_folder, app_settings)

        callback = MagicMock()
        install._install_callback = callback

        install._on_install_clicked()

        callback.assert_called_once()

    def test_on_install_clicked_without_callback(self):
        """测试无回调时不报错"""
        tab = MagicMock()
        on_check_env = MagicMock()
        on_open_folder = MagicMock()
        app_settings = {}

        with patch("threading.Thread"):
            install = InstallTab(tab, on_check_env, on_open_folder, app_settings)

        # No callback set, should not raise
        install._on_install_clicked()

    def test_set_button_state_enable(self):
        """测试启用按钮"""
        tab = MagicMock()
        on_check_env = MagicMock()
        on_open_folder = MagicMock()
        app_settings = {}

        with patch("threading.Thread"):
            install = InstallTab(tab, on_check_env, on_open_folder, app_settings)

        install.install_btn = MagicMock()

        install.set_button_state(True)

        install.install_btn.configure.assert_called_with(state="normal")

    def test_set_button_state_disable(self):
        """测试禁用按钮"""
        tab = MagicMock()
        on_check_env = MagicMock()
        on_open_folder = MagicMock()
        app_settings = {}

        with patch("threading.Thread"):
            install = InstallTab(tab, on_check_env, on_open_folder, app_settings)

        install.install_btn = MagicMock()

        install.set_button_state(False)

        install.install_btn.configure.assert_called_with(state="disabled")

    def test_set_button_state_with_custom_text(self):
        """测试设置按钮文字"""
        tab = MagicMock()
        on_check_env = MagicMock()
        on_open_folder = MagicMock()
        app_settings = {}

        with patch("threading.Thread"):
            install = InstallTab(tab, on_check_env, on_open_folder, app_settings)

        install.install_btn = MagicMock()

        install.set_button_state(True, "自定义文字")

        # Should be called twice: state and text
        calls = install.install_btn.configure.call_args_list
        assert any(call[1].get("state") == "normal" for call in calls)
        assert any(call[1].get("text") == "自定义文字" for call in calls)
