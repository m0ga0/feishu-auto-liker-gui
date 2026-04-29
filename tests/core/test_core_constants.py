"""Tests for core constants - tests behavior not internal implementation."""

from src.core.constants import FEISHU_CHAT_URL, SELECTORS


class TestCoreConstants:
    """Test core constants are valid."""

    def test_feishu_chat_url_is_valid_url(self):
        """FEISHU_CHAT_URL should be valid URL."""
        assert FEISHU_CHAT_URL.startswith("https://")
        assert "feishu.cn" in FEISHU_CHAT_URL
        assert "messenger" in FEISHU_CHAT_URL

    def test_selectors_has_required_keys(self):
        """SELECTORS should have all required keys."""
        required = [
            "message_wrapper",
            "message_text",
            "reaction_button",
            "chat_item",
            "message_input",
            "search_input",
        ]
        for key in required:
            assert key in SELECTORS, f"Missing selector: {key}"

    def test_selectors_are_non_empty(self):
        """Each selector should be non-empty string."""
        for key, selector in SELECTORS.items():
            assert isinstance(selector, str)
            assert len(selector) > 0, f"Empty selector: {key}"

    def test_message_wrapper_selector(self):
        """message_wrapper should contain expected patterns."""
        selector = SELECTORS["message_wrapper"]
        assert "message-section" in selector

    def test_reaction_button_selector(self):
        """reaction_button should contain praise/like patterns."""
        selector = SELECTORS["reaction_button"]
        assert "praise" in selector.lower() or "like" in selector.lower()
