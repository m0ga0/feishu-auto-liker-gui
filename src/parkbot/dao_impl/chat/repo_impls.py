# src/parkbot/dao_impl/chat/repo_impls.py
import json
from pathlib import Path
from typing import List, Optional, Dict, Iterator
from datetime import datetime
from sqlmodel import Session, select, col
from .dao import IFeishuMessageRepository
from parkbot.chat.models import FeishuMessage
from .models_impls import SqliteFeishuMessage
from parkbot.utils.datetime_utils import utcnow


class SqliteFeishuMessageRepository(IFeishuMessageRepository):
    """SQLite implementation of IFeishuMessageRepository."""

    BATCH_SIZE = 100

    def __init__(self, engine):
        self.engine = engine

    def get_by_ids(self, message_ids: List[str]) -> Dict[str, Optional[FeishuMessage]]:
        result = {}
        # Process in batches to avoid memory issues
        for i in range(0, len(message_ids), self.BATCH_SIZE):
            batch = message_ids[i : i + self.BATCH_SIZE]
            with Session(self.engine) as session:
                statement = select(SqliteFeishuMessage).where(
                    col(SqliteFeishuMessage.id).in_(batch)
                )
                db_messages = session.exec(statement).all()
                # Map found messages
                for db_msg in db_messages:
                    result[db_msg.id] = db_msg.to_domain()
                # Mark not-found as None
                for msg_id in batch:
                    if msg_id not in result:
                        result[msg_id] = None
        return result

    def save_batch(self, messages: List[FeishuMessage]) -> None:
        # Process in batches
        for i in range(0, len(messages), self.BATCH_SIZE):
            batch = messages[i : i + self.BATCH_SIZE]
            with Session(self.engine) as session:
                for msg in batch:
                    db_msg = SqliteFeishuMessage.from_domain(msg)
                    session.merge(db_msg)  # Upsert
                session.commit()

    def mark_reacted_batch(self, message_ids: List[str]) -> int:
        updated_count = 0
        now = utcnow()

        for i in range(0, len(message_ids), self.BATCH_SIZE):
            batch = message_ids[i : i + self.BATCH_SIZE]
            with Session(self.engine) as session:
                statement = select(SqliteFeishuMessage).where(
                    col(SqliteFeishuMessage.id).in_(batch)
                )
                db_messages = session.exec(statement).all()
                for db_msg in db_messages:
                    db_msg.is_reacted = True
                    db_msg.reacted_at = now
                    updated_count += 1
                session.commit()

        return updated_count

    def exists(self, message_id: str) -> bool:
        with Session(self.engine) as session:
            return session.get(SqliteFeishuMessage, message_id) is not None

    def exists_batch(self, message_ids: List[str]) -> Dict[str, bool]:
        result = {msg_id: False for msg_id in message_ids}

        for i in range(0, len(message_ids), self.BATCH_SIZE):
            batch = message_ids[i : i + self.BATCH_SIZE]
            with Session(self.engine) as session:
                statement = select(SqliteFeishuMessage.id).where(
                    col(SqliteFeishuMessage.id).in_(batch)
                )
                found_ids = set(session.exec(statement).all())
                for msg_id in batch:
                    if msg_id in found_ids:
                        result[msg_id] = True

        return result

    def get_by_ids_iter(self, message_ids: List[str]) -> Iterator[FeishuMessage]:
        """Generator for memory-efficient iteration."""
        for i in range(0, len(message_ids), self.BATCH_SIZE):
            batch = message_ids[i : i + self.BATCH_SIZE]
            with Session(self.engine) as session:
                statement = select(SqliteFeishuMessage).where(
                    col(SqliteFeishuMessage.id).in_(batch)
                )
                for db_msg in session.exec(statement):
                    yield db_msg.to_domain()


class FileFeishuMessageRepository(IFeishuMessageRepository):
    """File-based JSON repository for simple deployments."""

    def __init__(self, file_path: str = "messages.json"):
        self.file_path = Path(file_path)
        self._cache: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self.file_path.exists() and self.file_path.stat().st_size > 0:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cache = {m["id"]: m for m in data.get("messages", [])}
            except (json.JSONDecodeError, IOError):
                self._cache = {}

    def _save(self) -> None:
        data = {"messages": list(self._cache.values())}
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def get_by_ids(self, message_ids: List[str]) -> Dict[str, Optional[FeishuMessage]]:
        result = {}
        for msg_id in message_ids:
            data = self._cache.get(msg_id)
            if data:
                result[msg_id] = FeishuMessage(**self._convert_datetime_fields(data))
            else:
                result[msg_id] = None
        return result

    def save_batch(self, messages: List[FeishuMessage]) -> None:
        for msg in messages:
            self._cache[msg.id] = json.loads(msg.model_dump_json())
        self._save()

    def mark_reacted_batch(self, message_ids: List[str]) -> int:
        now = utcnow().isoformat()
        count = 0
        for msg_id in message_ids:
            if msg_id in self._cache:
                self._cache[msg_id]["is_reacted"] = True
                self._cache[msg_id]["reacted_at"] = now
                count += 1
        self._save()
        return count

    def exists(self, message_id: str) -> bool:
        return message_id in self._cache

    def exists_batch(self, message_ids: List[str]) -> Dict[str, bool]:
        return {msg_id: msg_id in self._cache for msg_id in message_ids}

    def get_by_ids_iter(self, message_ids: List[str]) -> Iterator[FeishuMessage]:
        """Generator for memory-efficient iteration."""
        for msg_id in message_ids:
            data = self._cache.get(msg_id)
            if data:
                yield FeishuMessage(**self._convert_datetime_fields(data))

    def _convert_datetime_fields(self, data: dict) -> dict:
        """Convert ISO datetime strings back to datetime objects."""
        for field in ["created_at", "reacted_at"]:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        return data


class InMemoryFeishuMessageRepository(IFeishuMessageRepository):
    """In-memory repository for testing."""

    def __init__(self):
        self._storage: Dict[str, FeishuMessage] = {}

    def get_by_ids(self, message_ids: List[str]) -> Dict[str, Optional[FeishuMessage]]:
        return {msg_id: self._storage.get(msg_id) for msg_id in message_ids}

    def save_batch(self, messages: List[FeishuMessage]) -> None:
        for msg in messages:
            self._storage[msg.id] = msg

    def mark_reacted_batch(self, message_ids: List[str]) -> int:
        now = utcnow()
        count = 0
        for msg_id in message_ids:
            msg = self._storage.get(msg_id)
            if msg:
                msg.is_reacted = True
                msg.reacted_at = now
                count += 1
        return count

    def exists(self, message_id: str) -> bool:
        return message_id in self._storage

    def exists_batch(self, message_ids: List[str]) -> Dict[str, bool]:
        return {msg_id: msg_id in self._storage for msg_id in message_ids}

    def get_by_ids_iter(self, message_ids: List[str]) -> Iterator[FeishuMessage]:
        """Generator for memory-efficient iteration."""
        for msg_id in message_ids:
            msg = self._storage.get(msg_id)
            if msg:
                yield msg

    def clear_all(self) -> None:
        """Helper for tests."""
        self._storage.clear()
