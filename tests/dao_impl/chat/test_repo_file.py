"""Tests for FileFeishuMessageRepository"""

import pytest
import tempfile
import os
from parkbot.chat.models import FeishuMessage
from parkbot.dao_impl.chat.repo_impls import FileFeishuMessageRepository


class TestFileFeishuMessageRepository:
    """Test File-based repository implementation"""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing"""
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        yield path
        # Cleanup
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def repo(self, temp_file):
        """Create a fresh repository for each test"""
        return FileFeishuMessageRepository(temp_file)

    def test_save_and_get_single_message(self, repo):
        """Test saving and retrieving a single message"""
        msg = FeishuMessage(id="msg1", text="Hello")
        repo.save_batch([msg])

        result = repo.get_by_ids(["msg1"])

        assert result["msg1"] is not None
        assert result["msg1"].text == "Hello"

    def test_persistence_across_instances(self, temp_file):
        """Test that data persists across repository instances"""
        # Create first repository and save data
        repo1 = FileFeishuMessageRepository(temp_file)
        msg = FeishuMessage(id="msg1", text="Persistent")
        repo1.save_batch([msg])

        # Create second repository pointing to same file
        repo2 = FileFeishuMessageRepository(temp_file)
        result = repo2.get_by_ids(["msg1"])

        assert result["msg1"] is not None
        assert result["msg1"].text == "Persistent"

    def test_file_created_on_save(self, repo, temp_file):
        """Test that file is created when saving"""
        assert not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0

        msg = FeishuMessage(id="msg1", text="Create file")
        repo.save_batch([msg])

        assert os.path.exists(temp_file)
        assert os.path.getsize(temp_file) > 0

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
        assert result["msg2"].is_reacted is True

    def test_get_by_ids_iter(self, repo):
        """Test iterator version of get_by_ids"""
        msgs = [
            FeishuMessage(id="msg1", text="First"),
            FeishuMessage(id="msg2", text="Second"),
        ]
        repo.save_batch(msgs)

        results = list(repo.get_by_ids_iter(["msg1", "msg2", "msg3"]))

        assert len(results) == 2
        ids = [m.id for m in results]
        assert "msg1" in ids
        assert "msg2" in ids

    def test_file_json_format(self, repo, temp_file):
        """Test that file contains valid JSON"""
        import json

        msg = FeishuMessage(id="msg1", text="JSON test")
        msg.mark_processed(is_reacted=True, target_pattern="pattern")
        repo.save_batch([msg])

        with open(temp_file, "r") as f:
            data = json.load(f)

        assert "messages" in data
        assert len(data["messages"]) == 1
        assert data["messages"][0]["id"] == "msg1"
        assert data["messages"][0]["text"] == "JSON test"
        assert data["messages"][0]["is_reacted"] is True

    def test_corrupted_file_handling(self, temp_file):
        """Test handling of corrupted file"""
        # Write corrupted JSON
        with open(temp_file, "w") as f:
            f.write("not valid json")

        repo = FileFeishuMessageRepository(temp_file)
        # Should initialize with empty cache
        assert repo._cache == {}

    def test_concurrent_writes(self, temp_file):
        """Test handling of concurrent writes (last write wins)"""
        repo1 = FileFeishuMessageRepository(temp_file)
        repo2 = FileFeishuMessageRepository(temp_file)

        msg1 = FeishuMessage(id="msg1", text="From repo1")
        msg2 = FeishuMessage(id="msg2", text="From repo2")

        repo1.save_batch([msg1])
        repo2.save_batch([msg2])

        # Last write should win
        repo3 = FileFeishuMessageRepository(temp_file)
        result = repo3.get_by_ids(["msg1", "msg2"])
        assert result["msg2"] is not None  # msg2 was saved last

    def test_unicode_content(self, repo):
        """Test handling of unicode content"""
        msg = FeishuMessage(id="msg1", text="有车位啦！请联系")
        repo.save_batch([msg])

        result = repo.get_by_ids(["msg1"])
        assert result["msg1"].text == "有车位啦！请联系"

    def test_empty_file_initialization(self, temp_file):
        """Test that empty file is handled correctly"""
        # Create empty file
        with open(temp_file, "w") as f:
            f.write("")

        repo = FileFeishuMessageRepository(temp_file)
        assert repo._cache == {}

    def test_large_batch_save(self, repo):
        """Test saving large batch of messages"""
        msgs = [FeishuMessage(id=f"msg{i}", text=f"Message {i}") for i in range(1000)]

        repo.save_batch(msgs)

        ids = [f"msg{i}" for i in range(1000)]
        result = repo.get_by_ids(ids)

        assert len(result) == 1000
        assert all(result[f"msg{i}"] is not None for i in range(1000))
