# Multiagent Council Public Demo

`Multiagent Council Public Demo` is a public-safe demonstration repo for `Hive Nova Council`.

Hive Nova Council is a council-style review engine for written artifacts. You give it a structured review packet, it routes the artifact through distinct member lenses, and it saves a structured review output in Markdown.

This demo keeps the core runnable council code and the key docs, but trims away internal notes, messy historical artifacts, and business-specific examples.

## What Is Included

- runnable Python CLI for packet validation, council orchestration, and Markdown output
- canonical council member definitions
- packet and output contract docs
- persona fidelity rubric
- safe tests for contracts and member definitions
- two polished public example packets
- two polished public example outputs

## Repo Layout

- `app/` - CLI entrypoint, council orchestration, models, and LLM client
- `docs/` - PRD, packet contract, output schema, member definitions, and rubrics
- `examples/packets/` - public-safe input packets
- `examples/outputs/` - public-safe sample outputs
- `prompts/` - orchestration prompt references
- `tests/` - shareable validation tests

## Quick Start

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Create your local env file:

```bash
cp .env.example .env
```

Then add your real `OPENAI_API_KEY` to `.env`.

## Run A Sample Review

```bash
python3 app/main.py --input examples/packets/demo_packet_product_requirements.yaml
```

If you omit `--output`, the runner writes a deterministic Markdown file next to the input packet.

## Run Tests

```bash
python3 -m pytest tests/ -v
```

## Key Docs

- [Hive Nova Council PRD](docs/hive-nova-council-prd.md)
- [Review Packet Template](docs/COUNCIL_REVIEW_PACKET_TEMPLATE.md)
- [Output Schema](docs/COUNCIL_OUTPUT_SCHEMA.md)
- [Council Member Definitions](docs/COUNCIL_MEMBER_DEFINITIONS.md)
- [Persona Fidelity Rubric](docs/PERSONA_FIDELITY_RUBRIC.md)

## Environment Notes

- `.env` is local-only and should never be committed
- `.env.example` is the placeholder template for local setup
- this public demo does not include any real credentials or private environment values
