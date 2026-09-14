"""Offline recovery of a saved model assessment after fixing validation code.

No key loading, model calls, source reads or assessment editing. The original run
and candidate remain unchanged; acceptance is separately recorded with hashes.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from .config import InvestigatorError
from .models import InvestigationResult
from .validation import validate_sources


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def revalidate(directory: Path):
    report = json.loads((directory / "report.json").read_text())
    raw = json.loads((directory / "rejected-result.json").read_text())
    calls = json.loads((directory / "tool-calls.json").read_text())
    result = InvestigationResult.model_validate(raw)
    validate_sources(result, calls, result.case_id)
    normalized = result.model_dump(mode="json")
    # Apart from canonical citation spelling, this path cannot rewrite model facts.
    for ref in raw["source_references"]:
        ref["tool_name"] = ref["tool_name"].removeprefix("functions.")
    if raw != normalized:
        raise InvestigatorError("revalidation_would_change_assessment")
    fd = os.open(directory / "result.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(normalized, handle, indent=2)
    receipt = {"status": "validated", "trace_id": report["trace_id"], "model_calls": 0,
               "original_run_status": report["status"], "original_error": report.get("error_category"),
               "business_assessment_unchanged": True,
               "corrections": ["Canonicalize functions namespace in source citations",
                               "Recognize milestone_id in dependency projections"],
               "candidate_sha256": digest(directory / "rejected-result.json"),
               "result_sha256": digest(directory / "result.json")}
    fd = os.open(directory / "revalidation.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(receipt, handle, indent=2)
    return receipt


def main():
    parser = argparse.ArgumentParser(description="Revalidate a saved assessment offline; no paid requests.")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = revalidate(args.run_dir)
    except Exception:
        print(json.dumps({"status": "failed", "error": "offline_revalidation_failed"}))
        return 1
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
