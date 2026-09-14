"""Read known artifacts only. Browser identifiers never become filesystem paths."""
import json
from pathlib import Path
from ..application.observability import identifier, visible
from .operations_models import OpsEval, OpsEvalCase

# Explicit artifact index, not a duplicate result store. Missing files stay missing.
EVAL_ARTIFACTS = (
 ('live-original', 'Historical full smoke', '.cache/phase07/eval_6740fdbd4c984ca9a64740d4d17fdde0/results.json'),
 ('live-full-followup', 'Historical full smoke · follow-up', '.cache/phase07/eval_1dac4b6dd4dc468e949b5fdde8a32d1e/results.json'),
 ('live-covered', 'Later targeted validation · cr017_covered', '.cache/phase07/eval_13433d0c5b77431981e79e0f51ff39fa/results.json'),
 ('live-scheduled', 'Later targeted validation · cr017_scheduled', '.cache/phase07/eval_7232aeb309cd4715ac5055ad23956e0a/results.json'),
 ('offline-08-5', 'Phase 08.5 offline', '.cache/phase07/phase08-5-full/results.json'),
 ('offline-08-6', 'Phase 08.6 integrated offline', '.cache/phase07/phase08-6-full/results.json'),
)


def read_json(root, relative, *, limit=8_000_000):
    """Reject traversal, symlinks (including ancestors), non-files and oversized files."""
    root=Path(root).absolute(); rel=Path(relative)
    if rel.is_absolute() or '..' in rel.parts:raise ValueError('UNSAFE_ARTIFACT')
    path=root/rel
    if any(p.is_symlink() for p in [path,*path.parents]):raise ValueError('UNSAFE_ARTIFACT')
    if not path.is_file() or path.stat().st_nlink!=1 or path.stat().st_size>limit:raise ValueError('ARTIFACT_UNAVAILABLE')
    with path.open('r') as handle:
        value=handle.read(limit+1)
    if len(value)>limit:raise ValueError('ARTIFACT_TOO_LARGE')
    return json.loads(value)


def evals(root):
    values=[];unavailable=[]
    for key,label,path in EVAL_ARTIFACTS:
        try:
            r=read_json(root,path);card=r['scorecard'];cases=r['cases']
            if r['mode'] not in ('offline','live'):raise ValueError('INVALID_MODE')
            if not isinstance(cases,list) or not cases or len(cases)>1000:raise ValueError('INVALID_CASES')
            # Check the report's own denominator and critical failures; never infer success from missing fields.
            critical=[(c['case_id'],v) for c in cases for v in c['critical_failures']]
            if any(type(c['passed']) is not bool for c in cases):raise ValueError('INVALID_PASS')
            if (card['total_cases'],card['passed_cases'],card['failed_cases'])!=(len(cases),sum(c['passed'] for c in cases),sum(not c['passed'] for c in cases)):raise ValueError('INVALID_COUNTS')
            if critical!=[(c['case_id'],c['code']) for c in card['critical_failures']]:raise ValueError('INVALID_CRITICAL_COUNT')
            if card['hard_gate_status'] not in ('PASS','FAIL'):raise ValueError('MISSING_GATE')
            if not card['hard_gates'] or card['hard_gate_status']!=('PASS' if all(card['hard_gates'].values()) else 'FAIL'):raise ValueError('INVALID_GATE')
            semantic=sum(bool(c.get('semantic')) for c in cases)
            config=r.get('configuration',{})
            values.append(OpsEval(eval_id=key,label=label,mode=r['mode'],timestamp=r['timestamp'],total=len(cases),passed=card['passed_cases'],
                failed=card['failed_cases'],critical_failures=[(visible(a),visible(b)) for a,b in critical],hard_gate=card['hard_gate_status'],
                semantic=f'{semantic}/{len(cases)} evaluated' if semantic else 'Skipped / unavailable',model=identifier(config.get('model')),
                cases=[OpsEvalCase(case_id=visible(c['case_id']),passed=c['passed'],critical_failures=[visible(v) for v in c['critical_failures']],
                    semantic='Evaluated' if c.get('semantic') else 'Skipped / unavailable') for c in cases]))
        except (OSError,ValueError,TypeError,KeyError):unavailable.append(label)
    return values,unavailable


def run_artifacts(host,run):
    if not identifier(run.run_id) or '/' in run.run_id:return {},'Unavailable'
    # Host-generated run directory only. Legacy arbitrary artifact_directory is ignored.
    prefix=Path('runs')/run.run_id
    result={};missing=[]
    for name in ('case-state','report','tool-calls','trace-metadata'):
        try:result[name]=read_json(host.store.directory,prefix/(name+'.json'))
        except (OSError,ValueError):missing.append(name)
    state=result.get('case-state')
    if state is not None and not isinstance(state,dict):return {},'Invalid checkpoint · unavailable'
    if state and (state.get('run_id'),state.get('case_id'),state.get('customer_id'),state.get('program_id'))!=(run.run_id,run.case_id,run.customer_id,run.program_id):
        return {},'Scope mismatch · unavailable'
    report=result.get('report')
    if report is not None and not isinstance(report,dict):result.pop('report');report=None;missing.append('invalid report')
    for name in ('tool-calls','trace-metadata'):
        if name in result and (not isinstance(result[name],list) or any(not isinstance(v,dict) for v in result[name])):
            result.pop(name);missing.append('invalid '+name)
    if report and (report.get('run_id'),report.get('case_id'))!=(run.run_id,run.case_id):result.pop('report');missing.append('report scope')
    return result,('Available' if not missing else 'Unavailable: '+', '.join(missing))
