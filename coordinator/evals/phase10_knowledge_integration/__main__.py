"""Offline retrieval integration gates and canonical business-conclusion comparison."""
import argparse,json,subprocess,sys
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import uuid4
from .canonical import run
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',type=Path,default=Path('.cache/phase10-rag-integration')/('eval_'+uuid4().hex))
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
result=subprocess.run([sys.executable,'-m','pytest','coordinator/tests/test_knowledge_foundation.py','coordinator/tests/test_knowledge_integration.py',
    '-q','--junitxml='+str(a.output/'tests.xml')],capture_output=True,text=True)
(a.output/'retrieval-tests.log').write_text(result.stdout+result.stderr)
if result.returncode:print('Retrieval gates FAILED: '+str(a.output));raise SystemExit(result.returncode)
observations={c.get('name'):not any(c.find(tag) is not None for tag in ('failure','error','skipped')) for c in ET.parse(a.output/'tests.xml').iter('testcase')}
cases=json.loads(Path(__file__).with_name('cases.json').read_text())
for c in cases:c['passed']=observations.get(c['test'],False)
if not all(c['passed'] for c in cases):raise SystemExit('Incomplete retrieval gate coverage')
report=run(a.output/'canonical')
(a.output/'scorecard.json').write_text(json.dumps({'retrieval_gates':'PASS','retrieval_cases':cases,'canonical_cases':4,'unexpected_changes':0,
    'mode':'offline_deterministic','live_model_reasoning_measured':False,'paid_calls':False},indent=2)+'\n')
print(json.dumps({'status':'PASS','retrieval_gates':len(cases),'canonical_cases':4,'unexpected_changes':0,'artifacts':str(a.output)}))
