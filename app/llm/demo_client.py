from __future__ import annotations

import re


def call_demo_llm(system_prompt: str, user_prompt: str) -> str:
    if "structured council debate" in system_prompt.lower():
        return _build_demo_debate(system_prompt, user_prompt)
    return _build_demo_member_review(system_prompt, user_prompt)


def _build_demo_member_review(system_prompt: str, user_prompt: str) -> str:
    member_name = _extract_member_name(system_prompt)
    artifact_title = _extract_artifact_title(user_prompt)

    templates = {
        "Ben Thompson": {
            "overall": (
                f"Demo mode: {artifact_title} addresses a real problem, but the business shape is still softer "
                "than the workflow description. The concept needs a narrower wedge and a clearer reason this becomes "
                "a product instead of a feature."
            ),
            "working": [
                "The artifact identifies a real workflow pain instead of inventing a speculative AI use case.",
                "The draft shows useful scope discipline and avoids trying to launch every adjacent feature at once.",
            ],
            "not_working": [
                "The strategic wedge is still broad, which weakens defensibility in the first release.",
                "The artifact does not fully explain why the value capture mechanism becomes durable over time.",
            ],
            "cut": [
                "Cut secondary scope that does not strengthen the first user wedge.",
            ],
            "improve": [
                "Define the single highest-value buyer and the exact repeated workflow that makes the product sticky.",
                "Clarify why this should stand alone rather than living inside an existing tool.",
            ],
            "question": "What is the durable strategic wedge if a larger platform adds the same workflow?",
            "score": 3,
        },
        "April Dunford": {
            "overall": (
                f"Demo mode: {artifact_title} has a plausible message, but the positioning is still under-specified. "
                "The best-fit customer and the real alternative are not yet sharp enough."
            ),
            "working": [
                "The draft names a useful job-to-be-done rather than relying on abstract innovation language.",
                "There is enough structure to begin defining a credible category and differentiated value claim.",
            ],
            "not_working": [
                "The target user is still broader than a crisp best-fit customer.",
                "The competitive alternative is implied rather than named directly.",
            ],
            "cut": [
                "Cut blended audience language that tries to serve adjacent buyers at the same time.",
            ],
            "improve": [
                "State the exact alternative the buyer uses today.",
                "Rewrite the value claim so differentiation is expressed as customer value instead of generic features.",
            ],
            "question": "Who is the one best-fit customer for V1, and what are they comparing this against?",
            "score": 3,
        },
        "Kara Swisher": {
            "overall": (
                f"Demo mode: {artifact_title} is cleaner than most early AI-adjacent drafts, but it still avoids the "
                "hard choice about who it is for and what claim really matters."
            ),
            "working": [
                "The artifact mostly avoids inflated magic-language and reads as grounded.",
                "The scope is contained enough that the concept does not feel like platform cosplay.",
            ],
            "not_working": [
                "The audience language is still too polite and broad to sound decisive.",
                "Some of the value language sounds competent rather than urgent or memorable.",
            ],
            "cut": [
                "Cut generic market language that could describe dozens of productivity tools.",
            ],
            "improve": [
                "Replace soft convenience language with the sharper consequence of the current problem.",
                "Make one harder editorial choice about who the launch is actually for.",
            ],
            "question": "What is the one sentence a skeptical reader would remember after seeing this?",
            "score": 3,
        },
        "Marques Brownlee": {
            "overall": (
                f"Demo mode: {artifact_title} earns baseline trust and clarity, but it still needs a stronger first "
                "impression to feel distinctive."
            ),
            "working": [
                "The artifact is readable and does not feel chaotic.",
                "The current scope signals discipline rather than feature sprawl.",
            ],
            "not_working": [
                "The opening still feels slightly broad, which softens the first impression.",
                "The value claim is believable, but not yet memorable enough to stand out.",
            ],
            "cut": [
                "Cut generic launch language that does not improve trust or comprehension.",
            ],
            "improve": [
                "Make the opening sentence more concrete and user-specific.",
                "Tighten the main claim so a smart first-time reader instantly understands why it matters.",
            ],
            "question": "Would a skeptical, smart reader understand the exact use case within seconds?",
            "score": 4,
        },
        "Andrew Chen": {
            "overall": (
                f"Demo mode: {artifact_title} has a believable first-use case, but the repeat behavior and retention "
                "logic are still implied more than designed."
            ),
            "working": [
                "The artifact points to a recurring workflow rather than a one-time novelty action.",
                "The first release is operationally light enough to improve adoption odds.",
            ],
            "not_working": [
                "The retention loop is not explicit yet.",
                "The artifact does not say enough about what makes users return after the first successful run.",
            ],
            "cut": [
                "Cut future complexity until the repeat usage pattern is clearly validated.",
            ],
            "improve": [
                "Define the recurring trigger that brings users back.",
                "Name the habit or workflow signal that proves this is becoming part of normal behavior.",
            ],
            "question": "What keeps the user coming back after the first successful output?",
            "score": 3,
        },
        "Ethan Mollick": {
            "overall": (
                f"Demo mode: {artifact_title} is reasonably practical and avoids overclaiming, but it still needs a "
                "clearer description of what the system does reliably versus what the human must still own."
            ),
            "working": [
                "The draft stays grounded in a realistic workflow.",
                "The artifact leaves room for human judgment instead of pretending the system is autonomous.",
            ],
            "not_working": [
                "The handoff between system output and human review could be more explicit.",
                "Some quality expectations are still subjective instead of operationally defined.",
            ],
            "cut": [
                "Cut any implication that the system can replace judgment-heavy editing on its own.",
            ],
            "improve": [
                "Clarify what the system is consistently good at producing.",
                "Add one concrete example that shows where human review still improves the result.",
            ],
            "question": "What output quality is realistic to expect before human review steps in?",
            "score": 4,
        },
        "Steve Jobs": {
            "overall": (
                f"Demo mode: {artifact_title} has the right instinct toward simplicity, but it still needs more ruthless "
                "focus and a stronger standard for what makes the result excellent."
            ),
            "working": [
                "The concept does one understandable job instead of trying to be a full platform.",
                "The current direction is simple enough to refine into something sharp.",
            ],
            "not_working": [
                "The user definition is still too loose.",
                "The artifact talks about speed more clearly than it talks about quality.",
            ],
            "cut": [
                "Cut anything that dilutes the one core user and the one core outcome.",
            ],
            "improve": [
                "Make the promise more opinionated.",
                "Define what a great end result looks like, not just how quickly it appears.",
            ],
            "question": "What is the one thing this system should do exceptionally well?",
            "score": 3,
        },
    }

    template = templates[member_name]
    return _format_member_review(member_name=member_name, **template)


def _build_demo_debate(system_prompt: str, user_prompt: str) -> str:
    speaker = _extract_debate_speaker(system_prompt)
    participants = _extract_participants(user_prompt)
    target = next((name for name in participants if name != speaker), participants[0] if participants else "the prior reviewer")
    topic = _extract_topic(user_prompt)
    return (
        f"Demo mode: {speaker} is responding to {target}'s claim about {topic.lower()}. "
        f"{target} is directionally right, but the sharper conclusion is that the artifact still needs one more pass "
        "on focus before the council should treat it as fully ready.\n\n"
        "The council should conclude that the concept is promising, but the next revision needs to tighten the buyer, "
        "scope, or operating logic before confidence is warranted."
    )


def _format_member_review(
    member_name: str,
    overall: str,
    working: list[str],
    not_working: list[str],
    cut: list[str],
    improve: list[str],
    question: str,
    score: int,
) -> str:
    lines = [
        "### Overall judgment",
        overall,
        "",
        "### What is working",
        *[f"- {item}" for item in working],
        "",
        "### What is not working",
        *[f"- {item}" for item in not_working],
        "",
        "### What to cut",
        *[f"- {item}" for item in cut],
        "",
        "### What to improve",
        *[f"- {item}" for item in improve],
        "",
        "### Biggest question",
        question,
        "",
        "### Score (1-5)",
        str(score),
    ]
    return "\n".join(lines)


def _extract_member_name(system_prompt: str) -> str:
    match = re.search(r"Member name:\s*(.+)", system_prompt)
    if match:
        return match.group(1).strip()
    raise ValueError("Could not determine council member name for demo mode.")


def _extract_artifact_title(user_prompt: str) -> str:
    match = re.search(r"artifact_title:\s*(.+)", user_prompt)
    if match:
        return match.group(1).strip()
    return "this artifact"


def _extract_debate_speaker(system_prompt: str) -> str:
    match = re.search(r"You are (.+?)\.", system_prompt)
    if match:
        return match.group(1).strip()
    return "The speaker"


def _extract_participants(user_prompt: str) -> list[str]:
    return re.findall(r"- ([^:\n]+):", user_prompt)


def _extract_topic(user_prompt: str) -> str:
    match = re.search(r"Debate topic:\n(.+?)\n\nParticipants", user_prompt, flags=re.DOTALL)
    if match:
        return " ".join(match.group(1).split())
    return "the main disagreement"
