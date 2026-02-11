"""Data models for the Agent Table deliberation protocol."""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Phase(str, Enum):
    """Phases within a single deliberation round."""

    PLAN = "plan"
    IMPLEMENT = "implement"
    RESOLVE = "resolve"
    APPROVE = "approve"


class MessageType(str, Enum):
    """Types of messages exchanged between agents."""

    PLAN = "plan"
    CRITIQUE = "critique"
    RESPONSE = "response"
    DECISION = "decision"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    APPROVAL = "approval"
    REJECTION = "rejection"
    ESCALATION = "escalation"
    VOTE = "vote"
    COUNTER_PROPOSAL = "counter_proposal"
    CLARIFICATION = "clarification"


class Severity(str, Enum):
    """Issue severity levels used by the Critic."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Confidence(str, Enum):
    """Confidence levels for decisions and votes."""

    CERTAIN = "certain"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ---------------------------------------------------------------------------
# AgentMessage
# ---------------------------------------------------------------------------


class AgentMessage:
    """A single message in the agent deliberation.

    Attributes:
        sender: The role that sent this message.
        recipient: The role this message is addressed to.
        msg_type: The type of message (plan, critique, decision, etc.).
        content: The text content of the message.
        round_number: The round this message belongs to.
        phase: The phase during which this message was sent.
        metadata: Arbitrary key-value metadata.
        timestamp: ISO-8601 timestamp of when the message was created.
    """

    __slots__ = (
        "sender",
        "recipient",
        "msg_type",
        "content",
        "round_number",
        "phase",
        "metadata",
        "timestamp",
    )

    def __init__(
        self,
        sender: str,
        recipient: str,
        msg_type: str,
        content: str,
        *,
        round_number: int = 0,
        phase: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        self.sender = sender
        self.recipient = recipient
        self.msg_type = msg_type
        self.content = content
        self.round_number = round_number
        self.phase = phase
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "msg_type": self.msg_type,
            "content": self.content,
            "round_number": self.round_number,
            "phase": self.phase,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Deserialize from a dictionary."""
        return cls(
            sender=data["sender"],
            recipient=data["recipient"],
            msg_type=data["msg_type"],
            content=data["content"],
            round_number=data.get("round_number", 0),
            phase=data.get("phase", ""),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp"),
        )

    def __repr__(self) -> str:
        return f"<AgentMessage {self.sender}→{self.recipient} " f"[{self.msg_type}] round={self.round_number}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AgentMessage):
            return NotImplemented
        return (
            self.sender == other.sender
            and self.recipient == other.recipient
            and self.msg_type == other.msg_type
            and self.content == other.content
            and self.round_number == other.round_number
        )
