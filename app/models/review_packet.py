from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from council.members import MEMBER_BY_NAME


ALLOWED_ARTIFACT_TYPES = {"PRD"}
ALLOWED_REVIEW_MODES = {"full council", "subset review", "single-seat review"}
REQUIRED_KEYS = [
    "artifact_title",
    "artifact_type",
    "goal",
    "intended_audience",
    "context",
    "specific_questions",
    "constraints",
    "requested_review_mode",
    "selected_members",
    "artifact_text",
]


class SimpleYamlContractError(ValueError):
    pass


class SimpleYamlLoader:
    def __init__(self, text: str):
        self.lines = text.splitlines()
        self.index = 0

    def parse(self) -> dict[str, object]:
        data: dict[str, object] = {}
        while self.index < len(self.lines):
            line = self.lines[self.index]
            if self._is_skip(line):
                self.index += 1
                continue
            if self._indent(line) != 0:
                raise SimpleYamlContractError(f"Unexpected indentation at line {self.index + 1}.")
            key, raw_value = self._split_key_value(line)
            self.index += 1
            if raw_value == "|":
                data[key] = self._parse_block_scalar(indent=2)
            elif raw_value == "":
                data[key] = self._parse_nested_value(expected_indent=2)
            elif raw_value == "[]":
                data[key] = []
            else:
                data[key] = self._parse_scalar(raw_value)
        return data

    def _parse_nested_value(self, expected_indent: int) -> object:
        next_line = self._next_content_line()
        if next_line is None:
            raise SimpleYamlContractError("Expected nested value but reached end of file.")
        if self._indent(next_line) != expected_indent:
            raise SimpleYamlContractError("Nested values must use two-space indentation.")
        if next_line.strip().startswith("- "):
            return self._parse_list(expected_indent)
        raise SimpleYamlContractError("Only flat lists are supported as nested YAML values.")

    def _parse_list(self, expected_indent: int) -> list[str]:
        items: list[str] = []
        while self.index < len(self.lines):
            line = self.lines[self.index]
            if self._is_skip(line):
                self.index += 1
                continue
            indent = self._indent(line)
            if indent < expected_indent:
                break
            if indent != expected_indent or not line.strip().startswith("- "):
                raise SimpleYamlContractError(f"Invalid list item at line {self.index + 1}.")
            items.append(self._parse_scalar(line.strip()[2:]))
            self.index += 1
        return items

    def _parse_block_scalar(self, indent: int) -> str:
        lines: list[str] = []
        while self.index < len(self.lines):
            line = self.lines[self.index]
            if line.strip() == "" and not lines:
                self.index += 1
                continue
            current_indent = self._indent(line)
            if line.strip() == "":
                lines.append("")
                self.index += 1
                continue
            if current_indent < indent:
                break
            if current_indent < indent:
                raise SimpleYamlContractError(f"Invalid block scalar indentation at line {self.index + 1}.")
            lines.append(line[indent:])
            self.index += 1
        return "\n".join(lines).rstrip()

    @staticmethod
    def _parse_scalar(value: str) -> str:
        stripped = value.strip()
        if stripped.startswith(("'", '"')) and stripped.endswith(("'", '"')) and len(stripped) >= 2:
            return stripped[1:-1]
        return stripped

    def _next_content_line(self) -> str | None:
        probe = self.index
        while probe < len(self.lines):
            line = self.lines[probe]
            if not self._is_skip(line):
                return line
            probe += 1
        return None

    @staticmethod
    def _split_key_value(line: str) -> tuple[str, str]:
        if ":" not in line:
            raise SimpleYamlContractError("Each YAML line must contain a key and value separated by ':'.")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if not key:
            raise SimpleYamlContractError("YAML keys may not be empty.")
        return key, raw_value.lstrip()

    @staticmethod
    def _indent(line: str) -> int:
        return len(line) - len(line.lstrip(" "))

    @staticmethod
    def _is_skip(line: str) -> bool:
        stripped = line.strip()
        return stripped == "" or stripped.startswith("#")


@dataclass(frozen=True)
class ReviewPacket:
    artifact_title: str
    artifact_type: str
    goal: str
    intended_audience: str
    context: str
    specific_questions: list[str]
    constraints: list[str]
    requested_review_mode: str
    selected_members: list[str]
    artifact_text: str

    @classmethod
    def from_yaml_file(cls, path: Path) -> "ReviewPacket":
        text = path.read_text(encoding="utf-8")
        raw = SimpleYamlLoader(text).parse()
        cls._validate_raw_contract(raw)
        packet = cls(
            artifact_title=raw["artifact_title"],
            artifact_type=raw["artifact_type"],
            goal=raw["goal"],
            intended_audience=raw["intended_audience"],
            context=raw["context"],
            specific_questions=list(raw["specific_questions"]),
            constraints=list(raw["constraints"]),
            requested_review_mode=raw["requested_review_mode"],
            selected_members=list(raw["selected_members"]),
            artifact_text=raw["artifact_text"],
        )
        packet.validate()
        return packet

    @staticmethod
    def _validate_raw_contract(raw: dict[str, object]) -> None:
        if set(raw.keys()) != set(REQUIRED_KEYS):
            missing = [key for key in REQUIRED_KEYS if key not in raw]
            unknown = [key for key in raw.keys() if key not in REQUIRED_KEYS]
            problems = []
            if missing:
                problems.append(f"missing keys: {', '.join(missing)}")
            if unknown:
                problems.append(f"unknown keys: {', '.join(unknown)}")
            raise SimpleYamlContractError("Packet contract violation: " + "; ".join(problems))

    def validate(self) -> None:
        if self.artifact_type not in ALLOWED_ARTIFACT_TYPES:
            raise SimpleYamlContractError(
                f"artifact_type must be one of: {', '.join(sorted(ALLOWED_ARTIFACT_TYPES))}"
            )
        if self.requested_review_mode not in ALLOWED_REVIEW_MODES:
            raise SimpleYamlContractError(
                f"requested_review_mode must be one of: {', '.join(sorted(ALLOWED_REVIEW_MODES))}"
            )
        for field_name in ("artifact_title", "goal", "intended_audience", "context"):
            value = getattr(self, field_name)
            if not value.strip():
                raise SimpleYamlContractError(f"{field_name} must not be empty.")
        if not self.artifact_text.strip():
            raise SimpleYamlContractError("artifact_text must not be empty.")
        if not self.specific_questions:
            raise SimpleYamlContractError("specific_questions must contain at least one question.")
        if not self.constraints:
            raise SimpleYamlContractError("constraints must contain at least one constraint.")
        if self.requested_review_mode == "full council":
            if self.selected_members:
                raise SimpleYamlContractError("selected_members must be empty for full council reviews.")
        elif self.requested_review_mode == "subset review":
            if len(self.selected_members) < 2:
                raise SimpleYamlContractError("subset review requires at least two selected members.")
        elif self.requested_review_mode == "single-seat review":
            if len(self.selected_members) != 1:
                raise SimpleYamlContractError("single-seat review requires exactly one selected member.")
        unknown_members = [name for name in self.selected_members if name not in MEMBER_BY_NAME]
        if unknown_members:
            raise SimpleYamlContractError(
                "Unknown council member(s): " + ", ".join(unknown_members)
            )
