"""AgentTable orchestrator — multi-agent deliberation controller.

This is the primary entry-point class that unifies all sub-modules.
It preserves full backward-compatibility with the original monolithic
AgentTable while exposing new capabilities (strategies, consensus,
trust scoring, hooks, validation).
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .consensus import ConsensusEngine
from .context import ContextBuilder
from .hooks import (
    EVENT_APPROVAL,
    EVENT_CRITIQUE_SUBMITTED,
    EVENT_DEADLOCK_DETECTED,
    EVENT_DECISION,
    EVENT_ESCALATION,
    EVENT_IMPLEMENTATION_SUBMITTED,
    EVENT_MESSAGE_SENT,
    EVENT_PHASE_CHANGE,
    EVENT_PLAN_SUBMITTED,
    EVENT_REJECTION,
    EVENT_REVIEW_SUBMITTED,
    EVENT_ROUND_END,
    EVENT_ROUND_START,
    EVENT_TABLE_FINALIZED,
    EVENT_TABLE_INITIALIZED,
    EVENT_TABLE_RESET,
    HookManager,
)
from .models import AgentMessage, MessageType, Phase
from .protocol import ProtocolEngine
from .roles import ROLE_ARBITER, ROLE_CRITIC, ROLE_DOER
from .scoring import TrustScoring
from .state import TABLE_STATE_FILE, TableState
from .strategies import DefaultStrategy, DeliberationStrategy, get_strategy
from .transcript import TranscriptStore
from .validators import MessageValidator, StateValidator


class AgentTable:
    """Orchestrates multi-agent deliberation for a task.

    Directory layout under ``.ralph-mode/table/``::

        table-state.json     – Current table state
        transcript.jsonl     – Full log of all messages
        trust-scores.json    – Per-agent trust data
        rounds/
            round-001/
                plan.md          – Doer's plan
                critique.md      – Critic's review
                decision.md      – Arbiter's decision (if escalated)
                implementation.md – Doer's implementation notes
                review.md        – Critic's review of implementation
                approval.md      – Arbiter's final approval
    """

    def __init__(self, ralph_dir: Optional[Path] = None) -> None:
        if ralph_dir is None:
            ralph_dir = Path.cwd() / ".ralph-mode"
        self.ralph_dir = Path(ralph_dir)

        # Sub-modules
        self._state_mgr = TableState(self.ralph_dir)
        self._transcript = TranscriptStore(self._state_mgr.table_dir)
        self._protocol = ProtocolEngine()
        self._hooks = HookManager()
        self._validator = MessageValidator()
        self._state_validator = StateValidator()
        self._scoring = TrustScoring(self._state_mgr.table_dir)
        self._consensus = ConsensusEngine()
        self._strategy: DeliberationStrategy = DefaultStrategy()

        # Context builder (wired to our getters)
        self._context = ContextBuilder(
            get_state=self.get_state,
            get_last_message=self.get_last_message,
            get_messages=self.get_messages,
        )

        # Convenience aliases matching old monolith attribute names
        self.table_dir = self._state_mgr.table_dir
        self.rounds_dir = self._state_mgr.rounds_dir
        self.transcript_file = self._transcript.filepath
        self.state_file = self._state_mgr.state_file

    # ------------------------------------------------------------------
    # Sub-module Access
    # ------------------------------------------------------------------

    @property
    def hooks(self) -> HookManager:
        """Access the hook manager for event registration."""
        return self._hooks

    @property
    def consensus(self) -> ConsensusEngine:
        """Access the consensus engine."""
        return self._consensus

    @property
    def trust(self) -> TrustScoring:
        """Access the trust scoring system."""
        return self._scoring

    @property
    def strategy(self) -> DeliberationStrategy:
        """Current deliberation strategy."""
        return self._strategy

    @strategy.setter
    def strategy(self, value: DeliberationStrategy) -> None:
        self._strategy = value

    def set_strategy(self, name: str) -> None:
        """Set strategy by name (default, strict, lenient, democratic, autocratic)."""
        self._strategy = get_strategy(name)

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(
        self,
        task_description: str,
        *,
        max_rounds: int = 10,
        require_unanimous: bool = False,
        auto_escalate: bool = True,
    ) -> Dict[str, Any]:
        """Initialize a new Agent Table session.

        Args:
            task_description: The task to be deliberated on.
            max_rounds: Maximum deliberation rounds before forced decision.
            require_unanimous: If True, Critic must approve before Arbiter.
            auto_escalate: If True, automatically escalate on disagreement.

        Returns:
            The initial table state dict.
        """
        state = self._state_mgr.initialize(
            task_description,
            max_rounds=max_rounds,
            require_unanimous=require_unanimous,
            auto_escalate=auto_escalate,
        )
        self._hooks.emit(EVENT_TABLE_INITIALIZED, state=state)
        return state

    # ------------------------------------------------------------------
    # State Management
    # ------------------------------------------------------------------

    def is_active(self) -> bool:
        """Check if an Agent Table session is active."""
        return self._state_mgr.is_active()

    def get_state(self) -> Optional[Dict[str, Any]]:
        """Get current table state."""
        return self._state_mgr.get_state()

    def _save_state(self, state: Dict[str, Any]) -> None:
        self._state_mgr._save_state(state)

    # ------------------------------------------------------------------
    # Round Management
    # ------------------------------------------------------------------

    def new_round(self) -> Dict[str, Any]:
        """Start a new deliberation round.

        Returns:
            Updated state with new round number.

        Raises:
            ValueError: If table is not active or max rounds reached.
        """
        state = self._state_mgr.new_round()

        # Reset per-round consensus
        self._consensus.clear_votes()

        self._hooks.emit(EVENT_ROUND_START, state=state)

        # Deadlock check
        if self._protocol.detect_deadlock(state):
            self._hooks.emit(EVENT_DEADLOCK_DETECTED, state=state)

        return state

    def _round_dir(self, round_number: int) -> Path:
        return self._state_mgr._round_dir(round_number)

    def get_round_dir(self, round_number: Optional[int] = None) -> Path:
        """Get the directory for a specific round (or current)."""
        if round_number is None:
            state = self.get_state()
            round_number = state["current_round"] if state else 1
        return self._round_dir(round_number)

    # ------------------------------------------------------------------
    # Message Handling
    # ------------------------------------------------------------------

    def send_message(self, message: AgentMessage) -> AgentMessage:
        """Record a message in the transcript and round directory.

        Args:
            message: The AgentMessage to record.

        Returns:
            The same message (with timestamp filled in).
        """
        state = self.get_state()
        if not state or not state.get("active"):
            raise ValueError("Agent Table is not active.")

        # Ensure round number is set
        if message.round_number == 0:
            message.round_number = state["current_round"]

        # Append to transcript
        self._transcript.append(message)

        # Write per-round markdown file
        round_dir = self._round_dir(message.round_number)
        self._transcript.write_round_file(message, round_dir)

        # Update state counters
        state["total_messages"] = state.get("total_messages", 0) + 1
        self._save_state(state)

        # Fire hook
        self._hooks.emit(EVENT_MESSAGE_SENT, message=message, state=state)

        return message

    def get_messages(
        self,
        *,
        round_number: Optional[int] = None,
        sender: Optional[str] = None,
        recipient: Optional[str] = None,
        msg_type: Optional[str] = None,
    ) -> List[AgentMessage]:
        """Retrieve messages from transcript with optional filters."""
        return self._transcript.get_messages(
            round_number=round_number,
            sender=sender,
            recipient=recipient,
            msg_type=msg_type,
        )

    def get_last_message(
        self,
        *,
        sender: Optional[str] = None,
        msg_type: Optional[str] = None,
    ) -> Optional[AgentMessage]:
        """Get the most recent message matching the filters."""
        return self._transcript.get_last_message(sender=sender, msg_type=msg_type)

    # ------------------------------------------------------------------
    # Phase Transitions
    # ------------------------------------------------------------------

    def advance_phase(self) -> Dict[str, Any]:
        """Advance to the next phase.

        Phase order: plan → implement → resolve → approve (stays at approve).

        Returns:
            Updated state.
        """
        state = self.get_state()
        if not state or not state.get("active"):
            raise ValueError("Agent Table is not active.")

        old_phase = state["current_phase"]
        state = self._protocol.advance_phase(state)
        self._save_state(state)

        if state["current_phase"] != old_phase:
            self._hooks.emit(
                EVENT_PHASE_CHANGE,
                old_phase=old_phase,
                new_phase=state["current_phase"],
                state=state,
            )
        return state

    def set_phase(self, phase: str) -> Dict[str, Any]:
        """Explicitly set the current phase."""
        state = self.get_state()
        if not state or not state.get("active"):
            raise ValueError("Agent Table is not active.")

        old_phase = state["current_phase"]
        state = self._protocol.set_phase(state, phase)
        self._save_state(state)

        if phase != old_phase:
            self._hooks.emit(
                EVENT_PHASE_CHANGE,
                old_phase=old_phase,
                new_phase=phase,
                state=state,
            )
        return state

    # ------------------------------------------------------------------
    # High-Level Protocol Methods
    # ------------------------------------------------------------------

    def submit_plan(self, plan_content: str) -> AgentMessage:
        """Doer submits an implementation plan for Critic review."""
        state = self.get_state()
        if not state or not state.get("active"):
            raise ValueError("Agent Table is not active.")

        msg = AgentMessage(
            sender=ROLE_DOER,
            recipient=ROLE_CRITIC,
            msg_type=MessageType.PLAN.value,
            content=plan_content,
            round_number=state["current_round"],
            phase=Phase.PLAN.value,
        )
        self.send_message(msg)
        self._hooks.emit(EVENT_PLAN_SUBMITTED, message=msg, state=state)
        return msg

    def submit_critique(self, critique_content: str, *, approved: bool = False) -> AgentMessage:
        """Critic submits a critique of the Doer's plan or implementation.

        Args:
            critique_content: The critique text.
            approved: Whether the Critic approves the current work.
        """
        state = self.get_state()
        if not state or not state.get("active"):
            raise ValueError("Agent Table is not active.")

        msg = AgentMessage(
            sender=ROLE_CRITIC,
            recipient=ROLE_DOER,
            msg_type=MessageType.CRITIQUE.value,
            content=critique_content,
            round_number=state["current_round"],
            phase=state["current_phase"],
            metadata={"approved": approved},
        )
        self.send_message(msg)
        self._hooks.emit(EVENT_CRITIQUE_SUBMITTED, message=msg, state=state)

        # Auto-escalate if not approved and auto_escalate is on
        if not approved and state.get("auto_escalate"):
            self.escalate(reason="Critic did not approve. Escalating to Arbiter for decision.")

        return msg

    def submit_implementation(self, implementation_notes: str) -> AgentMessage:
        """Doer submits implementation notes after making changes."""
        state = self.get_state()
        if not state or not state.get("active"):
            raise ValueError("Agent Table is not active.")

        msg = AgentMessage(
            sender=ROLE_DOER,
            recipient=ROLE_CRITIC,
            msg_type=MessageType.IMPLEMENTATION.value,
            content=implementation_notes,
            round_number=state["current_round"],
            phase=Phase.IMPLEMENT.value,
        )
        self.send_message(msg)

        # Advance to implement phase
        state = self.get_state()
        state["current_phase"] = Phase.IMPLEMENT.value
        self._save_state(state)

        self._hooks.emit(EVENT_IMPLEMENTATION_SUBMITTED, message=msg, state=state)
        return msg

    def submit_review(self, review_content: str, *, approved: bool = False) -> AgentMessage:
        """Critic submits a review of the Doer's implementation."""
        state = self.get_state()
        if not state or not state.get("active"):
            raise ValueError("Agent Table is not active.")

        msg = AgentMessage(
            sender=ROLE_CRITIC,
            recipient=ROLE_DOER,
            msg_type=MessageType.REVIEW.value,
            content=review_content,
            round_number=state["current_round"],
            phase=Phase.IMPLEMENT.value,
            metadata={"approved": approved},
        )
        self.send_message(msg)
        self._hooks.emit(EVENT_REVIEW_SUBMITTED, message=msg, state=state)

        if not approved and state.get("auto_escalate"):
            self.escalate(reason="Critic did not approve implementation. Escalating to Arbiter.")

        return msg

    def escalate(self, reason: str = "") -> AgentMessage:
        """Escalate to the Arbiter for a final decision."""
        state = self.get_state()
        if not state or not state.get("active"):
            raise ValueError("Agent Table is not active.")

        state["escalation_count"] = state.get("escalation_count", 0) + 1
        state["current_phase"] = Phase.RESOLVE.value
        self._save_state(state)

        msg = AgentMessage(
            sender=ROLE_DOER,
            recipient=ROLE_ARBITER,
            msg_type=MessageType.ESCALATION.value,
            content=reason,
            round_number=state["current_round"],
            phase=Phase.RESOLVE.value,
        )
        result = self.send_message(msg)

        # Record trust event
        self._scoring.record_event(ROLE_CRITIC, "escalation", details=reason)
        self._hooks.emit(EVENT_ESCALATION, message=msg, state=state)

        return result

    def submit_decision(self, decision_content: str, *, side_with: str = "") -> AgentMessage:
        """Arbiter submits a decision resolving a disagreement."""
        state = self.get_state()
        if not state or not state.get("active"):
            raise ValueError("Agent Table is not active.")

        msg = AgentMessage(
            sender=ROLE_ARBITER,
            recipient=ROLE_DOER,
            msg_type=MessageType.DECISION.value,
            content=decision_content,
            round_number=state["current_round"],
            phase=Phase.RESOLVE.value,
            metadata={"side_with": side_with},
        )
        self.send_message(msg)

        # Move to approve phase
        state = self.get_state()
        state["current_phase"] = Phase.APPROVE.value
        self._save_state(state)

        # Track trust — if arbiter overrides critic
        if side_with == ROLE_DOER:
            self._scoring.record_event(
                ROLE_CRITIC,
                "decision",
                aligned_with_outcome=False,
                details="Arbiter sided with doer",
            )
        elif side_with == ROLE_CRITIC:
            self._scoring.record_event(
                ROLE_DOER,
                "decision",
                aligned_with_outcome=False,
                details="Arbiter sided with critic",
            )

        self._hooks.emit(EVENT_DECISION, message=msg, state=state)
        return msg

    def submit_approval(self, notes: str = "") -> AgentMessage:
        """Arbiter gives final approval for the round."""
        state = self.get_state()
        if not state or not state.get("active"):
            raise ValueError("Agent Table is not active.")

        msg = AgentMessage(
            sender=ROLE_ARBITER,
            recipient=ROLE_DOER,
            msg_type=MessageType.APPROVAL.value,
            content=notes or "Approved. Proceed with implementation.",
            round_number=state["current_round"],
            phase=Phase.APPROVE.value,
            metadata={"approved": True},
        )
        self.send_message(msg)

        # Record round summary
        state = self.get_state()
        summary = {
            "round": state["current_round"],
            "outcome": "approved",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        state.setdefault("rounds_summary", []).append(summary)
        self._save_state(state)

        # Trust
        self._scoring.record_event(ROLE_ARBITER, "approval")
        self._hooks.emit(EVENT_APPROVAL, message=msg, state=state)
        self._hooks.emit(EVENT_ROUND_END, state=state)

        return msg

    def submit_rejection(self, reason: str) -> AgentMessage:
        """Arbiter rejects the current approach and requests rework."""
        state = self.get_state()
        if not state or not state.get("active"):
            raise ValueError("Agent Table is not active.")

        msg = AgentMessage(
            sender=ROLE_ARBITER,
            recipient=ROLE_DOER,
            msg_type=MessageType.REJECTION.value,
            content=reason,
            round_number=state["current_round"],
            phase=Phase.APPROVE.value,
            metadata={"approved": False},
        )
        self.send_message(msg)

        # Record round summary
        state = self.get_state()
        summary = {
            "round": state["current_round"],
            "outcome": "rejected",
            "reason": reason,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        state.setdefault("rounds_summary", []).append(summary)
        self._save_state(state)

        # Trust
        self._scoring.record_event(ROLE_ARBITER, "rejection")
        self._hooks.emit(EVENT_REJECTION, message=msg, state=state)
        self._hooks.emit(EVENT_ROUND_END, state=state)

        return msg

    # ------------------------------------------------------------------
    # Finalization
    # ------------------------------------------------------------------

    def finalize(self, outcome: str = "approved") -> Dict[str, Any]:
        """Finalize the Agent Table session."""
        state = self.get_state()
        if not state:
            raise ValueError("No active Agent Table session.")

        state["active"] = False
        state["completed_at"] = datetime.now(timezone.utc).isoformat()
        state["outcome"] = outcome
        self._save_state(state)

        self._hooks.emit(EVENT_TABLE_FINALIZED, state=state, outcome=outcome)
        return state

    def reset(self) -> None:
        """Remove all Agent Table data."""
        if self.table_dir.exists():
            shutil.rmtree(self.table_dir)
        self._hooks.emit(EVENT_TABLE_RESET)

    # ------------------------------------------------------------------
    # Context Building
    # ------------------------------------------------------------------

    def build_doer_context(self) -> str:
        return self._context.build_doer_context()

    def build_critic_context(self) -> str:
        return self._context.build_critic_context()

    def build_arbiter_context(self) -> str:
        return self._context.build_arbiter_context()

    # ------------------------------------------------------------------
    # Full Protocol Round
    # ------------------------------------------------------------------

    def run_protocol_round(
        self,
        plan: str,
        critique: str,
        critique_approved: bool,
        implementation: str = "",
        review: str = "",
        review_approved: bool = False,
        arbiter_decision: str = "",
        arbiter_side_with: str = "",
        arbiter_approves: bool = True,
    ) -> Dict[str, Any]:
        """Run a complete deliberation round programmatically.

        Useful for testing and automated workflows.
        """
        self.new_round()

        # Phase 1: Plan
        self.submit_plan(plan)
        self.submit_critique(critique, approved=critique_approved)

        # If critic approved, proceed to implementation
        if critique_approved and implementation:
            self.submit_implementation(implementation)

            if review:
                self.submit_review(review, approved=review_approved)

        # Arbiter decision (if there was an escalation or at the end)
        if arbiter_decision:
            self.submit_decision(arbiter_decision, side_with=arbiter_side_with)

        # Final approval or rejection
        if arbiter_approves:
            self.submit_approval()
        else:
            self.submit_rejection(arbiter_decision or "Rejected by Arbiter.")

        return self.get_state()

    # ------------------------------------------------------------------
    # Status & Summary
    # ------------------------------------------------------------------

    def status(self) -> Optional[Dict[str, Any]]:
        """Get a human-readable status summary."""
        state = self.get_state()
        if not state:
            return None

        msg_by_sender = self._transcript.count_by_sender()

        return {
            "active": state.get("active", False),
            "task": state.get("task", ""),
            "current_round": state.get("current_round", 0),
            "max_rounds": state.get("max_rounds", 10),
            "current_phase": state.get("current_phase", ""),
            "outcome": state.get("outcome"),
            "total_messages": state.get("total_messages", 0),
            "escalation_count": state.get("escalation_count", 0),
            "messages_by_agent": msg_by_sender,
            "rounds_summary": state.get("rounds_summary", []),
            "started_at": state.get("started_at"),
            "completed_at": state.get("completed_at"),
        }

    def get_transcript_text(self) -> str:
        """Get the full transcript as readable text."""
        return self._transcript.to_text()
