"""
Contract and validation tests for Hive Nova Council V1.

Covers:
  1. Packet validation (ReviewPacket.validate + YAML parsing)
  2. Output model validation (CouncilReviewOutput + MemberReview __post_init__)
  3. Member review parsing and required-section ordering (parse_member_review)
  4. Runner-level smoke tests that do not call the LLM
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from council.runner import REQUIRED_MEMBER_SECTIONS, CouncilRunner, parse_member_review
from main import build_output_path
from models.review_output import (
    ALLOWED_FINAL_RECOMMENDATIONS,
    CouncilReviewOutput,
    MemberReview,
)
from models.review_packet import (
    ALLOWED_ARTIFACT_TYPES,
    ALLOWED_REVIEW_MODES,
    ReviewPacket,
    SimpleYamlContractError,
)


# ---------------------------------------------------------------------------
# Shared factories
# ---------------------------------------------------------------------------

def _valid_packet(**overrides) -> ReviewPacket:
    kwargs: dict = dict(
        artifact_title="Test PRD",
        artifact_type="PRD",
        goal="Validate the system works.",
        intended_audience="Internal team",
        context="This is a test context.",
        specific_questions=["Is this working?"],
        constraints=["Keep it simple."],
        requested_review_mode="full council",
        selected_members=[],
        artifact_text="This is the full artifact text.",
    )
    kwargs.update(overrides)
    return ReviewPacket(**kwargs)


def _valid_member_review(**overrides) -> MemberReview:
    kwargs: dict = dict(
        member_name="Ben Thompson",
        overall_judgment="Strong foundation.",
        what_is_working=["Clear scope."],
        what_is_not_working=["Positioning is weak."],
        what_to_cut=["Redundant section."],
        what_to_improve=["Sharpen the ICP definition."],
        biggest_question="Does this differentiate from alternatives?",
        score=3,
    )
    kwargs.update(overrides)
    return MemberReview(**kwargs)


def _valid_output(**overrides) -> CouncilReviewOutput:
    kwargs: dict = dict(
        overall_judgment="Promising but needs work.",
        strongest_strengths=["Clear value proposition."],
        biggest_weaknesses=["Scope creep risk."],
        recommended_next_move="Revise and rerun.",
        member_reviews=[_valid_member_review()],
        agreement_map=["Schema enforcement is needed."],
        disagreement_map=["Ben and Kara disagree on scope."],
        debate_highlights=[],
        top_risks=["Contract drift."],
        recommended_changes=["Tighten contract enforcement."],
        final_recommendation="revise",
        suggested_next_draft_focus="Lock the schema before implementation.",
    )
    kwargs.update(overrides)
    return CouncilReviewOutput(**kwargs)


# Minimal valid YAML that satisfies all packet contract rules.
MINIMAL_VALID_YAML = textwrap.dedent("""\
    artifact_title: Test PRD
    artifact_type: PRD
    goal: Validate the system works.
    intended_audience: Internal team
    context: This is a test context.
    specific_questions:
      - Is this working?
    constraints:
      - Keep it simple.
    requested_review_mode: full council
    selected_members: []
    artifact_text: |
      Full artifact text here.
""")

# Valid LLM-style member review markdown with all required sections in order.
VALID_MEMBER_MARKDOWN = textwrap.dedent("""\
    ## Overall judgment
    Strong foundation but positioning needs work.

    ## What is working
    - Clear scope definition.
    - Solid differentiation claim.

    ## What is not working
    - Audience is too broad.
    - Missing retention story.

    ## What to cut
    - Section 3 is redundant.

    ## What to improve
    - Sharpen the ICP definition.
    - Add a concrete first user example.

    ## Biggest question
    Does this differentiate from ad hoc single-model prompting?

    ## Score (1-5)
    3
""")

# Same sections but "What is working" and "What is not working" are swapped.
OUT_OF_ORDER_MEMBER_MARKDOWN = textwrap.dedent("""\
    ## Overall judgment
    Strong foundation but positioning needs work.

    ## What is not working
    - Audience is too broad.
    - Missing retention story.

    ## What is working
    - Clear scope definition.
    - Solid differentiation claim.

    ## What to cut
    - Section 3 is redundant.

    ## What to improve
    - Sharpen the ICP definition.

    ## Biggest question
    Does this differentiate from ad hoc single-model prompting?

    ## Score (1-5)
    3
""")


# ---------------------------------------------------------------------------
# 1. Packet validation — direct construction + validate()
# ---------------------------------------------------------------------------

class TestPacketValidation:

    def test_valid_full_council_packet_passes(self):
        _valid_packet().validate()

    def test_valid_subset_packet_with_two_members_passes(self):
        _valid_packet(
            requested_review_mode="subset review",
            selected_members=["Ben Thompson", "April Dunford"],
        ).validate()

    def test_valid_single_seat_packet_with_one_member_passes(self):
        _valid_packet(
            requested_review_mode="single-seat review",
            selected_members=["Steve Jobs"],
        ).validate()

    def test_all_allowed_artifact_types_pass(self):
        for artifact_type in ALLOWED_ARTIFACT_TYPES:
            _valid_packet(artifact_type=artifact_type).validate()

    def test_all_allowed_review_modes_pass(self):
        for mode in ALLOWED_REVIEW_MODES:
            selected = (
                []
                if mode == "full council"
                else (
                    ["Ben Thompson"]
                    if mode == "single-seat review"
                    else ["Ben Thompson", "April Dunford"]
                )
            )
            _valid_packet(requested_review_mode=mode, selected_members=selected).validate()

    # --- artifact_type ---

    def test_invalid_artifact_type_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="artifact_type"):
            _valid_packet(artifact_type="landing page").validate()

    def test_unknown_artifact_type_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="artifact_type"):
            _valid_packet(artifact_type="blog post").validate()

    # --- requested_review_mode ---

    def test_invalid_review_mode_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="requested_review_mode"):
            _valid_packet(requested_review_mode="quick review").validate()

    def test_empty_review_mode_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="requested_review_mode"):
            _valid_packet(requested_review_mode="").validate()

    # --- required non-empty string fields ---

    def test_empty_artifact_title_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="artifact_title"):
            _valid_packet(artifact_title="").validate()

    def test_whitespace_only_artifact_title_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="artifact_title"):
            _valid_packet(artifact_title="   ").validate()

    def test_empty_goal_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="goal"):
            _valid_packet(goal="").validate()

    def test_empty_intended_audience_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="intended_audience"):
            _valid_packet(intended_audience="").validate()

    def test_empty_context_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="context"):
            _valid_packet(context="").validate()

    def test_empty_artifact_text_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="artifact_text"):
            _valid_packet(artifact_text="").validate()

    def test_whitespace_only_artifact_text_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="artifact_text"):
            _valid_packet(artifact_text="   \n  ").validate()

    # --- required list fields ---

    def test_empty_specific_questions_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="specific_questions"):
            _valid_packet(specific_questions=[]).validate()

    def test_empty_constraints_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="constraints"):
            _valid_packet(constraints=[]).validate()

    # --- selected_members rules per mode ---

    def test_full_council_with_selected_members_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="selected_members"):
            _valid_packet(
                requested_review_mode="full council",
                selected_members=["Ben Thompson"],
            ).validate()

    def test_subset_review_with_one_member_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="subset review"):
            _valid_packet(
                requested_review_mode="subset review",
                selected_members=["Ben Thompson"],
            ).validate()

    def test_subset_review_with_zero_members_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="subset review"):
            _valid_packet(
                requested_review_mode="subset review",
                selected_members=[],
            ).validate()

    def test_single_seat_with_zero_members_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="single-seat review"):
            _valid_packet(
                requested_review_mode="single-seat review",
                selected_members=[],
            ).validate()

    def test_single_seat_with_two_members_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="single-seat review"):
            _valid_packet(
                requested_review_mode="single-seat review",
                selected_members=["Ben Thompson", "April Dunford"],
            ).validate()

    # --- member name validation ---

    def test_unknown_council_member_rejected(self):
        with pytest.raises(SimpleYamlContractError, match="Unknown council member"):
            _valid_packet(
                requested_review_mode="subset review",
                selected_members=["Unknown Person", "April Dunford"],
            ).validate()

    def test_all_seven_canonical_members_are_valid(self):
        canonical = [
            "Ben Thompson",
            "April Dunford",
            "Kara Swisher",
            "Marques Brownlee",
            "Andrew Chen",
            "Ethan Mollick",
            "Steve Jobs",
        ]
        for name in canonical:
            _valid_packet(
                requested_review_mode="single-seat review",
                selected_members=[name],
            ).validate()


# ---------------------------------------------------------------------------
# 2. Packet validation — YAML parsing layer
# ---------------------------------------------------------------------------

class TestPacketYamlParsing:

    def test_minimal_valid_yaml_loads_successfully(self, tmp_path):
        f = tmp_path / "packet.yaml"
        f.write_text(MINIMAL_VALID_YAML, encoding="utf-8")
        packet = ReviewPacket.from_yaml_file(f)
        assert packet.artifact_type == "PRD"
        assert packet.requested_review_mode == "full council"
        assert packet.artifact_text.strip() == "Full artifact text here."

    def test_missing_required_field_rejected(self, tmp_path):
        yaml_without_goal = MINIMAL_VALID_YAML.replace(
            "goal: Validate the system works.\n", ""
        )
        f = tmp_path / "packet.yaml"
        f.write_text(yaml_without_goal, encoding="utf-8")
        with pytest.raises(SimpleYamlContractError, match="missing keys"):
            ReviewPacket.from_yaml_file(f)

    def test_extra_unknown_field_rejected(self, tmp_path):
        yaml_with_extra = MINIMAL_VALID_YAML + "notes: this field is not in the contract\n"
        f = tmp_path / "packet.yaml"
        f.write_text(yaml_with_extra, encoding="utf-8")
        with pytest.raises(SimpleYamlContractError, match="unknown keys"):
            ReviewPacket.from_yaml_file(f)

    def test_invalid_artifact_type_in_yaml_rejected(self, tmp_path):
        bad_yaml = MINIMAL_VALID_YAML.replace(
            "artifact_type: PRD", "artifact_type: landing page"
        )
        f = tmp_path / "packet.yaml"
        f.write_text(bad_yaml, encoding="utf-8")
        with pytest.raises(SimpleYamlContractError, match="artifact_type"):
            ReviewPacket.from_yaml_file(f)

    def test_sample_packet_file_loads_cleanly(self):
        sample = Path(__file__).parent.parent / "examples" / "sample_packet_prd.yaml"
        packet = ReviewPacket.from_yaml_file(sample)
        assert packet.artifact_type == "PRD"
        assert packet.requested_review_mode == "full council"
        assert len(packet.artifact_text) > 200
        assert packet.artifact_text.startswith("# PRD: Hive Nova Council")


# ---------------------------------------------------------------------------
# 3. MemberReview model validation
# ---------------------------------------------------------------------------

class TestMemberReviewValidation:

    def test_valid_member_review_passes(self):
        _valid_member_review()

    def test_empty_member_name_rejected(self):
        with pytest.raises(ValueError, match="member_name"):
            _valid_member_review(member_name="")

    def test_whitespace_only_member_name_rejected(self):
        with pytest.raises(ValueError, match="member_name"):
            _valid_member_review(member_name="   ")

    def test_empty_overall_judgment_rejected(self):
        with pytest.raises(ValueError, match="overall_judgment"):
            _valid_member_review(overall_judgment="")

    def test_empty_biggest_question_rejected(self):
        with pytest.raises(ValueError, match="biggest_question"):
            _valid_member_review(biggest_question="")

    def test_empty_what_is_working_rejected(self):
        with pytest.raises(ValueError, match="what_is_working"):
            _valid_member_review(what_is_working=[])

    def test_empty_what_is_not_working_rejected(self):
        with pytest.raises(ValueError, match="what_is_not_working"):
            _valid_member_review(what_is_not_working=[])

    def test_empty_what_to_cut_rejected(self):
        with pytest.raises(ValueError, match="what_to_cut"):
            _valid_member_review(what_to_cut=[])

    def test_empty_what_to_improve_rejected(self):
        with pytest.raises(ValueError, match="what_to_improve"):
            _valid_member_review(what_to_improve=[])

    def test_score_0_rejected(self):
        with pytest.raises(ValueError, match="score"):
            _valid_member_review(score=0)

    def test_score_6_rejected(self):
        with pytest.raises(ValueError, match="score"):
            _valid_member_review(score=6)

    def test_score_negative_rejected(self):
        with pytest.raises(ValueError, match="score"):
            _valid_member_review(score=-1)

    def test_score_1_passes(self):
        _valid_member_review(score=1)

    def test_score_5_passes(self):
        _valid_member_review(score=5)

    def test_score_3_passes(self):
        _valid_member_review(score=3)


# ---------------------------------------------------------------------------
# 4. CouncilReviewOutput model validation
# ---------------------------------------------------------------------------

class TestCouncilReviewOutputValidation:

    def test_valid_output_passes(self):
        _valid_output()

    def test_all_allowed_final_recommendations_pass(self):
        for rec in ALLOWED_FINAL_RECOMMENDATIONS:
            _valid_output(final_recommendation=rec)

    def test_invalid_final_recommendation_rejected(self):
        with pytest.raises(ValueError, match="final_recommendation"):
            _valid_output(final_recommendation="maybe")

    def test_capitalised_recommendation_rejected(self):
        with pytest.raises(ValueError, match="final_recommendation"):
            _valid_output(final_recommendation="Revise")

    def test_compound_recommendation_rejected(self):
        # Old bug: "Revise: lock schema enforcement..." was being produced
        with pytest.raises(ValueError, match="final_recommendation"):
            _valid_output(final_recommendation="Revise: lock schema enforcement")

    def test_empty_overall_judgment_rejected(self):
        with pytest.raises(ValueError, match="overall_judgment"):
            _valid_output(overall_judgment="")

    def test_empty_recommended_next_move_rejected(self):
        with pytest.raises(ValueError, match="recommended_next_move"):
            _valid_output(recommended_next_move="")

    def test_empty_suggested_next_draft_focus_rejected(self):
        with pytest.raises(ValueError, match="suggested_next_draft_focus"):
            _valid_output(suggested_next_draft_focus="")

    def test_empty_member_reviews_rejected(self):
        with pytest.raises(ValueError, match="member_reviews"):
            _valid_output(member_reviews=[])

    def test_empty_strongest_strengths_rejected(self):
        with pytest.raises(ValueError, match="strongest_strengths"):
            _valid_output(strongest_strengths=[])

    def test_empty_biggest_weaknesses_rejected(self):
        with pytest.raises(ValueError, match="biggest_weaknesses"):
            _valid_output(biggest_weaknesses=[])

    def test_empty_agreement_map_rejected(self):
        with pytest.raises(ValueError, match="agreement_map"):
            _valid_output(agreement_map=[])

    def test_empty_disagreement_map_rejected(self):
        with pytest.raises(ValueError, match="disagreement_map"):
            _valid_output(disagreement_map=[])

    def test_empty_top_risks_rejected(self):
        with pytest.raises(ValueError, match="top_risks"):
            _valid_output(top_risks=[])

    def test_empty_recommended_changes_rejected(self):
        with pytest.raises(ValueError, match="recommended_changes"):
            _valid_output(recommended_changes=[])

    def test_to_markdown_does_not_crash(self):
        md = _valid_output().to_markdown()
        assert "## 1. Executive Summary" in md
        assert "## 8. Final Recommendation" in md
        assert "revise" in md


# ---------------------------------------------------------------------------
# 5. Member review parsing and section ordering
# ---------------------------------------------------------------------------

class TestMemberReviewParsing:

    def test_valid_markdown_parses_successfully(self):
        review = parse_member_review("Ben Thompson", VALID_MEMBER_MARKDOWN)
        assert review.member_name == "Ben Thompson"
        assert review.score == 3

    def test_overall_judgment_is_extracted(self):
        review = parse_member_review("Ben Thompson", VALID_MEMBER_MARKDOWN)
        assert "Strong foundation" in review.overall_judgment

    def test_bullet_items_are_preserved(self):
        review = parse_member_review("Ben Thompson", VALID_MEMBER_MARKDOWN)
        assert "Clear scope definition." in review.what_is_working
        assert "Audience is too broad." in review.what_is_not_working
        assert "Section 3 is redundant." in review.what_to_cut
        assert "Sharpen the ICP definition." in review.what_to_improve

    def test_biggest_question_is_extracted(self):
        review = parse_member_review("Ben Thompson", VALID_MEMBER_MARKDOWN)
        assert "differentiate" in review.biggest_question.lower()

    def test_out_of_order_sections_rejected(self):
        with pytest.raises(ValueError, match="out of order"):
            parse_member_review("Ben Thompson", OUT_OF_ORDER_MEMBER_MARKDOWN)

    def test_missing_section_rejected(self):
        without_question = "\n".join(
            line
            for line in VALID_MEMBER_MARKDOWN.splitlines()
            if "Biggest question" not in line
            and "Does this differentiate" not in line
        )
        with pytest.raises(ValueError, match="missing required sections"):
            parse_member_review("Ben Thompson", without_question)

    def test_missing_score_section_rejected(self):
        without_score = "\n".join(
            line
            for line in VALID_MEMBER_MARKDOWN.splitlines()
            if "Score" not in line and line.strip() != "3"
        )
        with pytest.raises(ValueError, match="missing required sections"):
            parse_member_review("Ben Thompson", without_score)

    def test_bold_score_accepted(self):
        markdown = VALID_MEMBER_MARKDOWN.replace(
            "## Score (1-5)\n3", "## Score (1-5)\n**4**"
        )
        review = parse_member_review("Ben Thompson", markdown)
        assert review.score == 4

    def test_score_with_contextual_text_accepted(self):
        markdown = VALID_MEMBER_MARKDOWN.replace(
            "## Score (1-5)\n3", "## Score (1-5)\n4 out of 5"
        )
        review = parse_member_review("Ben Thompson", markdown)
        assert review.score == 4

    def test_non_numeric_score_fails(self):
        markdown = VALID_MEMBER_MARKDOWN.replace(
            "## Score (1-5)\n3", "## Score (1-5)\nexcellent"
        )
        with pytest.raises(ValueError):
            parse_member_review("Ben Thompson", markdown)

    def test_extra_name_heading_before_sections_is_tolerated(self):
        with_heading = "# Ben Thompson\n\n" + VALID_MEMBER_MARKDOWN
        review = parse_member_review("Ben Thompson", with_heading)
        assert review.score == 3

    def test_required_sections_list_has_seven_entries(self):
        assert len(REQUIRED_MEMBER_SECTIONS) == 7

    def test_required_sections_starts_with_overall_judgment(self):
        assert REQUIRED_MEMBER_SECTIONS[0] == "Overall judgment"

    def test_required_sections_ends_with_score(self):
        assert REQUIRED_MEMBER_SECTIONS[-1] == "Score (1-5)"


# ---------------------------------------------------------------------------
# 6. Runner smoke tests (no LLM calls)
# ---------------------------------------------------------------------------

class TestRunnerSmoke:

    def test_select_members_full_council_returns_seven(self):
        packet = _valid_packet(requested_review_mode="full council", selected_members=[])
        members = CouncilRunner()._select_members(packet)
        assert len(members) == 7

    def test_select_members_full_council_includes_all_names(self):
        packet = _valid_packet(requested_review_mode="full council", selected_members=[])
        names = {m.name for m in CouncilRunner()._select_members(packet)}
        expected = {
            "Ben Thompson", "April Dunford", "Kara Swisher",
            "Marques Brownlee", "Andrew Chen", "Ethan Mollick", "Steve Jobs",
        }
        assert names == expected

    def test_select_members_subset_returns_named_members_in_order(self):
        packet = _valid_packet(
            requested_review_mode="subset review",
            selected_members=["Ben Thompson", "April Dunford"],
        )
        members = CouncilRunner()._select_members(packet)
        assert len(members) == 2
        assert members[0].name == "Ben Thompson"
        assert members[1].name == "April Dunford"

    def test_select_members_single_seat_returns_exactly_one(self):
        packet = _valid_packet(
            requested_review_mode="single-seat review",
            selected_members=["Steve Jobs"],
        )
        members = CouncilRunner()._select_members(packet)
        assert len(members) == 1
        assert members[0].name == "Steve Jobs"

    def test_build_output_path_replaces_packet_with_output(self):
        result = build_output_path(Path("examples/sample_packet_prd.yaml"))
        assert result.name == "sample_output_prd.md"
        assert result.suffix == ".md"

    def test_build_output_path_appends_review_when_no_packet_in_stem(self):
        result = build_output_path(Path("examples/review_001.yaml"))
        assert result.name == "review_001.review.md"

    def test_build_output_path_preserves_parent_directory(self):
        result = build_output_path(Path("some/dir/my_packet.yaml"))
        assert result.parent == Path("some/dir")
