from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = {
    "orchestrator",
    "continuous-learning",
    "eval-harness",
    "verification-loop",
    "software-architecture",
    "concurrency-performance",
}
REQUIRED_WORKFLOW_HEADINGS = (
    "## Entry conditions",
    "## Evidence required",
    "## Procedure",
    "## Failure handling",
    "## Verification",
    "## Output contract",
)
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{16,}"),
    re.compile(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
)
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".ps1", ".py", ".txt"}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def shipped_text_files() -> list[Path]:
    files: list[Path] = []
    ignored_parts = {".git", "docs", "tests", "examples"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in ignored_parts for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return files


def validate_required_structure() -> None:
    required = [
        ROOT / "skills",
        ROOT / "rules",
        ROOT / "contexts",
        ROOT / "workflows",
        ROOT / "scripts",
        ROOT / "mcp",
        ROOT / "templates",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        fail(f"missing required paths: {missing}")


def validate_skill_set() -> None:
    skills_root = ROOT / "skills"
    actual = {path.name for path in skills_root.iterdir() if path.is_dir()}
    if actual != EXPECTED_SKILLS:
        fail(f"skill set mismatch: expected={sorted(EXPECTED_SKILLS)} actual={sorted(actual)}")

    for skill in sorted(EXPECTED_SKILLS):
        skill_dir = skills_root / skill
        skill_file = skill_dir / "SKILL.md"
        metadata = skill_dir / "agents" / "openai.yaml"
        if not skill_file.is_file():
            fail(f"missing skills/{skill}/SKILL.md")
        if not metadata.is_file():
            fail(f"missing skills/{skill}/agents/openai.yaml")


def validate_orchestrator() -> None:
    roles_root = ROOT / "skills" / "orchestrator" / "references" / "roles"
    required_roles = {
        "architect",
        "planner",
        "code-reviewer",
        "security-reviewer",
        "build-error-resolver",
        "e2e-runner",
        "tdd-guide",
        "refactor-cleaner",
        "doc-updater",
    }
    actual_roles = {path.stem for path in roles_root.glob("*.md")} if roles_root.exists() else set()
    if actual_roles != required_roles:
        fail(f"role set mismatch: expected={sorted(required_roles)} actual={sorted(actual_roles)}")

    orchestrator = read(ROOT / "skills" / "orchestrator" / "SKILL.md")
    for intent in ("architecture", "plan", "review", "security", "build", "e2e", "tdd", "refactor", "docs"):
        if intent not in orchestrator.lower():
            fail(f"orchestrator routing contract missing intent: {intent}")


def validate_workflows() -> None:
    workflows_root = ROOT / "workflows"
    for path in workflows_root.glob("*.md"):
        text = read(path)
        missing = [heading for heading in REQUIRED_WORKFLOW_HEADINGS if heading not in text]
        if missing:
            fail(f"{path.relative_to(ROOT)} missing workflow headings: {missing}")


def validate_forbidden_content() -> None:
    for path in shipped_text_files():
        text = read(path)
        lowered = text.lower()
        if ".claude/skills" in lowered:
            fail(f"Claude skill path leaked into active shipped file: {path.relative_to(ROOT)}")
        if "auto_approve: true" in lowered:
            fail(f"unsafe learning auto-approval in {path.relative_to(ROOT)}")
        if re.search(r"\b(?:TODO|TBD)\b", text):
            fail(f"placeholder marker in shipped file: {path.relative_to(ROOT)}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"secret-like value in {path.relative_to(ROOT)}")


def main() -> int:
    validate_required_structure()
    validate_skill_set()
    validate_orchestrator()
    validate_workflows()
    validate_forbidden_content()
    print("PASS: repository content contracts satisfied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
