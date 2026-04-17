from __future__ import annotations

import re

from council.members import ALL_COUNCIL_MEMBERS, MEMBER_BY_NAME, CouncilMember
from council.prompts import build_debate_prompts, build_member_prompts
from council.synthesize import DebateTopic, MemberReviewResult, identify_debate_topics, synthesize_review
from llm.client import call_llm
from models.review_output import DebateHighlight, DebateTurn, MemberReview
from models.review_packet import ReviewPacket


TAG_KEYWORDS = {
    "sharp_positioning": ("position", "different", "category", "single-model", "single llm"),
    "strict_contract": ("contract", "schema", "field", "format", "structure"),
    "runner_precision": ("runner", "file", "deterministic", "save", "packet"),
    "prd_first": ("prd", "proving ground", "primary validation", "first build"),
    "deterministic_output": ("deterministic", "consistent", "repeatable", "same output"),
    "user_cluster": ("user", "audience", "founder", "writer", "broad audience"),
    "artifact_breadth": ("artifact", "scope", "landing page", "too broad"),
    "needs_revision_lift_bar": ("revision", "shallow", "non-useful", "meaningful revision"),
    "contract_drift_risk": ("drift", "flexible", "interpretation", "inconsistent"),
}


class CouncilRunner:
    def run(self, packet: ReviewPacket):
        members = self._select_members(packet)
        member_results = [self._review_member(member, packet) for member in members]
        debate_topics = identify_debate_topics(member_results)
        debate_highlights = [self._run_debate(topic, packet, member_results) for topic in debate_topics]
        return synthesize_review(member_results, debate_highlights)

    def _select_members(self, packet: ReviewPacket) -> list[CouncilMember]:
        if packet.requested_review_mode == "full council":
            return list(ALL_COUNCIL_MEMBERS)
        return [MEMBER_BY_NAME[name] for name in packet.selected_members]

    def _review_member(
        self,
        member: CouncilMember,
        packet: ReviewPacket,
    ) -> MemberReviewResult:
        system_prompt, user_prompt = build_member_prompts(member, packet)
        raw_response = call_llm(system_prompt, user_prompt)
        review = parse_member_review(member.name, raw_response)
        return MemberReviewResult(review=review, tags=self._derive_tags(review))

    def _run_debate(
        self,
        topic: DebateTopic,
        packet: ReviewPacket,
        member_results: list[MemberReviewResult],
    ) -> DebateHighlight:
        review_by_name = {result.review.member_name: result.review for result in member_results}
        claims_text = self._build_claims_text(topic.participants, review_by_name)
        print(f"debate topic: {topic.topic}")
        print(f"participants: {', '.join(topic.participants[:3])}")
        print(f"claims_text:\n{claims_text}")
        exchange: list[DebateTurn] = []

        for participant_name in topic.participants[:3]:
            member = MEMBER_BY_NAME[participant_name]
            system_prompt, user_prompt = build_debate_prompts(
                member=member,
                packet=packet,
                topic=topic.topic,
                claims_text=claims_text,
            )
            response = call_llm(system_prompt, user_prompt)
            exchange.append(DebateTurn(member_name=participant_name, text=_normalize_text(response)))

        return DebateHighlight(topic=topic.topic, participants=topic.participants[:3], exchange=exchange)

    @staticmethod
    def _build_claims_text(
        participant_names: list[str],
        review_by_name: dict[str, MemberReview],
    ) -> str:
        claims = []
        for name in participant_names:
            review = review_by_name[name]
            claim = _build_claim_from_review(review)
            claims.append(f"- {review.member_name}: {claim}")
        return "\n".join(claims)

    @staticmethod
    def _derive_tags(review: MemberReview) -> list[str]:
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
        tags = []
        for tag, keywords in TAG_KEYWORDS.items():
            if any(keyword in combined for keyword in keywords):
                tags.append(tag)
        return tags


REQUIRED_MEMBER_SECTIONS = [
    "Overall judgment",
    "What is working",
    "What is not working",
    "What to cut",
    "What to improve",
    "Biggest question",
    "Score (1-5)",
]


def parse_member_review(member_name: str, raw_markdown: str) -> MemberReview:
    sections = _split_sections(raw_markdown)
    missing = [name for name in REQUIRED_MEMBER_SECTIONS if name not in sections]
    if missing:
        raise ValueError(f"{member_name} response is missing required sections: {', '.join(missing)}")
    section_keys = list(sections.keys())
    required_positions = [section_keys.index(name) for name in REQUIRED_MEMBER_SECTIONS]
    for i in range(len(required_positions) - 1):
        if required_positions[i] >= required_positions[i + 1]:
            raise ValueError(
                f"{member_name} response has sections out of order: "
                f"'{REQUIRED_MEMBER_SECTIONS[i]}' must appear before '{REQUIRED_MEMBER_SECTIONS[i + 1]}'"
            )
    score_text = sections["Score (1-5)"].strip()
    score = extract_int(score_text)
    if score < 1 or score > 5:
        raise ValueError(f"{member_name} returned an out-of-range score: {score}")
    return MemberReview(
        member_name=member_name,
        overall_judgment=_normalize_text(sections["Overall judgment"]),
        what_is_working=_parse_bullets(sections["What is working"]),
        what_is_not_working=_parse_bullets(sections["What is not working"]),
        what_to_cut=_parse_bullets(sections["What to cut"]),
        what_to_improve=_parse_bullets(sections["What to improve"]),
        biggest_question=_normalize_text(sections["Biggest question"]),
        score=score,
    )


def _split_sections(raw_markdown: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_key: str | None = None
    buffer: list[str] = []
    for line in raw_markdown.splitlines():
        normalized_line = line.strip()
        heading_match = re.match(r"^#+\s+(.*)$", normalized_line)
        if heading_match:
            if current_key is not None:
                sections[current_key] = "\n".join(buffer).strip()
            current_key = _normalize_heading(heading_match.group(1))
            buffer = []
        else:
            buffer.append(line)
    if current_key is not None:
        sections[current_key] = "\n".join(buffer).strip()
    return sections


def _parse_bullets(text: str) -> list[str]:
    items: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        bullet_match = re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)(.+)$", line)
        if bullet_match:
            items.append(_normalize_text(bullet_match.group(1)))
            continue
        if items:
            items[-1] = f"{items[-1]} {_normalize_text(line)}".strip()
        else:
            items.append(_normalize_text(line))
    if not items:
        raise ValueError("Expected bullet list content in member response.")
    return items


def extract_int(value: str) -> int:
    cleaned = _normalize_text(value)
    match = re.search(r"\d+", cleaned)
    if not match:
        raise ValueError(f"Could not extract integer from score field: {value!r}")
    return int(match.group(0))


def _normalize_heading(value: str) -> str:
    return _normalize_text(value).rstrip(":")


def _normalize_text(value: str) -> str:
    cleaned = value.strip()
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"__(.*?)__", r"\1", cleaned)
    cleaned = re.sub(r"`(.*?)`", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _build_claim_from_review(review: MemberReview) -> str:
    if review.what_is_not_working:
        return _to_claim_sentence(review.what_is_not_working[0])
    if review.overall_judgment:
        return _to_claim_sentence(review.overall_judgment)
    return _to_claim_sentence(review.biggest_question)


def _to_claim_sentence(value: str) -> str:
    text = _normalize_text(value)
    text = text.rstrip(".")
    if not text:
        return "No clear claim was provided"
    return text + "."
