# PRD: Hive Nova Council

## Executive Summary

Hive Nova Council is a structured review engine for written artifacts. It runs one artifact through distinct council lenses and returns actionable critique in a fixed format.

V1 exists to do one job well: review artifacts with clear, non-generic feedback that helps the next draft improve. The product is not a chatbot, not an autonomous decision-maker, and not a broad AI platform.

The first version should be simple enough to run immediately from the CLI.

## Contract Authority

The authoritative contract documents are:
- **`docs/COUNCIL_REVIEW_PACKET_TEMPLATE.md`** — packet field requirements, allowed values, and rejection rules
- **`docs/COUNCIL_OUTPUT_SCHEMA.md`** — output section requirements, field requirements, ordering rules, and rejection criteria

These documents are the enforcement source of truth. The PRD defines scope, positioning, and quality criteria. If any rule appears in both this document and a contract document, the contract document governs.

## Positioning

### Target user
- founder
- product builder
- strategist
- writer working on high-leverage drafts

### Primary use case
Review an artifact before shipping or building it, surface weak assumptions and scope problems, and produce a revision-ready output.

## V1 Scope

### Allowed artifact types (exact strings, V1 only)
- `PRD`

Any packet with an `artifact_type` value other than `PRD` is invalid and must be rejected before the review runs.
V1 reviews PRDs only. No other artifact type is permitted.

### Allowed review modes (exact strings, V1 only)
- `full council`
- `subset review`
- `single-seat review`

Any packet with a `requested_review_mode` value other than these three exact strings is invalid and must be rejected before the review runs.

V1 includes:
- fixed council member definitions
- fixed review rubric
- review packet input format
- structured council output format
- three review modes: full council, subset review, single-seat review
- CLI runner with packet validation and structured file output

V1 does not include:
- large UI systems
- automatic artifact classification
- automatic reviewer recommendation
- scoring dashboards
- weighted reviewers
- review history analysis
- multiple domain-specific councils

## Inputs

Every review starts with a review packet. The packet is a fixed contract, not a flexible guide. Field definitions, allowed values, and rejection rules are in `docs/COUNCIL_REVIEW_PACKET_TEMPLATE.md`.

## Outputs

Every review returns the same structured output. Section definitions, field requirements, ordering rules, and rejection criteria are in `docs/COUNCIL_OUTPUT_SCHEMA.md`.

## Review Modes

### Full Council
All seven members. Use for PRDs.

Members: Ben Thompson, April Dunford, Kara Swisher, Marques Brownlee, Andrew Chen, Ethan Mollick, Steve Jobs

### Subset Review
Two or more selected members. Preserve the full output structure. Do not add off-lens commentary.

### Single-Seat Review
Exactly one member. Stay inside that member's lens. Return only that member's review and final recommendation.

## Orchestration Flow

1. **Prepare** — Fill and validate the packet against `docs/COUNCIL_REVIEW_PACKET_TEMPLATE.md`.
2. **Review** — Each selected member reviews the artifact through their own lens and returns the required fields.
3. **Debate** — Identify 2 to 4 real disagreement topics. Select the most relevant members. Run a short exchange that forces direct challenge.
4. **Synthesize** — Build the executive summary, agreement and disagreement maps, debate highlights, top risks, recommended changes, final recommendation, and next draft focus.
5. **Save** — Write the output file in the format defined in `docs/COUNCIL_OUTPUT_SCHEMA.md`.

## Runner Contract

The runner must be minimal and deterministic.

- **Input**: one packet file, validated against `docs/COUNCIL_REVIEW_PACKET_TEMPLATE.md` before any LLM call. Any contract violation must reject the run immediately.
- **Output**: one output file, validated against `docs/COUNCIL_OUTPUT_SCHEMA.md` before saving. Any contract violation must fail hard — no recovery attempts.
- **Save**: each run writes one file. No invented field names or sections.

## Validation Criteria

Runner-enforced rules are defined in `docs/COUNCIL_REVIEW_PACKET_TEMPLATE.md` and `docs/COUNCIL_OUTPUT_SCHEMA.md`. The runner enforces these mechanically.

Review quality — distinctness of member voices, specificity of critique, revision value — is assessed after each run. If quality is insufficient, refine prompts before proceeding.

## V1 Build Plan

1. Lock the spec — finalize PRD, rubric, member definitions, packet template, output schema.
2. Run reviews — run full council on the PRD; save to `examples/`.
3. Refine quality — tighten prompts where voices blur or feedback gets generic.
4. Ship the runner — minimal CLI; input packet, validate, run, save output.

V1 is ready when full council and subset reviews are distinct, actionable, and worth revising from.
