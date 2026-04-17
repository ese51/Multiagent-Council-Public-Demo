# Multiagent Council Public Demo

![Multiagent Council banner](<assets/MultiAgent Council.png>)

`Multiagent Council Public Demo` is a generic, public-facing demonstration of a council-style review system for written artifacts.

You give the system a structured review packet, it routes the artifact through distinct reviewer lenses, and it saves a structured review output in Markdown.

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

## Run In Demo Mode

This path is deterministic and does not call the real API:

```bash
python3 app/main.py --demo --input examples/packets/demo_packet_product_requirements.yaml
```

You can also omit `--demo` and the runner will automatically fall back to demo mode if `OPENAI_API_KEY` is missing.

## Run In Real API Mode

With `OPENAI_API_KEY` present in your local `.env`, run:

```bash
python3 app/main.py --input examples/packets/demo_packet_product_requirements.yaml
```

If you omit `--output`, the runner writes a deterministic Markdown file next to the input packet.

## Run Tests

```bash
python3 -m pytest tests/ -v
```

## Key Docs

- [Demo System PRD](docs/multiagent-council-demo-prd.md)
- [Review Packet Template](docs/COUNCIL_REVIEW_PACKET_TEMPLATE.md)
- [Output Schema](docs/COUNCIL_OUTPUT_SCHEMA.md)
- [Council Member Definitions](docs/COUNCIL_MEMBER_DEFINITIONS.md)
- [Persona Fidelity Rubric](docs/PERSONA_FIDELITY_RUBRIC.md)

## Environment Notes

- `.env` is local-only and should never be committed
- `.env.example` is the placeholder template for local setup
- this public demo does not include any real credentials or private environment values
