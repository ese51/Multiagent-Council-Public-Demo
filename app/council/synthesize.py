from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from models.review_output import CouncilReviewOutput, DebateHighlight, MemberReview


@dataclass(frozen=True)
class MemberReviewResult:
    review: MemberReview
    tags: list[str]


@dataclass(frozen=True)
class DebateTopic:
    topic: str
    participants: list[str]


TAG_LABELS = {
    "sharp_positioning": "The differentiation is clear enough to separate Hive Nova Council from ordinary single-model prompting.",
    "strict_contract": "The packet and output contracts are rigid enough to keep the first build from drifting.",
    "runner_precision": "The runner behavior is explicit enough to implement without inventing missing rules.",
    "prd_first": "PRDs are correctly treated as the primary proving ground for the first build.",
    "deterministic_output": "Saved output behavior is deterministic and implementation-friendly.",
    "user_cluster": "The target user is still broader than the first build actually needs.",
    "artifact_breadth": "Even in V1, the artifact list is wider than the first proving cycle requires.",
    "needs_revision_lift_bar": "The quality bar still depends on proving real revision lift, not just structured output.",
    "contract_drift_risk": "Any deviation from the packet or output contracts will create implementation drift.",
}


def synthesize_review(
    member_results: Iterable[MemberReviewResult],
    debate_highlights: list[DebateHighlight],
) -> CouncilReviewOutput:
    results = list(member_results)
    reviews = [result.review for result in results]
    average_score = sum(review.score for review in reviews) / len(reviews)
    tag_counts = Counter(tag for result in results for tag in result.tags)

    strongest_strengths = []
    biggest_weaknesses = []

    strengths_counter = Counter(item for review in reviews for item in review.what_is_working)
    weaknesses_counter = Counter(item for review in reviews for item in review.what_is_not_working)
    primary_debate = _select_primary_debate(debate_highlights)
    issue_signals = _collect_issue_signals(reviews, debate_highlights)

    strongest_strengths.extend(_top_items(strengths_counter, 3))
    biggest_weaknesses.extend(_top_items(weaknesses_counter, 3))
    top_risks = _build_top_risks(issue_signals)
    recommended_changes = _build_recommended_changes(issue_signals)

    agreement_map = [TAG_LABELS[tag] for tag, count in tag_counts.items() if count >= 2 and tag in TAG_LABELS]
    disagreement_map = _build_disagreement_map(debate_highlights)
    final_recommendation = _build_final_recommendation(average_score, primary_debate, top_risks, recommended_changes)
    next_focus = _build_next_focus(recommended_changes, top_risks)

    return CouncilReviewOutput(
        overall_judgment=_build_overall_judgment(average_score),
        strongest_strengths=strongest_strengths[:3] or ["The review surfaced clear strengths, but the strongest themes were not repeated verbatim across members."],
        biggest_weaknesses=biggest_weaknesses[:3] or ["The review surfaced weaknesses, but the members emphasized different problems."],
        recommended_next_move=_build_recommended_next_move(final_recommendation),
        member_reviews=reviews,
        agreement_map=agreement_map[:6] or ["No cross-member agreement patterns were strong enough to surface a clear consensus point."],
        disagreement_map=disagreement_map[:3] or ["No strong disagreement patterns were identified across the selected members."],
        debate_highlights=debate_highlights[:4],
        top_risks=top_risks[:5] or ["No dominant risk signal was identified; review individual member concerns for the most relevant issues."],
        recommended_changes=recommended_changes[:5] or ["Review individual member sections for the highest-leverage revision targets."],
        final_recommendation=final_recommendation,
        suggested_next_draft_focus=next_focus,
    )


def _top_items(counter: Counter[str], limit: int) -> list[str]:
    return [item for item, _count in counter.most_common(limit) if item]


def _build_overall_judgment(average_score: float) -> str:
    if average_score >= 4.5:
        return "The artifact is strong and close to build-ready, with only narrow issues left to resolve."
    if average_score >= 4.0:
        return "The artifact is solid but still has issues that should be tightened before or during implementation."
    if average_score >= 3.0:
        return "The artifact is promising but still has meaningful weaknesses that need revision."
    return "The artifact is not ready. The current weaknesses are too significant to ignore."


def _build_recommended_next_move(final_recommendation: str) -> str:
    if final_recommendation == "go":
        return "Proceed, but use the review to tighten the most repeated weaknesses before momentum creates drift."
    if final_recommendation == "revise":
        return "Revise the artifact on the most repeated issues, then rerun the council."
    if final_recommendation == "pause":
        return "Pause implementation and resolve the core contradictions before moving forward."
    return "Do not proceed until the underlying problems are addressed."


def identify_debate_topics(member_results: Iterable[MemberReviewResult]) -> list[DebateTopic]:
    results = list(member_results)
    reviews = [result.review for result in results]
    member_by_name = {review.member_name: review for review in reviews}
    score_range = max(review.score for review in reviews) - min(review.score for review in reviews) if reviews else 0
    topics: list[DebateTopic] = []

    if score_range >= 1:
        highest = max(reviews, key=lambda review: review.score)
        lowest = min(reviews, key=lambda review: review.score)
        participants = _unique_names([highest.member_name, lowest.member_name, "Kara Swisher"], member_by_name)
        if len(participants) >= 2:
            topics.append(
                DebateTopic(
                    topic="Is this artifact ready to act on now, or does it still need another revision cycle?",
                    participants=participants[:3],
                )
            )

    audience_participants = _find_participants(
        member_by_name,
        preferred=("April Dunford", "Ben Thompson", "Ethan Mollick"),
        keywords=("user", "audience", "for whom", "operator", "broad"),
    )
    if len(audience_participants) >= 2:
        topics.append(
            DebateTopic(
                topic="Is the first user clear enough, or is the positioning still too broad for a sharp first build?",
                participants=audience_participants[:3],
            )
        )

    contract_participants = _find_participants(
        member_by_name,
        preferred=("Marques Brownlee", "Ethan Mollick", "Steve Jobs"),
        keywords=("contract", "runner", "schema", "deterministic", "drift", "file"),
    )
    if len(contract_participants) >= 2:
        topics.append(
            DebateTopic(
                topic="How rigid does the runner and contract enforcement need to be for V1 to avoid implementation drift?",
                participants=contract_participants[:3],
            )
        )

    scope_participants = _find_participants(
        member_by_name,
        preferred=("Andrew Chen", "Steve Jobs", "Ben Thompson"),
        keywords=("scope", "landing page", "prds", "first build", "proving ground", "too broad"),
    )
    if len(scope_participants) >= 2:
        topics.append(
            DebateTopic(
                topic="Should the first proving ground stay tightly centered on PRDs, or is the current scope already disciplined enough?",
                participants=scope_participants[:3],
            )
        )

    deduped: list[DebateTopic] = []
    seen_topics: set[str] = set()
    for topic in topics:
        if topic.topic not in seen_topics:
            deduped.append(topic)
            seen_topics.add(topic.topic)
    return deduped[:4]


def _find_participants(
    member_by_name: dict[str, MemberReview],
    preferred: tuple[str, ...],
    keywords: tuple[str, ...],
) -> list[str]:
    matches = []
    for name in preferred:
        review = member_by_name.get(name)
        if not review:
            continue
        combined = " ".join(
            [
                review.overall_judgment,
                *review.what_is_working,
                *review.what_is_not_working,
                *review.what_to_cut,
                *review.what_to_improve,
                review.biggest_question,
            ]
        ).lower()
        if any(keyword in combined for keyword in keywords):
            matches.append(name)
    return matches


def _unique_names(names: list[str], member_by_name: dict[str, MemberReview]) -> list[str]:
    seen: set[str] = set()
    unique = []
    for name in names:
        if name in member_by_name and name not in seen:
            unique.append(name)
            seen.add(name)
    return unique


def _build_disagreement_map(debate_highlights: list[DebateHighlight]) -> list[str]:
    items = []
    for highlight in debate_highlights:
        if len(highlight.exchange) >= 2:
            items.append(_summarize_disagreement(highlight))
        else:
            items.append(f"{highlight.topic} Multiple members see the issue differently enough to warrant direct debate.")
    return items[:4]


def _build_top_risks(issue_signals: list[tuple[str, str]]) -> list[str]:
    risks = []
    seen = set()
    for issue_key, statement in issue_signals:
        if issue_key not in seen:
            risks.append(statement)
            seen.add(issue_key)
    return risks[:5]


def _build_recommended_changes(issue_signals: list[tuple[str, str]]) -> list[str]:
    change_map = {
        "contract_drift": "Enforce packet and output schemas at the runner level so the implementation cannot drift.",
        "positioning_blur": "Define one primary first user so the product direction stays narrow and testable.",
        "scope_leak": "Cut secondary validation scope until PRD reviews are consistently strong.",
        "revision_lift": "Raise the acceptance bar so reviews must change the next draft, not just fill the schema.",
        "readiness_tension": "Decide whether the artifact is ready to act on now or needs one more revision cycle before the next run.",
    }
    changes = []
    seen = set()
    for issue_key, _statement in issue_signals:
        change = change_map.get(issue_key)
        if change and change not in seen:
            changes.append(change)
            seen.add(change)
    return changes[:5]


def _build_final_recommendation(
    average_score: float,
    primary_debate: DebateHighlight | None,
    top_risks: list[str],
    recommended_changes: list[str],
) -> str:
    strong_tension = bool(primary_debate and _exchange_contains_challenge(primary_debate))
    if primary_debate:
        topic_lower = primary_debate.topic.lower()
        if "ready to act" in topic_lower or "revision cycle" in topic_lower:
            return "revise"
        if strong_tension:
            return "revise"
    if average_score >= 4.2 and not strong_tension:
        return "go"
    if average_score >= 3.0:
        return "revise"
    return "pause"


def _build_next_focus(recommended_changes: list[str], top_risks: list[str]) -> str:
    if recommended_changes:
        return recommended_changes[0]
    if top_risks:
        return top_risks[0]
    return "Tighten the most repeated weakness before the next run."


def _combined_review_text(reviews: list[MemberReview]) -> str:
    return " ".join(
        " ".join(
            [
                review.overall_judgment,
                *review.what_is_working,
                *review.what_is_not_working,
                *review.what_to_cut,
                *review.what_to_improve,
                review.biggest_question,
            ]
        ).lower()
        for review in reviews
    )


def _debate_text(highlight: DebateHighlight) -> str:
    return " ".join(turn.text for turn in highlight.exchange)


def _exchange_contains_challenge(highlight: DebateHighlight) -> bool:
    combined = _debate_text(highlight).lower()
    challenge_markers = ("but", "however", "wrong", "misses", "underestimates", "overstates", "not enough", "too broad")
    return any(marker in combined for marker in challenge_markers)


def _select_primary_debate(debate_highlights: list[DebateHighlight]) -> DebateHighlight | None:
    if not debate_highlights:
        return None
    ranked = sorted(
        debate_highlights,
        key=lambda highlight: (
            1 if _exchange_contains_challenge(highlight) else 0,
            len(highlight.exchange),
            len(_debate_text(highlight)),
        ),
        reverse=True,
    )
    return ranked[0]


def _summarize_disagreement(highlight: DebateHighlight) -> str:
    if len(highlight.exchange) < 2:
        return f"{highlight.topic} Multiple members see the issue differently enough to warrant direct debate."
    first = highlight.exchange[0].member_name
    second = highlight.exchange[1].member_name
    topic = highlight.topic.rstrip("?")
    return f"{first} and {second} disagree on {topic.lower()}, and that conflict materially affects the next decision."


def _collect_issue_signals(
    reviews: list[MemberReview],
    debate_highlights: list[DebateHighlight],
) -> list[tuple[str, str]]:
    combined_text = _combined_review_text(reviews) + " " + " ".join(_debate_text(highlight) for highlight in debate_highlights)
    issue_map = {
        "contract_drift": (
            ("contract", "schema", "field", "format", "runner", "deterministic", "drift", "file"),
            "Schema enforcement is not operationalized tightly enough, risking implementation drift.",
        ),
        "positioning_blur": (
            ("user", "audience", "operator", "broad", "position", "category"),
            "The first user is still not defined sharply enough, weakening product positioning and decision quality.",
        ),
        "scope_leak": (
            ("scope", "landing page", "artifact", "too broad", "proving ground", "first build"),
            "Primary validation scope is still vulnerable to expansion, which could dilute early learning.",
        ),
        "revision_lift": (
            ("revision", "shallow", "non-useful", "generic", "meaningful revision", "structured but shallow"),
            "The system still risks producing structured but non-decision-driving feedback, which would make the council look smarter than it is useful.",
        ),
        "readiness_tension": (
            ("ready", "revision cycle", "build now", "not ready", "act on now"),
            "Council disagreement on readiness indicates unresolved tension about whether the artifact is tight enough to move forward cleanly.",
        ),
    }
    ordered = []
    for issue_key, (keywords, statement) in issue_map.items():
        if any(keyword in combined_text for keyword in keywords):
            ordered.append((issue_key, statement))
    primary_debate = _select_primary_debate(debate_highlights)
    if primary_debate and _exchange_contains_challenge(primary_debate):
        topic = primary_debate.topic.lower()
        if "contract" in topic or "drift" in topic or "runner" in topic:
            _promote_issue(ordered, "contract_drift")
        elif "user" in topic or "positioning" in topic:
            _promote_issue(ordered, "positioning_blur")
        elif "proving ground" in topic or "scope" in topic:
            _promote_issue(ordered, "scope_leak")
        elif "ready to act" in topic or "revision cycle" in topic:
            _promote_issue(ordered, "readiness_tension")
    return ordered


def _promote_issue(ordered: list[tuple[str, str]], issue_key: str) -> None:
    for index, (existing_key, statement) in enumerate(ordered):
        if existing_key == issue_key:
            ordered.insert(0, ordered.pop(index))
            return
