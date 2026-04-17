"""
Structural completeness tests for council member definitions.

Covers:
  1. All canonical members are defined
  2. Each member has all required definition fields
  3. No member is missing priorities, anti_patterns, or good/bad output signs
  4. Prompts pull from canonical member data (no ad hoc text drift)
  5. Member names are consistent across the codebase
"""
from __future__ import annotations

import pytest

from council.members import ALL_COUNCIL_MEMBERS, MEMBER_BY_NAME, CouncilMember
from council.prompts import build_member_prompts
from models.review_packet import ReviewPacket


CANONICAL_MEMBER_NAMES = {
    "Ben Thompson",
    "April Dunford",
    "Kara Swisher",
    "Marques Brownlee",
    "Andrew Chen",
    "Ethan Mollick",
    "Steve Jobs",
}

REQUIRED_MEMBER_FIELDS = (
    "name",
    "lens",
    "tone",
    "priorities",
    "critique_style",
    "notices_first",
    "deprioritizes",
    "anti_patterns",
    "distinct_from",
    "typical_recommendations",
    "good_output_signs",
    "bad_output_signs",
)


def _minimal_packet() -> ReviewPacket:
    return ReviewPacket(
        artifact_title="Test Artifact",
        artifact_type="PRD",
        goal="Test the prompt build.",
        intended_audience="Internal team",
        context="Test context.",
        specific_questions=["Does this work?"],
        constraints=["Keep it simple."],
        requested_review_mode="single-seat review",
        selected_members=["Ben Thompson"],
        artifact_text="This is the full artifact text for testing purposes.",
    )


# ---------------------------------------------------------------------------
# 1. Canonical member completeness
# ---------------------------------------------------------------------------

class TestCanonicalMemberSet:

    def test_seven_canonical_members_are_defined(self):
        assert len(ALL_COUNCIL_MEMBERS) == 7

    def test_all_canonical_names_are_present(self):
        defined_names = {m.name for m in ALL_COUNCIL_MEMBERS}
        assert defined_names == CANONICAL_MEMBER_NAMES

    def test_member_by_name_index_has_all_members(self):
        assert set(MEMBER_BY_NAME.keys()) == CANONICAL_MEMBER_NAMES

    def test_member_by_name_index_matches_all_council_members(self):
        for member in ALL_COUNCIL_MEMBERS:
            assert MEMBER_BY_NAME[member.name] is member

    def test_no_duplicate_member_names(self):
        names = [m.name for m in ALL_COUNCIL_MEMBERS]
        assert len(names) == len(set(names))


# ---------------------------------------------------------------------------
# 2. Required field presence on each member
# ---------------------------------------------------------------------------

class TestMemberFieldCompleteness:

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_member_has_all_required_fields(self, member: CouncilMember):
        for field in REQUIRED_MEMBER_FIELDS:
            assert hasattr(member, field), f"{member.name} is missing field: {field}"

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_member_name_is_non_empty(self, member: CouncilMember):
        assert member.name.strip(), f"Member has empty name"

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_member_lens_is_non_empty(self, member: CouncilMember):
        assert member.lens.strip(), f"{member.name} has empty lens"

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_member_tone_is_non_empty(self, member: CouncilMember):
        assert member.tone.strip(), f"{member.name} has empty tone"

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_member_critique_style_is_non_empty(self, member: CouncilMember):
        assert member.critique_style.strip(), f"{member.name} has empty critique_style"

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_member_notices_first_is_non_empty(self, member: CouncilMember):
        assert member.notices_first.strip(), f"{member.name} has empty notices_first"

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_member_deprioritizes_is_non_empty(self, member: CouncilMember):
        assert member.deprioritizes.strip(), f"{member.name} has empty deprioritizes"

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_member_distinct_from_is_non_empty(self, member: CouncilMember):
        assert member.distinct_from.strip(), f"{member.name} has empty distinct_from"


# ---------------------------------------------------------------------------
# 3. Tuple fields — minimum length requirements
# ---------------------------------------------------------------------------

class TestMemberTupleFields:

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_priorities_has_at_least_three_items(self, member: CouncilMember):
        assert len(member.priorities) >= 3, (
            f"{member.name} priorities has fewer than 3 items: {member.priorities}"
        )

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_anti_patterns_has_at_least_three_items(self, member: CouncilMember):
        assert len(member.anti_patterns) >= 3, (
            f"{member.name} anti_patterns has fewer than 3 items: {member.anti_patterns}"
        )

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_typical_recommendations_has_at_least_two_items(self, member: CouncilMember):
        assert len(member.typical_recommendations) >= 2, (
            f"{member.name} typical_recommendations has fewer than 2 items"
        )

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_good_output_signs_has_at_least_two_items(self, member: CouncilMember):
        assert len(member.good_output_signs) >= 2, (
            f"{member.name} good_output_signs has fewer than 2 items"
        )

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_bad_output_signs_has_at_least_two_items(self, member: CouncilMember):
        assert len(member.bad_output_signs) >= 2, (
            f"{member.name} bad_output_signs has fewer than 2 items"
        )

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_no_empty_strings_in_priorities(self, member: CouncilMember):
        for item in member.priorities:
            assert item.strip(), f"{member.name} has empty string in priorities"

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_no_empty_strings_in_anti_patterns(self, member: CouncilMember):
        for item in member.anti_patterns:
            assert item.strip(), f"{member.name} has empty string in anti_patterns"

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_no_empty_strings_in_good_output_signs(self, member: CouncilMember):
        for item in member.good_output_signs:
            assert item.strip(), f"{member.name} has empty string in good_output_signs"

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_no_empty_strings_in_bad_output_signs(self, member: CouncilMember):
        for item in member.bad_output_signs:
            assert item.strip(), f"{member.name} has empty string in bad_output_signs"


# ---------------------------------------------------------------------------
# 4. Prompt wiring — prompts pull from canonical member data
# ---------------------------------------------------------------------------

class TestPromptWiring:

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_system_prompt_contains_member_name(self, member: CouncilMember):
        system_prompt, _ = build_member_prompts(member, _minimal_packet())
        assert member.name in system_prompt

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_system_prompt_contains_lens(self, member: CouncilMember):
        system_prompt, _ = build_member_prompts(member, _minimal_packet())
        assert member.lens in system_prompt

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_system_prompt_contains_first_priority(self, member: CouncilMember):
        system_prompt, _ = build_member_prompts(member, _minimal_packet())
        assert member.priorities[0] in system_prompt

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_system_prompt_contains_critique_style(self, member: CouncilMember):
        system_prompt, _ = build_member_prompts(member, _minimal_packet())
        # Critique style is a long string; check a fragment is present
        fragment = member.critique_style[:40]
        assert fragment in system_prompt

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_system_prompt_contains_first_anti_pattern(self, member: CouncilMember):
        system_prompt, _ = build_member_prompts(member, _minimal_packet())
        fragment = member.anti_patterns[0][:30]
        assert fragment in system_prompt

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_user_prompt_contains_artifact_text(self, member: CouncilMember):
        _, user_prompt = build_member_prompts(member, _minimal_packet())
        assert "full artifact text for testing" in user_prompt

    @pytest.mark.parametrize("member", ALL_COUNCIL_MEMBERS, ids=lambda m: m.name)
    def test_system_prompt_is_non_trivially_long(self, member: CouncilMember):
        system_prompt, _ = build_member_prompts(member, _minimal_packet())
        assert len(system_prompt) > 300, (
            f"{member.name} system prompt is suspiciously short: {len(system_prompt)} chars"
        )


# ---------------------------------------------------------------------------
# 5. Lens distinctness — no two members share the same lens string
# ---------------------------------------------------------------------------

class TestLensDistinctness:

    def test_all_member_lenses_are_unique(self):
        lenses = [m.lens for m in ALL_COUNCIL_MEMBERS]
        assert len(lenses) == len(set(lenses)), (
            "Two or more council members share the same lens string"
        )

    def test_all_member_tones_are_unique(self):
        tones = [m.tone for m in ALL_COUNCIL_MEMBERS]
        assert len(tones) == len(set(tones)), (
            "Two or more council members share the same tone string"
        )
