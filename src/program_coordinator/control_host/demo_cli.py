"""Explicit loopback demo reset/verification using the same host boundary as UI."""
import argparse
import json
import os
import re
import sys
import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-url', default='http://127.0.0.1:18082')
    parser.add_argument('--ui-origin', default='http://127.0.0.1:5188')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('reset','verify'):
        command = sub.add_parser(name)
        command.add_argument('--scope', choices=('full','CR-017','CR-019','QE-004','DR-009','QE-011'), default='full')
        if name=='reset': command.add_argument('--yes', action='store_true')
    args = parser.parse_args()
    if os.environ.get('DEMO_MODE')!='true': parser.error('DEMO_MODE=true is required')
    if not all(re.fullmatch(r'http://127\.0\.0\.1:\d{1,5}', v) for v in (args.host_url,args.ui_origin)):
        parser.error('Host and UI must use loopback HTTP')
    try:
        with httpx.Client(base_url=args.host_url,trust_env=False,follow_redirects=False,timeout=60) as client:
            if args.command=='verify':
                response = client.get('/control-api/demo/verify',params={'scope':args.scope})
            else:
                preview = client.get('/control-api/demo/preview',params={'scope':args.scope})
                preview.raise_for_status()
                plan = preview.json()
                print(json.dumps(plan,indent=2))
                if not plan['allowed']: parser.exit(1,'Shared dependency conflict; use Full Demo Reset.\n')
                if not args.yes and not (sys.stdin.isatty() and input('Type RESET to restore this demo scope: ')=='RESET'):
                    parser.exit(1,'Reset requires explicit confirmation (--yes or type RESET).\n')
                response = client.post('/control-api/demo/reset',json={'scope':args.scope,'confirmation':'RESET','expected_epoch':plan['epoch']},
                    headers={'Origin':args.ui_origin,'X-Stratos-Action':'1','X-Stratos-Demo-Maintainer':'local-demo-reset'})
            value = response.json()
            print(json.dumps(value,indent=2))
            if not response.is_success or not value.get('validation',value).get('baseline_valid'):
                parser.exit(1,'Baseline not confirmed. Inspect discrepancies and retry/reconcile explicitly.\n')
    except (httpx.HTTPError,ValueError):
        parser.exit(1,'Demo host request failed. Verify host/source connections; no reset success is claimed.\n')


if __name__=='__main__': main()
