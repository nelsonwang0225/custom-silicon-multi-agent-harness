"""Observed live scope regression; isolated HTTP/MCP with deterministic SDK output."""
from coordinator.evals.phase08_4a.probe import environment, investigate, source_counts
from coordinator.evals.phase08_4a.doubles import StandardModelDouble
from program_coordinator.models import CoordinatorReview


def test_sdk_wrapped_failure_retains_only_safe_guard_code():
    from agents.exceptions import AgentsException
    from program_coordinator.controls import HarnessError, failure_code
    wrapper=AgentsException('Untrusted SDK payload must not be retained')
    wrapper.__cause__=HarnessError('source_version_changed_during_case')
    assert failure_code(wrapper,'specialist_failed')=='source_version_changed_during_case'
    unrelated=RuntimeError('Untrusted payload')
    unrelated.__cause__=unrelated
    assert failure_code(unrelated,'specialist_failed')=='specialist_failed'


def test_standard_intake_preserves_separate_pending_requirement(tmp_path):
    with environment(tmp_path) as env:
        client, host, double, settings = env
        milestone = host.source.read.get_program_milestone('PRG-A17', 'MS-ACCEPT-01')
        assert any(d.get('requirement_revision_id') == 'REQ-042-V2'
                   and d.get('state') == 'pending_assessment' for d in milestone['dependencies'])
        before = source_counts(settings)
        result = investigate(env)
        assert result['context']['request']['baseline_requirement_revision_id'] == 'REQ-042-V1'
        assert result['handoffs'][0]['status'] == 'handoff_verified'
        assert result['runs'][0]['recommendation']['requires_human_review'] is False
        assert host.source.read.get_program_milestone('PRG-A17', 'MS-ACCEPT-01') == milestone
        assert source_counts(settings) == {**before, 'validation.intake': 1}
        assert client.get('/control-api/cases/CR-017').json()['proposals'] == []
        from program_coordinator.control_host.concierge_reads import grounded_cards
        snapshot=host.snapshot()
        cards=grounded_cards(host,snapshot,'CR-019','policy')
        handoff=next(c for c in cards if c.title=='Validation Operations handoff')
        intake=result['handoffs'][0]['intake']
        assert ('Intake ID',intake['id']) in handoff.facts
        assert ('Physical testing','not started') in handoff.facts
        assert handoff.links[-1].href=='/validation/intakes/'+intake['id']
        # A prior handoff must not be presented as the outcome of a fresh run.
        snapshot.standard.runs[0].run_id='run_fresh'
        assert not any(c.title=='Validation Operations handoff'
                       for c in grounded_cards(host,snapshot,'CR-019','policy'))


def test_standard_source_eligibility_cannot_override_unresolved_blocker(tmp_path, monkeypatch):
    original = StandardModelDouble.__call__

    async def unresolved(self, agent, prompt, **kwargs):
        result = await original(self, agent, prompt, **kwargs)
        if isinstance(result.final_output, CoordinatorReview):
            result.final_output.blocking_issues = ['A conflicting requested-scope fact remains unresolved.']
            result.final_output.ready_to_synthesize = False
        return result

    monkeypatch.setattr(StandardModelDouble, '__call__', unresolved)
    with environment(tmp_path) as env:
        before = source_counts(env[3])
        result = investigate(env)
        assert result['eligibility']['touchless_eligible'] is True
        assert result['handoffs'][0]['status'] == 'review_required'
        assert result['handoffs'][0]['package'] is None
        assert result['runs'][0]['recommendation']['requires_human_review'] is True
        assert source_counts(env[3]) == before


def test_final_schema_diagnostic_preserves_no_invalid_values_or_field_names():
    import json
    from helpers import harness, seed_sources, triage, final
    from program_coordinator.harness import final_output_diagnostic
    h=seed_sources(harness());h.state.triage=triage()
    good=final(h).model_dump(mode='json')
    assert final_output_diagnostic(json.dumps(good))['output']==good
    bad={**good,'approval_granted':True,'private_extra_field':'private input value'}
    result=final_output_diagnostic(json.dumps(bad))
    assert result['output'] is None
    assert any(e['type']=='literal_error' and e['path']==['approval_granted'] for e in result['schema_errors'])
    assert 'private_extra_field' not in json.dumps(result)
    assert 'private input value' not in json.dumps(result)


def test_sdk_final_schema_rejection_stays_failed_with_safe_code():
    import asyncio
    import pytest
    from agents.exceptions import ModelBehaviorError
    from helpers import harness
    from program_coordinator.controls import HarnessError
    async def rejected(*args,**kwargs):
        raise ModelBehaviorError('Invalid response contains private input')
    h=harness(runner=rejected)
    with pytest.raises(HarnessError,match='^malformed_agent_output$'):
        asyncio.run(h.run_agent('coordinator','synthesis',{}))
    assert h.state.final_package is None


def test_final_consistency_diagnostics_name_the_rule_without_exposing_input():
    import json
    from helpers import harness, seed_sources, triage, final
    from program_coordinator.harness import final_output_diagnostic
    h=seed_sources(harness());h.state.triage=triage()
    good=final(h).model_dump(mode='json')
    variants=[({**good,'requires_human_review':False},'review_flag_matches_policy'),
              ({**good,'policy_path':'escalation_required'},'escalation_reason_required'),
              ({**good,'confirmed_facts':[{**good['confirmed_facts'][0],'basis':'inference'}]},'confirmed_facts_are_factual')]
    for value,expected in variants:
        result=final_output_diagnostic(json.dumps(value))
        assert result['output'] is None
        assert result['schema_errors'][0]['constraint']==expected


def test_delivery_proposal_eligibility_cannot_override_missing_intake(tmp_path,monkeypatch):
    from coordinator.evals.phase08_4c.doubles import DeliveryModelDouble
    from coordinator.evals.phase08_4c.probe import environment as delivery_environment, investigate as delivery_investigate
    from program_coordinator.models import TriageDecision
    original=DeliveryModelDouble.__call__
    async def missing(self,*args,**kwargs):
        result=await original(self,*args,**kwargs)
        if isinstance(result.final_output,TriageDecision):
            result.final_output.missing_information=['Conflicting request destination needs clarification.']
        return result
    monkeypatch.setattr(DeliveryModelDouble,'__call__',missing)
    with delivery_environment(tmp_path) as env:
        state=delivery_investigate(env)
        assert state['context']['analysis']['proposal_allowed']
        assert state['runs'][0]['recommendation']['policy_path']=='escalation_required'
        assert not state['records']['plans'] and not state['records']['commitments']
        assert not env[2].harnesses[0].state.requested_specialists
