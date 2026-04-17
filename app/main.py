from __future__ import annotations

import argparse
import sys
from pathlib import Path

from council.runner import CouncilRunner
from models.review_packet import ReviewPacket


def build_output_path(input_path: Path) -> Path:
    stem = input_path.stem
    if "packet" in stem:
        output_stem = stem.replace("packet", "output")
    else:
        output_stem = f"{stem}.review"
    return input_path.with_name(f"{output_stem}.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Hive Nova Council review.")
    parser.add_argument("--input", required=True, help="Path to the review packet YAML file.")
    parser.add_argument(
        "--output",
        required=False,
        help="Optional output path. If omitted, a deterministic path is derived from the input file name.",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output).resolve() if args.output else build_output_path(input_path)

    try:
        packet = ReviewPacket.from_yaml_file(input_path)
        runner = CouncilRunner()
        review_output = runner.run(packet)
        output_path.write_text(review_output.to_markdown(), encoding="utf-8")
    except Exception as exc:  # pragma: no cover - CLI surface
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
