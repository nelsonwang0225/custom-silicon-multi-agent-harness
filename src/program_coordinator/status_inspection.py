"""Read-only intent admission and source checks inside requirement-change analysis.

This module installs no tools or executors. Natural-language screening is a
conservative routing check, not authorization; the unchanged MCP read scopes and
Phase 06 execution boundary remain the authority controls.
"""

import re

from .controls import HarnessError


def read_only_status_request(text):
    # Accept questions/inspection requests, with an additional conservative veto
    # on action directives even when a model misclassifies them as status reads.
    if not re.match(r"\s*(?:please\s+)?(?:inspect|report|check|show|verify|what|which|has|have|is|are|does|do)\b", text, re.I):
        return False
    if not re.search(r"\b(?:CR-017|validation|planner|program plan|customer acceptance)\b", text, re.I):
        return False
    for clause in re.split(r"[.!?;\n]|\b(?:and|then|but)\b", text, flags=re.I):
        clause = re.sub(r"\b(?:do not|don't|never)\s+(?:schedule|approve|grant|execute|create|modify|update|change|delete|release|send|accept|book)\b", "", clause, flags=re.I)
        if re.search(r"\b(?:schedule|approve|grant|execute|create|modify|update|delete|release|send|accept|book|change)\b", clause, re.I):
            return False
    return True


def status_scope_error(state, registry):
    triage = state.triage
    scope = triage.status_inspection
    if triage.classified_change_type != "existing_case_status":
        return "status_scope_without_status_classification" if scope else None
    if (not scope or not state.scope_verified or triage.confidence < 0.75
            or state.workflow_id not in {None, "requirement_change_analysis"}
            or state.event.change_id != "CR-017"
            or not read_only_status_request(state.event.request_summary)):
        return "status_inspection_scope_unverified"
    if any(getattr(scope, k) != getattr(state.event, k) for k in ("change_id", "customer_id", "program_id")):
        return "status_inspection_scope_mismatch"
    call = next((c for c in registry.calls if c["tool"] == "get_change_request"
                 and c["invocation_id"] == "intake" and c["arguments"].get("change_id") == scope.change_id), None)
    if not call:
        return "status_inspection_intake_missing"
    change = call["data"]
    plans = [p for p in change.get("plans", []) if p.get("id") == change.get("current_plan_id") == scope.plan_id]
    if len(plans) != 1:
        return "status_inspection_current_plan_missing"
    plan = plans[0]
    if (any(change.get(k) != getattr(scope, k) for k in ("customer_id", "program_id"))
            or change.get("id") != scope.change_id
            or any(plan.get(k) != getattr(scope, k) for k in
                   ("change_id", "customer_id", "program_id", "job_id", "implementation_link_id"))):
        return "status_inspection_plan_scope_mismatch"
    roles = {w.specialist for w in triage.specialists_required}
    if not {"validation_evidence", "program_commercial"} <= roles:
        return "status_inspection_required_specialists_missing"
    return None


def validate_status_reads(output, registry, invocation_id, role):
    """Require specialist-owned, cited current reads; intake snapshots cannot substitute."""
    scope = registry.state.triage.status_inspection if registry.state.triage else None
    if not scope:
        return
    cited = {r.source_id for r in output.source_references}
    calls = [c for c in registry.calls if c["invocation_id"] == invocation_id
             and c["role"] == role and c["source_id"] in cited]
    common = {k: getattr(scope, k) for k in ("change_id", "program_id", "customer_id", "plan_id")}
    if role == "validation_evidence":
        jobs = []
        for c in calls:
            if c["tool"] == "get_validation_job" and c["arguments"] == {"job_id": scope.job_id}:
                jobs.append(c["data"])
            elif c["tool"] == "get_validation_jobs" and c["arguments"] == {"change_id": scope.change_id}:
                jobs.extend(c["data"].get("items", []))
        matching = [j for j in jobs if j.get("id") == scope.job_id and j.get("owning_system") == "validation"
                    and all(j.get(k) == v for k, v in common.items())]
        if not matching:
            raise HarnessError("status_inspection_job_read_missing")
        for job in matching:
            reservation = job.get("reservation") or {}
            if (reservation.get("id") != job.get("reservation_id") or not reservation.get("id")
                    or reservation.get("job_id") != scope.job_id
                    or any(reservation.get(k) != common[k] for k in ("change_id", "program_id", "plan_id"))):
                raise HarnessError("status_inspection_reservation_mismatch")
    if role == "program_commercial":
        links = [link for c in calls if c["tool"] == "get_implementation_links"
                 and c["arguments"] == {"program_id": scope.program_id, "change_id": scope.change_id}
                 for link in c["data"].get("items", []) if link.get("id") == scope.implementation_link_id]
        # Repeating an identical read is harmless; conflicting returned copies
        # of the same link must still fail rather than selecting one silently.
        links = [link for index, link in enumerate(links) if link not in links[:index]]
        if len(links) != 1 or any(links[0].get(k) != v for k, v in common.items()) or links[0].get("job_id") != scope.job_id:
            raise HarnessError("status_inspection_planner_link_missing")
        link, task = links[0], links[0].get("task") or {}
        if (not task.get("id") or task.get("id") != link.get("task_id")
                or task.get("link_id") != scope.implementation_link_id or task.get("job_id") != scope.job_id
                or any(task.get(k) != common[k] for k in ("change_id", "program_id", "plan_id"))):
            raise HarnessError("status_inspection_planner_task_mismatch")


def status_completion_error(state, registry):
    if state.triage.classified_change_type != "existing_case_status":
        return None
    for role in ("validation_evidence", "program_commercial"):
        results = [r for r in state.completed_assessments if r.specialist == role
                   and not hasattr(r.assessment, "clarification_type")]
        if not results:
            return "status_inspection_required_work_incomplete"
        try:
            for result in results:
                validate_status_reads(result.assessment, registry, result.invocation_id, role)
        except HarnessError as exc:
            return str(exc)
    return None
