"""Tests for message ID validation functions."""

from parkbot.core.bot import RPABotCore


class TestIsTemporaryMessageId:
    """Tests for is_temporary_message_id static method."""

    def test_temporary_id_10_chars_with_letters(self):
        """Temporary IDs are 10 chars with letters."""
        assert RPABotCore.is_temporary_message_id("TrCbtDNOPi") is True
        assert RPABotCore.is_temporary_message_id("mlD0HVHwxI") is True
        assert RPABotCore.is_temporary_message_id("3y6IegQHQH") is True

    def test_real_id_19_digits(self):
        """Real message IDs are 19 digits."""
        assert RPABotCore.is_temporary_message_id("7643842788513042144") is False
        assert RPABotCore.is_temporary_message_id("7643842845769469666") is False
        assert RPABotCore.is_temporary_message_id("7643843154713546464") is False

    def test_empty_string(self):
        """Empty string should be treated as temporary (invalid)."""
        assert RPABotCore.is_temporary_message_id("") is True

    def test_none_value(self):
        """None should be handled gracefully."""
        assert RPABotCore.is_temporary_message_id(None) is True  # ty: ignore[invalid-argument-type]

    def test_mixed_alphanumeric_19_chars(self):
        """19-char mixed alphanumeric is not temporary (unusual but possible)."""
        assert RPABotCore.is_temporary_message_id("7643842788513042144A") is False

    def test_10_digit_only(self):
        """10 digits only might be a shortened ID, not temporary format."""
        # 10 digits without letters is ambiguous - could be timestamp
        # We only flag as temporary if it has letters (which real IDs never do)
        assert RPABotCore.is_temporary_message_id("1234567890") is False

    def test_various_lengths(self):
        """Various length strings."""
        # Too short
        assert RPABotCore.is_temporary_message_id("abc") is False
        # Too long with letters
        assert RPABotCore.is_temporary_message_id("abcdefghijklmnopqrs") is False
        # Exactly 10 digits only
        assert RPABotCore.is_temporary_message_id("0123456789") is False
