"""BotState 核心逻辑测试"""

import time

import pytest

from src.state import BotState


class TestBotStateGroupState:
    """BotState 群组状态方法测试"""

    @pytest.fixture(autouse=True)
    def mock_state_file(self, tmp_path, monkeypatch):
        """Mock STATE_PATH and disable file loading."""
        from src.state import tracker

        mock_path = tmp_path / "nonexistent_state.json"
        monkeypatch.setattr(tracker, "STATE_PATH", mock_path)

    def test_get_group_state_creates_new(self):
        """新群组获取默认状态"""
        state = BotState()
        gs = state.get_group_state("test_group")
        assert "seen_ids" in gs
        assert "reacted_ids" in gs
        assert "last_checked_ids" in gs
        assert "last_check_time" in gs

    def test_get_group_state_returns_existing(self):
        """已存在群组返回缓存状态"""
        state = BotState()
        gs1 = state.get_group_state("test_group")
        gs1["seen_ids"].add("msg_123")

        gs2 = state.get_group_state("test_group")
        assert "msg_123" in gs2["seen_ids"]

    def test_mark_seen_adds_to_seen_ids(self):
        """mark_seen 添加到 seen_ids"""
        state = BotState()
        state.mark_seen("group1", "msg_001")
        assert state.is_seen("group1", "msg_001") is True

    def test_is_seen_returns_true_when_seen(self):
        """已见消息返回 True"""
        state = BotState()
        state.mark_seen("group1", "msg_001")
        assert state.is_seen("group1", "msg_001") is True

    def test_is_seen_returns_false_when_not_seen(self):
        """未见消息返回 False"""
        state = BotState()
        assert state.is_seen("group1", "msg_001") is False

    def test_mark_reacted_adds_to_reacted_ids(self):
        """mark_reacted 添加到 reacted_ids"""
        state = BotState()
        state.mark_reacted("group1", "msg_001")
        assert state.is_reacted("group1", "msg_001") is True

    def test_is_reacted_returns_true_when_reacted(self):
        """已点赞消息返回 True"""
        state = BotState()
        state.mark_reacted("group1", "msg_001")
        assert state.is_reacted("group1", "msg_001") is True

    def test_is_reacted_returns_false_when_not(self):
        """未点赞消息返回 False"""
        state = BotState()
        assert state.is_reacted("group1", "msg_001") is False

    def test_update_last_checked_ids_stores_ids(self):
        """update_last_checked_ids 存储 IDs"""
        state = BotState()
        state.update_last_checked_ids("group1", ["msg_001", "msg_002"])
        gs = state.get_group_state("group1")
        assert gs["last_checked_ids"] == ["msg_001", "msg_002"]

    def test_get_last_checked_ids_returns_empty_for_new_group(self):
        """新群组返回空列表"""
        state = BotState()
        ids = state.get_last_checked_ids("new_group")
        assert ids == []

    def test_get_last_checked_ids_returns_stored_ids(self):
        """返回之前存储的 IDs"""
        state = BotState()
        state.update_last_checked_ids("group1", ["msg_001", "msg_002"])
        ids = state.get_last_checked_ids("group1")
        assert ids == ["msg_001", "msg_002"]

    def test_log_appends_to_recent_logs(self):
        """log 添加到日志"""
        state = BotState()
        state.log("test message")
        assert "test message" in state.recent_logs[0]

    def test_log_only_keeps_100(self):
        """仅保留最后100条日志"""
        state = BotState()
        for i in range(150):
            state.log(f"msg_{i}")
        assert len(state.recent_logs) == 100
        assert "msg_149" in state.recent_logs[-1]
        assert "msg_50" not in state.recent_logs[-1]


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
