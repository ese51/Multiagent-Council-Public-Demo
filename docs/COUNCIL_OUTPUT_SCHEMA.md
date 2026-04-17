# Hive Nova Council Output Schema

This schema is the fixed V1 output contract.
All nine sections must be present in every saved review.
Sections must appear in the exact numbered order defined below.
Per-member fields must be present for every selected member.
Any output that is missing a section, has sections out of order, or has an invalid field value is invalid and must be rejected.

## 1. Executive Summary
- overall judgment
- strongest strengths
- biggest weaknesses
- recommended next move

## 2. Per-Member Reviews
For each selected council member, all seven fields below must be present in this exact order.
A member review with any field missing, renamed, or out of order is invalid and must be rejected.

### Member Name
### Overall judgment
### What is working
(required, at least one bullet)
### What is not working
(required, at least one bullet)
### What to cut
(required, at least one bullet)
### What to improve
(required, at least one bullet)
### Biggest question
### Score (1-5)
(must be an integer from 1 to 5 inclusive)

## 3. Agreement Map
List the points where multiple members agree.

## 4. Disagreement Map
List where members disagree and why.

## 5. Debate Highlights
For each key disagreement, return:
- topic
- participants
- short exchange

## 6. Top Risks
List the highest-risk issues.

## 7. Recommended Changes
Give a short ranked list of changes.

## 8. Final Recommendation
Must be exactly one of these four values:
- `go`
- `revise`
- `pause`
- `reject`

Any value other than these four exact strings is invalid and must be rejected.

## 9. Suggested Next Draft Focus
What should the next revision focus on?

## V1 Contract Rules
- Do not rename, remove, or reorder sections or per-member fields. Any deviation is invalid.
- All nine sections must be present in every full-council and subset review. Omitting any section is invalid and the output must be rejected.
- For single-seat review, sections 1 and 8 are required; sections 3–7 are omitted (there is only one member). Section 9 is required.
- `agreement_map`, `disagreement_map`, `top_risks`, and `recommended_changes` must each contain at least one item in full-council and subset reviews. An empty list in any of these fields is invalid and the output must be rejected.
- `member_reviews` must contain one entry per selected member. Missing or extra entries are invalid.
- `final_recommendation` must be one of the four exact values defined in section 8. Any other value is invalid and must be rejected.
- If output is structured but shallow, or does not create meaningful revision guidance, the review is a failure and prompts must be refined.
- The compact output format is not permitted in V1. All nine sections must be present.
