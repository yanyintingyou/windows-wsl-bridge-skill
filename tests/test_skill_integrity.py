#!/usr/bin/env python3
"""Lightweight integrity checks for the windows-wsl-bridge skill."""
from __future__ import annotations

import re
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required for this test") from exc

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"

REQUIRED_FRONTMATTER = {
    "name",
    "description",
    "version",
    "author",
    "license",
    "platforms",
    "metadata",
}

REQUIRED_SECTIONS = [
    "Overview",
    "When to Use",
    "Core Guardrails",
    "Discovery Workflow",
    "Access Patterns",
    "Permission Model",
    "Safe Write Pattern",
    "Common Pitfalls",
    "Verification Checklist",
    "Output Discipline",
]

FORBIDDEN_PATTERNS = {
    "pipe_shell_installer": re.compile(r"\b(curl|wget)\b[^\n|]*\|\s*(bash|sh)", re.I),
    "explicit_sensitive_home_paths": re.compile(r"~/(\.ssh|\.gnupg|\.hermes|\.config)"),
    "unattended_elevation_probe": re.compile(r"\bsudo\s+-n\b", re.I),
    "broad_recursive_delete": re.compile(r"\brm\s+-[^\n]*r[f]?\b|Remove-Item\b[^\n]*-Recurse", re.I),
}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    match = re.search(r"\n---\s*\n", text[4:])
    assert match, "frontmatter must close with ---"
    end = match.end() + 4
    frontmatter = yaml.safe_load(text[4 : match.start() + 4])
    assert isinstance(frontmatter, dict), "frontmatter must parse as a mapping"
    return frontmatter, text[end:]


def main() -> None:
    text = SKILL.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)

    missing = REQUIRED_FRONTMATTER - set(frontmatter)
    assert not missing, f"missing frontmatter keys: {sorted(missing)}"
    assert frontmatter["name"] == "windows-wsl-bridge"
    assert len(frontmatter["description"]) <= 1024
    assert body.strip(), "skill body must not be empty"

    headings = set(re.findall(r"^##\s+(.+)$", body, re.M))
    missing_sections = [section for section in REQUIRED_SECTIONS if section not in headings]
    assert not missing_sections, f"missing sections: {missing_sections}"

    for label, pattern in FORBIDDEN_PATTERNS.items():
        assert not pattern.search(text), f"forbidden pattern found: {label}"

    yaml.safe_load((ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    assert (ROOT / "README.md").exists()
    assert (ROOT / "README.zh-CN.md").exists()
    assert (ROOT / "LICENSE").exists()
    print("windows-wsl-bridge skill integrity checks passed")


if __name__ == "__main__":
    main()
