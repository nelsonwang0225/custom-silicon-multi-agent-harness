"""Developer-only isolated variants, never imported by agent/runtime code."""
import copy
import hashlib
import json
from mock_enterprise.standard_upgrade import extension, install
from mock_enterprise.seed import initialize, load_seed

VARIANTS = ('success','wrong_firmware','wrong_hardware','unapproved_condition','conflicting_evidence',
            'missing_procedure','nonstandard_parameter','engineering_exception','acceptance_change',
            'missing_owner','unknown_configuration','closed_queue','missing_evidence')


def additions(variant='success'):
    if variant not in VARIANTS:
        raise ValueError('Unknown developer variant')
    rows=extension()
    request=rows['engineering.standard_request'][0]
    rule=rows['engineering.standard_rule'][0]
    if variant=='wrong_firmware':request['configuration']['firmware']='FW-2.4'
    elif variant=='wrong_hardware':request['configuration']['product_revision']='REV-A'
    elif variant=='unapproved_condition':request['conditions']['context_bins']=[8192,65536]
    elif variant=='missing_procedure':request['procedure_id']=None;request['procedure_content_version']=None
    elif variant=='nonstandard_parameter':request['conditions']['concurrency']=8
    elif variant=='engineering_exception':request['material_exception_ids']=['EXCEPTION-STD-019'];request['requests_waiver']=True
    elif variant=='acceptance_change':request['changes_acceptance_criteria']=True;request['request_type']='acceptance_change'
    elif variant=='missing_owner':rule['downstream_queue_id']=None;rule['downstream_owner']=None
    elif variant=='unknown_configuration':request['configuration']=None
    elif variant=='closed_queue':rows['validation.intake_queue'][0]['status']='closed'
    request.setdefault('synthetic',True)
    # Fill the explicit source model defaults before hashing the public request document.
    from enterprise_api.standard_models import StandardRequest
    request=StandardRequest.model_validate(request).model_dump(mode='json')
    rows['engineering.standard_request'][0]=request
    doc=next(d for d in rows['engineering.document'] if d['id']=='DOC-STD-REQUEST-019')
    doc['content']=json.dumps(request,indent=2)+'\n';doc['content_hash']=hashlib.sha256(doc['content'].encode()).hexdigest()
    return rows


def prepare(settings,variant='success'):
    if variant=='missing_evidence':
        from mock_enterprise.config import PROJECT
        seed=json.loads((PROJECT/'fixtures/seed.json').read_text())
        seed['validation']['results']=[r for r in seed['validation']['results'] if r['workload_profile_id']!='WF-LC-V1']
        initialize(settings,source=seed)
    else:
        initialize(settings)
    install(settings,additions=additions(variant))
    if variant=='conflicting_evidence':
        from mock_enterprise.db import Store,connect
        con=connect(settings.db_path)
        try:
            con.execute('BEGIN IMMEDIATE')
            store=Store(con)
            record=store.get('validation.result','RES-BASELINE-B')
            record.update(id='RES-STD-CONFLICT',criteria_passed=False)
            store.insert('validation.result',record)
            con.commit()
        finally:con.close()
