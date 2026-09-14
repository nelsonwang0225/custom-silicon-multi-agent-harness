"""One semantic layer over existing source/host projections; no business writes.

Current facts outrank old run outcomes. A successful run never substitutes for
source execution/readback or a matching Validation Lab result.
"""
from .integration_models import CaseSummary, DecisionSummary, CaseDependency
from ..application.contracts import digest

ROOT='/control/programs/PRG-A17/cases/'
CASES={
 'CR-017':('requirement_change_analysis','material_change_human_review','Material change','This demo completes when a passing Validation Lab result matches the exact approved plan.','/engineering/changes/CR-017'),
 'CR-019':('requirement_change_analysis','standard_touchless_handoff','Standard change / Touchless','Verified intake is separate from lab authorization, physical testing and customer acceptance.','/engineering/changes/CR-019'),
 'QE-004':('yield_exception_recovery','quality_recovery','Yield / Quality Exception','Recovery routing does not release held material, change tests or reallocate supply.','/manufacturing/quality/QE-004'),
 'QE-011':('yield_exception_recovery','standard_quality_investigation_handoff','Final-test anomaly','Approved standard investigation only; lot remains on hold and customer commitments unchanged.','/manufacturing/quality/QE-011'),
 'DR-009':('delivery_readiness','delivery_commitment','Delivery readiness','A partial commitment does not erase the remaining gap or grant customer agreement.','/erp/delivery/DR-009'),
}
LABELS={'handoff_verified':'Handoff verified','new':'New','investigating':'Investigating','draft_ready':'Operator review','needs_review':'Needs review','approved':'Approved · Execution pending',
 'executing':'Executing','verification_required':'Verification required','waiting_external':'Waiting for external source',
 'completed_technical':'Technical validation complete','completed_recovery':'Recovery workflow complete','escalated':'Escalated','partial_failure':'Partial failure',
 'stale':'Stale · Reassessment required','failed':'Failed','unavailable':'Current source unavailable'}


def decision_status(status, error=None):
    if status in {'stale','superseded'}:return 'stale'
    if error=='VERIFICATION_MISMATCH' or status in {'verification_failed','attention_required','outcome_unknown'}:return 'verification_required'
    if status in {'partial_completion','partially_executed','execution_failed','failed','write_failed'}:return 'partial_failure'
    if status in {'completed_execution','verified','commitment_current'}:return 'executed'
    if status in {'approved','executing','verifying','resuming'}:return 'approved'
    if status=='rejected':return 'rejected'
    return 'needs_review'


def decisions(s):
    rows=[]
    for value in s.operator_escalations:
        if value.stage == 'evidence_review':
            continue
        if any(p.proposal.origin.run_id == value.run_id for p in s.proposals):
            continue
        rows.append(DecisionSummary(id=value.escalation_id,change_id='CR-017',kind='engineering_escalation',
            title=value.subject,status='needs_review',current=True,requires_human=True,
            digest=value.recommendation_digest,required_role='engineer',run_id=value.run_id,
            execution='Operator escalation submitted',
            href=f'{ROOT}CR-017?run={value.run_id}&tab=options&focus=human-decision&escalation={value.escalation_id}'))
    for p in s.proposals:
        # A technical draft is not an Engineering queue item until the Program
        # Operator submits the editable handoff for the same investigation.
        if not any(e.run_id == p.proposal.origin.run_id for e in s.operator_escalations):
            continue
        status=decision_status(p.effective_status,p.execution.error_code)
        current=p.current_check in {'current','completed_before_lab_result'} and p.effective_status not in {'stale','superseded'}
        if not s.source_available:status='unavailable';current=False
        ref=p.proposal
        rows.append(DecisionSummary(id=ref.proposal_id,change_id='CR-017',kind='validation_authorization',
            title='Authorize supplemental validation',status=status,current=current,
            requires_human=current and status=='needs_review' and not p.review,version=ref.proposal_version,
            digest=ref.proposal_digest,source_decision_id=p.review.source_decision_id if p.review else None,
            reviewer=p.review.actor_id if p.review else None,required_role='engineer',run_id=ref.origin.run_id,
            execution=p.effective_status,href=f'/control/decisions/{ref.proposal_id}/{ref.proposal_version}?digest={ref.proposal_digest}'))
    # Historical evidence-review records remain available through their source
    # APIs, but the shortened demo ends at an exact passing lab result. They are
    # therefore not projected as active control-plane decisions.
    for case,v in (('QE-004',s.quality),('QE-011',s.autonomous_quality),('DR-009',s.delivery)):
        if not v or not v.records:continue
        for plan in v.records.plans:
            progress=next((p for p in v.progress if p.plan_id==plan.id),None)
            if case=='QE-004' and (not progress or not progress.submitted_at):
                continue
            review=next((r for r in v.records.decisions if r.plan_id==plan.id and r.plan_digest==plan.plan_digest),None)
            run=next((r for r in v.runs if progress and r.run_id==progress.run_id),None)
            effective=run.business_outcome if run else progress.status if progress else 'awaiting_review'
            status=decision_status(effective,progress.error_code if progress else None)
            current=v.source_available and effective!='stale'
            if review and status=='needs_review':status='approved' if review.decision=='approve' else 'rejected'
            if not v.source_available:status='unavailable'
            rows.append(DecisionSummary(id=plan.id,change_id=case,kind='quality_recovery' if case in {'QE-004','QE-011'} else 'delivery_commitment',
                title='Review recovery plan' if case in {'QE-004','QE-011'} else 'Review delivery commitment',status=status,current=current,
                requires_human=current and status=='needs_review' and review is None and (run is None or run.status=='completed'),version=plan.plan_version,digest=plan.plan_digest,
                source_decision_id=review.id if review else None,reviewer=review.signer_identity if review else None,required_role='program_owner',
                run_id=progress.run_id if progress else None,execution=effective,href=ROOT+case+'?plan='+plan.id))
    return rows


def summarize(s, change=None, coverage=None):
    decision_rows=decisions(s)
    values=[]
    for case,(workflow,route,title,boundary,source_href) in CASES.items():
        v={'CR-017':s,'CR-019':s.standard,'QE-004':s.quality,'DR-009':s.delivery,'QE-011':s.autonomous_quality}[case]
        if case=='QE-011' and not v: continue
        available=bool(v and v.source_available)
        runs=v.runs if v else []
        run=runs[0] if runs else None
        own=[d for d in decision_rows if d.change_id==case]
        state='new';attention='none';priority=80;key=case
        detail='Source request exists; no investigation recorded.';next_action='Investigate the current source request.'
        if case=='CR-017':
            attention='blocker';priority=40
            detail='Requested workload evidence gap.'
            if coverage and coverage.get('coverage_satisfied'):
                detail='Applicable workload evidence is available.'
                attention='external';priority=55;next_action='Inspect the current evidence.'
            physical=s.downstream.physical if s.downstream else None
            if physical and physical.job:
                state='waiting_external';attention='external';priority=60
                detail='Validation job scheduled; physical result pending.';next_action='Await the Validation Lab result.'
                if physical.result:
                    key=physical.evidence_digest or key
                    if physical.applicability!='confirmed':
                        state='escalated';attention='blocker';priority=30;detail='The lab result does not match the exact approved validation plan.';next_action='Inspect the recorded mismatch before continuing.'
                    else:
                        state='completed_technical';attention='none';priority=100
                        detail='Passing lab result matched the exact approved plan. Technical validation is complete.'
                        next_action='This demo workflow is complete.'
            # Unresolved execution takes precedence over a lab result or old analysis.
            pending=next((d for d in own if d.kind=='validation_authorization' and d.current and d.status not in {'executed','rejected'}),None)
            if pending:
                key=pending.digest
                state={'needs_review':'needs_review','approved':'approved','verification_required':'verification_required','partial_failure':'partial_failure','unavailable':'unavailable'}.get(pending.status,'stale')
                attention='human_review' if state=='needs_review' else 'failure' if state in {'partial_failure','verification_required'} else 'none';priority=10 if state=='needs_review' else 0 if attention=='failure' else 70
                detail={'needs_review':'Exact supplemental validation plan awaits Engineering approval.','approved':'Exact validation plan approved; governed execution pending.',
                        'partial_failure':'Validation/Planner execution is incomplete; inspect each recorded action.','verification_required':'Action readback or reconciliation is required.'}.get(state,'Proposal needs reassessment.')
                next_action='Review the exact proposal.' if state=='needs_review' else 'Inspect the exact approved plan and continue its governed execution.'
                if pending.execution in {'executing','resuming','verifying'}:
                    state='verification_required' if pending.execution=='verifying' else 'executing'
                    attention='none';priority=90
                    detail='Governed execution is verifying source readback.' if state=='verification_required' else 'The existing governed execution is in progress.'
                    next_action='Read progress and the recorded per-system actions; no new approval or blind retry is implied.'
            elif not (physical and physical.result):
                latest=own[0] if own else None
                if latest and latest.status in {'stale','rejected'}:
                    state='stale' if latest.status=='stale' else 'escalated';attention='stale' if state=='stale' else 'blocker';priority=20;key=latest.digest
                    detail='Validation proposal '+latest.status+'.';next_action='Reassess current sources before preparing a replacement.'
                elif change and change.get('execution_state')=='lab_scheduled_pending_planner':
                    state='partial_failure';attention='failure';priority=0;detail='Validation scheduling succeeded; Planner link remains missing.';next_action='Reconcile the existing scheduled job with Program Planner.'
        elif case=='CR-019' and v:
            h=v.handoffs[0] if v.handoffs else None
            status=h.status if h else None
            key=h.package.context_digest if h and h.package else case
            if status=='handoff_verified':
                state='waiting_external';detail='Handed to Validation Operations';next_action='Lab authorization and physical work remain downstream.';attention='none'
                if v.eligibility and not v.eligibility.touchless_eligible:
                    state='stale';detail='Intake was verified against its recorded scope; current approved applicability has changed.'
                    next_action='Inspect current policy/evidence blockers with Validation Operations; the recorded intake remains historical.'
                    attention='stale';priority=20
            elif status=='review_required' or (v.eligibility and not v.eligibility.touchless_eligible):
                state='escalated';attention='blocker';priority=30;detail='Standard eligibility not established; no touchless intake authorized.';next_action='Resolve the recorded applicability or policy blockers. No approval proposal has been invented.'
            elif status in {'outcome_unknown','verification_failed','action_succeeded'}:
                state='verification_required';attention='failure';priority=0;detail=v.status;next_action='Reconcile the existing intake and verify it before continuing.'
            elif status=='write_failed':
                state='failed';attention='failure';priority=0;detail=v.status;next_action='Inspect the failed handoff and retry through the existing case controls.'
            elif status in {'prepared','action_started'}:
                state='executing';detail=v.status;next_action='Read the existing handoff progress.'
            else:
                # An untouched standard request still needs the operator to
                # launch the investigation. Source availability alone is not a
                # recorded policy result.
                attention='blocker';priority=45
                detail='Source request exists; policy eligibility has not been assessed.'
                next_action='Run the agent investigation to assess the standard route.'
        elif case in {'QE-004','QE-011','DR-009'} and v:
            status=v.status
            context=v.context
            key=context.context_digest if context else case
            progress=v.progress[0] if v.progress else None
            # Legacy QE-004 plans were marked awaiting review before there was
            # an explicit Program Operator submission boundary.
            if case=='QE-004' and status=='awaiting_review' and progress and not progress.submitted_at and not progress.decision:
                status='draft_ready'
            state={'handoff_verified':'handoff_verified','draft_ready':'draft_ready','awaiting_review':'needs_review','approved':'approved','verified':'waiting_external','commitment_current':'waiting_external',
                'partial_completion':'partial_failure','verification_failed':'verification_required','outcome_unknown':'verification_required',
                'failed':'failed','stale':'stale','readiness_blocked':'escalated','review_required':'escalated','escalated':'escalated','rejected':'escalated'}.get(status,'new')
            if status.endswith('_started'):state='executing'
            if status.endswith('_action_succeeded'):state='verification_required'
            if state=='failed' and progress and any(step.source_id and step.status=='verified' for step in progress.steps.values()):state='partial_failure'
            attention='human_review' if state=='needs_review' else 'failure' if state in {'failed','partial_failure','verification_required'} else 'stale' if state=='stale' else 'blocker'
            priority=10 if attention=='human_review' else 0 if attention=='failure' else 20 if attention=='stale' else 35
            if case in {'QE-004','QE-011'}:
                a=context.analysis if context else None
                detail=f'Quality exception {context.exception.status}; {a.held_quantity} held and ineligible; {a.eligible_quantity}/{a.requested_quantity} eligible supply.' if a else 'Quality source facts unavailable.'
                if status=='verified' and case=='QE-004':
                    state='completed_recovery';detail='Approved Planner recovery task created and independently verified. Product Quality follow-up remains separate.';attention='none';priority=100
                elif status=='verified':detail='Recovery task verified; held material remains governed.';attention='external';priority=60
                if state=='draft_ready':
                    attention='blocker';priority=30
                    detail='Agent recovery recommendation is ready; it has not been submitted to the Program Owner.'
                    next_action='Program Operator reviews, edits and submits the recovery proposal.'
                else:
                    next_action='Review the exact recovery plan as Program Owner.' if state=='needs_review' else 'Reconcile the recorded investigation / recovery task.' if attention=='failure' else 'No further action in this recovery workflow. Product Quality disposition remains separate.' if state=='completed_recovery' else 'Continue the approved investigation; disposition remains separate.' if status=='verified' else 'Inspect comparison, material scope and recovery options.'
            else:
                a=context.analysis if context else None
                detail=f'{a.eligible_quantity}/{a.requested_quantity} eligible; {a.gap_quantity} gap. Technical readiness: {a.technical_readiness}.' if a else 'Delivery source facts unavailable.'
                if status in {'verified','commitment_current'}:
                    detail=f'Commitment and Planner link verified; {a.gap_quantity} gap remains.' if a else detail;attention='external';priority=60
                next_action='Review the exact quantity/date commitment as Program Owner.' if state=='needs_review' else 'Reconcile ERP and Planner separately; preserve the confirmed first step.' if attention=='failure' else 'Resolve the remaining supply gap; customer agreement stays separate.' if status in {'verified','commitment_current'} else 'Inspect technical scope, reconciled inventory and commitment options.'
        if case=='QE-011' and state=='handoff_verified':
            attention='none';priority=100;detail='Standard quality investigation routed and independently verified. Lot remains on hold; root cause unresolved; customer commitment unchanged.'
            next_action='No human approval required for executed actions. Inspect the recorded handoff.'
        # Active or incomplete runtime is never hidden by an old successful handoff.
        if run and run.status=='running':state='investigating';attention='none';priority=90;detail='Agent investigation is running; no new business outcome is implied.';next_action='Read progress; polling never starts a model call.'
        elif run and run.status in {'failed','cancelled'}:
            state='failed';attention='failure';priority=0;detail='Investigation '+run.status+'; source work remains separately recorded.';next_action='Inspect the failed run and current source records before an explicit retry.'
        elif run and run.recommendation and run.recommendation.policy_path=='escalation_required' and state=='new':
            state='escalated';attention='blocker';priority=30;detail='Investigation requires escalation; no new execution authorized.';next_action='Inspect unresolved scope and evidence.'
        if not available:
            state='unavailable';attention='blocker';priority=25;detail='No current business state is confirmed. Retained run observations are historical.';next_action='Restore the source connection and refresh before acting.'
        values.append(CaseSummary(change_id=case,workflow_id=workflow,route=route,title=title,state=state,state_label=LABELS[state],
            detail=detail,next_action=next_action,boundary=boundary,source_available=available,attention=attention,priority=priority,
            issue_key=f'{case}/{state}/'+digest([key,run.run_id if run else None])[:16],run_id=run.run_id if run else None,
            decision_ids=[d.id for d in own],href=ROOT+case,source_href=source_href))
    dependencies=[]
    q,d=s.quality,s.delivery
    if d and d.context:
        c=d.context
        if q and q.context:
            common=sorted({m.id for m in q.context.material}&{m.id for m in c.material})
            if common:dependencies.append(CaseDependency(from_case='QE-004',to_case='DR-009',kind='supply',source_ids=common,
                detail=f'Shared Manufacturing records: {c.analysis.held_quantity} held units remain excluded from eligible delivery supply.',source_available=q.source_available and d.source_available))
        r=c.request
        dependencies.append(CaseDependency(from_case=r.technical_change_id,to_case='DR-009',kind='technical',
            source_ids=[r.configuration_id,r.requirement_revision_id,*([r.technical_change_id] if r.technical_change_id else [])],
            detail=f'{r.configuration_id} / {r.requirement_revision_id}: {c.analysis.technical_readiness}. '+
                ('Current technical validation for '+r.technical_change_id+' is required.' if r.technical_change_id else 'Approved baseline scope; CR-017 requested V2 evidence is a separate obligation.'),source_available=d.source_available))
    return values,decision_rows,dependencies
