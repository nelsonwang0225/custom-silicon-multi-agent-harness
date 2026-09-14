"""Offline synthetic variants; never imported by runtime agents or source retrieval."""
from mock_enterprise.seed import initialize
from mock_enterprise.quality_upgrade import extension,install
VARIANTS=('comparable','incomparable','missing_conditions','no_alternative_supply','allocation_tradeoff','missing_evidence')
def prepare(settings,variant='comparable'):
    if variant not in VARIANTS:raise ValueError('Unknown quality variant')
    initialize(settings);data=extension()
    if variant=='incomparable':data['manufacturing.quality_observation'][0]['test_program_version']='FT-B-8.0'
    if variant=='missing_conditions':data['manufacturing.quality_observation'][0]['conditions_id']=None
    if variant in ('no_alternative_supply','allocation_tradeoff'):
        m=data['manufacturing.quality_material'][1];m['eligible_unallocated_quantity']=0
        if variant=='no_alternative_supply':m.update(disposition='hold',held_quantity=600,released_quantity=0);data['manufacturing.lot'][1]['restrictions']=['quality_hold']
        else:m.update(allocated_quantity=100,eligible_unallocated_quantity=500,allocation_order_id='ORD-1204')
    if variant=='missing_evidence':data['manufacturing.quality_exception'][0]['evidence_ids']=['RES-MISSING']
    install(settings,additions=data)
