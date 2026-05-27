# src/parkbot/dao_impl/chat/models_impls.py
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from parkbot.chat.models import FeishuMessage
from parkbot.utils.datetime_utils import utcnow


class SqliteFeishuMessage(SQLModel, table=True):
    """Database model for FeishuMessage persistence in SQLite."""

    __tablename__ = "feishu_messages"

    # Single primary key - Feishu message IDs are globally unique
    id: str = Field(primary_key=True)

    group_name: str = Field(default="")
    text: str
    sender_id: str = Field(default="")
    sender_name: str = Field(default="")

    # State flags
    is_reacted: Optional[bool] = Field(default=None, index=True)
    target_pattern: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=utcnow)
    reacted_at: Optional[datetime] = None

    def to_domain(self) -> FeishuMessage:
        """Convert DB model to domain model."""
        return FeishuMessage(
            id=self.id,
            group_name=self.group_name,
            text=self.text,
            sender_id=self.sender_id,
            sender_name=self.sender_name,
            is_reacted=self.is_reacted,
            target_pattern=self.target_pattern,
            created_at=self.created_at,
            reacted_at=self.reacted_at,
        )

    @classmethod
    def from_domain(cls, msg: FeishuMessage) -> "SqliteFeishuMessage":
        """Convert domain model to DB model."""
        return cls(
            id=msg.id,
            group_name=msg.group_name,
            text=msg.text,
            sender_id=msg.sender_id,
            sender_name=msg.sender_name,
            is_reacted=msg.is_reacted,
            target_pattern=msg.target_pattern,
            created_at=msg.created_at,
            reacted_at=msg.reacted_at,
        )
