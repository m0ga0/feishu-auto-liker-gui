from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional


def _default_runner(cmd: str, timeout: int = 10) -> tuple[bool, str]:
    if getattr(sys, "frozen", False):
        return True, "Frozen"
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


class EnvChecker:
    """Check and install required dependencies."""

    def __init__(
        self,
        log_callback: Optional[Callable] = None,
        runner: Optional[Callable[[str, int], tuple[bool, str]]] = None,
    ):
        self.log = log_callback or (lambda msg: None)
        self._runner = runner or _default_runner
        self._results = {}

    def _run(self, cmd: str, timeout: int = 10) -> tuple[bool, str]:
        return self._runner(cmd, timeout)

    def check_all(self) -> dict:
        """Check all dependencies."""
        browser_status = self._check_playwright_browser()

        if getattr(sys, "frozen", False):
            self.log("检测到已打包环境...")
            self._results = {
                "python": {
                    "installed": True,
                    "version": "Frozen",
                    "path": sys.executable,
                },
                "pip": {"installed": True, "version": "Frozen"},
                "playwright_pkg": {"installed": True, "version": "Frozen"},
                "playwright_browser": browser_status,
            }
        else:
            self.log("检查环境依赖...")
            self._results = {
                "python": self._check_python(),
                "pip": self._check_pip(),
                "playwright_pkg": self._check_playwright_pkg(),
                "playwright_browser": browser_status,
            }
        return self._results

    def _check_python(self) -> dict:
        ok, version = self._run(f'"{sys.executable}" --version')
        if ok:
            return {"installed": True, "version": version, "path": sys.executable}
        return {"installed": False, "version": "", "path": ""}

    def _check_pip(self) -> dict:
        ok, version = self._run(f'"{sys.executable}" -m pip --version')
        return {"installed": ok, "version": version.split()[1] if ok else ""}

    def _check_playwright_pkg(self) -> dict:
        ok, _ = self._run(f'"{sys.executable}" -c "import playwright"')
        if ok:
            ok2, ver = self._run(
                f'"{sys.executable}" -c "import playwright; print(playwright.__version__)"'
            )
            return {"installed": True, "version": ver if ok2 else "unknown"}
        return {"installed": False, "version": ""}

    def _check_playwright_browser(self) -> dict:
        self._run(f'"{sys.executable}" -m playwright install --dry-run chromium 2>&1')
        pw_base = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""))
        if not pw_base.exists():
            if platform.system() == "Windows":
                pw_base = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright"
            elif platform.system() == "Darwin":
                pw_base = Path.home() / "Library" / "Caches" / "ms-playwright"
            else:
                pw_base = Path.home() / ".cache" / "ms-playwright"

        ok_import, _ = self._run(
            f'"{sys.executable}" -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); p.chromium.launch(); p.stop()"'
        )
        return {"installed": ok_import, "version": "chromium" if ok_import else ""}

    def install_all(self, progress_callback: Optional[Callable] = None) -> bool:
        """Install all missing dependencies."""
        steps = [
            ("pip", self._install_pip),
            ("playwright_pkg", self._install_playwright_pkg),
            ("playwright_browser", self._install_playwright_browser),
        ]

        for name, install_func in steps:
            status = self._results.get(name, {})
            if status.get("installed"):
                self.log(f"✅ {name} 已安装")
                continue

            self.log(f"⏳ 正在安装 {name}...")
            if progress_callback:
                progress_callback(name)
            success = install_func()
            if not success:
                self.log(f"❌ {name} 安装失败")
                return False
            self.log(f"✅ {name} 安装成功")

        self.log("🎉 所有依赖安装完成！")
        return True

    def _install_pip(self) -> bool:
        ok, _ = self._run(f'"{sys.executable}" -m ensurepip --upgrade')
        return ok

    def _install_playwright_pkg(self) -> bool:
        ok, _ = self._run(
            f'"{sys.executable}" -m pip install playwright --quiet',
            timeout=120,
        )
        return ok

    def _install_playwright_browser(self) -> bool:
        ok, _ = self._run(
            f'"{sys.executable}" -m playwright install chromium --with-deps',
            timeout=300,
        )
        return ok
