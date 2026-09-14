"""Load and validate developer fixtures; no runtime retrieval registration."""
import hashlib
import json
from pathlib import Path
from .models import EvalCase, Observation, SourceFixture

DATA = Path(__file__).parent / 'data'
ROOT = Path(__file__).resolve().parents[3]


def load_dataset(directory=DATA):
    cases = [EvalCase.model_validate(v) for v in json.loads((directory / 'cases.json').read_text())]
    observations = [Observation.model_validate(v) for v in json.loads((directory / 'observations.json').read_text())]
    sources = {k: SourceFixture.model_validate(v) for k, v in json.loads((directory / 'sources.json').read_text()).items()}
    ids = [c.case_id for c in cases]
    if len(set(ids)) != len(ids) or len({o.case_id for o in observations}) != len(observations):
        raise ValueError('Duplicate case or observation ID')
    if set(ids) != {o.case_id for o in observations}:
        raise ValueError('Exactly one authored observation per case is required')
    for case in cases:
        source = sources[case.source_fixture]
        if not set(case.expected_evidence + case.irrelevant_evidence + list(case.expected_applicability)) <= source.records.keys():
            raise ValueError('Case references missing source evidence')
    return cases, {o.case_id: o for o in observations}, sources


def fingerprint_files(paths, root=ROOT):
    entries = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    return {'sha256': hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest(), 'files': entries}


def versions():
    return {'dataset': fingerprint_files(list(DATA.glob('*.json'))),
        'eval_engine': fingerprint_files(list(Path(__file__).parent.glob('*.py'))),
        'source_seed': fingerprint_files([ROOT / 'fixtures/seed.json']),
        'instructions': fingerprint_files([ROOT / 'src/program_coordinator/agents.py', ROOT / 'src/program_coordinator/controls.py',
            ROOT / 'src/program_coordinator/policy.py', ROOT / 'src/program_coordinator/sources.py', ROOT / 'src/program_coordinator/models.py']),
        'runtime': fingerprint_files([ROOT / 'coordinator/uv.lock', ROOT / 'src/program_coordinator/harness.py',
            ROOT / 'src/program_coordinator/application/execution.py', ROOT / 'src/program_coordinator/application/execution_policy.py'])}
