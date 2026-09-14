"""Optional, explicitly paid six-message Concierge smoke against a running live host.

No invocation, approval or execution confirmation is sent. The action case previews
an existing proposal only. Artifacts contain visible turns and safe model telemetry.
"""
import argparse
import json
import time
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4
import httpx
from program_coordinator.control_host.concierge_models import Turn

CASES=[('overview','What needs my attention?',None,'EXPLAIN'),
       ('cr017','Why is CR-017 still open?','CR-017','EXPLAIN'),
       ('qe_cause','What caused QE-004?','QE-004','EXPLAIN'),
       ('dr_quantity','Can we commit 800 units?','DR-009','EXPLAIN'),
       ('approval','Approve this proposal.','CR-017','ACT'),
       ('touchless','Why is CR-019 eligible for touchless routing?','CR-019','EXPLAIN')]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host-url',required=True);p.add_argument('--ui-origin',default='http://127.0.0.1:5188')
    p.add_argument('--allow-paid',action='store_true');p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if not args.allow_paid:p.error('--allow-paid is required; six real manager calls may incur cost')
    for url in (args.host_url,args.ui_origin):
        parsed=urlsplit(url)
        if parsed.scheme!='http' or parsed.hostname!='127.0.0.1' or parsed.username or parsed.password:p.error('Only local loopback HTTP is supported')
    args.output.mkdir(parents=True,exist_ok=False)
    with httpx.Client(base_url=args.host_url,trust_env=False,follow_redirects=False,timeout=15) as client:
        health=client.get('/control-api/health');health.raise_for_status()
        if health.json()['mode']!='live_model':p.error('A configured live-model host is required')
        session='chat_'+uuid4().hex;report=[]
        for name,text,case,intent in CASES:
            mid='msg_'+uuid4().hex;body={'session_id':session,'message_id':mid,'context':'/control/programs/PRG-A17/cases/'+case if case else '/control/overview','text':text}
            response=client.post('/control-api/concierge/messages',json=body,headers={'Origin':args.ui_origin,'X-Stratos-Action':'1','X-Stratos-Demo-Profile':'reader'})
            response.raise_for_status();deadline=time.monotonic()+120
            turn=Turn.model_validate(response.json())
            while turn.status=='running' and time.monotonic()<deadline:
                time.sleep(.5);response=client.get(f'/control-api/concierge/{session}/{mid}');response.raise_for_status();turn=Turn.model_validate(response.json())
            passed=turn.status=='completed' and turn.intent==intent and turn.classification in {'READ','DECISION'}
            report.append({'case':name,'passed_routing_gate':passed,'semantic_review':'Manual review required: inspect grounding, uncertainty, exact references and refusal boundaries','turn':turn.model_dump(mode='json')})
            (args.output/(name+'.json')).write_text(json.dumps(report[-1],indent=2)+'\n')
        result={'mode':'explicit paid manager smoke','approval_or_execution_confirmations':0,'all_routing_gates_passed':all(r['passed_routing_gate'] for r in report),'cases':report}
        (args.output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'all_routing_gates_passed':result['all_routing_gates_passed'],'cases':len(report),'semantic_review':'required'}))
        return 0 if result['all_routing_gates_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
