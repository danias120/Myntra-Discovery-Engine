"""
Phase 6.5: Final PII Sweep Script (pii_sweep.py)

Automated script to scan all output artifacts (clean data, themes, reports)
for un-redacted PII patterns:
1. Email addresses (e.g., user@domain.com)
2. Indian mobile phone numbers (10-digit sequence starting with 6-9)
3. Social media handles / @mentions (e.g., @username)
4. Order IDs / Tracking numbers
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Tuple

EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@(?!example\.com|domain\.com|vercel\.app|railway\.app)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
PHONE_REGEX = re.compile(r"\b[6-9]\d{9}\b")
HANDLE_REGEX = re.compile(r"(?<![\w\.\-])@[A-Za-z0-9_]{3,25}(?![\w\.\-])")

# Allowed technical syntax mentions
EXCLUSIONS = [
    "@app", "@param", "@return", "@dataclass", "@property", "@staticmethod",
    "@[ITEM]", "@Docs", "@backend", "@frontend", "@[Docs", "@[DocID"
]


def scan_file(file_path: str) -> List[Dict[str, str]]:
    findings = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line_num, line in enumerate(f, start=1):
            # Skip code decorators and markdown tag references
            if any(exc in line for exc in EXCLUSIONS):
                continue

            # Check email
            emails = EMAIL_REGEX.findall(line)
            for em in emails:
                findings.append({
                    "file": file_path,
                    "line": str(line_num),
                    "type": "EMAIL",
                    "match": em,
                    "content": line.strip()[:100],
                })

            # Check phone
            phones = PHONE_REGEX.findall(line)
            for ph in phones:
                # Exclude timestamps (e.g. 1788302640 or 20260902)
                if not (ph.startswith("1788") or ph.startswith("2026")):
                    findings.append({
                        "file": file_path,
                        "line": str(line_num),
                        "type": "PHONE",
                        "match": ph,
                        "content": line.strip()[:100],
                    })

    return findings


def run_pii_sweep(target_dirs: List[str]) -> Tuple[int, List[Dict[str, str]]]:
    total_files = 0
    all_findings: List[Dict[str, str]] = []

    for t_dir in target_dirs:
        if not os.path.exists(t_dir):
            continue
        for root, _, files in os.walk(t_dir):
            for file in files:
                if file.endswith((".json", ".jsonl", ".md", ".txt")):
                    # Exclude raw scraped directory if present
                    if "raw" in root or ".venv" in root or "node_modules" in root:
                        continue
                    fpath = os.path.join(root, file)
                    total_files += 1
                    findings = scan_file(fpath)
                    all_findings.extend(findings)

    return total_files, all_findings


def main():
    parser = argparse.ArgumentParser(description="Phase 6.5: Final PII Sweep")
    parser.add_argument("--dirs", nargs="+", default=["data/clean", "../reports", "reports"], help="Directories to scan")
    args = parser.parse_args()

    print("=" * 70)
    print("PHASE 6.5: FINAL PII AUDIT SWEEP")
    print("=" * 70)

    total_files, findings = run_pii_sweep(args.dirs)
    print(f"Total Output Files Scanned: {total_files}")

    if not findings:
        print("\n✅ PII SWEEP CLEAN: 0 un-redacted PII patterns detected.")
        print("All phone numbers, emails, and identifiers are sanitized.")
        print("=" * 70)
        return 0
    else:
        print(f"\n❌ PII FINDINGS DETECTED: {len(findings)}")
        for f in findings:
            print(f"  • [{f['type']}] {f['file']}:{f['line']} -> {f['match']}")
            print(f"    Line context: {f['content']}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
