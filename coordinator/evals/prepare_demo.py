"""DEVELOPER-ONLY synthetic source initialization and persisted-state fingerprint.

Run with the backend environment. This module is never imported by agent runtime
and is not exposed through MCP. Creates new isolated storage; never resets a DB.
Only the three explicitly listed business documents are added to retrieval.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

from mock_enterprise.config import PROJECT, Settings
from mock_enterprise.db import Store, connect
from mock_enterprise.seed import initialize, lifecycle_lock, load_seed, validate_graph
from mock_enterprise.app import create_app
import uvicorn

DOCUMENTS = {
    "DOC-COORD-REQUEST-018": ("phase05_evidence_request.json", "coordination_request", "requested"),
    "DOC-COORD-POLICY-01": ("phase05_coordination_policy.json", "coordination_policy", "approved"),
    "DOC-BASE-PROC-05": ("phase05_baseline_procedure.md", "procedure", "approved"),
}


def extension():
    common = {"content_version": 1, "updated_at": "2026-11-16T09:00:00Z", "synthetic": True,
              "owning_system": "engineering", "program_id": "PRG-A17"}
    scoped = {**common, "customer_id": "CUST-FML01"}
    docs = []
    for rid, (filename, kind, status) in DOCUMENTS.items():
        path = PROJECT / "fixtures" / "documents" / filename
        if path.is_symlink():
            raise ValueError("Synthetic document symlinks are refused")
        content = path.read_text()
        docs.append({**scoped, "id": rid, "document_type": kind, "document_version": "1",
                     "status": status, "content": content, "content_hash": hashlib.sha256(content.encode()).hexdigest()})
    return {
        "engineering.document": docs,
        "engineering.change": [{**scoped, "id": "CR-018", "record_version": 1,
            "baseline_requirement_revision_id": "REQ-042-V1", "proposed_requirement_revision_id": "REQ-042-V1",
            "configuration_id": "CFG-B-01", "milestone_id": "MS-ACCEPT-01", "order_id": "ORD-1204",
            "request_document_id": "DOC-COORD-REQUEST-018", "workflow_state": "new",
            "request_received_at": "2026-11-16T09:00:00Z", "title": "Existing runtime compatibility evidence reference packet",
            "category": "Administrative runtime/firmware compatibility evidence reference", "priority": "low",
            "owner": "Mara Chen", "next_action": "Assess existing evidence for an internal reference packet"}],
        "engineering.procedure": [{**common, "id": "PROC-BASE-01", "status": "approved",
            "document_id": "DOC-BASE-PROC-05", "supported_configuration_ids": ["CFG-B-01"],
            "workload_profile_id": "WF-LC-V1", "setup_minutes": 120, "suite_minutes": 120,
            "per_bin_minutes": 60, "review_minutes": 240, "acceptance_limits_ref": "CRIT-BASE-V1"}],
        "engineering.policy": [{**common, "id": "POLICY-BASE-01", "status": "approved",
            "permitted_procedure_ids": ["PROC-BASE-01"], "approver_role": "engineer",
            "max_incremental_cost_cents": 0, "currency": "USD", "permitted_actions": [],
            "document_id": "DOC-BASE-PROC-05"}],
    }


def prepare(settings):
    additions = extension()
    rows, _ = load_seed()
    for kind, items in additions.items():
        rows[kind].extend(items)
    validate_graph(rows)
    # initialize refuses an existing file; the following import belongs to the
    # same developer-only setup, before any agent or verification snapshot runs.
    initialize(settings)
    with lifecycle_lock(settings):
        con = connect(settings.db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            store = Store(con)
            for kind in ("engineering.document", "engineering.procedure", "engineering.policy", "engineering.change"):
                for record in additions[kind]:
                    store.insert(kind, record)
            if con.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Phase 05 synthetic reference integrity failed")
            meta = store.meta
            meta["phase05_extension"] = "existing-evidence-packet-v1"
            meta["phase05_extension_sha256"] = hashlib.sha256(json.dumps(additions, sort_keys=True).encode()).hexdigest()
            con.execute("UPDATE demo_metadata SET data=? WHERE id=1", (json.dumps(meta, sort_keys=True),))
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()


def fingerprint(settings):
    settings.validate(existing=True)
    with sqlite3.connect(f"file:{settings.db_path}?mode=ro", uri=True) as con:
        # Includes ALL persisted tables, metadata, audit, and idempotency rows.
        return hashlib.sha256("\n".join(con.iterdump()).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="DEVELOPER synthetic Phase 05 source setup; never an AI action or real human approval.")
    parser.add_argument("--storage", type=Path, required=True)
    parser.add_argument("--port", type=int, default=9011)
    parser.add_argument("--fingerprint", action="store_true")
    parser.add_argument("--serve-existing", action="store_true")
    args = parser.parse_args()
    storage = args.storage.absolute()
    if not storage.is_relative_to(PROJECT / ".cache" / "multi-agent-demo"):
        parser.error("Storage must be a new directory beneath .cache/multi-agent-demo")
    settings = Settings(storage / "enterprise.sqlite3", storage, True)
    if args.fingerprint:
        print(fingerprint(settings))
        return
    if not args.serve_existing:
        prepare(settings)
    else:
        settings.validate(existing=True)
    uvicorn.run(create_app(settings), host="127.0.0.1", port=args.port, access_log=False, log_level="warning")


if __name__ == "__main__":
    main()
