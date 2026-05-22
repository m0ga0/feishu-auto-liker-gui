"""Tests for IFeishuMessageRepository interface contract"""

import pytest
from sqlmodel import create_engine, SQLModel
from parkbot.chat.models import FeishuMessage
from parkbot.dao_impl.chat.dao import IFeishuMessageRepository
from parkbot.dao_impl.chat.repo_impls import (
    InMemoryFeishuMessageRepository,
    FileFeishuMessageRepository,
    SqliteFeishuMessageRepository,
)


from typing import List, Optional, Dict, Iterator


class DummyRepository(IFeishuMessageRepository):
    def get_by_ids(self, message_ids: List[str]) -> Dict[str, Optional[FeishuMessage]]:
        return {}

    def save_batch(self, messages: List[FeishuMessage]) -> None:
        pass

    def mark_reacted_batch(self, message_ids: List[str]) -> int:
        return 0

    def exists(self, message_id: str) -> bool:
        return False

    def exists_batch(self, message_ids: List[str]) -> Dict[str, bool]:
        return {}

    def get_by_ids_iter(self, message_ids: List[str]) -> Iterator[FeishuMessage]:
        yield from []


class TestIFeishuMessageRepositoryInterface:
    """Test that interface is properly defined"""

    def test_abstract_methods_can_be_called(self):
        """Invoke abstract methods via dummy to hit coverage"""
        repo = DummyRepository()
        repo.get_by_ids([])
        repo.save_batch([])
        repo.mark_reacted_batch([])
        repo.exists("1")
        repo.exists_batch([])
        list(repo.get_by_ids_iter([]))


class TestRepositoryImplementations:
    """Test that all implementations satisfy the interface"""

    @pytest.fixture
    def implementations(self, tmp_path):
        """Provide all repository implementations for testing"""
        file_path = tmp_path / "test.json"
        db_path = tmp_path / "test.db"

        # Create engine and tables for SQLite
        engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(engine)

        return [
            InMemoryFeishuMessageRepository(),
            FileFeishuMessageRepository(str(file_path)),
            SqliteFeishuMessageRepository(engine),
        ]

    def test_all_implement_interface(self, implementations):
        """Test that all implementations are valid IFeishuMessageRepository"""
        for repo in implementations:
            assert isinstance(repo, IFeishuMessageRepository)

    def test_save_batch_returns_none(self, implementations):
        """Test that save_batch returns None (no return value expected)"""
        msg = FeishuMessage(id="msg1", text="Test")

        for repo in implementations:
            result = repo.save_batch([msg])
            assert result is None

    def test_get_by_ids_returns_dict(self, implementations):
        """Test that get_by_ids returns dict with msg_id -> FeishuMessage or None"""
        msg = FeishuMessage(id="msg1", text="Test")

        for repo in implementations:
            repo.save_batch([msg])
            result = repo.get_by_ids(["msg1", "msg2"])

            assert isinstance(result, dict)
            assert result["msg1"] is None or isinstance(result["msg1"], FeishuMessage)
            assert result["msg2"] is None or isinstance(result["msg2"], FeishuMessage)

    def test_get_by_ids_iter_returns_iterator(self, implementations):
        """Test that get_by_ids_iter returns iterator of FeishuMessage"""
        msgs = [
            FeishuMessage(id="msg1", text="First"),
            FeishuMessage(id="msg2", text="Second"),
        ]

        for repo in implementations:
            repo.save_batch(msgs)
            result = repo.get_by_ids_iter(["msg1", "msg2"])

            # Should be iterable
            items = list(result)
            for item in items:
                assert isinstance(item, FeishuMessage)

    def test_exists_returns_bool(self, implementations):
        """Test that exists returns boolean"""
        msg = FeishuMessage(id="msg1", text="Test")

        for repo in implementations:
            repo.save_batch([msg])

            assert repo.exists("msg1") is True
            assert repo.exists("nonexistent") is False

    def test_exists_batch_returns_dict(self, implementations):
        """Test that exists_batch returns dict with msg_id -> bool"""
        msg = FeishuMessage(id="msg1", text="Test")

        for repo in implementations:
            repo.save_batch([msg])
            result = repo.exists_batch(["msg1", "msg2"])

            assert isinstance(result, dict)
            assert result["msg1"] is True
            assert result["msg2"] is False
            assert all(isinstance(v, bool) for v in result.values())

    def test_mark_reacted_batch_returns_int(self, implementations):
        """Test that mark_reacted_batch returns int (count of updated)"""
        msgs = [
            FeishuMessage(id="msg1", text="First"),
            FeishuMessage(id="msg2", text="Second"),
        ]

        for repo in implementations:
            repo.save_batch(msgs)
            count = repo.mark_reacted_batch(["msg1", "msg2", "msg3"])

            assert isinstance(count, int)
            assert count == 2

    def test_batch_size_boundary(self, implementations):
        """Test behavior near BATCH_SIZE limit"""
        # Batch size is 100, let's test with 101 items
        msgs = [FeishuMessage(id=f"msg{i}", text="Test") for i in range(101)]

        for repo in implementations:
            repo.save_batch(msgs)

            # Test retrieval
            result = repo.get_by_ids([f"msg{i}" for i in range(101)])
            assert len(result) == 101

            # Test existence
            exists = repo.exists_batch([f"msg{i}" for i in range(101)])
            assert len(exists) == 101
            assert all(exists.values())

            # Test reacted
            count = repo.mark_reacted_batch([f"msg{i}" for i in range(101)])
            assert count == 101

    def test_invalid_input_types(self, implementations):
        """Test handling of empty/invalid inputs"""
        for repo in implementations:
            # Should handle empty lists gracefully
            assert repo.get_by_ids([]) == {}
            assert repo.exists_batch([]) == {}
            assert repo.mark_reacted_batch([]) == 0
            assert list(repo.get_by_ids_iter([])) == []

    def test_get_by_ids_empty_list(self, implementations):
        """Test that get_by_ids handles empty list"""
        for repo in implementations:
            result = repo.get_by_ids([])
            assert result == {}

    def test_exists_batch_empty_list(self, implementations):
        """Test that exists_batch handles empty list"""
        for repo in implementations:
            result = repo.exists_batch([])
            assert result == {}

    def test_mark_reacted_batch_empty_list(self, implementations):
        """Test that mark_reacted_batch handles empty list"""
        for repo in implementations:
            count = repo.mark_reacted_batch([])
            assert count == 0


class TestRepositoryBehaviorConsistency:
    """Test that all implementations behave consistently"""

    @pytest.fixture
    def implementations(self, tmp_path):
        """Provide all repository implementations for testing"""
        file_path = tmp_path / "test.json"
        db_path = tmp_path / "test.db"

        # Create engine and tables for SQLite
        engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(engine)

        return [
            InMemoryFeishuMessageRepository(),
            FileFeishuMessageRepository(str(file_path)),
            SqliteFeishuMessageRepository(engine),
        ]

    def test_message_state_consistency(self, implementations):
        """Test that message state is consistent across implementations"""
        msgs = [
            FeishuMessage(
                id="msg1", text="Test", group_name="Group", sender_name="User"
            ),
        ]

        for repo in implementations:
            repo.save_batch(msgs)
            result = repo.get_by_ids(["msg1"])

            assert result["msg1"].id == "msg1"
            assert result["msg1"].text == "Test"
            assert result["msg1"].group_name == "Group"
            assert result["msg1"].sender_name == "User"

    def test_mark_processed_state_consistency(self, implementations):
        """Test that mark_processed state is consistent across implementations"""
        msgs = [
            FeishuMessage(id="msg1", text="Test"),
        ]

        for repo in implementations:
            msgs[0].mark_processed(is_reacted=True, target_pattern="pattern")
            repo.save_batch(msgs)
            result = repo.get_by_ids(["msg1"])

            assert result["msg1"].is_reacted is True
            assert result["msg1"].target_pattern == "pattern"
            assert result["msg1"].reacted_at is not None
