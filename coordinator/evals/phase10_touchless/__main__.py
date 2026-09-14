"""Offline QE-011 authority/concurrency scorecard. No live/paid mode exists."""
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
import xml.etree.ElementTree as ET

root=Path('.cache/phase10-touchless')/('eval_'+uuid4().hex)
root.mkdir(parents=True)
command=[sys.executable,'-m','pytest','-q','tests/test_autonomous_quality.py',
    'coordinator/tests/test_phase10_autonomous.py','coordinator/tests/test_phase10_touchless_concurrency.py',
    '--basetemp='+str(root/'test-storage'),'--junitxml='+str(root/'tests.xml')]
result=subprocess.run(command,capture_output=True,text=True)
(root/'tests.log').write_text(result.stdout+result.stderr)
cases=list(ET.parse(root/'tests.xml').iter('testcase')) if (root/'tests.xml').exists() else []
def passed(fragment):
    matches=[c for c in cases if fragment in c.get('name','')]
    return bool(matches) and all(not any(c.find(t) is not None for t in ('failure','error','skipped')) for c in matches)
checks={
    'A_standard_policy_eligible':'test_event_source_shared_workflow_handoff_and_replay',
    'B_approved_quality_knowledge':'test_actual_participation_then_human_handoff_and_operations',
    'C_lot_stays_held':'test_touchless_has_no_decision_or_consequential_writes',
    'D_root_cause_not_fabricated':'test_touchless_has_no_decision_or_consequential_writes',
    'E_standard_handoff_permitted':'test_event_source_shared_workflow_handoff_and_replay',
    'F_no_program_owner_decision':'test_touchless_has_no_decision_or_consequential_writes',
    'G_no_quality_release':'test_touchless_has_no_decision_or_consequential_writes',
    'H_no_customer_commitment_change':'test_touchless_has_no_decision_or_consequential_writes',
    'I_independent_handoff_verification':'test_event_source_shared_workflow_handoff_and_replay',
    'J_ineligible_zero_write_escalation':'test_ineligible_policy_escalates_without_handoff',
    'concurrent_run_evidence_and_activity_isolation':'test_independent_event_and_manual_runs_and_receipts',
    'bounded_retryable_capacity':'test_capacity_denial_is_retryable_and_does_not_claim_or_lose_key',
    'three_active_cases':'test_default_capacity_admits_three_independent_cases_then_rejects_fourth',
    'scoped_reset_preserves_cr017':'test_scoped_autonomous_reset_preserves_concurrent_cr017',
    'full_reset_busy_policy':'test_full_reset_disarms_qe_and_preserves_existing_busy_policy',
    'source_authority_checks':'test_standard_policy_fails_closed_at_source_write_boundary',
}
checks={name:{'test':test,'passed':passed(test)} for name,test in checks.items()}
success=result.returncode==0 and all(c['passed'] for c in checks.values())
report={'status':'PASS' if success else 'FAIL','mode':'offline deterministic HTTP/MCP/SDK doubles',
    'paid_model_calls':False,'live_reasoning_measured':False,'tests':len(cases),'checks':checks,'command':command,
    'artifacts':str(root)}
(root/'scorecard.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
raise SystemExit(0 if success else 1)
