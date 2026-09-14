"""Repeatable offline default; explicitly selected live runs reuse the existing CLI."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from .dataset import ROOT, load_dataset, versions
from .graders import grade
from .models import CaseResult, Check, Observation
from .reporting import markdown, scorecard


def runtime_observation(case, authored, run_dir):
    if case.runtime_probe in {'duplicate_invocation', 'duplicate_trigger'}:
        from .service_probe import duplicate_probe
        overlay = duplicate_probe(run_dir / case.case_id)
    elif case.runtime_probe in {'missing_system', 'source_timeout', 'malformed_tool'}:
        from .service_probe import source_failure_probe
        overlay = source_failure_probe(case.runtime_probe)
    else:
        storage = run_dir / ('source-' + case.case_id)
        env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src') + os.pathsep + str(ROOT)}
        env.pop('OPENAI_API_KEY', None)
        result = subprocess.run([str(ROOT / '.venv/bin/python'), '-m',
            'coordinator.evals.phase07.execution_probe', '--probe', case.runtime_probe,
            '--storage', str(storage)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
        if result.returncode:
            # Never echo arbitrary subprocess errors (or credentials) into reports.
            raise RuntimeError('EXECUTION_PROBE_FAILED')
        overlay = json.loads(result.stdout)
    value = authored.model_dump(mode='json')
    value['mode'] = 'runtime_probe'
    value['output'].update(overlay.pop('output'))
    value.update(overlay)
    return Observation.model_validate(value)


def failure(case, mode, code):
    return CaseResult(case_id=case.case_id, title=case.title, workflow_type=case.workflow_type,
        scenario_family=case.scenario_family, mode=mode, severity=case.severity,
        checks=[Check(dimension='factual_correctness', description='Case evaluation completed with valid observation', passed=False)],
        passed=False, critical_failures=[], error_code=code)


def run(*, mode='offline', selection='all', output=None, mocked_only=False, semantic=False, allow_paid=False, include_standard=False, include_quality=False, include_delivery=False, include_concierge=False):
    cases, authored, sources = load_dataset()
    if mode == 'live' and not allow_paid:
        raise ValueError('Live evaluation requires explicit --allow-paid')
    if semantic and not allow_paid:
        raise ValueError('Semantic grading requires explicit --allow-paid')
    if mode == 'live':
        cases = [c for c in cases if c.live_fixture]
    if selection == 'smoke':
        cases = [c for c in cases if c.smoke]
    elif selection != 'all':
        cases = [c for c in cases if c.case_id == selection]
    if not cases:
        raise ValueError('No eligible cases match selection')
    run_id = 'eval_' + uuid4().hex
    run_dir = (output or ROOT / '.cache/phase07' / run_id).absolute()
    if not run_dir.resolve().is_relative_to(ROOT / '.cache/phase07') or run_dir.exists():
        raise ValueError('Output must be a new directory under .cache/phase07')
    run_dir.mkdir(parents=True, mode=0o700)
    provenance = versions()
    results, observations = [], []
    for case in cases:
        try:
            source = sources[case.source_fixture]
            if mode == 'live':
                from .live import run_live_case
                observed, source = run_live_case(case, source, run_dir)
            elif case.runtime_probe and not mocked_only:
                observed = runtime_observation(case, authored[case.case_id], run_dir)
            else:
                observed = authored[case.case_id]
            result = grade(case, observed, source)
            # Runtime adapter records failures even if the final candidate looked safe.
            if observed.metadata.get('runtime_valid') is False:
                result.error_code = observed.metadata.get('error_code', 'RUNTIME_VALIDATION_FAILED')
            if semantic:
                from .semantic import grade_semantic
                try:
                    result.semantic, metadata = grade_semantic(case, observed, source)
                    observed.metadata['semantic_grader'] = metadata
                except Exception:
                    # Preserve every deterministic failure if the optional judge fails.
                    result.semantic_error = 'SEMANTIC_GRADER_FAILED'
            observations.append(observed.model_dump(mode='json'))
        except Exception as exc:
            # Failed cases remain in denominators; no empty/missing-run green score.
            safe_code = 'case_timeout' if isinstance(exc, subprocess.TimeoutExpired) else type(exc).__name__
            result = failure(case, 'live_agent' if mode == 'live' else 'runtime_probe', safe_code)
        results.append(result)
        (run_dir / (case.case_id + '.result.json')).write_text(result.model_dump_json(indent=2) + '\n')
    expected_ids = [c.case_id for c in cases]
    if include_standard:
        if mode != 'offline' or mocked_only:
            raise ValueError('Standard extension requires full offline runtime probes')
        from .standard import run_standard, standard_ids
        standard_dir=run_dir/'standard';standard_dir.mkdir()
        additional=run_standard(standard_dir)
        results.extend(additional);expected_ids.extend(standard_ids())
        for result in additional:
            (run_dir/(result.case_id+'.result.json')).write_text(result.model_dump_json(indent=2)+'\n')
    if include_quality:
        if mode != 'offline' or mocked_only: raise ValueError('Quality extension requires full offline runtime probes')
        from .quality import run_quality, quality_ids
        quality_dir=run_dir/'quality';quality_dir.mkdir()
        additional=run_quality(quality_dir)
        results.extend(additional);expected_ids.extend(quality_ids())
        for result in additional:
            (run_dir/(result.case_id+'.result.json')).write_text(result.model_dump_json(indent=2)+'\n')
    if include_delivery:
        if mode != 'offline' or mocked_only: raise ValueError('Delivery extension requires full offline runtime probes')
        from .delivery import run_delivery, delivery_ids
        delivery_dir=run_dir/'delivery';delivery_dir.mkdir()
        additional=run_delivery(delivery_dir)
        results.extend(additional);expected_ids.extend(delivery_ids())
        for result in additional:
            (run_dir/(result.case_id+'.result.json')).write_text(result.model_dump_json(indent=2)+'\n')
    if include_concierge:
        if mode != 'offline' or mocked_only: raise ValueError('Concierge requires full offline runtime probes')
        from .concierge import run_concierge, concierge_ids
        concierge_dir=run_dir/'concierge'
        additional=run_concierge(concierge_dir)
        results.extend(additional);expected_ids.extend(concierge_ids())
        for result in additional:
            (run_dir/(result.case_id+'.result.json')).write_text(result.model_dump_json(indent=2)+'\n')
    skipped = []
    if mode != 'live':
        skipped.append('Paid live agents not run. No live-model reasoning baseline measured.')
    if not semantic:
        skipped.append('Optional model-based semantic grader not run; semantic score is null.')
    if any(r.semantic_error for r in results):
        skipped.append(f'Optional semantic grader failed for {sum(bool(r.semantic_error) for r in results)} case(s); see case-level semantic_error.')
    if mocked_only:
        skipped.append('Actual Phase 06/service probes skipped by --mocked-only; fixtures only.')
    report = {'schema_version': 1, 'run_id': run_id, 'timestamp': datetime.now(timezone.utc).isoformat(),
        'mode': mode, 'dataset_sha256': provenance['dataset']['sha256'], 'provenance': provenance,
        'configuration': {'mode': mode, 'selection': selection, 'mocked_only': mocked_only,
            'include_standard': include_standard, 'include_quality':include_quality, 'include_delivery':include_delivery, 'include_concierge':include_concierge, 'semantic_enabled': semantic, 'model': 'gpt-6-astra' if mode == 'live' else None,
            'runtime_reused': 'program_coordinator / openai-agents==0.22.2',
            'hard_gates': '100% deterministic cases; zero critical failures; complete selected set',
            'semantic_policy': 'informational baseline; never overrides deterministic failures'},
        'skipped_checks': skipped, 'scorecard': scorecard(results, expected_ids),
        'cases': [r.model_dump(mode='json') for r in results], 'artifact_directory': str(run_dir)}
    (run_dir / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
    (run_dir / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    (run_dir / 'report.md').write_text(markdown(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description='Phase 07 offline evaluation; paid options require explicit opt-in.')
    parser.add_argument('--mode', choices=['offline', 'live'], default='offline')
    parser.add_argument('--case', default='all', help='Case ID, smoke, or all (all eligible cases).')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--mocked-only', action='store_true', help='Skip actual Phase 06 service probes; grade authored fixtures only.')
    parser.add_argument('--semantic', action='store_true', help='Optional paid semantic grading of observable output.')
    parser.add_argument('--allow-paid', action='store_true')
    parser.add_argument('--include-concierge', action='store_true', help='Add A–Q connected Concierge hard gates; no paid calls.')
    parser.add_argument('--include-delivery', action='store_true', help='Add connected delivery HTTP/MCP probes and hard-failure gates.')
    parser.add_argument('--include-quality', action='store_true', help='Add connected quality recovery HTTP/MCP probes and hard-failure gates.')
    parser.add_argument('--include-standard', action='store_true', help='Add connected standard-route HTTP/MCP probes; preserve all original hard gates.')
    parser.add_argument('--list', action='store_true', help='Offline inventory without credential loading.')
    args = parser.parse_args(argv)
    if args.list:
        cases, _, _ = load_dataset()
        print(json.dumps([{'case_id': c.case_id, 'family': c.scenario_family, 'live': bool(c.live_fixture), 'smoke': c.smoke} for c in cases], indent=2))
        return 0
    try:
        report = run(mode=args.mode, selection=args.case, output=args.output,
            mocked_only=args.mocked_only, semantic=args.semantic, allow_paid=args.allow_paid, include_standard=args.include_standard, include_quality=args.include_quality, include_delivery=args.include_delivery, include_concierge=args.include_concierge)
    except ValueError as exc:
        parser.error(str(exc))
    card = report['scorecard']
    print(json.dumps({'hard_gate_status': card['hard_gate_status'], 'passed': card['passed_cases'],
        'failed': card['failed_cases'], 'total': card['total_cases'], 'critical_failures': card['critical_failures'],
        'semantic_score_average': card['semantic_score_average'], 'artifact_directory': report['artifact_directory'],
        'skipped_checks': report['skipped_checks']}, indent=2))
    return 0 if card['hard_gate_status'] == 'PASS' else 1
