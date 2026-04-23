"""BotState 核心逻辑测试"""

import time

from src.state import BotState


class TestBotState:
    """BotState 核心计时逻辑测试"""

    def test_initial_state(self):
        """初始状态: start_time=None, is_running=False"""
        state = BotState()
        assert state.uptime == "0秒"
        assert state.is_running is False
        assert state.start_time is None

    def test_start_sets_start_time(self):
        """启动后 start_time 被设置"""
        state = BotState()
        state.is_running = True
        state.start_time = time.time()

        time.sleep(1)
        elapsed = state.uptime
        assert elapsed != "0秒"

    def test_reset_clears_start_time(self):
        """reset() 清除 start_time"""
        state = BotState()
        state.is_running = True
        state.start_time = time.time()

        state.reset()
        assert state.uptime == "0秒"
        assert state.start_time is None
        assert state.is_running is False

    def test_uptime_format_seconds(self):
        """uptime 格式: 秒"""
        state = BotState()
        state.is_running = True
        state.start_time = time.time()

        time.sleep(2)
        uptime = state.uptime
        assert "秒" in uptime

    def test_uptime_format_minutes(self):
        """uptime 格式: 分秒"""
        state = BotState()
        state.is_running = True
        state.start_time = time.time() - 65  # 65 秒前

        uptime = state.uptime
        assert "分" in uptime
        assert "秒" in uptime

    def test_uptime_format_hours(self):
        """uptime 格式: 小时分秒"""
        state = BotState()
        state.is_running = True
        state.start_time = time.time() - 3665  # 1小时1分5秒前

        uptime = state.uptime
        assert "小时" in uptime

    def test_uptime_none_when_not_started(self):
        """未启动时 uptime 返回 0秒"""
        state = BotState()
        assert state.uptime == "0秒"

    def test_counters_initial_zero(self):
        """计数器初始为 0"""
        state = BotState()
        assert state.match_count == 0
        assert state.reaction_count == 0
        assert state.fail_count == 0

    def test_reset_clears_counters(self):
        """reset() 清除计数器"""
        state = BotState()
        state.match_count = 5
        state.reaction_count = 3
        state.fail_count = 2

        state.reset()

        assert state.match_count == 0
        assert state.reaction_count == 0
        assert state.fail_count == 0
