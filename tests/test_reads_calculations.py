import copy
import pytest
from mock_enterprise.db import read_store
from conftest import AUTOMATION, get


READS = [
    '/engineering/changes/CR-017', '/engineering/requirements/REQ-042-V1',
    '/engineering/requirements/REQ-042-V2', '/engineering/configurations/CFG-B-01',
    '/engineering/workloads/WF-LC-V2', '/engineering/procedures/PROC-LC-02',
    '/engineering/policies/POLICY-APP-01', '/engineering/acceptance-criteria/CRIT-BASE-V1',
    '/engineering/documents?program_id=PRG-A17', '/engineering/documents/DOC-REQUEST-01',
    '/validation/coverage?change_id=CR-017', '/validation/options?change_id=CR-017',
    '/validation/results/RES-SHORT-B', '/validation/samples?program_id=PRG-A17',
    '/validation/jobs?change_id=CR-017', '/manufacturing/units/UNIT-B-017',
    '/manufacturing/lots/LOT-4491', '/erp/orders/ORD-1204', '/erp/cost-rates?program_id=PRG-A17',
    '/programs/PRG-A17', '/programs/PRG-A17/milestones/MS-ACCEPT-01',
    '/programs/PRG-A17/implementation-links?change_id=CR-017', '/audit/events?change_id=CR-017',
]


@pytest.mark.parametrize('path', READS)
def test_reads(env, path):
    client, settings = env
    with read_store(settings.db_path) as store:
        before = store.con.iterdump()
        before = list(before)
    get(client, path)
    with read_store(settings.db_path) as store:
        assert list(store.con.iterdump()) == before


def test_seed_coverage_and_option_math(env):
    client, _ = env
    cov = get(client, '/validation/coverage?change_id=CR-017')
    assert not cov['coverage_satisfied']
    reasons = {r['result']['id']: r['mismatch_reasons'] for r in cov['items']}
    assert 'WRONG_PROFILE' in reasons['RES-BASELINE-B']
    assert 'WRONG_PRODUCT_REVISION' in reasons['RES-LONG-A']
    assert reasons['RES-SHORT-B'] == ['INSUFFICIENT_DURATION']
    opts = get(client, '/validation/options?change_id=CR-017')['items']
    assert len(opts) == 9
    eligible = {o['slot']['id']: o for o in opts if o['resource_eligible']}
    assert set(eligible) == {'SLOT-STANDARD', 'SLOT-PRIORITY'}
    for slot, ready, slack, cents in [('SLOT-STANDARD', '2026-11-20T22:00:00Z', -1680, 0),
                                    ('SLOT-PRIORITY', '2026-11-18T20:00:00Z', 1320, 180000)]:
        option = eligible[slot]
        assert (option['timing']['review_ready_at'], option['timing']['deadline_slack_minutes'], option['cost_cents']) == (ready, slack, cents)
        assert option['approval_eligible']
    assert eligible['SLOT-PRIORITY']['timing']['execution_start_at'] == '2026-11-18T08:00:00Z'
    assert all(o['timing'] is None for o in opts if not o['resource_eligible'])
    assert all('MANUFACTURING_RESTRICTION' in o['eligibility_reasons'] for o in opts if o['sample']['id'] == 'SAMPLE-B-018')


@pytest.mark.parametrize('mutation,satisfied', [
    ('complete', True), ('short_bin', False), ('failed', False), ('running', False), ('model', False), ('runtime', False),
])
def test_positive_and_negative_evidence(factory, seed, mutation, satisfied):
    result = seed['validation']['results'][-1]
    result['actual_suite_minutes'] = 480
    result['observed_minutes_by_context_bin'] = {'32768': 160, '65536': 160, '131072': 160}
    if mutation == 'short_bin':
        result['observed_minutes_by_context_bin'] = {'32768': 200, '65536': 160, '131072': 120}
    if mutation == 'failed':
        result['criteria_passed'] = False
    if mutation == 'running':
        result['status'] = 'running'
    client, settings = factory(seed)
    if mutation in ('model', 'runtime'):
        from mock_enterprise.db import connect
        con = connect(settings.db_path)
        field = 'model_bundle_id' if mutation == 'model' else 'runtime'
        con.execute(f'UPDATE engineering_configuration SET {field}=?, content_version=2 WHERE id=?', ('changed', 'CFG-B-01'))
        # Keep the target model/workload aligned so only historical evidence becomes stale.
        if mutation == 'model':
            con.execute('UPDATE engineering_workload SET model_bundle_id=? WHERE id=?', ('changed', 'WF-LC-V2'))
        con.close()
    assert get(client, '/validation/coverage?change_id=CR-017')['coverage_satisfied'] is satisfied


def test_option_rules_ignore_names_and_order(factory, seed):
    original_client, _ = factory(seed)
    original = get(original_client, '/validation/options?change_id=CR-017')['items']
    remap = {r['id']: f'renamed-{i}' for i, r in enumerate(seed['validation']['slots'])}
    for slot in seed['validation']['slots']:
        slot['id'] = remap[slot['id']]
    seed['validation']['slots'].reverse()
    seed['validation']['samples'].reverse()
    client, _ = factory(seed)
    changed = get(client, '/validation/options?change_id=CR-017')['items']
    summarize = lambda rows: sorted((r['cost_cents'], r['resource_eligible'], r['approval_eligible'], str(r['timing'])) for r in rows)
    assert summarize(original) == summarize(changed)
