from __future__ import annotations

from council.prompts import build_debate_prompts, build_member_prompts
from council.runner import parse_member_review
from llm.client import configure_client_mode, call_llm
from models.review_output import CouncilReviewOutput, MemberReview
from models.review_packet import ReviewPacket


def _packet() -> ReviewPacket:
    return ReviewPacket(
        artifact_title="Demo Artifact",
        artifact_type="PRD",
        goal="Verify demo mode.",
        intended_audience="Public users",
        context="Public-safe demo packet.",
        specific_questions=["Does demo mode work?"],
        constraints=["Keep it deterministic."],
        requested_review_mode="full council",
        selected_members=[],
        artifact_text="This is the artifact text used for demo mode tests.",
    )


def test_demo_mode_returns_parseable_member_review():
    packet = _packet()
    member = next(member for member in __import__("council.members", fromlist=["ALL_COUNCIL_MEMBERS"]).ALL_COUNCIL_MEMBERS if member.name == "Ben Thompson")
    system_prompt, user_prompt = build_member_prompts(member, packet)

    configure_client_mode(force_demo=True)
    response = call_llm(system_prompt, user_prompt)
    parsed = parse_member_review(member.name, response)

    assert parsed.member_name == "Ben Thompson"
    assert parsed.overall_judgment.startswith("Demo mode:")
    assert parsed.score == 3


def test_demo_mode_returns_debate_text_without_headers():
    packet = _packet()
    member_module = __import__("council.members", fromlist=["MEMBER_BY_NAME"])
    member = member_module.MEMBER_BY_NAME["April Dunford"]
    system_prompt, user_prompt = build_debate_prompts(
        member=member,
        packet=packet,
        topic="Is the user definition too broad?",
        claims_text="- April Dunford: The target user is still broad.\n- Kara Swisher: The message is too polite.",
    )

    configure_client_mode(force_demo=True)
    response = call_llm(system_prompt, user_prompt)

    assert "Demo mode:" in response
    assert "April Dunford" in response
    assert "##" not in response


def test_markdown_can_label_demo_mode():
    output = CouncilReviewOutput(
        overall_judgment="Promising but needs work.",
        strongest_strengths=["Clear value proposition."],
        biggest_weaknesses=["Scope creep risk."],
        recommended_next_move="Revise and rerun.",
        member_reviews=[
            MemberReview(
                member_name="Ben Thompson",
                overall_judgment="Strong foundation.",
                what_is_working=["Clear scope."],
                what_is_not_working=["Positioning is weak."],
                what_to_cut=["Redundant section."],
                what_to_improve=["Sharpen the ICP definition."],
                biggest_question="Does this differentiate from alternatives?",
                score=3,
            )
        ],
        agreement_map=["Schema enforcement is needed."],
        disagreement_map=["Ben and Kara disagree on scope."],
        debate_highlights=[],
        top_risks=["Contract drift."],
        recommended_changes=["Tighten contract enforcement."],
        final_recommendation="revise",
        suggested_next_draft_focus="Lock the schema before implementation.",
    )

    markdown = output.to_markdown(demo_mode=True)
    assert "Demo mode:" in markdown
    assert "No live API call was made." in markdown
