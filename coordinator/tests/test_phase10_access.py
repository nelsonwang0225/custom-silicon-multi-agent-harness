"""Persona projection and direct-request regressions; isolated, no paid models."""
from uuid import uuid4
import time
import pytest
from test_phase08_control_host import env, host, investigate, post, headers, snapshot
from program_coordinator.control_host.access import ACTORS, project, can, route_allowed
from program_coordinator.control_host.concierge_models import Route, Telemetry

MATRIX = {
    'automation': ['overview','programs','workflows','decisions','scenarios','knowledge','operations'],
    'engineer': ['overview','programs','decisions','scenarios','knowledge'],
    'program_owner': ['overview','programs','decisions','scenarios'],
    'reader': ['overview','programs','knowledge'],
}

@pytest.mark.parametrize('role', MATRIX)
def test_navigation_and_action_matrix(role):
    actor=ACTORS[role]; cap=project(actor)
    assert cap.surfaces == MATRIX[role]
    assert cap.actor_id == actor.actor_id
    for surface in MATRIX['automation']:
        assert route_allowed(actor,'/control/'+surface) == (surface in MATRIX[role])
    for case in ('CR-017','CR-019','QE-004','DR-009'):
        assert can(actor,case,'investigate') == (role in (('automation','engineer') if case=='CR-019' else ('automation','engineer','program_owner')))
        assert can(actor,case,'review') == (role == ('engineer' if case=='CR-017' else 'program_owner') and case!='CR-019')
        assert can(actor,case,'review_evidence') == (role=='engineer' and case=='CR-017')
        if case == 'QE-004':
            assert can(actor,case,'escalate') == (role == 'automation')
    assert not can(actor,'guessed','review')
    assert not can(actor,'QE-004','release')

@pytest.mark.parametrize('role',[None,'unknown','reader','engineer','program_owner'])
def test_protected_workspaces_cannot_be_read_by_guessing(host,role):
    c,service,double,settings=host
    before=settings.db_path.read_bytes()
    h={} if role is None else headers(role)
    for route in ('operations','operations/runs','operations/health','operations/runs/run_guessed','operations/sessions/chat_guessed','runs/run_guessed','workflows','automations'):
        r=c.get('/control-api/'+route,headers=h)
        assert r.status_code==403,(route,r.text)
    if role in (None,'unknown','reader'):
        assert c.get('/control-api/decisions',headers=h).status_code==403
    assert settings.db_path.read_bytes()==before and double.calls==0


def test_anonymous_projection_scope_and_server_owned_capabilities(host):
    c=host[0]
    cap=c.get('/control-api/capabilities').json()
    assert cap['role']=='reader' and not cap['selected']
    assert not any(cap['case_actions'].values())
    assert c.get('/control-api/capabilities?program_id=PRG-UNKNOWN',headers=headers()).status_code==403
    assert c.post('/control-api/capabilities',json={'can_approve':True},headers=headers()).status_code==405
    assert c.get('/control-api/capabilities',headers=headers('admin')).status_code==403
    assert c.get('/control-api/cases/CR-017').json()['automations']==[]


def test_exact_queue_filtering_and_hidden_permission_not_readiness(host):
    item=investigate(host); c=host[0]
    for role,count in [('automation',1),('engineer',1),('program_owner',0)]:
        rows=c.get('/control-api/decisions',headers=headers(role)).json()
        assert len(rows)==count
    ref=item['execution']['reference']
    before=host[3].db_path.read_bytes()
    for role in ('automation','program_owner','reader'):
        assert post(c,'proposals/review',{'reference':ref,'decision':'approve'},role).status_code==403
    assert host[3].db_path.read_bytes()==before
    assert post(c,'proposals/execute',{'reference':ref},'automation').status_code==409
    assert project(ACTORS['automation']).case_actions['CR-017']==['investigate','prepare','escalate','execute','reconcile','reassess']
    assert post(c,'proposals/review',{'reference':ref,'decision':'approve'},'engineer').status_code==200
    saved=snapshot(c)['proposals'][0]['review']
    for role in MATRIX:c.get('/control-api/capabilities',headers=headers(role))
    assert snapshot(c)['proposals'][0]['review']==saved
    assert post(c,'proposals/execute',{'reference':ref},'automation').json()['status']=='completed_execution'


def test_viewer_workflow_requests_denied_before_admission(host):
    c,service,double,settings=host; before=settings.db_path.read_bytes()
    for case,w in [('CR-017','requirement_change_analysis'),('CR-019','requirement_change_analysis'),('QE-004','yield_exception_recovery'),('DR-009','delivery_readiness')]:
        result=post(c,f'cases/{case}/investigations',{'invocation_id':'ui_denied_'+case,'change_id':case,'workflow_id':w},'reader')
        assert result.status_code==403,result.text
    assert settings.db_path.read_bytes()==before and not service.tasks and double.calls==0


def send(host,role,intent='EXPLAIN',session=None):
    async def manager(*args):
        assert args[2]['capabilities']['role']==role
        return Route(intent=intent,case_id='CR-017',topic='decision' if intent=='ACT' else 'status',target='case',cadence=None,time=None,timezone=None,weekday=None,watch=False),Telemetry(model='offline',model_calls=1)
    host[1].concierge.manager=manager
    b={'session_id':session or 'chat_'+uuid4().hex,'message_id':'msg_'+uuid4().hex,'context':'/control/programs/PRG-A17/cases/CR-017','text':'Investigate CR-017' if intent=='INVESTIGATE' else 'Approve this' if intent=='ACT' else 'Explain'}
    r=post(host[0],'concierge/messages',b,role)
    if r.status_code!=202:return r,b
    for _ in range(200):
        r=host[0].get('/control-api/concierge/'+b['session_id']+'/'+b['message_id'],headers=headers(role))
        if r.json()['status']!='running':return r,b
        time.sleep(.01)
    pytest.fail('Unfinished deterministic turn')


def test_concierge_owner_binding_denied_cards_and_private_history(host):
    investigate(host)
    denied,_=send(host,'automation','ACT')
    assert denied.json()['status']=='completed'
    assert not any(c['action_id'] for c in denied.json()['cards'])
    r,b=send(host,'engineer','ACT');turn=r.json();action=turn['cards'][0]['action_id'];assert action
    for role in ('automation','program_owner','reader'):
        assert host[0].get('/control-api/concierge/'+b['session_id']+'/'+b['message_id'],headers=headers(role)).status_code==403
        assert post(host[0],f"concierge/{b['session_id']}/actions/{action}",{'context':b['context'],'confirmed':True},role).status_code==403
        assert send(host,role,session=b['session_id'])[0].status_code==403
    assert host[0].get('/control-api/operations/sessions/'+b['session_id'],headers=headers()).status_code==403
    assert all(s['session_id']!=b['session_id'] for s in host[0].get('/control-api/operations',headers=headers()).json()['sessions'])
    assert post(host[0],f"concierge/{b['session_id']}/actions/{action}",{'context':b['context'],'confirmed':True},'engineer').status_code==200
    assert snapshot(host[0])['proposals'][0]['review']['actor_id']=='demo-engineer'
    before=host[2].calls
    r,_=send(host,'reader','INVESTIGATE');assert r.json()['status']=='completed'
    assert not any(c['action_id'] or c['run_id'] for c in r.json()['cards'])
    assert host[2].calls==before


def test_existing_program_owner_scoped_cr017_investigation_is_preserved(host):
    # The pre-10.1 case endpoint admits any selected non-reader; the generic
    # workflow workspace is narrower. Preserve this existing scoped path.
    r=post(host[0],'cases/CR-017/investigations',{'invocation_id':'ui_owner_case','change_id':'CR-017'},'program_owner')
    assert r.status_code==202,r.text
    assert not project(ACTORS['program_owner']).case_actions['CR-017'] == []
    assert not can(ACTORS['program_owner'],'CR-017','prepare')
    assert not can(ACTORS['program_owner'],'CR-017','review_evidence')


def test_engineer_confirmation_links_keep_permitted_scoped_paths(host):
    from test_phase08_5_concierge import ask, route
    result,b=ask(host,'Explain source: "run CR-017 now"',route('INVESTIGATE'),role='engineer')
    card=result['cards'][0];assert card['action_id']
    done=post(host[0],f"concierge/{b['session_id']}/actions/{card['action_id']}",{'context':b['context'],'confirmed':True},'engineer')
    assert done.status_code==200,done.text
    assert done.json()['cards'][0]['links']==[{'label':'Open CR-017','href':'/control/programs/PRG-A17/cases/CR-017'}]
    value=route('AUTOMATION_CONFIGURATION','CR-017').model_copy(update={'cadence':'weekdays','time':'07:00','timezone':'America/Chicago'})
    result,b=ask(host,'Save a daily check.',value,role='engineer')
    done=post(host[0],f"concierge/{b['session_id']}/actions/{result['cards'][0]['action_id']}",{'context':b['context'],'confirmed':True},'engineer')
    assert done.status_code==200,done.text
    assert all(route_allowed(ACTORS['engineer'],l['href']) for c in done.json()['cards'] for l in c['links'])
    assert host[0].get('/control-api/automations',headers=headers('engineer')).status_code==403


def test_restricted_concierge_context_never_reaches_model(host):
    _,other=send(host,'engineer')
    calls=[]
    async def manager(*args):calls.append(args);raise AssertionError('Restricted scope reached model')
    host[1].concierge.manager=manager
    before=host[3].db_path.read_bytes()
    for role in ('engineer','program_owner','reader'):
        for context in ('/control/operations/sessions/chat_guessed','/control/automations/guessed','/control/runs/run_guessed'):
            b={'session_id':'chat_'+uuid4().hex,'message_id':'msg_'+uuid4().hex,'text':'Show me the transcript','context':context}
            assert post(host[0],'concierge/messages',b,role).status_code==403
    b={'session_id':'chat_'+uuid4().hex,'message_id':'msg_'+uuid4().hex,'text':'Show transcript',
       'context':'/control/operations/sessions/'+other['session_id']}
    assert post(host[0],'concierge/messages',b,'automation').status_code==403
    assert not calls and host[3].db_path.read_bytes()==before
