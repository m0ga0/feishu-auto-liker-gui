"""Tests for InMemoryFeishuMessageRepository"""

import pytest
from parkbot.chat.models import FeishuMessage
from parkbot.dao_impl.chat.repo_impls import InMemoryFeishuMessageRepository


class TestInMemoryFeishuMessageRepository:
    """Test InMemory repository implementation"""

    @pytest.fixture
    def repo(self):
        """Create a fresh repository for each test"""
        return InMemoryFeishuMessageRepository()

    def test_save_and_get_single_message(self, repo):
        """Test saving and retrieving a single message"""
        msg = FeishuMessage(id="msg1", text="Hello")
        repo.save_batch([msg])

        result = repo.get_by_ids(["msg1"])

        assert result["msg1"] is not None
        assert result["msg1"].text == "Hello"

    def test_save_and_get_multiple_messages(self, repo):
        """Test batch save and retrieve"""
        msgs = [
            FeishuMessage(id="msg1", text="First"),
            FeishuMessage(id="msg2", text="Second"),
            FeishuMessage(id="msg3", text="Third"),
        ]
        repo.save_batch(msgs)

        result = repo.get_by_ids(["msg1", "msg2", "msg3"])

        assert len(result) == 3
        assert result["msg1"].text == "First"
        assert result["msg2"].text == "Second"
        assert result["msg3"].text == "Third"

    def test_get_nonexistent_message_returns_none(self, repo):
        """Test retrieving non-existent message returns None"""
        result = repo.get_by_ids(["nonexistent"])

        assert result["nonexistent"] is None

    def test_get_mixed_existing_and_nonexisting(self, repo):
        """Test batch get with mix of existing and non-existing messages"""
        msg = FeishuMessage(id="exists", text="I exist")
        repo.save_batch([msg])

        result = repo.get_by_ids(["exists", "notexists"])

        assert result["exists"] is not None
        assert result["notexists"] is None

    def test_update_existing_message(self, repo):
        """Test that saving updates existing message"""
        msg = FeishuMessage(id="msg1", text="Original")
        repo.save_batch([msg])

        # Update the message
        msg.text = "Updated"
        msg.mark_processed(is_reacted=True, target_pattern="test")
        repo.save_batch([msg])

        result = repo.get_by_ids(["msg1"])
        assert result["msg1"].text == "Updated"
        assert result["msg1"].is_reacted is True

    def test_exists_single(self, repo):
        """Test exists method for single message"""
        msg = FeishuMessage(id="msg1", text="Hello")
        repo.save_batch([msg])

        assert repo.exists("msg1") is True
        assert repo.exists("msg2") is False

    def test_exists_batch(self, repo):
        """Test batch exists check"""
        msgs = [
            FeishuMessage(id="msg1", text="First"),
            FeishuMessage(id="msg2", text="Second"),
        ]
        repo.save_batch(msgs)

        result = repo.exists_batch(["msg1", "msg2", "msg3"])

        assert result["msg1"] is True
        assert result["msg2"] is True
        assert result["msg3"] is False

    def test_mark_reacted_batch(self, repo):
        """Test batch mark as reacted"""
        msgs = [
            FeishuMessage(id="msg1", text="First"),
            FeishuMessage(id="msg2", text="Second"),
        ]
        repo.save_batch(msgs)

        count = repo.mark_reacted_batch(["msg1", "msg2"])

        assert count == 2

        result = repo.get_by_ids(["msg1", "msg2"])
        assert result["msg1"].is_reacted is True
        assert result["msg1"].reacted_at is not None
        assert result["msg2"].is_reacted is True
        assert result["msg2"].reacted_at is not None

    def test_mark_reacted_batch_partial(self, repo):
        """Test batch mark with some non-existent messages"""
        msg = FeishuMessage(id="msg1", text="Only one")
        repo.save_batch([msg])

        count = repo.mark_reacted_batch(["msg1", "msg2"])

        assert count == 1

        result = repo.get_by_ids(["msg1"])
        assert result["msg1"].is_reacted is True

    def test_get_by_ids_iter(self, repo):
        """Test iterator version of get_by_ids"""
        msgs = [
            FeishuMessage(id="msg1", text="First"),
            FeishuMessage(id="msg2", text="Second"),
            FeishuMessage(id="msg3", text="Third"),
        ]
        repo.save_batch(msgs)

        results = list(repo.get_by_ids_iter(["msg1", "msg2", "msg3"]))

        assert len(results) == 3
        ids = [m.id for m in results]
        assert "msg1" in ids
        assert "msg2" in ids
        assert "msg3" in ids

    def test_get_by_ids_iter_skips_nonexistent(self, repo):
        """Test iterator skips non-existent messages"""
        msg = FeishuMessage(id="msg1", text="Only one")
        repo.save_batch([msg])

        results = list(repo.get_by_ids_iter(["msg1", "msg2"]))

        assert len(results) == 1
        assert results[0].id == "msg1"

    def test_clear_all(self, repo):
        """Test clear_all helper method"""
        msgs = [
            FeishuMessage(id="msg1", text="First"),
            FeishuMessage(id="msg2", text="Second"),
        ]
        repo.save_batch(msgs)

        assert repo.exists("msg1") is True

        repo.clear_all()

        assert repo.exists("msg1") is False
        assert repo.exists("msg2") is False

    def test_empty_batch_save(self, repo):
        """Test saving empty batch doesn't error"""
        repo.save_batch([])
        assert True  # Should not raise

    def test_empty_batch_mark_reacted(self, repo):
        """Test marking empty batch doesn't error"""
        count = repo.mark_reacted_batch([])
        assert count == 0

    def test_message_state_preserved(self, repo):
        """Test that message state is correctly preserved"""
        msg = FeishuMessage(id="msg1", text="Test")
        msg.mark_processed(is_reacted=False, target_pattern="checked")

        repo.save_batch([msg])
        result = repo.get_by_ids(["msg1"])

        retrieved = result["msg1"]
        assert retrieved.is_reacted is False
        assert retrieved.target_pattern == "checked"
        assert retrieved.reacted_at is not None
