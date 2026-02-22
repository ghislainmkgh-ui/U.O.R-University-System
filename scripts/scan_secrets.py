"""Scan staged files for potential secrets before commit.

Usage: run via pre-commit hook. Exits non-zero if potential secrets are detected.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_FILE = ROOT / ".secrets-allowlist"

SUSPECT_PATTERNS: list[tuple[str, str]] = [
    (r"(?i)twilio_auth_token\s*[:=]\s*['\"]?([A-Za-z0-9]{10,})", "TWILIO_AUTH_TOKEN"),
    (r"(?i)twilio_account_sid\s*[:=]\s*['\"]?(AC[a-f0-9]{32})", "TWILIO_ACCOUNT_SID"),
    (r"(?i)ultramsg_token\s*[:=]\s*['\"]?([A-Za-z0-9]{8,})", "ULTRAMSG_TOKEN"),
    (r"(?i)ultramsg_instance_id\s*[:=]\s*['\"]?([A-Za-z0-9_-]{6,})", "ULTRAMSG_INSTANCE_ID"),
    (r"(?i)email_password\s*[:=]\s*['\"]?(.{8,})", "EMAIL_PASSWORD"),
    (r"(?i)api[_-]?key\s*[:=]\s*['\"]?([A-Za-z0-9_-]{8,})", "API_KEY"),
    (r"(?i)secret\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{8,})", "SECRET"),
    (r"(?i)token\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{8,})", "TOKEN"),
    (r"AKIA[0-9A-Z]{16}", "AWS_ACCESS_KEY_ID"),
]


def load_allowlist() -> list[re.Pattern[str]]:
    patterns: list[re.Pattern[str]] = []
    if not ALLOWLIST_FILE.exists():
        return patterns
    for line in ALLOWLIST_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        patterns.append(re.compile(stripped))
    return patterns


def is_allowlisted(text: str, allowlist: list[re.Pattern[str]]) -> bool:
    return any(pattern.search(text) for pattern in allowlist)


def get_staged_files() -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("❌ Impossible de lister les fichiers indexés.")
        print(result.stderr)
        return []
    files = [ROOT / Path(p.strip()) for p in result.stdout.splitlines() if p.strip()]
    return [p for p in files if p.exists()]


def is_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:1024]
    except OSError:
        return True
    return b"\x00" in chunk


def redact(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:3]}***{value[-3:]}"


def scan_file(path: Path, allowlist: list[re.Pattern[str]]) -> list[str]:
    if is_binary(path):
        return []
    findings: list[str] = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []

    for idx, line in enumerate(content, start=1):
        if not line.strip() or line.strip().startswith("#"):
            continue
        if is_allowlisted(line, allowlist):
            continue
        for pattern, label in SUSPECT_PATTERNS:
            match = re.search(pattern, line)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                findings.append(
                    f"{path.relative_to(ROOT)}:{idx} [{label}] {redact(value)}"
                )
    return findings


def main() -> int:
    allowlist = load_allowlist()
    staged_files = get_staged_files()
    if not staged_files:
        return 0

    all_findings: list[str] = []
    for path in staged_files:
        all_findings.extend(scan_file(path, allowlist))

    if not all_findings:
        return 0

    print("\n🚨 Secrets potentiels détectés dans les fichiers indexés :")
    for finding in all_findings:
        print(f"  - {finding}")

    print(
        "\nCorrigez ces valeurs, ou ajoutez un motif dans .secrets-allowlist "
        "si c'est un exemple non sensible."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
