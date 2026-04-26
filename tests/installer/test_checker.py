"""EnvChecker 核心逻辑测试"""

from src.installer.checker import EnvChecker


class TestEnvChecker:
    """EnvChecker 核心测试 - 通过注入 mock runner 测试"""

    def test_check_python_success(self):
        """Python 检查成功"""

        def mock_runner(cmd, timeout=10):
            if "--version" in cmd:
                return True, "Python 3.12.0"
            return False, ""

        checker = EnvChecker(runner=mock_runner)
        result = checker._check_python()

        assert result["installed"] is True
        assert "3.12.0" in result["version"]

    def test_check_python_failure(self):
        """Python 检查失败"""

        def mock_runner(cmd, timeout=10):
            return False, "command not found"

        checker = EnvChecker(runner=mock_runner)
        result = checker._check_python()

        assert result["installed"] is False
        assert result["version"] == ""

    def test_check_pip_success(self):
        """pip 检查成功"""

        def mock_runner(cmd, timeout=10):
            if "pip" in cmd and "--version" in cmd:
                return True, "pip 24.0 from /path"
            return False, ""

        checker = EnvChecker(runner=mock_runner)
        result = checker._check_pip()

        assert result["installed"] is True
        assert result["version"] == "24.0"

    def test_check_pip_version_extraction(self):
        """pip 版本号提取"""

        def mock_runner(cmd, timeout=10):
            return True, "pip 24.0 from /usr/lib/python3.12"

        checker = EnvChecker(runner=mock_runner)
        result = checker._check_pip()

        assert result["version"] == "24.0"

    def test_check_playwright_pkg_success(self):
        """playwright 包检查成功"""
        captured_cmds = []

        def mock_runner(cmd, timeout=10):
            captured_cmds.append(cmd)
            if "import playwright" in cmd and "print" not in cmd:
                return True, ""
            if "print" in cmd:
                return True, "1.40.0"
            return False, ""

        checker = EnvChecker(runner=mock_runner)
        result = checker._check_playwright_pkg()

        assert result["installed"] is True
        assert result["version"] == "1.40.0"

    def test_check_playwright_pkg_failure(self):
        """playwright 包未安装"""

        def mock_runner(cmd, timeout=10):
            return False, "ModuleNotFoundError"

        checker = EnvChecker(runner=mock_runner)
        result = checker._check_playwright_pkg()

        assert result["installed"] is False
        assert result["version"] == ""

    def test_check_playwright_browser_success(self):
        """playwright 浏览器已安装"""

        def mock_runner(cmd, timeout=10):
            return True, "chromium installed"

        checker = EnvChecker(runner=mock_runner)
        result = checker._check_playwright_browser()

        assert result["installed"] is True
        assert result["version"] == "chromium"

    def test_check_playwright_browser_failure(self):
        """playwright 浏览器未安装"""

        def mock_runner(cmd, timeout=10):
            return False, "not found"

        checker = EnvChecker(runner=mock_runner)
        result = checker._check_playwright_browser()

        assert result["installed"] is False
        assert result["version"] == ""

    def test_check_all_returns_all_results(self):
        """check_all 返回完整结果"""

        def mock_runner(cmd, timeout=10):
            if "--version" in cmd:
                return True, "pip 24.0"
            if "import playwright" in cmd:
                return True, "ok"
            return True, "ok"

        checker = EnvChecker(runner=mock_runner)
        results = checker.check_all()

        assert "python" in results
        assert "pip" in results
        assert "playwright_pkg" in results
        assert "playwright_browser" in results

    def test_install_all_skips_installed(self):
        """install_all 跳过已安装的"""
        log_msgs = []

        def mock_runner(cmd, timeout=10):
            return True, "ok"

        def log(msg):
            log_msgs.append(msg)

        checker = EnvChecker(log_callback=log, runner=mock_runner)
        checker._results = {
            "pip": {"installed": True},
            "playwright_pkg": {"installed": True},
            "playwright_browser": {"installed": True},
        }

        result = checker.install_all()

        assert result is True
        assert "已安装" in log_msgs[0]

    def test_install_all_calls_each_step(self):
        """install_all 依次调用安装步骤"""
        call_order = []

        def mock_runner(cmd, timeout=10):
            call_order.append(cmd)
            return True, "ok"

        checker = EnvChecker(runner=mock_runner)
        checker._results = {
            "pip": {"installed": False},
            "playwright_pkg": {"installed": False},
            "playwright_browser": {"installed": False},
        }

        result = checker.install_all()

        assert result is True
        assert len(call_order) > 0

    def test_install_all_stops_on_failure(self):
        """install_all 失败时停止"""

        def mock_runner(cmd, timeout=10):
            if "pip" in cmd:
                return False, "error"
            return True, "ok"

        log_msgs = []

        def log(msg):
            log_msgs.append(msg)

        checker = EnvChecker(log_callback=log, runner=mock_runner)
        checker._results = {
            "pip": {"installed": False},
            "playwright_pkg": {"installed": False},
            "playwright_browser": {"installed": False},
        }

        result = checker.install_all()

        assert result is False
        assert any("安装失败" in msg for msg in log_msgs)

    def test_install_pip(self):
        """_install_pip 执行安装"""
        called = []

        def mock_runner(cmd, timeout=10):
            called.append(cmd)
            return True, "ok"

        checker = EnvChecker(runner=mock_runner)
        result = checker._install_pip()

        assert result is True
        assert any("ensurepip" in cmd for cmd in called)

    def test_install_playwright_pkg(self):
        """_install_playwright_pkg 执行安装"""
        called = []

        def mock_runner(cmd, timeout=10):
            called.append(cmd)
            return True, "ok"

        checker = EnvChecker(runner=mock_runner)
        result = checker._install_playwright_pkg()

        assert result is True
        assert any("playwright" in cmd for cmd in called)

    def test_install_playwright_browser(self):
        """_install_playwright_browser 执行安装"""
        called = []

        def mock_runner(cmd, timeout=10):
            called.append(cmd)
            return True, "ok"

        checker = EnvChecker(runner=mock_runner)
        result = checker._install_playwright_browser()

        assert result is True
        assert any("chromium" in cmd for cmd in called)

    def test_default_runner_handles_exception(self):
        """默认 runner 处理异常"""
        from src.installer.checker import _default_runner

        result = _default_runner("nonexistent_command_xyz_123", timeout=1)
        assert result[0] is False
        assert isinstance(result[1], str)
