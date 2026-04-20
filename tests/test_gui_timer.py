"""GUI Timer 行为测试 (Mock App)"""
import pytest
import time
import sys

sys.path.insert(0, ".")

from main import _BotState


class MockApp:
    """Mock GUI App, 跳过 GUI 实际初始化"""

    def __init__(self):
        self.config_data = {}
        self.bot_state = _BotState()
        self.bot = None

    def _start_bot(self):
        """模拟 _start_bot()"""
        self.bot_state.reset()
        self.bot_state.is_running = True
        self.bot_state.start_time = time.time()  # 模拟 bot 线程设置
        self._update_stats_loop()

    def _stop_bot(self):
        """模拟 _stop_bot()"""
        if self.bot:
            self.bot.stop()
        self.bot_state.reset()  # reset 会清除 is_running

    def _update_stats_loop(self):
        """模拟 GUI 循环, 验证 is_running"""
        while self.bot_state.is_running:
            _ = self.bot_state.uptime
            break


class TestGUITimer:
    """GUI Timer 行为测试"""

    def test_start_button_starts_timer(self):
        """点击 Start 后 timer 开始"""
        app = MockApp()

        app._start_bot()

        assert app.bot_state.is_running is True
        assert app.bot_state.start_time is not None

    def test_stop_button_resets_timer(self):
        """点击 Stop 后 timer 重置为 0"""
        app = MockApp()

        app._start_bot()
        time.sleep(1)

        app._stop_bot()

        assert app.bot_state.uptime == "0秒"
        assert app.bot_state.is_running is False

    def test_multiple_start_stop_cycle(self):
        """多次 start/stop 循环"""
        app = MockApp()

        # 第一次 start
        app._start_bot()
        time.sleep(1)
        t1 = app.bot_state.uptime

        # stop
        app._stop_bot()
        assert app.bot_state.uptime == "0秒"

        # 第二次 start
        app._start_bot()
        time.sleep(1)
        t2 = app.bot_state.uptime

        # stop 后也应该为 0
        app._stop_bot()
        assert app.bot_state.uptime == "0秒"

        # 两次运行都应该是非 0
        assert t1 != "0秒"
        assert t2 != "0秒"

    def test_timer_counts_up_correctly(self):
        """timer 正确累加计数"""
        app = MockApp()

        app._start_bot()
        time.sleep(2)

        uptime = app.bot_state.uptime
        # 提取秒数 (可能是 "2秒" 或 "0分2秒")
        seconds = int(uptime.replace("秒", "").replace("分", " ").split()[-1])
        assert seconds >= 2

    def test_timer_while_running(self):
        """运行中 timer 持续累加"""
        app = MockApp()

        app._start_bot()
        time.sleep(1)
        t1 = app.bot_state.uptime

        time.sleep(1)
        t2 = app.bot_state.uptime

        time.sleep(1)
        t3 = app.bot_state.uptime

        # 每次都应该增加
        s1 = int(t1.replace("秒", "").split()[-1])
        s2 = int(t2.replace("秒", "").split()[-1])
        s3 = int(t3.replace("秒", "").split()[-1])

        assert s2 >= s1
        assert s3 >= s2

    def test_stop_during_run(self):
        """运行中点击 stop 立即停止"""
        app = MockApp()

        app._start_bot()
        time.sleep(2)

        first_uptime = app.bot_state.uptime

        app._stop_bot()
        stopped_uptime = app.bot_state.uptime

        # stop 后应该重置为 0
        assert stopped_uptime == "0秒"

        # 再等 2 秒，不应该变化
        time.sleep(2)
        after_wait = app.bot_state.uptime

        # 依然是 0，因为 stop 了
        assert after_wait == "0秒"