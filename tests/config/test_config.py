from parkbot.infra import get_settings_repository


class TestConfigModule:
    """Test config module behavior."""

    def test_get_config_repository(self):
        repo = get_settings_repository()
        assert repo is not None
        assert repo.monitor is not None
        assert repo.internal is not None

    def test_monitor_settings_roundtrip(self):
        repo = get_settings_repository()
        monitor = repo.monitor.get()
        assert monitor is not None
        original_patterns = monitor.patterns

        monitor.patterns = ["test_pattern"]
        repo.monitor.save(monitor)

        new_monitor = repo.monitor.get()
        assert new_monitor is not None
        assert new_monitor.patterns == ["test_pattern"]

        # Cleanup
        monitor.patterns = original_patterns
        repo.monitor.save(monitor)
