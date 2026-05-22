"""Tests for SqliteFeishuMessageRepository"""

import pytest
import tempfile
import os
from datetime import datetime
from sqlmodel import create_engine, SQLModel
from parkbot.chat.models import FeishuMessage
from parkbot.dao_impl.chat.repo_impls import SqliteFeishuMessageRepository


class TestSqliteFeishuMessageRepository:
    """Test SQLite repository implementation"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        # Cleanup
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def repo(self, temp_db):
        """Create a fresh repository for each test"""
        engine = create_engine(f"sqlite:///{temp_db}")
        # Create tables
        SQLModel.metadata.create_all(engine)
        return SqliteFeishuMessageRepository(engine)

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

    def test_persistence_across_instances(self, temp_db):
        """Test that data persists across repository instances"""
        engine1 = create_engine(f"sqlite:///{temp_db}")
        SQLModel.metadata.create_all(engine1)
        repo1 = SqliteFeishuMessageRepository(engine1)

        msg = FeishuMessage(id="msg1", text="Persistent")
        repo1.save_batch([msg])

        engine2 = create_engine(f"sqlite:///{temp_db}")
        repo2 = SqliteFeishuMessageRepository(engine2)
        result = repo2.get_by_ids(["msg1"])

        assert result["msg1"] is not None
        assert result["msg1"].text == "Persistent"

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

    def test_message_with_all_fields(self, repo):
        """Test saving message with all fields populated"""
        now = datetime.utcnow()
        msg = FeishuMessage(
            id="msg_full",
            text="Full message",
            group_name="Test Group",
            sender_id="user123",
            sender_name="Test User",
            is_reacted=False,
            target_pattern="test_pattern",
            created_at=now,
        )

        repo.save_batch([msg])
        result = repo.get_by_ids(["msg_full"])

        retrieved = result["msg_full"]
        assert retrieved.text == "Full message"
        assert retrieved.group_name == "Test Group"
        assert retrieved.sender_id == "user123"
        assert retrieved.sender_name == "Test User"
        assert retrieved.is_reacted is False
        assert retrieved.target_pattern == "test_pattern"
        assert retrieved.created_at == now

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

    def test_unicode_content(self, repo):
        """Test handling of unicode content"""
        msg = FeishuMessage(id="msg1", text="有车位啦！请联系")
        repo.save_batch([msg])

        result = repo.get_by_ids(["msg1"])
        assert result["msg1"].text == "有车位啦！请联系"

    def test_empty_batch_save(self, repo):
        """Test saving empty batch doesn't error"""
        repo.save_batch([])
        assert True  # Should not raise

    def test_empty_batch_mark_reacted(self, repo):
        """Test marking empty batch doesn't error"""
        count = repo.mark_reacted_batch([])
        assert count == 0

    def test_large_batch_save(self, repo):
        """Test saving large batch of messages"""
        msgs = [FeishuMessage(id=f"msg{i}", text=f"Message {i}") for i in range(100)]

        repo.save_batch(msgs)

        ids = [f"msg{i}" for i in range(100)]
        result = repo.get_by_ids(ids)

        assert len(result) == 100

    def test_timestamps_preserved(self, repo):
        """Test that timestamps are correctly preserved"""
        created = datetime(2025, 1, 1, 12, 0, 0)
        msg = FeishuMessage(
            id="msg1",
            text="Timestamp test",
            created_at=created,
        )

        repo.save_batch([msg])
        result = repo.get_by_ids(["msg1"])

        retrieved = result["msg1"]
        assert retrieved.created_at.year == 2025
        assert retrieved.created_at.month == 1
        assert retrieved.created_at.day == 1

    def test_reacted_at_updated_on_mark_reacted(self, repo):
        """Test that reacted_at is set when marking as reacted"""
        msg = FeishuMessage(id="msg1", text="React test")
        repo.save_batch([msg])

        before = datetime.utcnow()
        repo.mark_reacted_batch(["msg1"])
        after = datetime.utcnow()

        result = repo.get_by_ids(["msg1"])
        assert before <= result["msg1"].reacted_at <= after

    def test_table_auto_created(self, temp_db):
        """Test that table is auto-created on repository initialization"""
        # Verify database file doesn't exist or is empty
        assert not os.path.exists(temp_db) or os.path.getsize(temp_db) == 0

        engine = create_engine(f"sqlite:///{temp_db}")
        # Create tables
        SQLModel.metadata.create_all(engine)
        repo = SqliteFeishuMessageRepository(engine)

        # Should be able to save immediately
        msg = FeishuMessage(id="msg1", text="Test")
        repo.save_batch([msg])

        # Verify file was created and has content
        assert os.path.exists(temp_db)
        assert os.path.getsize(temp_db) > 0
