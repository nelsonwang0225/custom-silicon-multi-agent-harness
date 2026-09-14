"""Phase 07 source fixture integrity; backend environment, isolated storage only."""
import json
from copy import deepcopy
from pathlib import Path

import pytest

from coordinator.evals.phase07.live_source import seed_variant, initialize_source
from mock_enterprise.seed import load_seed, DOCUMENT_PATHS
from mock_enterprise.db import read_store
from mock_enterprise.domains.validation_rules import context, coverage, calculate_option
from mock_enterprise.core import IDENTITIES


def test_covered_seed_changes_only_support_description_and_existing_evidence():
    base = json.loads(Path('fixtures/seed.json').read_text())
    covered = seed_variant('covered')
    full = covered['validation']['results'].pop()
    expected = deepcopy(next(r for r in base['validation']['results'] if r['id'] == 'RES-SHORT-B'))
    expected.update(id='RES-FULL-B-EVAL', actual_suite_minutes=480,
                    observed_minutes_by_context_bin={'32768': 160, '65536': 160, '131072': 160})
    assert full == expected  # Historical status, completion time and bindings are retained.
    config = next(r for r in covered['engineering']['configurations'] if r['id'] == 'CFG-B-01')
    assert config['validation_support'] == (
        'Applicable completed evidence for WF-LC-V2 is recorded in '
        'RES-FULL-B-EVAL; engineering review remains pending.'
    )
    config['validation_support'] = 'not_yet_demonstrated_for_WF-LC-V2'
    assert covered == base  # No other business state or authority is changed.


@pytest.mark.parametrize('variant', ['gap', 'wrong_software', 'bypass', 'scheduled', 'ambiguous'])
def test_other_variant_seed_content_is_unchanged(variant):
    base = json.loads(Path('fixtures/seed.json').read_text())
    seed = seed_variant(variant)
    if variant == 'wrong_software':
        old_config = seed['engineering']['configurations'].pop()
        expected = deepcopy(next(r for r in base['engineering']['configurations'] if r['id'] == 'CFG-B-01'))
        expected.update(id='CFG-OLD-SW-EVAL', firmware='FW-2.2', runtime='RT-4.0')
        assert old_config == expected
        old_result = seed['validation']['results'].pop()
        expected = deepcopy(next(r for r in base['validation']['results'] if r['id'] == 'RES-SHORT-B'))
        expected.update(id='RES-OLD-SW-EVAL', configuration_id='CFG-OLD-SW-EVAL', actual_suite_minutes=480,
                        observed_minutes_by_context_bin={'32768': 160, '65536': 160, '131072': 160})
        assert old_result == expected
    assert seed == base


@pytest.mark.parametrize('variant', ['gap', 'covered', 'wrong_software', 'bypass', 'scheduled', 'ambiguous'])
def test_live_seed_variants_use_valid_source_graph_and_preserve_golden_seed(variant):
    original = Path('fixtures/seed.json').read_bytes()
    seed = seed_variant(variant)
    rows, _ = load_seed(seed)
    assert Path('fixtures/seed.json').read_bytes() == original
    assert {d['id'] for d in rows['engineering.document']} == set(DOCUMENT_PATHS)
    assert all('evals/' not in json.dumps(d) for d in rows['engineering.document'])
    assert seed['engineering']['changes'][0]['id'] == 'CR-017'


def test_altered_evidence_does_not_weaken_source_approval_requirement(tmp_path):
    settings = initialize_source('covered', tmp_path)
    with read_store(settings.db_path) as store:
        actor = IDENTITIES['demo-reader-local-only']
        ctx = context(store, actor, 'CR-017')
        assert coverage(store, actor, ctx)['coverage_satisfied']
        assert ctx['policy']['approver_role'] == 'engineer'
        assert ctx['target']['status'] == 'requested'
        assert store.list('engineering.decision', actor) == []


def test_covered_snapshots_preserve_evidence_and_pending_business_states(tmp_path):
    settings = initialize_source('covered', tmp_path)
    with read_store(settings.db_path) as store:
        actor = IDENTITIES['demo-reader-local-only']
        ctx = context(store, actor, 'CR-017')
        result = coverage(store, actor, ctx)
        assert result['coverage_satisfied'] is True
        assert [r['result']['id'] for r in result['items'] if r['satisfies']] == ['RES-FULL-B-EVAL']
        full = next(r for r in result['items'] if r['satisfies'])
        assert full['mismatch_reasons'] == []
        assert full['result']['status'] == 'completed'
        assert full['result']['criteria_passed'] is True
        assert full['result']['completed_at'] == '2026-11-15T12:00:00Z'
        for item in result['items']:
            evidence = item['result']
            for kind, key, snapshot, version in (
                ('engineering.configuration', 'configuration_id', 'configuration_snapshot', 'configuration_content_version'),
                ('engineering.workload', 'workload_profile_id', 'workload_snapshot', 'workload_profile_content_version'),
                ('engineering.criteria', 'acceptance_limits_ref', 'criteria_snapshot', 'acceptance_criteria_content_version'),
            ):
                current = store.get(kind, evidence[key], actor)
                assert evidence[snapshot] == current
                assert evidence[version] == current['content_version']
            assert 'STALE_EVIDENCE_BINDING' not in item['mismatch_reasons']
        assert full['result']['configuration_snapshot']['validation_support'] == ctx['config']['validation_support']
        assert 'engineering review remains pending' in ctx['config']['validation_support']
        assert 'not_yet_demonstrated_for_WF-LC-V2' not in json.dumps(result)
        assert ctx['target']['status'] == 'requested'
        assert ctx['change']['workflow_state'] == 'pending_impact_assessment'
        assert ctx['change']['current_plan_id'] is None
        assert ctx['milestone']['dependencies'][0]['state'] == 'pending_assessment'
        assert ctx['order']['status'] == 'open'
        # Existing evidence is neither a new execution nor approval/acceptance.
        for kind in ('engineering.plan', 'engineering.decision', 'validation.job',
                     'validation.reservation', 'planner.link', 'planner.task'):
            assert store.list(kind, actor) == []


def test_priority_numeric_expectations_agree_with_real_source_calculator(tmp_path):
    settings = initialize_source('gap', tmp_path)
    with read_store(settings.db_path) as store:
        actor = IDENTITIES['demo-reader-local-only']
        ctx = context(store, actor, 'CR-017')
        for slot_id, cents, slack in [('SLOT-PRIORITY', 180000, 1320), ('SLOT-STANDARD', 0, -1680)]:
            option = calculate_option(store, actor, ctx, store.get('validation.slot', slot_id), store.get('validation.sample', 'SAMPLE-B-017'))
            assert option['cost_cents'] == cents
            assert option['timing']['deadline_slack_minutes'] == slack
            assert option['timing']['review_ready_at'] == ('2026-11-18T20:00:00Z' if slot_id == 'SLOT-PRIORITY' else '2026-11-20T22:00:00Z')
