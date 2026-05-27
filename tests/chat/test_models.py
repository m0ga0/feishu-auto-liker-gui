"""Tests for FeishuMessage domain model"""

from datetime import datetime
from parkbot.chat.models import FeishuMessage
from parkbot.utils.datetime_utils import utcnow


class TestFeishuMessage:
    """Test FeishuMessage domain model"""

    def test_create_message_with_required_fields(self):
        """Test creating message with only required fields"""
        msg = FeishuMessage(id="msg123", text="Hello World")

        assert msg.id == "msg123"
        assert msg.text == "Hello World"
        assert msg.group_name == ""
        assert msg.sender_id == ""
        assert msg.sender_name == ""
        assert msg.is_reacted is None
        assert msg.target_pattern is None
        assert isinstance(msg.created_at, datetime)
        assert msg.reacted_at is None

    def test_create_message_with_all_fields(self):
        """Test creating message with all fields"""
        now = utcnow()
        msg = FeishuMessage(
            id="msg456",
            text="Test message",
            group_name="Test Group",
            sender_id="user123",
            sender_name="Test User",
            is_reacted=False,
            target_pattern="test_pattern",
            created_at=now,
            reacted_at=now,
        )

        assert msg.id == "msg456"
        assert msg.text == "Test message"
        assert msg.group_name == "Test Group"
        assert msg.sender_id == "user123"
        assert msg.sender_name == "Test User"
        assert msg.is_reacted is False
        assert msg.target_pattern == "test_pattern"
        assert msg.created_at == now
        assert msg.reacted_at == now

    def test_mark_processed_success(self):
        """Test mark_processed with successful reaction"""
        msg = FeishuMessage(id="msg789", text="Match this")

        msg.mark_processed(is_reacted=True, target_pattern="match_pattern")

        assert msg.is_reacted is True
        assert msg.target_pattern == "match_pattern"
        assert msg.reacted_at is not None
        assert isinstance(msg.reacted_at, datetime)

    def test_mark_processed_no_match(self):
        """Test mark_processed with no match"""
        msg = FeishuMessage(id="msg000", text="No match")

        msg.mark_processed(is_reacted=False, target_pattern="checked_pattern")

        assert msg.is_reacted is False
        assert msg.target_pattern == "checked_pattern"
        assert msg.reacted_at is not None

    def test_mark_processed_initial_state(self):
        """Test mark_processed sets initial state"""
        msg = FeishuMessage(id="msg111", text="Initial")

        assert msg.is_reacted is None
        assert msg.target_pattern is None
        assert msg.reacted_at is None

    def test_message_mutation_allowed(self):
        """Test that message fields can be mutated (Config.frozen=False)"""
        msg = FeishuMessage(id="msg222", text="Mutable")

        # Should be able to modify fields
        msg.is_reacted = True
        msg.target_pattern = "pattern"
        msg.reacted_at = utcnow()

        assert msg.is_reacted is True
        assert msg.target_pattern == "pattern"
        assert msg.reacted_at is not None

    def test_reacted_at_always_updated(self):
        """Test that reacted_at is always updated on mark_processed"""
        msg = FeishuMessage(id="msg333", text="Update test")

        before = utcnow()
        msg.mark_processed(is_reacted=False, target_pattern="test")
        after = utcnow()

        assert before <= msg.reacted_at <= after  # ty: ignore[unsupported-operator]

    def test_multiple_mark_processed_calls(self):
        """Test multiple mark_processed calls update state correctly"""
        msg = FeishuMessage(id="msg444", text="Multiple")

        # First call - no match
        msg.mark_processed(is_reacted=False, target_pattern="first")
        first_reacted_at = msg.reacted_at

        # Second call - matched
        import time

        time.sleep(0.01)  # Small delay to ensure different timestamp
        msg.mark_processed(is_reacted=True, target_pattern="second")

        assert msg.is_reacted is True
        assert msg.target_pattern == "second"
        assert msg.reacted_at > first_reacted_at  # ty: ignore[unsupported-operator]

    def test_message_equality_by_value(self):
        """Test that messages with same values are equal"""
        msg1 = FeishuMessage(id="msg555", text="Same")
        msg2 = FeishuMessage(id="msg555", text="Same")

        assert msg1.id == msg2.id
        assert msg1.text == msg2.text
        # Note: created_at will be different, so we don't test full equality

    def test_message_with_unicode_text(self):
        """Test message with unicode/Chinese text"""
        msg = FeishuMessage(id="msg666", text="有车位啦！请联系")

        assert msg.text == "有车位啦！请联系"

    def test_message_json_serialization(self):
        """Test that message can be serialized to JSON"""
        msg = FeishuMessage(
            id="msg777", text="JSON test", is_reacted=True, target_pattern="test"
        )
        msg.mark_processed(is_reacted=True, target_pattern="test")

        json_str = msg.json()  # ty: ignore[deprecated]
        assert "msg777" in json_str
        assert "JSON test" in json_str
        assert "test" in json_str

    def test_message_dict_conversion(self):
        """Test that message can be converted to dict"""
        msg = FeishuMessage(id="msg888", text="Dict test")
        msg.mark_processed(is_reacted=False, target_pattern="pattern")

        d = msg.dict()  # ty: ignore[deprecated]
        assert d["id"] == "msg888"
        assert d["text"] == "Dict test"
        assert d["is_reacted"] is False
        assert d["target_pattern"] == "pattern"
        assert "reacted_at" in d
