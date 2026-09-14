"""Developer-only isolated delivery variants; never runtime-accessible fixtures."""
from mock_enterprise.seed import initialize
from mock_enterprise.delivery_upgrade import extension,install
from mock_enterprise.db import Store,connect

VARIANTS=('base','technical_blocked','technical_complete','future_conditional','wrong_configuration','held_released','requested_600','missing_date','missing_quantity','missing_logistics','duplicate_inventory','partial_failure','stale_proposal')


def mutate(settings,fn):
    con=connect(settings.db_path)
    try:
        con.execute('BEGIN IMMEDIATE');fn(Store(con));con.commit()
    except Exception:con.rollback();raise
    finally:con.close()


def complete_cr017(settings):
    from fastapi.testclient import TestClient
    from mock_enterprise.app import create_app
    from tests.conftest import get,post,draft,approve,book,link_body,ENGINEER
    PHYSICAL="/validation/changes/CR-017/physical-validation"
    REVIEW="/engineering/changes/CR-017/evidence-reviews"
    with TestClient(create_app(settings)) as client:
        plan=draft(client);approval=approve(client,plan);job=book(client,plan,approval)
        assert post(client,"/programs/PRG-A17/implementation-links",link_body(plan,approval,job),"delivery-fixture-link").status_code==201
        assert post(client,f"/validation/jobs/{job['id']}/synthetic-result",{'expected_plan_digest':job['plan_digest']},"delivery-fixture-result",{'Authorization':'Bearer demo-lab-local-only'}).status_code==201
        current=get(client,PHYSICAL)
        result=post(client,REVIEW,dict(expected_evidence_digest=current['evidence_digest'],decision='approve',reason='Synthetic exact Engineering review for the delivery dependency variant.'),'delivery-ready-fixture',ENGINEER)
        assert result.status_code==201,result.text


def prepare(settings,variant='base'):
    if variant not in VARIANTS:raise ValueError('Unknown delivery variant')
    initialize(settings);data=extension();r=data['erp.delivery_request'][0]
    if variant in ('technical_blocked','technical_complete'):
        r.update(technical_change_id='CR-017',requirement_revision_id='REQ-042-V2')
    if variant=='missing_date':r['requested_at']=None
    if variant=='missing_quantity':r['quantity']=None
    if variant=='missing_logistics':data['planner.delivery_logistics'][0]['transit_minutes']=None
    if variant=='requested_600':r['quantity']=600
    if variant=='duplicate_inventory':r['material_ids'].append('MAT-B-203')
    if variant=='future_conditional':
        r['future_supply_ids']=['FUT-HEL-300']
        future={k:data['erp.delivery_allocation'][0][k] for k in ('program_id','customer_id','content_version','synthetic','updated_at')}
        data['manufacturing.future_supply']=[dict(**future,id='FUT-HEL-300',owning_system='manufacturing',configuration_id='CFG-B-01',quantity=300,expected_at='2026-11-25T06:00:00Z',status='conditional',release_prerequisites=['Receipt confirmation','Quality release','Validation clearance'],quality_complete=False,validation_complete=False)]
    install(settings,additions=data)
    if variant=='technical_complete':complete_cr017(settings)
    if variant=='requested_600':
        # Variant-only order request quantity; original protected source fixture is untouched.
        def change_order(store):
            store.con.execute('DROP TRIGGER protect_erp_order')
            store.update('erp.order','ORD-HEL-800',{'quantity':600,'content_version':2})
        mutate(settings,change_order)
    if variant=='wrong_configuration':
        def wrong(store):
            store.update('manufacturing.quality_material','MAT-B-203',{'configuration_id':'CFG-A-01','content_version':2})
            store.update('manufacturing.lot','LOT-B-203',{'product_revision':'REV-A','content_version':2})
        mutate(settings,wrong)
    if variant=='held_released':
        def released(store):
            store.update('manufacturing.quality_material','MAT-B-204',{'disposition':'released','released_quantity':200,'held_quantity':0,'eligible_unallocated_quantity':200,'content_version':2})
            store.update('manufacturing.lot','LOT-B-204',{'restrictions':[],'hold_details':[],'content_version':2})
        mutate(settings,released)
