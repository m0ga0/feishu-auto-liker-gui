"""GUI ConsoleTab 逻辑测试"""

from unittest.mock import MagicMock
from src.gui.tabs.console_tab import ConsoleTab
import pytest


@pytest.fixture
def console_tab():
    tab = MagicMock()
    return ConsoleTab(tab, MagicMock(), MagicMock(), MagicMock())


def test_init(console_tab):
    assert hasattr(console_tab, "status_indicator")
    assert hasattr(console_tab, "start_btn")
    assert hasattr(console_tab, "stop_btn")
    assert hasattr(console_tab, "console_log")


def test_log_message(console_tab):
    console_tab.console_log = MagicMock()
    console_tab.log_message("test")
    console_tab.console_log.insert.assert_called_with("end", "test\n")


def test_update_stats(console_tab):
    console_tab.stat_labels = {
        k: MagicMock()
        for k in ["match_count", "reaction_count", "fail_count", "uptime"]
    }
    console_tab.update_stats(1, 2, 3, "4s")
    console_tab.stat_labels["match_count"].configure.assert_called_with(text="1")


def test_bot_started(console_tab):
    console_tab.start_btn = MagicMock()
    console_tab.stop_btn = MagicMock()
    console_tab.status_indicator = MagicMock()
    console_tab.on_bot_started()
    console_tab.start_btn.configure.assert_called_with(state="disabled")


def test_bot_stopped(console_tab):
    console_tab.start_btn = MagicMock()
    console_tab.stop_btn = MagicMock()
    console_tab.status_indicator = MagicMock()
    console_tab.on_bot_stopped()
    console_tab.start_btn.configure.assert_called_with(state="normal")
