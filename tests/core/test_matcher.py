"""Tests for PatternMatcher - tests behavior not internal implementation."""

from parkbot.core.matcher import PatternMatcher


class TestPatternMatcher:
    """Test PatternMatcher behavior through public interface."""

    def test_empty_patterns_returns_never_matches(self):
        """When no patterns, matches() should always return False."""
        matcher = PatternMatcher([])
        assert matcher.matches("any text") is False

    def test_literal_string_match(self):
        """Literal pattern should match via substring (case-insensitive)."""
        matcher = PatternMatcher(["hello"])
        assert matcher.matches("hello world") is True
        assert matcher.matches("say hello there") is True
        # Patterns are now case-insensitive regex
        assert matcher.matches("HELLO world") is True

    def test_literal_string_no_match(self):
        """Literal pattern should not match when not present."""
        matcher = PatternMatcher(["hello"])
        assert matcher.matches("world") is False
        assert matcher.matches("hell") is False
        assert matcher.matches("") is False

    def test_multiple_patterns(self):
        """Multiple patterns should match if any matches."""
        matcher = PatternMatcher(["foo", "bar", "baz"])
        assert matcher.matches("foo") is True
        assert matcher.matches("bar") is True
        assert matcher.matches("baz") is True
        assert matcher.matches("bar foo") is True  # both present
        assert matcher.matches("nothing") is False

    def test_regex_pattern_match(self):
        """Regex pattern should match (no re: prefix needed)."""
        matcher = PatternMatcher([r"hello\d+"])
        assert matcher.matches("hello123") is True
        assert matcher.matches("hello") is False  # needs digits

    def test_regex_case_insensitive(self):
        """Regex should be case insensitive."""
        matcher = PatternMatcher(["hello"])
        assert matcher.matches("HELLO") is True
        assert matcher.matches("Hello") is True
        assert matcher.matches("hello") is True

    def test_regex_complex_pattern(self):
        """Complex regex patterns should work."""
        # Pattern requires BOTH (出 OR 整出) AND (车位 OR 停车位 OR 首赞)
        matcher = PatternMatcher([".*(出|整出).*(车位|停车位|首赞).*"])
        assert matcher.matches("有出车位啦") is True  # 出 + 车位
        assert matcher.matches("整出停车位") is True  # 整出 + 停车位
        assert matcher.matches("出首赞") is True  # 出 + 首赞
        # "首赞来袭" has no 出/整出, so doesn't match
        assert matcher.matches("首赞来袭") is False
        assert matcher.matches("没有车位") is False  # no 出/整出

    def test_invalid_regex_skipped_with_warning(self):
        """Invalid regex should be skipped but not raise."""
        # Single invalid pattern - should log error but not raise
        matcher = PatternMatcher(["[invalid"])
        assert matcher.matches("anything") is False

    def test_mixed_valid_and_invalid_patterns(self):
        """Mix of valid and invalid patterns - valid ones work."""
        matcher = PatternMatcher(["[invalid", "hello", "[also invalid"])
        # Should match the valid pattern
        assert matcher.matches("say hello") is True
        assert matcher.matches("nothing") is False

    def test_chinese_pattern(self):
        """Chinese characters as pattern."""
        matcher = PatternMatcher(["车位"])
        assert matcher.matches("有车位") is True
        assert matcher.matches("找车位") is True
        assert matcher.matches("车位") is True
