"""GUI Timer 行为测试 (Mock App)"""

import time

from parkbot.dao_impl.chat.repo_impls import InMemoryFeishuMessageRepository


class MockBot:
    """Mock Bot for testing"""

    def __init__(self):
        self.match_count = 0
        self.reaction_count = 0
        self.fail_count = 0
        self.start_time = None
        self._is_running = False

    @property
    def is_running(self):
        return self._is_running

    def start(self):
        self._is_running = True
        self.start_time = time.time()

    def stop(self):
        self._is_running = False

    def reset_stats(self):
        self.match_count = 0
        self.reaction_count = 0
        self.fail_count = 0
        self.start_time = None

    def get_uptime(self):
        """Calculate uptime string"""
        if not self.start_time:
            return "0秒"
        total = int(time.time() - self.start_time)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}小时{m}分{s}秒"
        elif m > 0:
            return f"{m}分{s}秒"
        return f"{s}秒"


class MockApp:
    """Mock GUI App, 跳过 GUI 实际初始化"""

    def __init__(self):
        self.config_data = {}
        self.message_repo = InMemoryFeishuMessageRepository()
        self.bot = None
        self.log_messages = []
        self._running = True

    def _log_to_ui(self, msg):
        self.log_messages.append(msg)

    def _start_bot(self):
        """模拟 _start_bot()"""
        self.bot = MockBot()
        self.bot.start()
        self._update_stats_loop()

    def _log_final_stats(self):
        if self.bot:
            uptime = self.bot.get_uptime()
            self._log_to_ui(
                f"📊 本次运行统计 - 匹配: {self.bot.match_count} | "
                f"点赞: {self.bot.reaction_count} | "
                f"失败: {self.bot.fail_count} | "
                f"时长: {uptime}"
            )

    def _do_reset(self):
        if self.bot:
            self.bot.reset_stats()

    def _update_ui_stopped(self):
        pass

    def _stop_monitoring(self):
        self._log_final_stats()
        self._do_reset()
        self._update_ui_stopped()

    def _stop_bot(self):
        if self.bot:
            self.bot.stop()
        self._stop_monitoring()

    def _update_stats_loop(self):
        while self.bot and self.bot.is_running:
            _ = self.bot.get_uptime()
            break

    def _on_bot_stopped(self):
        """模拟浏览器关闭时的回调"""
        self._stop_monitoring()

    def _simulate_stop_button_click(self):
        """模拟用户点击 Stop 按钮"""
        if self.bot:
            self.bot.stop()
            self.bot = None
        self._run_loop_on_stop()

    def _run_loop_on_stop(self):
        """模拟 _run_loop 结束时的处理"""
        self._stop_monitoring()
        self._log_to_ui("⏹ 监控已停止")

    def _simulate_browser_close(self):
        """模拟用户手动关闭浏览器"""
        error_msg = "Target page, context or browser has been closed"
        self._log_to_ui(f"⚠️ 浏览器已关闭，停止监控: {error_msg}")
        self._running = False
        self._on_bot_stopped()
        self._log_to_ui("⏹ 监控已停止")


class TestGUITimer:
    """GUI Timer 行为测试"""

    def test_start_button_starts_timer(self):
        """点击 Start 后 timer 开始"""
        app = MockApp()

        app._start_bot()

        assert app.bot.is_running is True  # ty: ignore[unresolved-attribute]
        assert app.bot.start_time is not None  # ty: ignore[unresolved-attribute]

    def test_stop_button_resets_timer(self):
        """点击 Stop 后 timer 重置为 0"""
        app = MockApp()

        app._start_bot()
        time.sleep(1)

        app._stop_bot()

        assert app.bot.get_uptime() == "0秒"  # ty: ignore[unresolved-attribute]
        assert app.bot.is_running is False  # ty: ignore[unresolved-attribute]

    def test_multiple_start_stop_cycle(self):
        """多次 start/stop 循环"""
        app = MockApp()

        # 第一次 start
        app._start_bot()
        time.sleep(1)
        t1 = app.bot.get_uptime()  # ty: ignore[unresolved-attribute]

        # stop
        app._stop_bot()
        assert app.bot.get_uptime() == "0秒"  # ty: ignore[unresolved-attribute]

        # 第二次 start
        app._start_bot()
        time.sleep(1)
        t2 = app.bot.get_uptime()  # ty: ignore[unresolved-attribute]

        # stop 后也应该为 0
        app._stop_bot()
        assert app.bot.get_uptime() == "0秒"  # ty: ignore[unresolved-attribute]

        # 两次运行都应该是非 0
        assert t1 != "0秒"
        assert t2 != "0秒"

    def test_timer_counts_up_correctly(self):
        """timer 正确累加计数"""
        app = MockApp()

        app._start_bot()
        time.sleep(2)

        uptime = app.bot.get_uptime()  # ty: ignore[unresolved-attribute]
        # 提取秒数 (可能是 "2秒" 或 "0分2秒")
        seconds = int(uptime.replace("秒", "").replace("分", " ").split()[-1])
        assert seconds >= 2

    def test_timer_while_running(self):
        """运行中 timer 持续累加"""
        app = MockApp()

        app._start_bot()
        time.sleep(1)
        t1 = app.bot.get_uptime()  # ty: ignore[unresolved-attribute]

        time.sleep(1)
        t2 = app.bot.get_uptime()  # ty: ignore[unresolved-attribute]

        # t2 应该大于 t1
        s1 = int(t1.replace("秒", "").replace("分", " ").split()[-1])
        s2 = int(t2.replace("秒", "").replace("分", " ").split()[-1])
        assert s2 > s1

    def test_log_final_stats_format(self):
        """停止时日志格式正确"""
        app = MockApp()

        app._start_bot()
        app.bot.match_count = 5  # ty: ignore[invalid-assignment]
        app.bot.reaction_count = 4  # ty: ignore[invalid-assignment]
        app.bot.fail_count = 1  # ty: ignore[invalid-assignment]
        time.sleep(1)

        app._stop_bot()

        # 检查日志中包含统计信息
        logs_str = " ".join(app.log_messages)
        assert "匹配: 5" in logs_str
        assert "点赞: 4" in logs_str
        assert "失败: 1" in logs_str

    def test_browser_close_callback(self):
        """浏览器关闭时回调正确执行"""
        app = MockApp()

        app._start_bot()
        app._simulate_browser_close()

        logs_str = " ".join(app.log_messages)
        assert "浏览器已关闭" in logs_str
        assert "监控已停止" in logs_str

    def test_stop_button_click_sequence(self):
        """点击 Stop 按钮的完整流程"""
        app = MockApp()

        app._start_bot()
        time.sleep(1)

        app._simulate_stop_button_click()

        # 应该有停止日志
        assert any("监控已停止" in msg for msg in app.log_messages)
        assert app.bot is None or not app.bot.is_running
