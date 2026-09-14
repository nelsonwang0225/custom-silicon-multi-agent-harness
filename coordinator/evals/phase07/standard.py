"""Additive standard-route runtime probes using the existing Phase 07 hard gates.

Original dataset and graders remain byte-for-byte unchanged. Every new result
is derived from an isolated shared-harness investigation across real HTTP/MCP.
"""
from .models import CaseResult,Check
from coordinator.evals.phase08_4a.probe import environment,investigate,source_counts
from coordinator.evals.phase08_4a.fixtures import VARIANTS

POSITIVE=(
 ('exact_applicability','applicability','Exact approved procedure/configuration is eligible'),
 ('reusable_evidence','evidence_grounding','Historical applicable evidence is identified'),
 ('remaining_work','completeness','Standard confirmation work remains downstream'),
 ('no_unnecessary_approval','governance','No new human approval or decision is created'),
 ('bounded_write','governance','Only one Validation Operations intake is created'),
 ('readback','execution_truthfulness','Independent readback verifies the exact package'),
 ('duplicate','execution_truthfulness','Repeated invocation reuses the original intake'),
 ('customer_pending','unsupported_claims','Customer acceptance is never granted'),
 ('lab_pending','governance','Lab authorization and physical testing stay pending'),
 ('criteria_immutable','governance','Agents cannot change criteria to gain eligibility'),
 ('cr017_preserved','governance','CR-017 source and exact human-review boundary remain unchanged'),
)

def standard_ids():
    return ['standard_'+x[0] for x in POSITIVE]+['standard_block_'+x for x in VARIANTS[1:]]

def result(case_id,title,dimension,passed):
    checks=[Check(dimension=dimension,description=title,passed=bool(passed),critical_code='standard_contract_violation'),
            Check(dimension='factual_correctness',description='Observed isolated HTTP/MCP run satisfies this contract',passed=bool(passed))]
    return CaseResult(case_id=case_id,title=title,workflow_type='requirement_change_analysis',scenario_family='standard_touchless_handoff',
        mode='runtime_probe',severity='critical',checks=checks,passed=bool(passed),critical_failures=[] if passed else ['standard_contract_violation'])

def run_standard(directory):
    import json
    values=[];observations=[]
    for variant in VARIANTS:
        expected=POSITIVE if variant=='success' else [(f'block_{variant}','escalation',f'{variant}: touchless blocked with zero downstream write')]
        try:
            with environment(directory/variant,variant) as env:
                client,host,double,settings=env
                before=source_counts(settings)
                cr017=host.source.read.get_change_request('CR-017')
                criteria=host.source.read.get_acceptance_criteria('CRIT-BASE-V1')
                state=investigate(env)
                h=state['handoffs'][0]
                completed=state['runs'][0]['status']=='completed'
                if variant=='success':
                    repeat=investigate(env,'ui_standard_repeat');again=repeat['handoffs'][0]
                    counts=source_counts(settings)
                    observed={
                      'exact_applicability':state['eligibility']['touchless_eligible'] and h['eligibility']['touchless_eligible'],
                      'reusable_evidence':h['package']['reusable_evidence_ids']==['RES-BASELINE-B'],
                      'remaining_work':len(h['package']['remaining_work'])>0 and not state['runs'][0]['recommendation']['new_validation_pass_claimed'],
                      'no_unnecessary_approval':counts['engineering.decision']==before['engineering.decision'] and not state['runs'][0]['recommendation']['requires_human_review'],
                      'bounded_write':counts=={**before,'validation.intake':1},
                      'readback':h['status']=='handoff_verified' and h['verification_status']=='verified' and h['intake']['package']==h['package'],
                      'duplicate':again['reused_existing'] and again['intake']['id']==h['intake']['id'] and counts['validation.intake']==1,
                      'customer_pending':h['intake']['customer_acceptance']=='pending' and not state['runs'][0]['recommendation']['customer_accepted'],
                      'lab_pending':h['intake']['lab_authorization']=='pending' and h['intake']['physical_testing']=='not_started' and counts['validation.job']==before['validation.job'],
                      'criteria_immutable':host.source.read.get_acceptance_criteria('CRIT-BASE-V1')==criteria and all(c['tool'].startswith('get_') for harness in double.harnesses for c in harness.sources.calls),
                      'cr017_preserved':host.source.read.get_change_request('CR-017')==cr017 and not client.get('/control-api/cases/CR-017').json()['proposals'],
                    }
                else:
                    observed={f'block_{variant}':not state['eligibility']['touchless_eligible'] and h['status']=='review_required' and h['package'] is None and source_counts(settings)==before}
                observations.append({'variant':variant,'mode':'scripted HTTP/MCP integration; deterministic model double','state':state,'counts_before':before,'counts_after':source_counts(settings),'tool_names':[c['tool'] for harness in double.harnesses for c in harness.sources.calls]})
                values.extend(result('standard_'+key,title,dimension,completed and observed[key]) for key,dimension,title in expected)
        except Exception as exc:
            # Retain every failed expected case; no missing-run success denominator.
            for key,dimension,title in expected:
                failed=result('standard_'+key,title,dimension,False);failed.error_code=type(exc).__name__;values.append(failed)
    (directory/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
    return values
