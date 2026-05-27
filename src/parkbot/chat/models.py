# src/parkbot/chat/models.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from parkbot.utils.datetime_utils import utcnow


class FeishuMessage(BaseModel):
    """
    Domain model representing a Feishu chat message.

    Business Logic:
    - If message not found in storage: Never seen before (new or missed)
    - If found in storage with is_reacted=None: Seen but no action taken
      (app killed/shutdown before processing)
    - If found with is_reacted=False, target_pattern=<pattern>: Checked but
      pattern did not match (target_pattern stores the checked pattern)
    - If found with is_reacted=True: Matched and reacted

    Config class purpose:
    - frozen=False allows mutation for state updates after creation
    - This is required because we update is_reacted and target_pattern
      after initial creation when processing occurs
    """

    id: str = Field(..., description="Unique message ID from Feishu (global)")
    group_name: str = Field(default="", description="Human-readable group name")
    text: str = Field(..., description="Message content")
    sender_id: str = Field(default="", description="Sender user ID (placeholder)")
    sender_name: str = Field(
        default="", description="Sender display name (placeholder)"
    )

    # Processing state (None = not checked yet, False = checked no match, True = matched & reacted)
    is_reacted: Optional[bool] = Field(
        default=None, description="None=unchecked, False=no match, True=reacted"
    )
    target_pattern: Optional[str] = Field(
        default=None,
        description="Pattern that was checked (stores checked pattern even on no-match)",
    )

    # Timestamp
    created_at: datetime = Field(default_factory=utcnow)
    reacted_at: Optional[datetime] = Field(default=None)

    class Config:
        """
        Pydantic configuration.
        frozen=False allows field mutation after creation, which is necessary
        for updating message state (is_reacted, target_pattern) during processing.
        """

        frozen = False

    def mark_processed(self, is_reacted: bool, target_pattern: Optional[str]) -> None:
        """
        Mark message as processed with result.

        Unified method to handle all processing scenarios:
        - is_reacted=True, target_pattern=<pattern>: Matched and reacted
        - is_reacted=False, target_pattern=<pattern>: Checked but no match
        - is_reacted=None: Not processed yet (initial state)

        Always updates reacted_at timestamp.
        """
        self.is_reacted = is_reacted
        self.target_pattern = target_pattern
        self.reacted_at = utcnow()
