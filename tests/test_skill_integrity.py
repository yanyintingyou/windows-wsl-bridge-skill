#!/usr/bin/env python3
"""No-dependency integrity checks for the windows-wsl-bridge-skill repository."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"

REQUIRED_TOP_LEVEL = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
}

FORBIDDEN_TOP_LEVEL = {
    "version",
    "author",
    "platforms",
}

REQUIRED_METADATA_KEYS = {
    "version",
    "author",
    "platforms",
    "tags",
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
    "nested_heredoc_wsl_example": re.compile(r"wsl\.exe[^\n]+bash -lc [^\n]+python3 - <<", re.I),
}


def split_frontmatter(text: str) -> tuple[str, str]:
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    end = text.find("\n---\n", 4)
    assert end != -1, "frontmatter must close with ---"
    return text[4:end], text[end + len("\n---\n") :]


def top_level_keys(frontmatter: str) -> set[str]:
    keys: set[str] = set()
    for line in frontmatter.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            keys.add(line.split(":", 1)[0].strip())
    return keys


def metadata_keys(frontmatter: str) -> set[str]:
    keys: set[str] = set()
    in_metadata = False
    for line in frontmatter.splitlines():
        if line.startswith("metadata:"):
            in_metadata = True
            continue
        if in_metadata and line and not line.startswith(" "):
            break
        if in_metadata and line.startswith("  ") and not line.startswith("    ") and ":" in line:
            keys.add(line.split(":", 1)[0].strip())
    return keys


def scalar(frontmatter: str, key: str) -> str:
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.*)$", re.M)
    match = pattern.search(frontmatter)
    assert match, f"missing scalar key: {key}"
    return match.group(1).strip().strip('"').strip("'")


def main() -> None:
    text = SKILL.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)

    keys = top_level_keys(frontmatter)
    missing = REQUIRED_TOP_LEVEL - keys
    assert not missing, f"missing top-level frontmatter keys: {sorted(missing)}"
    forbidden = FORBIDDEN_TOP_LEVEL & keys
    assert not forbidden, f"non-portable top-level keys should move to metadata: {sorted(forbidden)}"

    assert scalar(frontmatter, "name") == "windows-wsl-bridge-skill"
    assert len(scalar(frontmatter, "description")) <= 1024
    assert scalar(frontmatter, "license") == "MIT"
    assert "wsl.exe" in scalar(frontmatter, "compatibility")

    missing_metadata = REQUIRED_METADATA_KEYS - metadata_keys(frontmatter)
    assert not missing_metadata, f"missing metadata keys: {sorted(missing_metadata)}"
    assert "author: yanyintingyou" in frontmatter
    assert "- windows" in frontmatter

    assert body.strip(), "skill body must not be empty"
    headings = set(re.findall(r"^##\s+(.+)$", body, re.M))
    missing_sections = [section for section in REQUIRED_SECTIONS if section not in headings]
    assert not missing_sections, f"missing sections: {missing_sections}"

    for label, pattern in FORBIDDEN_PATTERNS.items():
        assert not pattern.search(text), f"forbidden pattern found: {label}"

    assert (ROOT / "README.md").exists()
    assert (ROOT / "README.zh-CN.md").exists()
    assert (ROOT / "LICENSE").exists()
    assert (ROOT / "agents" / "openai.yaml").exists()
    assert "$windows-wsl-bridge-skill" in (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    print("windows-wsl-bridge-skill integrity checks passed")


if __name__ == "__main__":
    main()
