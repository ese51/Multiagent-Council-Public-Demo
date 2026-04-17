from __future__ import annotations

from dataclasses import dataclass


ALLOWED_FINAL_RECOMMENDATIONS = {"go", "revise", "pause", "reject"}


@dataclass(frozen=True)
class MemberReview:
    member_name: str
    overall_judgment: str
    what_is_working: list[str]
    what_is_not_working: list[str]
    what_to_cut: list[str]
    what_to_improve: list[str]
    biggest_question: str
    score: int

    def __post_init__(self) -> None:
        if not self.member_name.strip():
            raise ValueError("MemberReview.member_name must not be empty.")
        if not self.overall_judgment.strip():
            raise ValueError(f"{self.member_name}: overall_judgment must not be empty.")
        if not self.biggest_question.strip():
            raise ValueError(f"{self.member_name}: biggest_question must not be empty.")
        for field_name in ("what_is_working", "what_is_not_working", "what_to_cut", "what_to_improve"):
            items = getattr(self, field_name)
            if not items:
                raise ValueError(f"{self.member_name}: {field_name} must contain at least one item.")
        if not (1 <= self.score <= 5):
            raise ValueError(f"{self.member_name}: score must be between 1 and 5, got {self.score}.")


@dataclass(frozen=True)
class DebateTurn:
    member_name: str
    text: str


@dataclass(frozen=True)
class DebateHighlight:
    topic: str
    participants: list[str]
    exchange: list[DebateTurn]


@dataclass(frozen=True)
class CouncilReviewOutput:
    overall_judgment: str
    strongest_strengths: list[str]
    biggest_weaknesses: list[str]
    recommended_next_move: str
    member_reviews: list[MemberReview]
    agreement_map: list[str]
    disagreement_map: list[str]
    debate_highlights: list[DebateHighlight]
    top_risks: list[str]
    recommended_changes: list[str]
    final_recommendation: str
    suggested_next_draft_focus: str

    def __post_init__(self) -> None:
        if not self.overall_judgment.strip():
            raise ValueError("CouncilReviewOutput.overall_judgment must not be empty.")
        if not self.recommended_next_move.strip():
            raise ValueError("CouncilReviewOutput.recommended_next_move must not be empty.")
        if not self.suggested_next_draft_focus.strip():
            raise ValueError("CouncilReviewOutput.suggested_next_draft_focus must not be empty.")
        if self.final_recommendation not in ALLOWED_FINAL_RECOMMENDATIONS:
            raise ValueError(
                f"final_recommendation must be one of: {', '.join(sorted(ALLOWED_FINAL_RECOMMENDATIONS))}. "
                f"Got: {self.final_recommendation!r}"
            )
        if not self.member_reviews:
            raise ValueError("CouncilReviewOutput.member_reviews must contain at least one review.")
        for field_name in ("strongest_strengths", "biggest_weaknesses", "agreement_map",
                           "disagreement_map", "top_risks", "recommended_changes"):
            items = getattr(self, field_name)
            if not items:
                raise ValueError(f"CouncilReviewOutput.{field_name} must contain at least one item.")

    def to_markdown(self, *, demo_mode: bool = False) -> str:
        lines: list[str] = []
        lines.append("# Council Review Output")
        if demo_mode:
            lines.append("")
            lines.append("> Demo mode: This output was generated from bundled deterministic mock reviewer responses.")
            lines.append("> No live API call was made.")
        lines.append("")
        lines.append("## 1. Executive Summary")
        lines.append(f"- overall judgment: {self.overall_judgment}")
        lines.append("- strongest strengths:")
        for item in self.strongest_strengths:
            lines.append(f"  - {item}")
        lines.append("- biggest weaknesses:")
        for item in self.biggest_weaknesses:
            lines.append(f"  - {item}")
        lines.append(f"- recommended next move: {self.recommended_next_move}")
        lines.append("")
        lines.append("## 2. Per-Member Reviews")
        lines.append("")
        for review in self.member_reviews:
            lines.extend(self._member_review_lines(review))
            lines.append("")
        lines.append("## 3. Agreement Map")
        for item in self.agreement_map:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("## 4. Disagreement Map")
        for item in self.disagreement_map:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("## 5. Debate Highlights")
        if self.debate_highlights:
            for highlight in self.debate_highlights:
                lines.append(f"### Topic")
                lines.append(highlight.topic)
                lines.append("")
                lines.append("- participants: " + ", ".join(highlight.participants))
                lines.append("- exchange:")
                for turn in highlight.exchange:
                    lines.append(f"  - {turn.member_name}: {turn.text}")
                lines.append("")
        else:
            lines.append("- No high-value debate topics were identified.")
            lines.append("")
        lines.append("## 6. Top Risks")
        for item in self.top_risks:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("## 7. Recommended Changes")
        for index, item in enumerate(self.recommended_changes, start=1):
            lines.append(f"{index}. {item}")
        lines.append("")
        lines.append("## 8. Final Recommendation")
        lines.append(self.final_recommendation)
        lines.append("")
        lines.append("## 9. Suggested Next Draft Focus")
        lines.append(self.suggested_next_draft_focus)
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _member_review_lines(review: MemberReview) -> list[str]:
        lines = [
            "### Member Name",
            review.member_name,
            "",
            "### Overall judgment",
            review.overall_judgment,
            "",
            "### What is working",
        ]
        lines.extend([f"- {item}" for item in review.what_is_working])
        lines.extend(["", "### What is not working"])
        lines.extend([f"- {item}" for item in review.what_is_not_working])
        lines.extend(["", "### What to cut"])
        lines.extend([f"- {item}" for item in review.what_to_cut])
        lines.extend(["", "### What to improve"])
        lines.extend([f"- {item}" for item in review.what_to_improve])
        lines.extend(["", "### Biggest question", review.biggest_question, "", "### Score (1-5)", str(review.score)])
        return lines
