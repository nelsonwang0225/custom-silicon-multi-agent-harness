"""Concise source-grounded projections. Model text never supplies business facts."""
from urllib.parse import quote
from .concierge_models import Card, Link
from .workflows import physical_outcome
from ..application.models import WorkflowError

CASES = {'CR-017': 'requirement_change_analysis', 'CR-019': 'standard_change',
         'QE-004': 'yield_exception_recovery', 'QE-011': 'yield_exception_recovery', 'DR-009': 'delivery_readiness'}
CASE_ROOT = '/control/programs/PRG-A17/cases/'

def words(value):
    if value is None: return 'Unknown / not recorded'
    if isinstance(value, bool): return 'Yes' if value else 'No'
    if isinstance(value, (list, tuple)): return '; '.join(words(v) for v in value) or 'None recorded'
    if isinstance(value, dict): return '; '.join(f'{k.replace("_", " ")}: {words(v)}' for k,v in value.items())
    return str(value).replace('_', ' ')

def fields(value, names):
    raw = value.model_dump(mode='json') if hasattr(value, 'model_dump') else value
    return [(k.replace('_', ' ').capitalize(), words(raw.get(k))) for k in names]

def case_link(case): return Link(label='Open ' + case, href=CASE_ROOT+case)
def source_link(case):
    system = {'CR-017':'engineering','CR-019':'engineering','QE-004':'manufacturing','QE-011':'manufacturing','DR-009':'erp'}[case]
    return Link(label='Open source app', href=('/'+system+'/quality/'+case if case in {'QE-004','QE-011'} else '/erp/delivery/DR-009' if case=='DR-009' else '/engineering/changes/'+case))
def run_card(run):
    return Card(kind='run', title=run.change_id + ' · ' + (run.business_outcome or 'Outcome unavailable'),
        facts=[('Runtime', words(run.status)), ('Business outcome', run.business_outcome or 'Not recorded'),
               ('Run', run.run_id), ('Invocation source', 'Source event' if run.trigger.kind=='source_event' else 'User initiated'), ('Invocation', run.invocation_id), ('Basis', 'Persisted run; completion alone is not business success')],
        links=[Link(label='Open run', href='/control/runs/'+quote(run.run_id,safe='')), case_link(run.change_id)], run_id=run.run_id)

def views(snapshot): return {'CR-017':snapshot, 'CR-019':snapshot.standard, 'QE-004':snapshot.quality, 'QE-011':getattr(snapshot,'autonomous_quality',None), 'DR-009':snapshot.delivery}
def all_runs(snapshot): return [r for v in views(snapshot).values() if v for r in v.runs]

def resolve(host, context):
    """Resolve route identifiers against installed records, before source access."""
    from urllib.parse import urlsplit, parse_qs
    url=urlsplit(context)
    if url.scheme or url.netloc or '%' in url.path or '\\' in context: raise WorkflowError('CHAT_SCOPE_UNAVAILABLE')
    parts=url.path.rstrip('/').split('/')
    if len(parts)<2 or parts[1]!='control': raise WorkflowError('CHAT_SCOPE_UNAVAILABLE')
    if len(parts)>3 and parts[2] in {'overview','knowledge','scenarios'}:
        raise WorkflowError('CHAT_SCOPE_UNAVAILABLE')
    if len(parts)>3 and parts[2]=='operations' and not (
        len(parts)==4 and parts[3] in {'evals','demo'} or len(parts)==5 and parts[3]=='sessions'):
        raise WorkflowError('CHAT_SCOPE_UNAVAILABLE')
    case=None; proposal=None; run_id=None
    if len(parts)>3 and parts[2]=='programs':
        if parts[3]!='PRG-A17': raise WorkflowError('CHAT_SCOPE_UNAVAILABLE')
        if len(parts)>4:
            if len(parts)!=6 or parts[4]!='cases' or parts[5] not in CASES: raise WorkflowError('CHAT_SCOPE_UNAVAILABLE')
            case=parts[5]
    elif len(parts)>3 and parts[2]=='runs':
        with host.store.transaction() as data:
            run=data.runs.get(parts[3]); record=data.cases.get(run.case_id) if run else None
            if not record or (record.customer_id,record.program_id)!=('CUST-FML01','PRG-A17') or record.change_id not in CASES: raise WorkflowError('RUN_NOT_FOUND')
            case=record.change_id; run_id=run.run_id
    elif len(parts)>3 and parts[2]=='decisions':
        if parts[3]=='evidence': case='CR-017'
        else:
            with host.store.transaction() as data:
                proposal=next((p for p in data.proposals.values() if p.proposal_id==parts[3] and len(parts)==5 and str(p.proposal_version)==parts[4]),None)
                if not proposal or (proposal.origin.customer_id,proposal.origin.program_id)!=('CUST-FML01','PRG-A17'): raise WorkflowError('PROPOSAL_NOT_FOUND')
                case='CR-017'
                supplied=parse_qs(url.query).get('digest')
                if supplied and supplied!=[proposal.proposal_digest]: raise WorkflowError('PROPOSAL_CONTENT_CHANGED')
    elif len(parts)>3 and parts[2]=='workflows':
        matches=[k for k,v in CASES.items() if v==parts[3]]
        if not matches: raise WorkflowError('WORKFLOW_NOT_CONNECTED')
        case=matches[0]
    elif len(parts)>3 and parts[2]=='automations':
        from ..application.demo_identity import READER
        case=host.automations.read(parts[3],READER).case_scope
    elif len(parts)>2 and parts[2] not in {'overview','programs','workflows','decisions','knowledge','operations','scenarios'}:
        raise WorkflowError('CHAT_SCOPE_UNAVAILABLE')
    return dict(case_id=case, proposal_id=proposal.proposal_id if proposal else None,
                proposal_version=proposal.proposal_version if proposal else None, run_id=run_id)

def grounded_cards(host, snapshot, case, topic):
    v=views(snapshot)[case]; links=[case_link(case),source_link(case)]
    if not v or not v.source_available:
        return [Card(kind='status',title=case+' · Current source unavailable',facts=[('State','No current business conclusion is available. Historical runs do not replace a fresh source read.')],links=links)]
    summary=next((item for item in snapshot.case_summaries if item.change_id==case),None)
    cards=[]
    if case=='CR-017':
        coverage=host.source.read.get_validation_coverage(case)
        title=physical_outcome(v.downstream) if v.downstream else 'Current validation evidence'
        cards.append(Card(kind='status',title=case+' · '+title,facts=[('Coverage satisfied',words(coverage['coverage_satisfied'])),
            ('Engineering review',words(v.downstream.physical.engineering_status) if v.downstream else 'Unknown'),
            ('Boundary','Scheduling, completed testing, Engineering review and customer acceptance are separate.')],links=links))
        if topic in {'policy','decision'}:
            proposal=next((p for p in v.proposals if p.effective_status!='superseded'),None)
            if proposal:
                plan=proposal.proposal.source_plan
                rule=next((s.content for s in plan.source_snapshot if s.resource_id==plan.policy_id),None)
                if rule:
                    cards.append(Card(kind='evidence',title='Recorded approval policy · '+plan.policy_id,
                        facts=[('Why approval is required','The exact plan schedules supplemental lab work and links it to the program. Its recorded policy requires an authorized reviewer; investigation does not grant approval.'),
                            ('Required reviewer',{'engineer':'Engineering approver'}.get(rule.get('approver_role'),words(rule.get('approver_role')))),
                            ('Exact plan',plan.id+' · v'+str(plan.plan_version)),
                            ('Cost',f'${plan.cost_cents/100:,.2f} USD'),*fields(rule,['permitted_actions']),
                            ('Boundary','Plan approval does not approve test evidence or customer acceptance.')],
                        links=[Link(label='Review exact decision',href=f'/control/decisions/{proposal.proposal.proposal_id}/{proposal.proposal.proposal_version}?digest={proposal.proposal.proposal_digest}')]))
        for e in coverage['items'][:12]:
            cards.append(Card(kind='evidence',title=e['result']['id'],facts=[('Applicability','Satisfies exact scope' if e['satisfies'] else words(e['mismatch_reasons']))],
                links=[Link(label='Inspect evidence',href=CASE_ROOT+case+'?tab=evidence&evidence='+quote(e['result']['id'],safe=''))]))
        if topic=='options':
            for o in host.source.read.get_validation_options(case)['items'][:12]:
                cards.append(Card(kind='options',title=o['slot']['id']+' · '+o['sample']['id'],facts=[('Cost',f"${o['cost_cents']/100:,.2f} USD"),
                    *fields(o,['resource_eligible','approval_eligible','eligibility_reasons','approval_reasons','timing']),('Evidence','A scheduled option does not supply a test result.')],links=[case_link(case)]))
    elif case=='CR-019':
        c=v.context;r=c.request;rule=c.rule
        cards.append(Card(kind='status',title=case+' · '+v.status,facts=[*fields(r,['request_source','requested_by','procedure_id','procedure_content_version','workload_profile_id','routing_rule_id']),
            ('Configuration',r.configuration.configuration_id if r.configuration else 'Missing'),
            ('Touchless eligibility',words(v.eligibility.touchless_eligible)),('Policy checks',words([x.reason for x in v.eligibility.checks])),
            ('Downstream','Intake is separate from lab authorization, scheduling, physical testing, Engineering review and customer acceptance.')],links=links))
        if rule: cards.append(Card(kind='evidence',title=rule.id,facts=fields(rule,['status','policy_version','permitted_action','downstream_owner','completion_criteria']),links=[case_link(case)]))
        current=next((h for h in v.handoffs if v.runs and h.run_id==v.runs[0].run_id),None)
        if current:
            intake=current.intake
            facts=[*fields(current,['status']),('Intake ID',intake.id if intake else 'Not recorded')]
            intake_links=[case_link(case)]
            if intake:
                facts.extend(fields(intake,['lab_authorization','physical_testing','customer_acceptance']))
                intake_links.append(Link(label='Open Validation intake',href='/validation/intakes/'+quote(intake.id,safe='')))
            cards.append(Card(kind='status',title='Validation Operations handoff',facts=facts,links=intake_links))
    else:
        c=v.context;a=c.analysis
        if not a: raise WorkflowError('CHAT_ANALYSIS_UNAVAILABLE')
        names=['technical_readiness','eligible_quantity','requested_quantity','gap_quantity','customer_ready_quantity','held_quantity','allocated_quantity','timing_status','proposed_at','blockers'] if case=='DR-009' else ['comparable','comparison_reasons','observed_rate_bps','baseline_rate_bps','confirmed_degradation','held_quantity','eligible_quantity','requested_quantity','gap_quantity','root_cause','evidence_status']
        cards.append(Card(kind='status',title=case+' · '+v.status,facts=fields(a,names),links=links))
        if case in {'QE-004','QE-011'}:
            cards.append(Card(kind='evidence',title=c.observation.id,facts=[('Lot',c.exception.lot_id),('Root cause',a.root_cause or 'Unresolved. A yield signal or site correlation does not establish causality.'),
                ('Authority','Held material stays excluded. Recovery planning does not release or reallocate supply.')],links=[case_link(case),source_link(case)]))
        else:
            cards.append(Card(kind='evidence',title=c.request.order_id,facts=[('Customer agreement',c.request.customer_agreement),('Commercial commitment',words(c.commitment.quantity) if c.commitment else 'Not recorded for this request'),
                ('Boundary','Technical acceptance, commercial commitment and physical delivery are separate.'),
                ('Full quantity/date','Supported by current source' if a.full_request_supportable else 'Full request is not supported; no full-delivery date promised.')],links=[case_link(case),source_link(case)]))
        for m in c.material:
            cards.append(Card(kind='evidence',title=m.id+' · '+m.lot_id,facts=fields(m,['disposition','held_quantity','allocated_quantity','eligible_unallocated_quantity']),links=[case_link(case),source_link(case)]))
        if topic=='options':
            for o in a.options:
                raw=o.model_dump(mode='json') if hasattr(o,'model_dump') else o
                cards.append(Card(kind='options',title=words(raw.get('id',raw.get('option_id','Source option'))),facts=[(k.replace('_',' ').capitalize(),words(val)) for k,val in raw.items()],links=[case_link(case)]))
    if summary and cards:
        current=next((c for c in cards if c.kind=='status'),None)
        if current:
            current.title=case+' · '+summary.state_label
            current.facts=[('Current case state',summary.state),('Current source',summary.detail),('Next step',summary.next_action),*current.facts]
    if v.runs:
        cards.append(run_card(v.runs[0]))
    return cards
