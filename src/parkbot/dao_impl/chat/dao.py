# src/parkbot/dao_impl/chat/dao.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Iterator
from parkbot.chat.models import FeishuMessage


class IFeishuMessageRepository(ABC):
    """
    Repository interface for FeishuMessage persistence.

    All operations are batch-based to avoid N+1 query problems.
    Implementations should handle batching with appropriate limits
    to manage memory usage.
    """

    # Batch size limit to prevent memory issues
    BATCH_SIZE: int = 100

    @abstractmethod
    def get_by_ids(self, message_ids: List[str]) -> Dict[str, Optional[FeishuMessage]]:
        """
        Get multiple messages by their IDs.

        Args:
            message_ids: List of message IDs to retrieve

        Returns:
            Dict mapping message_id -> FeishuMessage or None if not found

        Note:
            Implementation should batch queries if len(message_ids) > BATCH_SIZE
        """
        ...

    @abstractmethod
    def save_batch(self, messages: List[FeishuMessage]) -> None:
        """
        Save multiple messages (insert or update).

        Args:
            messages: List of messages to save

        Note:
            Implementation should batch inserts if len(messages) > BATCH_SIZE
        """
        ...

    @abstractmethod
    def mark_reacted_batch(self, message_ids: List[str]) -> int:
        """
        Mark multiple messages as reacted.

        Args:
            message_ids: List of message IDs to mark

        Returns:
            Number of messages actually updated

        Note:
            This is an optimization to avoid loading full objects.
            Updates is_reacted=True and reacted_at=now for all given IDs.
        """
        ...

    @abstractmethod
    def exists(self, message_id: str) -> bool:
        """
        Check if a message exists in storage.

        Args:
            message_id: Message ID to check

        Returns:
            True if message exists, False otherwise
        """
        ...

    @abstractmethod
    def exists_batch(self, message_ids: List[str]) -> Dict[str, bool]:
        """
        Check existence of multiple messages.

        Args:
            message_ids: List of message IDs to check

        Returns:
            Dict mapping message_id -> True/False for existence
        """
        ...

    @abstractmethod
    def get_by_ids_iter(self, message_ids: List[str]) -> Iterator[FeishuMessage]:
        """
        Generator version for memory-efficient iteration.

        Yields messages one by one to save memory for large batches.

        Args:
            message_ids: List of message IDs to retrieve

        Yields:
            FeishuMessage objects one at a time

        Example:
            for msg in repo.get_by_ids_iter(ids):
                process(msg)
        """
        ...
