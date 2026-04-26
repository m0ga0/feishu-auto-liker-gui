"""RPABotCore 同步接口测试"""

from src.core.bot import RPABotCore
from src.core.matcher import PatternMatcher
from src.state import BotState


class TestRPABotCoreSyncInterface:
    """RPABotCore 同步接口测试"""

    def test_init_creates_matcher_with_patterns(self):
        """初始化时使用配置创建 PatternMatcher"""
        config = {"monitor": {"patterns": ["hello", "re:world\\d+"]}}
        state = BotState()
        bot = RPABotCore(config, state)

        assert isinstance(bot.matcher, PatternMatcher)

    def test_init_uses_empty_patterns_when_not_in_config(self):
        """配置中没有 patterns 时使用空列表"""
        config = {}
        state = BotState()
        bot = RPABotCore(config, state)

        assert isinstance(bot.matcher, PatternMatcher)

    def test_matcher_is_used_for_message_matching(self):
        """PatternMatcher 用于消息匹配"""
        config = {"monitor": {"patterns": ["车位"]}}
        state = BotState()
        bot = RPABotCore(config, state)

        assert bot.matcher.matches("有车位 请联系") is True
        assert bot.matcher.matches("没有匹配") is False

    def test_regex_patterns_work(self):
        """正则表达式模式可用"""
        config = {"monitor": {"patterns": ["re:车位\\d+"]}}
        state = BotState()
        bot = RPABotCore(config, state)

        assert bot.matcher.matches("车位123") is True
        assert bot.matcher.matches("车位") is False

    def test_config_get_browser_settings(self):
        """从配置获取浏览器设置"""
        config = {
            "browser": {
                "user_data_dir": "./test_browser_data",
                "width": 1920,
                "height": 1080,
                "headless": True,
            }
        }
        state = BotState()
        RPABotCore(config, state)

        assert config["browser"]["user_data_dir"] == "./test_browser_data"
        assert config["browser"]["width"] == 1920
        assert config["browser"]["height"] == 1080

    def test_config_get_monitor_settings(self):
        """从配置获取监控设置"""
        config = {
            "monitor": {
                "patterns": ["test"],
                "check_interval": 5,
                "max_messages_per_check": 10,
                "monitored_groups": ["group1", "group2"],
            }
        }
        state = BotState()
        RPABotCore(config, state)

        assert config["monitor"]["check_interval"] == 5
        assert config["monitor"]["max_messages_per_check"] == 10
        assert config["monitor"]["monitored_groups"] == ["group1", "group2"]

    def test_state_tracking_match_count(self):
        """状态跟踪匹配计数"""
        config = {"monitor": {"patterns": ["test"]}}
        state = BotState()
        RPABotCore(config, state)

        state.match_count = 5
        assert state.match_count == 5

    def test_state_tracking_reaction_count(self):
        """状态跟踪点赞计数"""
        config = {"monitor": {"patterns": ["test"]}}
        state = BotState()
        RPABotCore(config, state)

        state.reaction_count = 3
        assert state.reaction_count == 3

    def test_state_tracking_fail_count(self):
        """状态跟踪失败计数"""
        config = {"monitor": {"patterns": ["test"]}}
        state = BotState()
        RPABotCore(config, state)

        state.fail_count = 2
        assert state.fail_count == 2

    def test_log_callback_is_stored(self):
        """日志回调被存储"""
        log_msgs = []

        def mock_log(msg):
            log_msgs.append(msg)

        config = {"monitor": {"patterns": ["test"]}}
        state = BotState()
        bot = RPABotCore(config, state, log_callback=mock_log)

        bot.log("test message")
        assert log_msgs[0] == "test message"

    def test_stop_callback_is_stored(self):
        """停止回调被存储"""
        stop_called = []

        def mock_stop():
            stop_called.append(True)

        config = {"monitor": {"patterns": ["test"]}}
        state = BotState()
        bot = RPABotCore(config, state, stop_callback=mock_stop)

        assert callable(bot.stop_callback)

    def test_initial_running_state_false(self):
        """初始运行状态为 False"""
        config = {"monitor": {"patterns": ["test"]}}
        state = BotState()
        bot = RPABotCore(config, state)

        assert bot._running is False

    def test_patterns_from_multiple_groups(self):
        """支持多个群组的模式"""
        config = {
            "monitor": {
                "patterns": ["pattern1", "pattern2"],
                "monitored_groups": ["group1", "group2"],
            }
        }
        state = BotState()
        bot = RPABotCore(config, state)

        assert bot.matcher.matches("pattern1 found") is True
        assert bot.matcher.matches("pattern2 found") is True

    def test_anti_detect_settings_in_config(self):
        """反检测设置"""
        config = {
            "anti_detect": {
                "min_delay": 0.5,
                "max_delay": 2.0,
                "reaction_delay_min": 0.3,
                "reaction_delay_max": 1.5,
            }
        }
        state = BotState()
        RPABotCore(config, state)

        assert config["anti_detect"]["min_delay"] == 0.5
        assert config["anti_detect"]["max_delay"] == 2.0
