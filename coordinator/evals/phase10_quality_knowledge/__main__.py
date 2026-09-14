"""Execute the focused QE-004 corpus gates offline; no paid calls or live models."""
import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import uuid4


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path('.cache/phase10-quality-corpus')/('eval_'+uuid4().hex))
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    result=subprocess.run([sys.executable,'-m','pytest','coordinator/tests/test_quality_knowledge_corpus.py','-q',
        '--basetemp='+str(args.output/'isolated'), '--junitxml='+str(args.output/'tests.xml')],capture_output=True,text=True)
    (args.output/'tests.log').write_text(result.stdout+result.stderr)
    cases=json.loads(Path(__file__).with_name('cases.json').read_text())
    observed={}
    if (args.output/'tests.xml').exists():
        observed={c.get('name'):not any(c.find(tag) is not None for tag in ('failure','error','skipped'))
            for c in ET.parse(args.output/'tests.xml').iter('testcase')}
    for c in cases:c['passed']=observed.get(c['test'],False)
    report={'status':'PASS' if result.returncode==0 and all(c['passed'] for c in cases) else 'FAIL',
        'mode':'deterministic_offline_HTTP_MCP_SDK_doubles','paid_calls':False,'live_model_reasoning_measured':False,
        'cases':cases,'passed':sum(c['passed'] for c in cases),'total':len(cases),'test_observations':len(observed)}
    (args.output/'scorecard.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'}|{'artifacts':str(args.output)}))
    raise SystemExit(0 if report['status']=='PASS' else 1)


if __name__=='__main__':main()
