from __future__ import annotations

from council.members import CouncilMember
from models.review_packet import ReviewPacket


def _format_packet_context(packet: ReviewPacket) -> str:
    return (
        f"artifact_title: {packet.artifact_title}\n"
        f"artifact_type: {packet.artifact_type}\n"
        f"goal: {packet.goal}\n"
        f"intended_audience: {packet.intended_audience}\n"
        f"context:\n{packet.context}\n\n"
        "specific_questions:\n"
        + "\n".join(f"- {item}" for item in packet.specific_questions)
        + "\n\nconstraints:\n"
        + "\n".join(f"- {item}" for item in packet.constraints)
        + "\n\nartifact_text:\n"
        + packet.artifact_text
    )


def _format_anti_patterns(anti_patterns: tuple[str, ...]) -> str:
    return "\n".join(f"- Do NOT: {p}" for p in anti_patterns)


def build_member_prompts(member: CouncilMember, packet: ReviewPacket) -> tuple[str, str]:
    system_prompt = (
        "You are simulating one council member only.\n"
        f"Member name: {member.name}\n"
        f"Lens: {member.lens}\n"
        f"Priorities: {', '.join(member.priorities)}\n\n"
        f"Critique style:\n{member.critique_style}\n\n"
        f"What you notice first:\n{member.notices_first}\n\n"
        f"What you deprioritize:\n{member.deprioritizes}\n\n"
        "Stay in your lane. Do not drift into the lens of other council members.\n\n"
        f"Anti-patterns — output failures that mean you have broken character:\n"
        f"{_format_anti_patterns(member.anti_patterns)}\n\n"
        "You are not here to summarize or be polite. You are here to critique.\n"
        "If your feedback could apply to any artifact, it is wrong.\n"
        "If you do not identify at least one thing that should be cut, you have failed.\n"
        "Be specific. Reference exact parts of the artifact. Avoid general statements.\n"
        "You must reference at least 2 specific elements from the artifact.\n\n"
        "Return structured markdown using these exact headings and no others:\n"
        "### Overall judgment\n"
        "### What is working\n"
        "### What is not working\n"
        "### What to cut\n"
        "### What to improve\n"
        "### Biggest question\n"
        "### Score (1-5)\n\n"
        "Rules for output:\n"
        "- Under the list sections, use bullet points.\n"
        "- Score must be a single integer from 1 to 5.\n"
        "- Return the score as a plain integer with no formatting, no markdown, and no extra text.\n"
        "- Do not add introductions, summaries, preambles, or closing remarks.\n"
        "- Do not say things like 'this could be clearer' or 'consider improving'. Replace vague feedback with specific critique.\n"
        "- If your critique is generic, could apply to any artifact, or avoids making hard judgments, you have failed.\n"
        "- Be specific to this artifact. Call out weak assumptions. Identify what should be cut, not just improved."
    )

    user_prompt = _format_packet_context(packet)
    return system_prompt, user_prompt


def build_debate_prompts(
    member: CouncilMember,
    packet: ReviewPacket,
    topic: str,
    claims_text: str,
) -> tuple[str, str]:
    system_prompt = (
        "You are participating in a structured council debate.\n\n"
        f"Your role:\n"
        f"You are {member.name}. Speak from your distinct lens.\n"
        f"Lens: {member.lens}\n"
        f"Priorities: {', '.join(member.priorities)}\n\n"
        f"What you notice first: {member.notices_first}\n\n"
        "Your job:\n"
        "Resolve the disagreement by directly engaging one specific participant's claim and pushing the council toward a decision.\n\n"
        "Rules:\n"
        "1. You MUST choose one claim from the list above.\n"
        "2. You MUST explicitly name the participant.\n"
        "3. You MUST quote or clearly restate the exact claim you are responding to.\n"
        "4. You MUST do one of the following:\n"
        "   - Challenge the claim and explain why it is wrong, incomplete, or based on a weak assumption, OR\n"
        "   - Defend the claim against another participant's implied or stated position.\n"
        "5. You MUST make a clear judgment about the claim: correct, partially correct, or wrong.\n"
        "6. Do NOT restate your full original review.\n"
        "7. Stay strictly on the disagreement relevant to this topic.\n"
        "8. Be concise, sharp, and opinionated.\n"
        "9. Do NOT give a neutral synthesis.\n"
        "10. Do NOT say everyone is partly right unless you identify a decisive winner.\n"
        "11. If another participant is missing the real issue, say so directly.\n"
        "12. End with one decisive sentence stating what the council should conclude on this disagreement.\n\n"
        "Output format:\n"
        "- 1–2 short paragraphs\n"
        "- No bullet points\n"
        "- No section headers\n"
        "- Must include the referenced participant's name\n"
    )

    user_prompt = (
        f"Debate topic:\n{topic}\n\n"
        f"Participants and their claims:\n{claims_text}\n\n"
        "Choose one claim from the list above and respond directly to it.\n"
        "Name the participant explicitly.\n"
        "Quote or clearly restate the claim before you challenge or extend it.\n\n"
        "Artifact context:\n"
        f"{_format_packet_context(packet)}"
    )

    return system_prompt, user_prompt
