"""Deterministic standard-handoff policy, independently enforced by host and source.

Pure functions over typed HTTP data. Neither model conclusions nor a policy ID
alone grant authority. No clocks, filesystem, databases, tools or network calls.
"""
import hashlib
import json
from datetime import datetime
from .standard_models import (StandardContext, ConfigurationBinding, TouchlessEligibility,
                              RuleCheck, HandoffPackage, EvidenceReference)


def digest(value):
    if hasattr(value, 'model_dump'):
        value = value.model_dump(mode='json')
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def configuration_binding(value):
    return ConfigurationBinding(configuration_id=value['id'], **{k: value[k] for k in ConfigurationBinding.model_fields if k != 'configuration_id'})


def evaluate(context: StandardContext):
    r, rule, checks = context.request, context.rule, []
    def check(code, passed, reason):
        checks.append(RuleCheck(code=code, passed=bool(passed), reason=reason))
    scope = (context.customer_id, context.program_id)
    try:
        request_document_matches = json.loads(context.request_document.get("content", "")) == r.model_dump(mode="json")
    except (ValueError, TypeError):
        request_document_matches = False
    check('REQUEST_SCOPE', (r.customer_id, r.program_id) == scope and r.change_id == context.change_id
          and context.change.get('id') == r.change_id and context.change.get('request_document_id') == r.request_document_id
          and context.request_document.get('id') == r.request_document_id and request_document_matches,
          'The source request, change and customer/program must agree.')
    check('RECOGNIZED_STANDARD_CHANGE', r.request_type == 'add_approved_profile', 'Only addition of an approved profile is standard.')
    approved = bool(rule and rule.status == 'approved' and (rule.customer_id, rule.program_id) == scope
                    and context.policy_document and context.policy_document.get('id') == rule.document_id
                    and context.policy_document.get('status') == 'approved')
    check('APPROVED_ROUTING_POLICY', approved, 'An approved, scoped routing policy and its approved business document are required.')
    baseline = context.baseline or {}
    check('APPROVED_BASELINE', baseline.get('id') == r.baseline_requirement_revision_id
          and baseline.get('content_version') == r.baseline_content_version and baseline.get('status') == 'approved'
          and context.change.get('baseline_requirement_revision_id') == context.change.get('proposed_requirement_revision_id') == baseline.get('id'),
          'The exact approved requirement remains unchanged; this is a package update.')
    procedure = context.procedure or {}
    check('APPROVED_PROCEDURE', rule and r.procedure_id == rule.procedure_id == procedure.get('id')
          and r.procedure_content_version == rule.procedure_content_version == procedure.get('content_version')
          and procedure.get('status') == 'approved' and context.procedure_document
          and context.procedure_document.get('id') == procedure.get('document_id') and context.procedure_document.get('status') == 'approved',
          'The exact approved procedure/version and its approved method document must exist.')
    config = context.configuration or {}
    try:
        current_binding = configuration_binding(config)
    except (KeyError, ValueError, TypeError):
        current_binding = None
    check('EXACT_HARDWARE_CONFIGURATION', r.configuration and rule and current_binding
          and all(getattr(r.configuration, k) == getattr(rule.configuration, k) == getattr(current_binding, k)
                  for k in ('configuration_id','content_version','product_id','product_revision','device_count','model_bundle_id','memory_configuration','quantization'))
          and context.program.get('configuration_id') == config.get('id')
          and config.get('id') in procedure.get('supported_configuration_ids', []),
          'The requested and approved current hardware, model, memory and quantization configuration must match exactly.')
    check('EXACT_SOFTWARE_BASELINE', r.configuration and rule and current_binding
          and all(getattr(r.configuration,k) == getattr(rule.configuration,k) == getattr(current_binding,k) for k in ('firmware','runtime')),
          'Firmware and runtime must match the explicitly approved versions.')
    workload = context.workload or {}
    check('APPROVED_OPERATING_CONDITIONS', rule and r.conditions and r.conditions == rule.conditions
          and r.workload_profile_id == rule.workload_profile_id == workload.get('id') == procedure.get('workload_profile_id')
          and r.workload_content_version == rule.workload_content_version == workload.get('content_version')
          and all(getattr(r.conditions,k) == workload.get(k) for k in type(r.conditions).model_fields)
          and procedure.get('suite_minutes') == r.conditions.total_suite_minutes
          and procedure.get('per_bin_minutes', 0) * len(r.conditions.context_bins) == r.conditions.total_suite_minutes,
          'The named profile, every operating parameter and method duration must be explicitly approved; no size-based inference.')
    criteria = context.criteria or {}
    check('UNCHANGED_ACCEPTANCE_CRITERIA', rule and not r.changes_acceptance_criteria
          and rule.criteria_id == criteria.get('id') == baseline.get('acceptance_limits_ref') == procedure.get('acceptance_limits_ref')
          and rule.criteria_content_version == criteria.get('content_version') and criteria.get('status') == 'approved',
          'Acceptance criteria stay at their exact approved version; no waiver or threshold change.')
    reusable, conflicting = [], []
    for evidence in context.evidence:
        exact = all(evidence.get(k) == v for k,v in {
            'configuration_id':config.get('id'), 'configuration_content_version':config.get('content_version'),
            'workload_profile_id':workload.get('id'), 'workload_profile_content_version':workload.get('content_version'),
            'acceptance_limits_ref':criteria.get('id'), 'acceptance_criteria_content_version':criteria.get('content_version')}.items())
        exact = exact and all(evidence.get(s) == v for s,v in [('configuration_snapshot',config),('workload_snapshot',workload),('criteria_snapshot',criteria)])
        if not exact:
            continue
        if evidence.get('status') == 'completed' and evidence.get('criteria_passed') is False:
            conflicting.append(evidence.get('id'))
        if (evidence.get('status') == 'completed' and evidence.get('criteria_passed') is True
                and evidence.get('completed_at', '9999') <= context.scenario_at
                and evidence.get('covered_context_bins') == workload.get('context_bins')
                and evidence.get('actual_suite_minutes') == workload.get('total_suite_minutes')
                and evidence.get('observed_minutes_by_context_bin') == {str(b):procedure.get('per_bin_minutes') for b in workload.get('context_bins', [])}):
            reusable.append(evidence['id'])
    check('NO_CONFLICTING_EVIDENCE', not conflicting, 'No unresolved contradictory observation may invalidate exact applicability.')
    check('REUSABLE_EVIDENCE_AVAILABLE', rule and (not rule.reusable_evidence_required or bool(reusable)), 'The approved route requires actual applicable historical evidence; unknown evidence cannot establish eligibility.')
    check('NO_ENGINEERING_EXCEPTION', not r.material_exception_ids and not r.requests_waiver, 'Open material exceptions and waiver requests require engineering review.')
    check('KNOWN_DOWNSTREAM_OWNER', rule and context.queue and context.queue.status == 'open'
          and context.queue.id == rule.downstream_queue_id and context.queue.owner == rule.downstream_owner
          and context.queue.permitted_action == rule.permitted_action, 'Validation Operations ownership and a named intake queue must be established.')
    check('PERMITTED_ACTION_ONLY', rule and r.requested_action == rule.permitted_action == 'create_standard_validation_intake', 'Only standard intake creation is pre-authorized, never scheduling or approval.')
    check('NO_CONSEQUENTIAL_DECISION', not any([r.changes_acceptance_criteria,r.requests_waiver,r.changes_customer_commitment,r.quality_disposition_requested]), 'No acceptance, customer commitment, engineering waiver or quality disposition can be requested.')
    check('STANDARD_SAMPLE_INPUTS', rule and len(r.sample_ids) == len(set(r.sample_ids)) == rule.sample_count
          and set(r.sample_ids) == {s.get('id') for s in context.samples}
          and all(s.get('configuration_id') == config.get('id') for s in context.samples),
          'The approved number of named samples must match the configuration; intake does not reserve or authorize them.')
    check('TIMING_CONTEXT', context.milestone and context.milestone.get('id') == context.change.get('milestone_id')
          and context.scenario_at <= r.requested_at <= context.milestone.get('baseline_at', ''),
          'Requested package timing must fit the recorded milestone; no forecast or commitment is changed.')
    check('STANDARD_WORK_DEFINED', rule and rule.remaining_work and rule.completion_criteria,
          'Approved remaining work, inputs and completion criteria must be specified; historical evidence does not complete that work.')
    eligible = all(c.passed for c in checks)
    return TouchlessEligibility(touchless_eligible=eligible, policy_path='standard_touchless_handoff' if eligible else 'review_required',
        rule_id=rule.id if rule else None, rule_version=rule.policy_version if rule else None, context_digest=context.context_digest,
        checks=checks, reusable_evidence_ids=sorted(reusable), remaining_work=rule.remaining_work if rule else [],
        requires_human_approval_for_handoff=not eligible)


def build_package(context, *, run_id, case_id, package_id=None):
    eligibility = evaluate(context)
    if not eligibility.touchless_eligible:
        raise ValueError('STANDARD_POLICY_INELIGIBLE')
    r, rule = context.request, context.rule
    records = [context.change, context.baseline, context.configuration, context.workload, context.criteria,
               context.procedure, context.procedure_document, context.policy_document, context.request_document,
               context.milestone, context.queue.model_dump(mode='json'), r.model_dump(mode='json'), rule.model_dump(mode='json'), *context.samples, *context.evidence]
    return HandoffPackage(package_id=package_id or 'package_' + digest([r.id,r.content_version,context.context_digest])[:32],
        customer_id=context.customer_id, program_id=context.program_id, change_id=context.change_id,
        request_id=r.id, request_content_version=r.content_version, customer_request_reference=r.request_reference,
        baseline_requirement_revision_id=r.baseline_requirement_revision_id, baseline_content_version=r.baseline_content_version,
        procedure_id=r.procedure_id, procedure_content_version=r.procedure_content_version, configuration=r.configuration,
        workload_profile_id=r.workload_profile_id, conditions=r.conditions,
        evidence_references=[EvidenceReference(result_id=e['id'],content_version=e['content_version'],result_digest=digest(e))
                             for e in context.evidence if e['id'] in eligibility.reusable_evidence_ids],
        reusable_evidence_ids=eligibility.reusable_evidence_ids, remaining_work=rule.remaining_work, sample_ids=r.sample_ids,
        requested_at=r.requested_at, downstream_queue_id=rule.downstream_queue_id, downstream_owner=rule.downstream_owner,
        completion_criteria=rule.completion_criteria, routing_rule_id=rule.id, routing_rule_version=rule.policy_version,
        context_digest=context.context_digest, source_record_digests={v['id']:digest(v) for v in records},
        workflow_run_id=run_id, workflow_case_id=case_id)
