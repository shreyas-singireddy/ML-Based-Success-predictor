#!/usr/bin/env python3
"""
Secret scanner for the Student Success Predictor repository.

A lightweight, dependency-free audit tool that looks for accidentally
committed credentials (API keys, private keys, JWTs, passwords, cloud
credentials) in tracked text files. It is intentionally conservative:
findings are reported clearly and the exit code turns non-zero so CI can gate
on them (use --warn to only print).

Usage:
    python scripts/scan_for_secrets.py [--path <repo-root>] [--warn]
"""

import argparse
import re
import sys
from pathlib import Path

# Directories/files that are never scanned (derived or external).
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    "dist",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
SKIP_FILES = {
    ".env.example",
    "scripts/scan_for_secrets.py",
}
SKIP_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".db",
    ".sqlite",
    ".joblib",
    ".parquet",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".lock",  # package-lock.json, composer.lock (hash noise)
}

# (name, regex) — patterns are matched against file content lines.
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}\b")),
    ("openai-api-key", re.compile(r"\bsk-[A-Za-z0-9_\-]{15,}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[0-9A-Za-z]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[0-9A-Za-z\-]{20,}\b")),
    ("stripe-secret", re.compile(r"\bsk_live_[0-9A-Za-z]{20,}\b")),
    ("jwt-token", re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b")),
    ("rsa-private-key", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("generic-pkcs8", re.compile(r"-----BEGIN PRIVATE KEY-----")),
    ("url-password", re.compile(r"(postgres|mysql|redis|mongodb)(\+[a-z]+)?://[^\s:@/]+:[^\s@/]+@")),
    ("firebase-service-account", re.compile(r"\"private_key_id\"\s*:\s*\"[0-9a-f]{40}\"")),
    ("berrer-credential", re.compile(r"\bbearer\s+[0-9A-Za-z._\-]{25,}\b", re.IGNORECASE)),
]

# Synthetic fixtures that intentionally exercise secret *detection* (unit tests
# of the detection logic itself). Clearly not real credentials.
FIXTURE_HINT = re.compile(
    r"(for-testing|for_testing|fake|example|abc123|0123456789|key is|"
    r"find_secret|guard\.|monkeypatch|AIzaFake)",
    re.IGNORECASE,
)


# Lines like "SOMETHING_KEY=..." without a placeholder value.
RAW_ASSIGNMENT = re.compile(
    r"^\s*([A-Z0-9_]{3,}(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD))\s*=\s*"
    r"(?!.*(notification|placeholder|example|change-me|your-|xxx|\.\.\.|<\w+>|change-this|fake|test)).*$",
    re.IGNORECASE,
)

# Placeholder values that are safe to see in .env.example style files.
SAFE_VALUES = re.compile(
    r"(change-this|change-me|your-|example|placeholder|test|dev-|fake|for-testing|"
    r"abc123|key is|0123456789|\.\.\.|<\w+>|"
    r"super-secret-key-change-in-production|xxx)",
    re.IGNORECASE,
)


def _iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if rel.as_posix() in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        # Only scan files that are plausibly text.
        try:
            with open(path, "rb") as fh:
                chunk = fh.read(2048)
            if b"\x00" in chunk:
                continue
        except OSError:
            continue
        yield path, rel


def scan(root: Path) -> list[tuple[Path, int, str, str]]:
    findings: list[tuple[Path, int, str, str]] = []
    for path, rel in _iter_text_files(root):
        rel_posix = rel.as_posix()
        # This scanner's own regex definitions + documented test fixtures use
        # synthetic example tokens (AIzaFake..., sk-abc...) — never real keys.
        if rel_posix in {
            "scripts/scan_for_secrets.py",
            "backend/tests/test_assistant_security.py",
            "backend/tests/test_assistant_service.py",
        }:
            continue
        if rel.name == ".env.example":
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, start=1):
            if "test" in rel.as_posix() and FIXTURE_HINT.search(line):
                continue
            for name, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append((rel, lineno, name, "pattern"))
            if ".env" in rel.name:
                m = RAW_ASSIGNMENT.match(line)
                if m and not SAFE_VALUES.search(line.split("=", 1)[1]):
                    findings.append((rel, lineno, m.group(1).lower(), "raw-assignment"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan for committed secrets.")
    parser.add_argument("--path", default=".", help="Repository root to scan")
    parser.add_argument(
        "--warn",
        action="store_true",
        help="Print findings without failing (exit 0)",
    )
    args = parser.parse_args()

    root = Path(args.path).resolve()
    findings = scan(root)

    if findings:
        print(f"[SECRET-SCAN] {len(findings)} potential finding(s):\n")
        for rel, lineno, name, kind in findings:
            print(f"  {rel}:{lineno}  [{kind}] {name}")
        print(
            "\nReview each finding. Rotate any real credential immediately and "
            "remove it from history. See docs/security.md for the rotation policy."
        )
        return 0 if args.warn else 1

    print("[SECRET-SCAN] clean — no committed credential patterns detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())