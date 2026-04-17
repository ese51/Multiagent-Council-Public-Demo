from __future__ import annotations

import argparse
import sys
from pathlib import Path

from council.runner import CouncilRunner
from llm.client import configure_client_mode
from models.review_packet import ReviewPacket


def build_output_path(input_path: Path) -> Path:
    stem = input_path.stem
    if "packet" in stem:
        output_stem = stem.replace("packet", "output")
    else:
        output_stem = f"{stem}.review"
    return input_path.with_name(f"{output_stem}.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a multi-agent council review.")
    parser.add_argument("--input", required=True, help="Path to the review packet YAML file.")
    parser.add_argument(
        "--output",
        required=False,
        help="Optional output path. If omitted, a deterministic path is derived from the input file name.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in deterministic demo mode without calling the real API.",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output).resolve() if args.output else build_output_path(input_path)
    demo_mode = configure_client_mode(force_demo=args.demo)

    try:
        packet = ReviewPacket.from_yaml_file(input_path)
        runner = CouncilRunner()
        review_output = runner.run(packet)
        if args.demo:
            print("Running in deterministic demo mode (--demo). No API call will be made.", file=sys.stderr)
        elif demo_mode:
            print("OPENAI_API_KEY not found. Falling back to deterministic demo mode.", file=sys.stderr)
        output_path.write_text(review_output.to_markdown(demo_mode=demo_mode), encoding="utf-8")
    except Exception as exc:  # pragma: no cover - CLI surface
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
