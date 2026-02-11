"""Context builder — generates per-agent markdown context prompts."""

from typing import Any, Dict, List, Optional

from .models import AgentMessage, MessageType
from .roles import ROLE_ARBITER, ROLE_CRITIC, ROLE_DOER


class ContextBuilder:
    """Builds rich context prompts for each agent role.

    The context includes task description, latest messages, history,
    and role-specific instructions.
    """

    def __init__(
        self,
        *,
        get_state: callable,
        get_last_message: callable,
        get_messages: callable,
    ) -> None:
        """
        Args:
            get_state: Callable returning current state dict or None.
            get_last_message: Callable(sender, msg_type) → AgentMessage | None
            get_messages: Callable(**filters) → List[AgentMessage]
        """
        self._get_state = get_state
        self._get_last_message = get_last_message
        self._get_messages = get_messages

    # ------------------------------------------------------------------
    # Doer Context
    # ------------------------------------------------------------------

    def build_doer_context(self) -> str:
        """Build context prompt for the Doer agent.

        Includes: task, latest critique, latest arbiter decision, history.
        """
        state = self._get_state()
        if not state:
            return ""

        parts: List[str] = []
        parts.append(f"# Agent Table — Doer Context (Round {state['current_round']})\n")
        parts.append(f"## Task\n\n{state['task']}\n")
        parts.append(f"## Current Phase: {state['current_phase']}\n")

        # Latest critique
        critique = self._get_last_message(sender=ROLE_CRITIC, msg_type=MessageType.CRITIQUE.value)
        if critique:
            parts.append(f"## Latest Critique from Critic\n\n{critique.content}\n")
            parts.append(f"**Approved:** {critique.metadata.get('approved', False)}\n")

        # Latest review
        review = self._get_last_message(sender=ROLE_CRITIC, msg_type=MessageType.REVIEW.value)
        if review:
            parts.append(f"## Latest Review from Critic\n\n{review.content}\n")
            parts.append(f"**Approved:** {review.metadata.get('approved', False)}\n")

        # Latest arbiter decision
        decision = self._get_last_message(sender=ROLE_ARBITER, msg_type=MessageType.DECISION.value)
        if decision:
            parts.append(f"## Arbiter's Decision\n\n{decision.content}\n")
            parts.append(f"**Sides with:** {decision.metadata.get('side_with', 'N/A')}\n")

        # Approval / rejection
        approval = self._get_last_message(sender=ROLE_ARBITER, msg_type=MessageType.APPROVAL.value)
        rejection = self._get_last_message(sender=ROLE_ARBITER, msg_type=MessageType.REJECTION.value)
        if approval:
            parts.append(f"## ✅ Arbiter Approval\n\n{approval.content}\n")
        if rejection:
            parts.append(f"## ❌ Arbiter Rejection\n\n{rejection.content}\n")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Critic Context
    # ------------------------------------------------------------------

    def build_critic_context(self) -> str:
        """Build context prompt for the Critic agent.

        Includes: task, Doer's latest plan/implementation, history.
        """
        state = self._get_state()
        if not state:
            return ""

        parts: List[str] = []
        parts.append(f"# Agent Table — Critic Context (Round {state['current_round']})\n")
        parts.append(f"## Task\n\n{state['task']}\n")
        parts.append(f"## Current Phase: {state['current_phase']}\n")

        # Latest plan from Doer
        plan = self._get_last_message(sender=ROLE_DOER, msg_type=MessageType.PLAN.value)
        if plan:
            parts.append(f"## Doer's Plan\n\n{plan.content}\n")

        # Latest implementation from Doer
        impl = self._get_last_message(sender=ROLE_DOER, msg_type=MessageType.IMPLEMENTATION.value)
        if impl:
            parts.append(f"## Doer's Implementation\n\n{impl.content}\n")

        # Arbiter's latest decision (for context)
        decision = self._get_last_message(sender=ROLE_ARBITER, msg_type=MessageType.DECISION.value)
        if decision:
            parts.append(f"## Arbiter's Previous Decision\n\n{decision.content}\n")

        parts.append(
            "\n## Your Role\n\n"
            "You are the **Critic**. Review the Doer's work critically.\n"
            "- Identify bugs, logic errors, security issues\n"
            "- Suggest improvements\n"
            "- State clearly if you APPROVE or REJECT\n"
            "- If you reject, explain exactly what needs to change\n"
        )

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Arbiter Context
    # ------------------------------------------------------------------

    def build_arbiter_context(self) -> str:
        """Build context prompt for the Arbiter agent.

        Includes: task, full conversation between Doer and Critic this round.
        """
        state = self._get_state()
        if not state:
            return ""

        parts: List[str] = []
        parts.append(f"# Agent Table — Arbiter Context (Round {state['current_round']})\n")
        parts.append(f"## Task\n\n{state['task']}\n")
        parts.append(f"## Escalation #{state.get('escalation_count', 0)}\n")

        # All messages this round
        round_messages = self._get_messages(round_number=state["current_round"])
        if round_messages:
            parts.append("## Full Conversation This Round\n")
            for msg in round_messages:
                role_emoji = {
                    "doer": "🛠️",
                    "critic": "🔍",
                    "arbiter": "⚖️",
                }.get(msg.sender, "")
                parts.append(f"### {role_emoji} {msg.sender} → " f"{msg.recipient} ({msg.msg_type})\n")
                parts.append(f"{msg.content}\n")

        parts.append(
            "\n## Your Role\n\n"
            "You are the **Arbiter**. You have final authority.\n"
            "- Read both the Doer's work and the Critic's feedback\n"
            "- Make a fair, well-reasoned decision\n"
            "- State which approach is correct and why\n"
            "- Your decision is final — the Doer must follow it\n"
        )

        return "\n".join(parts)
