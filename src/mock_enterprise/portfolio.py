"""Versioned, deterministic surrounding portfolio. Never imported by HTTP handlers.

The golden case is authored in seed.json. These templates describe fictional
programs and imported history, not predictions or a lab-result simulator.
"""
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256

from .core import Identity, at, canonical, digest, iso

VERSION = 'stratos-portfolio-1'
CUSTOMERS = [
    ('CUST-NORTH', 'Northstar AI', 'applied_model_lab'),
    ('CUST-VELA', 'Vela Compute', 'cloud_infrastructure'),
    ('CUST-MERIDIAN', 'Meridian Systems', 'network_systems'),
    ('CUST-QUANTA', 'QuantaForge AI', 'inference_platform'),
    ('CUST-ARCADIA', 'Arcadia Compute', 'high_performance_computing'),
    ('CUST-NOVA', 'NovaGrid Technologies', 'energy_edge_computing'),
    ('CUST-ATLAS', 'Atlas Robotics', 'industrial_robotics'),
    ('CUST-HORIZON', 'Horizon Intelligence', 'automotive_compute'),
]
# Customer, program name, product, owner, workload concern, health, next action.
TEMPLATES = [
    (0, 'Northstar Boreal', 'BOREAL-N2', 'Elena Park', 'Memory-bandwidth requirement', 'on_track', 'Continue sustained-load qualification against the approved memory profile'),
    (1, 'Vela Stream', 'STREAM-V4', 'Jonas Vale', 'Power-envelope validation', 'on_track', 'Review the extended-load reservation with platform engineering'),
    (2, 'Meridian Relay', 'RELAY-M3', 'Rina Sol', 'Interconnect configuration', 'manufacturing_constraint', 'Resolve pilot-lot traceability before allocating additional samples'),
    (3, 'QuantaForge Prism', 'PRISM-Q2', 'Theo Marin', 'Firmware/runtime compatibility', 'recovery_active', 'Complete engineering disposition of runtime compatibility evidence'),
    (4, 'Arcadia Vector', 'VECTOR-A6', 'Asha Reed', 'Thermal-stability validation', 'validation_risk', 'Compare extended-duration results against the required exposure'),
    (5, 'NovaGrid Ember', 'EMBER-E1', 'Owen Sato', 'Memory configuration', 'blocked', 'Resolve the validation-only sample restriction with manufacturing'),
    (6, 'Atlas Motion', 'MOTION-R3', 'Lena Ortiz', 'Latency acceptance evidence', 'waiting_on_customer', 'Confirm the customer workload concurrency profile'),
    (7, 'Horizon Pilot', 'PILOT-H2', 'Noah Kim', 'Customer acceptance-test revision', 'at_risk', 'Reconcile the proposed acceptance workload with the baseline'),
    (1, 'Vela Mesh', 'MESH-V2', 'Mira Dane', 'Packaging/interface qualification', 'manufacturing_constraint', 'Review assembly provenance and interface qualification evidence'),
    (4, 'Arcadia Tensor', 'TENSOR-A2', 'Evan Rao', 'Qualification evidence update', 'on_track', 'Collect engineering review of the latest qualification campaign'),
]
SCOPES = (('PRG-A17', 'CUST-FML01'),) + tuple((f'PRG-P{i:02}', CUSTOMERS[t[0]][0]) for i,t in enumerate(TEMPLATES,1))


def expand(rows, meta):
    """Append source records only. References and history are validated on import."""
    rows = deepcopy(rows)
    golden = deepcopy(rows)
    def add(kind, record):
        rows.setdefault(kind, []).append(record)
        return record
    def clone(record_type, i, **fields):
        return {**deepcopy(golden[record_type][i]), **fields}
    for cid, name, kind in CUSTOMERS:
        add('engineering.customer', clone('engineering.customer',0,id=cid,name=name,kind=kind))
    for n,t in enumerate(TEMPLATES,1):
        ci,name,product,owner,concern,health,action=t
        pid,cid=f'PRG-P{n:02}',CUSTOMERS[ci][0]
        def rid(prefix, suffix=''):
            return f'{prefix}-P{n:02}' + (f'-{suffix}' if suffix else '')
        def record(kind, i=0, **fields):
            return clone(kind,i,program_id=pid,**fields)
        cfg,oldcfg,work,basework,criteria,proc,policy,order= [rid(x) for x in ('CFG','CFG-OLD','WF','WF-BASE','CRIT','PROC','POLICY','ORD')]
        model=rid('MODEL')
        suite=240+60*(n%4); bins=[8192,32768,65536]; per=suite//3
        add('engineering.configuration',record('engineering.configuration',id=cfg,product_id=product,model_bundle_id=model,firmware=f'FW-{3+n//4}.{n%4}',runtime=f'RT-{5+n//5}.{n%5}',memory_configuration=f'MEM-{2+n%3}',validation_support='Review applicable evidence; no product acceptance implied'))
        add('engineering.configuration',record('engineering.configuration',1,id=oldcfg,product_id=product,model_bundle_id=model,firmware='FW-1.0',runtime='RT-2.0'))
        softwarecfg = rid('CFG-SW') if n in (2,4,6,8) else None
        if softwarecfg:
            add('engineering.configuration',record('engineering.configuration',id=softwarecfg,product_id=product,model_bundle_id=model,firmware='FW-0.9',runtime='RT-1.1',validation_support='Historical software stack; not equivalent to the requested configuration'))
        add('engineering.workload',record('engineering.workload',id=basework,model_bundle_id=model))
        add('engineering.workload',record('engineering.workload',1,id=work,model_bundle_id=model,context_bins=bins,total_suite_minutes=suite,concurrency=2*(n%4+1)))
        add('engineering.criteria',record('engineering.criteria',id=criteria,scope=f'Existing {concern.lower()} limits for {product}. Numerical acceptance thresholds are outside this scheduling model; engineering disposition remains required.'))
        # Generated documents are inline, controlled business templates, never arbitrary paths.
        docids={k:rid('DOC',k.upper()) for k in ('request','procedure','policy')}
        for kind,content in [
            ('request',f'# {CUSTOMERS[ci][1]} — {name}\n\nFictional customer request: {concern.lower()} for {product} REV-B.\n\n{action}. The proposed workload is {work}; the baseline is {basework}. Four campaign packages separate primary exposure, repeatability, integration review and customer clarification. Each exact requirement revision is recorded separately. Results apply only to their captured hardware, software and workload. Scheduling conveys no successful test or customer acceptance.'),
            ('procedure',f'# {concern} procedure\n\nApproved synthetic procedure {proc}: setup 60 minutes, execution {suite} minutes ({per} minutes for each of {bins}), then 120 minutes of engineering review. Supports {cfg} and workload {work}. Existing criteria {criteria} remain unchanged. The operating model covers evidence scheduling, not physical simulation.'),
            ('policy',f'# Delegated supplemental validation authority\n\nAn explicitly selected simulated engineer may approve {proc} for {name}, up to USD 2,000 incremental cost. Approval binds an immutable plan and its complete critical source versions. Only scheduling validation and linking the internal program plan are authorized. Manufacturing, ERP, results and acceptance criteria remain read-only.')]:
            d=record('engineering.document',id=docids[kind],customer_id=cid,document_type='customer_request' if kind=='request' else kind,status='requested' if kind=='request' else 'approved',document_version='1',content=content,content_hash=sha256(content.encode()).hexdigest())
            add('engineering.document',d)
        add('engineering.procedure',record('engineering.procedure',id=proc,document_id=docids['procedure'],supported_configuration_ids=[cfg],workload_profile_id=work,setup_minutes=60,suite_minutes=suite,per_bin_minutes=per,review_minutes=120,acceptance_limits_ref=criteria))
        add('engineering.policy',record('engineering.policy',id=policy,permitted_procedure_ids=[proc],document_id=docids['policy']))
        reqs=[]
        for k,package in enumerate(('primary exposure','repeatability','integration review','customer clarification'),1):
            for v in (1,2):
                req=rid('REQ',f'{k}-V{v}')
                add('engineering.requirement',record('engineering.requirement',v-1,id=req,requirement_id=rid('REQ',str(k)),revision=v,customer_id=cid,configuration_id=cfg,workload_profile_id=basework if v==1 else work,acceptance_limits_ref=criteria,summary=f'{concern}: {package} / '+('approved baseline' if v==1 else 'requested supplemental evidence')))
            reqs.append(req)
            state='pending_impact_assessment' if k<4 else ('new','awaiting_customer_clarification','blocked','closed','superseded')[n%5]
            next_action=action if k<4 else {'new':'Triage the new customer package','awaiting_customer_clarification':'Obtain the requested workload definition from the customer','blocked':'Resolve the recorded manufacturing restriction before scheduling','closed':'No further supplemental work; customer clarification package withdrawn','superseded':'Use the primary exposure package; this duplicate scope was consolidated'}[state]
            add('engineering.change',record('engineering.change',id=f'CR-{100+n*4+k:03}',customer_id=cid,baseline_requirement_revision_id=rid('REQ',f'{k}-V1'),proposed_requirement_revision_id=req,configuration_id=cfg,milestone_id=rid('MS',str(k)),order_id=order,request_document_id=docids['request'],workflow_state=state,title=f'{concern} — {package}',category=concern,owner=owner,priority=('critical','high','medium','low')[(n+k)%4],next_action=next_action,request_received_at=iso(at(meta['scenario_now'])-timedelta(days=n+k,hours=k)),updated_at=iso(at(meta['scenario_now'])-timedelta(hours=n+k))))
        for k in range(2):
            add('erp.order',record('erp.order',id=order if k==0 else rid('ORD','FOLLOWON'),customer_id=cid,product_id=product,quantity=64*(n+k+1),committed_delivery_at=iso(at('2026-12-01T18:00:00Z')+timedelta(days=n*2+k*14)),status='open' if k==0 else 'allocation_pending'))
        milestones=[]
        names=['Primary exposure review','Repeatability review','Integration evidence review','Customer workload clarification','Sample allocation gate','Qualification dossier review','Pilot readiness review','Customer delivery readiness','Baseline package archived']
        for k,label in enumerate(names,1):
            mid=rid('MS',str(k)); milestones.append(mid)
            date=iso(at('2026-11-20T18:00:00Z')+timedelta(days=n+k)) if k<9 else '2026-11-02T18:00:00Z'
            deps=[dict(kind='requirement_evidence',requirement_revision_id=reqs[(k-1)%4],state='pending_assessment' if k<5 else ('completed' if k==9 else 'review_required'),owner=owner,note=f'{label}: reconcile exact workload evidence'),dict(kind='requirement_evidence',requirement_revision_id=rid('REQ',f'{(k-1)%4+1}-V1'),state='completed',owner=owner,note='Approved baseline retained; proposed revision requires separate disposition')]
            if k == 9:
                deps[0]['requirement_revision_id'] = rid('REQ','1-V1')
                deps[0]['note'] = 'Archive the approved baseline package; no requested revision accepted'
                deps[1]['requirement_revision_id'] = rid('REQ','2-V1')
            add('planner.milestone',record('planner.milestone',id=mid,order_id=order,name=label,baseline_at=date,current_forecast_at=date,dependencies=deps,owner=owner,health='completed' if k==9 else health,next_action='Baseline archived; no proposed requirement promoted' if k==9 else action))
        add('planner.program',record('planner.program',id=pid,customer_id=cid,name=name,business_unit='Advanced Compute Programs',product_id=product,configuration_id=cfg,owner=owner,milestone_ids=milestones,order_id=order,lifecycle=('pilot_validation','qualification','integration_review')[n%3],health=health,next_action=action))
        for k in range(2):
            add('erp.rate',record('erp.rate',id=rid('RATE',str(k)),incremental_cost_cents=0 if k==0 else 90000+5000*n,service_name='Standard validation service' if k==0 else 'Extended runtime qualification',service_description=f'{name}: setup and {suite}-minute evidence campaign. Rate approval does not establish test coverage.',effective_to='2027-02-01T00:00:00Z'))
            add('validation.lab',record('validation.lab',id=rid('LAB',str(k)),campus=f'CAMPUS-{n%3+2}',supported_configuration_ids=[cfg,oldcfg],supported_procedure_ids=[proc]))
        restrictions=['engineering_hold','quality_hold','review_required','validation_only']
        for k in range(5):
            restriction=restrictions[n%4] if k==3 else None
            state=restriction or ('available','allocated','released','available','consumed')[k]
            detail=[] if not restriction else [dict(restriction=restriction,rationale={'engineering_hold':'Pilot assembly traceability awaits engineering review. No hardware failure is recorded.','quality_hold':'Supplier certificate reconciliation remains open; this is an administrative quality restriction.','review_required':'Configuration genealogy needs review before sample allocation.','validation_only':'Evaluation material is restricted to the approved qualification campaign; general allocation needs disposition.'}[restriction],responsible_team='Partner Quality' if restriction=='quality_hold' else 'Pilot Manufacturing Engineering',release_conditions='Reconcile the source dossier and record authorized disposition in the manufacturing system. No release control is exposed here.')]
            add('manufacturing.lot',record('manufacturing.lot',id=rid('LOT',str(k)),product_id=product,product_revision='REV-A' if k==4 else 'REV-B',restrictions=[restriction] if restriction else [],hold_details=detail,inventory_state=state))
        for k in range(11):
            lot=k%5; cfgid=oldcfg if lot==4 else cfg
            add('manufacturing.unit',record('manufacturing.unit',id=rid('UNIT',str(k)),source_lot_id=rid('LOT',str(lot)),product_id=product,product_revision='REV-A' if lot==4 else 'REV-B',restrictions=[],inventory_state=('available','allocated','released','review_required','consumed')[lot]))
            if k<5:
                add('validation.sample',record('validation.sample',id=rid('SAMPLE',str(k)),unit_id=rid('UNIT',str(k)),configuration_id=cfgid,campus=f'CAMPUS-{n%3+2}',availability='unavailable' if k==4 else 'available'))
                start=at('2026-11-17T06:00:00Z')+timedelta(days=k*2+n%3)
                add('validation.slot',record('validation.slot',id=rid('SLOT',str(k)),lab_id=rid('LAB',str(k%2)),rate_id=rid('RATE',str(k%2)),starts_at=iso(start),ends_at=iso(start+timedelta(hours=10)),availability='unavailable' if k==4 else 'available'))
        # Historical observations are authored independently of scheduled work.
        for k in range(11):
            variant=k%6
            configid=oldcfg if variant==1 else (softwarecfg if softwarecfg and variant==5 else cfg)
            profile=basework if variant==0 else work
            observed_bins=[8192,32768] if variant==0 else (bins[:2] if variant==4 else bins)
            minutes=60 if variant==0 else (20 if variant==3 else per)
            # Only selected programs have a full matching pass; others retain a real gap.
            passed=variant!=5 and not (variant==2 and n%2==0)
            add('validation.result',record('validation.result',id=rid('RES',str(k)),customer_id=cid,configuration_id=configid,configuration_content_version=1,workload_profile_id=profile,acceptance_limits_ref=criteria,product_revision='REV-A' if variant==1 else 'REV-B',model_bundle_id=model,sample_id=rid('SAMPLE','4' if variant==1 else str(k%3)),status='completed',criteria_passed=passed,covered_context_bins=observed_bins,actual_suite_minutes=minutes*len(observed_bins),observed_minutes_by_context_bin={str(b):minutes for b in observed_bins},completed_at=iso(at('2026-11-04T16:00:00Z')+timedelta(hours=k*12))))
        add('validation.history',dict(id=rid('HJOB'),program_id=pid,customer_id=cid,content_version=1,updated_at=meta['scenario_now'],owning_system='validation',synthetic=True,configuration_id=cfg,procedure_id=proc,sample_id=rid('SAMPLE','2'),lab_id=rid('LAB','0'),status='completed' if n%2 else 'engineering_disposition_pending',started_at=iso(at('2026-11-05T16:00:00Z')-timedelta(minutes=suite)),completed_at='2026-11-05T16:00:00Z',result_ids=[rid('RES','2')],recorded_by=f'{name} Lab Operations',source_reference=rid('LAB-LOG','EXPOSURE'),note='Authored synthetic historical execution record. Its linked observation is independent of new bookings; engineering/customer acceptance is not asserted.'))
    # Resolve historical snapshots from the generated records, never a current lookup at display time.
    indexes={kind:{r['id']:r for r in records} for kind,records in rows.items()}
    for result in rows['validation.result']:
        if result['program_id']=='PRG-A17': continue
        for field,kind,key in [('configuration_snapshot','engineering.configuration','configuration_id'),('workload_snapshot','engineering.workload','workload_profile_id'),('criteria_snapshot','engineering.criteria','acceptance_limits_ref')]:
            result[field]=deepcopy(indexes[kind][result[key]])
    meta={**meta,'generator_version':VERSION,'portfolio_scopes':[list(s) for s in SCOPES]}
    return rows,meta


def seed_history(store):
    """Import explicit synthetic plan history with computed immutable scope.

Not an HTTP request, human approval or AI execution. This initializer runs only
inside the guarded seed transaction, before a service can use the new file.
    """
    from .db import MODELS
    from .domains.validation_rules import context, coverage, calculate_option, ACTIONS
    from .snapshots import source_snapshot, plan_digest
    events=[]
    def event(record, action, changes, *, actor='synthetic-source-import', role='source_import', plan=None, approval=None, job=None):
        events.append(dict(id=f'evt-import-{len(events)+1:04}',synthetic=True,scenario_at=record['updated_at'],wall_clock_at=record['updated_at'],domain=record['owning_system'],actor_id=actor,actor_role=role,program_id=record.get('program_id'),customer_id=record.get('customer_id') or store.get('planner.program',record['program_id'])['customer_id'],change_id=record.get('change_id') or (record['id'] if action=='change_received' else None),action=action,outcome='succeeded',resource_id=record['id'],plan_id=plan,approval_id=approval,job_id=job,request_id=f'import-{len(events)+1:04}',correlation_id=VERSION+'-'+record['program_id'],idempotency_hash=None,changes={'provenance':'authored synthetic initial history',**changes}))
    for n,_ in enumerate(TEMPLATES,1):
        pid,cid=SCOPES[n]; actor=Identity('demo-portfolio-automation','automation',pid,cid)
        def meta(owner,id): return dict(id=id,program_id=pid,content_version=1,updated_at=store.now,synthetic=True,owning_system=owner)
        for kind,action in [('engineering.change','change_received'),('validation.result','evidence_imported'),('manufacturing.lot','manufacturing_status_imported'),('erp.order','customer_commitment_imported'),('planner.milestone','milestone_baseline_imported')]:
            for r in store.list(kind,actor):
                changes={k:r[k] for k in ('title','status','criteria_passed','completed_at','inventory_state','restrictions','committed_delivery_at','baseline_at','health') if k in r}
                event(r,action,changes)
        for k in range(1,4):
            changeid=f'CR-{100+n*4+k:03}'; ctx=context(store,actor,changeid)
            slot=store.get('validation.slot',f'SLOT-P{n:02}-{k-1}',actor); sample=store.get('validation.sample',f'SAMPLE-P{n:02}-{k-1}',actor)
            option=calculate_option(store,actor,ctx,slot,sample)
            if not option['approval_eligible']: raise ValueError('Synthetic history must use eligible, within-policy resources')
            evidence=coverage(store,actor,ctx)
            assessment=dict(facts=[dict(text=f"{ctx['change']['title']}. Review the exact exposure profile and independently recorded observations.",source_refs=[dict(resource_type='engineering.change',resource_id=changeid)])],evidence_gaps=[] if evidence['coverage_satisfied'] else ['No complete passing result for this exact exposure profile.'],unresolved_questions=['Future execution and engineering/customer disposition remain unknown.'])
            planid=f'plan-P{n:02}-{k}'
            plan={**meta('engineering',planid), 'customer_id':cid,'change_id':changeid,'plan_version':1,'plan_digest':'0'*64,'supersedes_plan_id':None,'target_requirement_revision_id':ctx['target']['id'],'configuration_id':ctx['config']['id'],'procedure_id':ctx['procedure']['id'],'sample_id':sample['id'],'slot_id':slot['id'],'milestone_id':ctx['milestone']['id'],'policy_id':ctx['policy']['id'],'assessment':assessment,'source_snapshot':source_snapshot(store,actor,ctx,option,assessment),'evidence_set_digest':evidence['evidence_set_digest'],'cost_cents':option['cost_cents'],'currency':'USD','timing':option['timing'],'review_minutes':ctx['procedure']['review_minutes'],'permitted_actions':ACTIONS,'coverage':evidence,'created_by':actor.id}
            plan=MODELS['engineering.plan'].model_validate(plan).model_dump(mode='json');plan['plan_digest']=plan_digest(plan);store.insert('engineering.plan',plan)
            decided=k<3 or n%3!=0; approved=k<3 or n%3==1; decisionid=f'decision-P{n:02}-{k}' if decided else None
            state='approved' if decided and approved else ('rejected' if decided else 'draft')
            store.insert('engineering.plan_state',dict(id=planid,program_id=pid,state=state,record_version=2 if decided else 1,decision_id=decisionid))
            store.update('engineering.change',changeid,dict(current_plan_id=planid,workflow_state={'approved':'approved_awaiting_scheduling','rejected':'plan_rejected','draft':'plan_drafted'}[state],record_version=3 if decided else 2, updated_at=store.now))
            event(plan,'assessment_recorded',{'plan_digest':plan['plan_digest']},actor=actor.id,role=actor.role,plan=planid)
            if decided:
                decision={**meta('engineering',decisionid),'customer_id':cid,'change_id':changeid,'plan_id':planid,'plan_version':1,'plan_digest':plan['plan_digest'],'decision':'approve' if approved else 'reject','signer_identity':'demo-portfolio-engineer','signer_role':'engineer','reason':'Authored synthetic initial engineering disposition: '+('authorize this exact supplemental scope; no test outcome or acceptance implied.' if approved else 'requested repeat scope needs clarification before spend authorization.'),'policy_id':ctx['policy']['id'],'policy_content_version':ctx['policy']['content_version'],**{f:plan[f] for f in ('cost_cents','permitted_actions','source_snapshot','configuration_id','sample_id','slot_id','milestone_id')}}
                store.insert('engineering.decision',decision);event(decision,'engineering_decision_imported',{'plan_state':['draft',state]},actor='demo-portfolio-engineer',role='engineer',plan=planid,approval=decisionid)
            if k==3: continue
            jobid=f'job-P{n:02}-{k}'; resid=f'reservation-P{n:02}-{k}'
            job={**meta('validation',jobid),'customer_id':cid,'change_id':changeid,'plan_id':planid,'approval_id':decisionid,'plan_digest':plan['plan_digest'],**{f:plan[f] for f in ('configuration_id','procedure_id','sample_id','slot_id','cost_cents','timing','review_minutes')},'workload_profile_id':ctx['workload']['id'],'lab_id':slot['lab_id'],'status':'scheduled','reservation_id':resid}
            store.insert('validation.job',job)
            store.insert('validation.reservation',{**meta('validation',resid),'change_id':changeid,'plan_id':planid,'job_id':jobid,'slot_id':slot['id'],'sample_id':sample['id'],'lab_id':slot['lab_id'],'starts_at':plan['timing']['lab_start_at'],'ends_at':plan['timing']['lab_end_at'],'slot_version_before':1,'slot_version_after':2,'sample_version_before':1,'sample_version_after':2})
            for kind,r in [('validation.slot',slot),('validation.sample',sample)]:store.update(kind,r['id'],dict(availability='reserved',availability_version=2,reserved_by_job_id=jobid))
            event(job,'validation_booking_imported',{'status':['unscheduled','scheduled'],'result_created':False},actor=actor.id,role=actor.role,plan=planid,approval=decisionid,job=jobid)
            if k==2: continue # Deliberate partial follow-through; planner action is still outstanding.
            linkid=f'link-P{n:02}-{k}';taskid=f'task-P{n:02}-{k}';mid=ctx['milestone']['id'];forecast=plan['timing']['review_ready_at']
            linked={**meta('planner',linkid),'customer_id':cid,'change_id':changeid,'plan_id':planid,'approval_id':decisionid,'job_id':jobid,'milestone_id':mid,'task_id':taskid,'forecast_at':forecast,'milestone_version_before':1,'milestone_version_after':2,'status':'linked'}
            store.insert('planner.link',linked);store.insert('planner.task',{**meta('planner',taskid),'change_id':changeid,'plan_id':planid,'job_id':jobid,'milestone_id':mid,'link_id':linkid,'name':ctx['change']['title']+' / engineering review','status':'scheduled','forecast_at':forecast})
            deps=ctx['milestone']['dependencies'];deps[0]['state']='validation_scheduled';deps.append(dict(kind='validation_job',job_id=jobid,state='scheduled'))
            store.update('planner.milestone',mid,dict(current_forecast_at=forecast,forecast_status='conditional_on_test_and_review',record_version=2,dependencies=deps))
            event(linked,'program_link_imported',{'forecast':[ctx['milestone']['current_forecast_at'],forecast]},actor=actor.id,role=actor.role,plan=planid,approval=decisionid,job=jobid)
    for e in events:
        store.con.execute('INSERT INTO audit_events(id,program_id,change_id,data) VALUES(?,?,?,?)',(e['id'],e['program_id'],e['change_id'],canonical(e)))
