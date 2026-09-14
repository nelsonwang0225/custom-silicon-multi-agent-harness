"""Owned local demo processes; explicit reset delegates to Phase 09.1 HTTP controls."""
import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
from uuid import uuid4

import httpx
from program_investigator.config import PROJECT

CASES = ('CR-017', 'CR-019', 'QE-004', 'DR-009')
SYSTEMS = ('Engineering Hub', 'Validation Lab', 'Manufacturing Portal', 'Commercial ERP', 'Program Planner')


class DemoError(Exception):
    """Only fixed operator-safe messages. Never raw library exceptions or environment."""


def safe_path(path):
    p = Path(os.path.abspath(path))
    if not p.is_relative_to(PROJECT / '.demo') or p == PROJECT / '.demo':
        raise DemoError('Harness storage must be a child of project .demo/. Use a separate directory for testing.')
    if any(x.is_symlink() for x in (p, *p.parents)):
        raise DemoError('Symlink storage is refused.')
    if p.exists() and not p.is_dir() and (not p.is_file() or p.stat().st_nlink != 1):
        raise DemoError('Storage must use ordinary files and directories.')
    return p


def write_json(path, value):
    safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(uuid4().hex + '.tmp')
    with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as handle:
        json.dump(value, handle, indent=2); handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, path)


def read_json(path):
    safe_path(path)
    if not path.exists():
        return {}
    try:
        if path.stat().st_size > 100_000:
            raise ValueError
        value = json.loads(path.read_text())
        if not isinstance(value, dict): raise ValueError
        return value
    except (ValueError, OSError):
        raise DemoError('Harness metadata unreadable. Inspect the owned state directory before retrying.') from None


@contextmanager
def exclusive(path):
    safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise DemoError('Another harness command or supervisor owns this directory.') from None
        yield


@dataclass(frozen=True)
class Config:
    state_dir: str
    source_db: str
    metadata_dir: str
    source_port: int = 8000
    mcp_port: int = 9000
    host_port: int = 18082
    ui_port: int = 5188

    @property
    def directory(self): return Path(self.state_dir)
    @property
    def urls(self):
        return {name: f'http://127.0.0.1:{getattr(self, name+"_port")}' for name in ('source', 'mcp', 'host', 'ui')}

    def validate(self):
        for value in (self.state_dir, self.source_db, self.metadata_dir): safe_path(value)
        ports = [self.source_port, self.mcp_port, self.host_port, self.ui_port]
        if len(set(ports)) != 4 or any(type(p) is not int or not 1024 <= p <= 65535 for p in ports):
            raise DemoError('Choose four distinct local ports between 1024 and 65535.')
        if Path(self.source_db) in (self.directory, Path(self.metadata_dir)):
            raise DemoError('Source database and metadata directory must be separate.')


def configuration(args):
    directory = safe_path(args.state_dir)
    saved = read_json(directory/'config.json')
    defaults = asdict(Config(str(directory), str(directory/'enterprise.sqlite3'), str(directory/'metadata')))
    if saved:
        if set(saved) != set(defaults) or saved['state_dir'] != str(directory):
            raise DemoError('Unexpected harness configuration. Do not reuse another directory’s ownership metadata.')
        defaults.update(saved)
    for field in defaults:
        value = getattr(args, field, None)
        if value is not None:
            defaults[field] = str(safe_path(value)) if field.endswith(('_dir', '_db')) else value
    config = Config(**defaults)
    config.validate()
    return config


def process_identity(pid):
    if type(pid) is not int or pid <= 1:
        return None
    result = subprocess.run(['ps', '-p', str(pid), '-o', 'lstart=', '-o', 'command='], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def owns_supervisor(state):
    token = state.get('token', '')
    current = process_identity(state.get('pid'))
    return bool(len(token) == 32 and current and current == state.get('identity')
                and 'program_coordinator.control_host.demo_harness' in current and '--ownership-token '+token in current)


def port_free(port):
    try:
        with socket.socket() as s:
            # Match the local servers' bind semantics: closed connections in
            # TIME_WAIT do not mean a listener still owns the port after stop.
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('127.0.0.1', port))
        return True
    except OSError:
        return False


def prerequisites(config, *, initialized=True):
    missing = [name for name in ('.venv/bin/python', 'mcp_server/.venv/bin/python', 'coordinator/.venv/bin/python',
                                'mock_apps_ui/node_modules/vite/bin/vite.js')
               if not (PROJECT/name).is_file()]
    if not shutil.which('node') or not shutil.which('npm'): missing.append('Node.js and npm on PATH')
    if missing:
        raise DemoError('Missing prerequisites: '+', '.join(missing)+'. Follow docs/DEMO_RUNBOOK.md.')
    for interpreter, modules in (('.venv/bin/python', 'fastapi,pydantic,uvicorn'),
                                  ('mcp_server/.venv/bin/python', 'mcp,httpx,uvicorn'),
                                  ('coordinator/.venv/bin/python', 'agents,mcp,dotenv,httpx,fastapi,uvicorn')):
        probe = subprocess.run([str(PROJECT/interpreter), '-c',
            'import sys,'+modules+'; assert sys.version_info[:2] == (3,12)'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        if probe.returncode:
            raise DemoError('Python 3.12 or locked dependencies unavailable in '+interpreter+'. Follow the runbook setup commands.')
    if initialized and not Path(config.source_db).is_file():
        raise DemoError('Demo database is not initialized. Run scripts/demo init --yes explicitly; start never seeds or resets.')


def child_commands(config):
    urls = config.urls
    return [
        ('source', [str(PROJECT/'.venv/bin/python'), '-m', 'mock_enterprise.cli', 'serve', '--port', str(config.source_port)], PROJECT),
        ('mcp', [str(PROJECT/'mcp_server/.venv/bin/python'), '-m', 'stratos_mcp', '--backend-url', urls['source'], '--port', str(config.mcp_port)], PROJECT),
        ('host', [str(PROJECT/'coordinator/.venv/bin/python'), '-m', 'program_coordinator.control_host', '--source-url', urls['source'], '--mcp-url', urls['mcp']+'/mcp', '--metadata-dir', config.metadata_dir, '--port', str(config.host_port), '--ui-origin', urls['ui'], '--enable-demo-controls'], PROJECT),
        ('frontend', [shutil.which('node'), str(PROJECT/'mock_apps_ui/node_modules/vite/bin/vite.js'), 'preview', '--port', str(config.ui_port), '--outDir', str(config.directory/'frontend')], PROJECT/'mock_apps_ui'),
    ]


def request(url, *, timeout=5, headers=None):
    try:
        with httpx.Client(trust_env=False, follow_redirects=False, timeout=timeout) as client:
            response = client.get(url, headers=headers)
        if not response.is_success: return None
        return response.json() if 'application/json' in response.headers.get('content-type', '') else response.text
    except (httpx.HTTPError, ValueError):
        return None


def service_health(config):
    urls = config.urls
    source = request(urls['source']+'/health')
    mcp = request(urls['mcp']+'/ready')
    host = request(urls['host']+'/control-api/health')
    ui = request(urls['ui']+'/control/overview')
    return {'source': isinstance(source, dict) and source.get('status') == 'ready',
            'mcp': isinstance(mcp, dict) and mcp.get('status') == 'ready',
            'control_host': isinstance(host, dict) and host.get('status') == 'ok',
            'frontend': isinstance(ui, str) and '<div id="root">' in ui}


def supervise(config, token):
    children, handles = [], []
    shutdown = False
    def stop_signal(signum, frame):
        nonlocal shutdown
        shutdown = True
    signal.signal(signal.SIGTERM, stop_signal)
    signal.signal(signal.SIGINT, stop_signal)
    path = config.directory/'processes.json'
    state = dict(pid=os.getpid(), token=token, identity=process_identity(os.getpid()), status='starting', config=asdict(config), children=[])
    with exclusive(config.directory/'run.lock'):
        write_json(path, state)
        env = {**os.environ, 'DEMO_MODE':'true', 'DEMO_DB':config.source_db, 'PYTHONPATH':str(PROJECT/'src')+os.pathsep+str(PROJECT),
               'MOCK_API_URL':config.urls['source'], 'CONTROL_HOST_URL':config.urls['host']}
        # Source, MCP and frontend never need runtime credentials from the parent environment.
        public_env = {k:v for k,v in env.items() if not k.startswith(('OPENAI_', 'VITE_'))}
        try:
            for name, command, cwd in child_commands(config):
                log = config.directory/(name+'.log')
                safe_path(log)
                handle = os.fdopen(os.open(log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), 'a')
                handles.append(handle)
                child = subprocess.Popen(command, cwd=cwd, env=env if name == 'host' else public_env, stdout=handle, stderr=handle, start_new_session=True)
                children.append(child)
                state['children'].append({'service':name, 'pid':child.pid})
                write_json(path, state)
            deadline = time.monotonic()+60
            while not shutdown:
                failed = next((state['children'][i]['service'] for i,p in enumerate(children) if p.poll() is not None), None)
                if failed:
                    raise DemoError(f'{failed} exited. Inspect its local service log; no other process was adopted.')
                if state['status'] == 'starting':
                    if all(service_health(config).values()) and all(p.poll() is None for p in children):
                        state['status'] = 'running'; write_json(path, state)
                    elif time.monotonic() > deadline:
                        raise DemoError('Required service readiness timed out. Inspect local service logs.')
                time.sleep(.25)
        except (DemoError, OSError) as exc:
            state['error'] = str(exc) if isinstance(exc, DemoError) else 'A required service could not start.'
        finally:
            # Popen handles, not arbitrary ports: terminate only children of this supervisor.
            for p in reversed(children):
                if p.poll() is None:
                    try: os.killpg(p.pid, signal.SIGTERM)
                    except ProcessLookupError: pass
                    try: p.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        try: os.killpg(p.pid, signal.SIGKILL)
                        except ProcessLookupError: pass
                        p.wait(timeout=5)
            for handle in handles: handle.close()
            state['status'] = 'failed' if state.get('error') else 'stopped'
            write_json(path, state)


def start(config):
    state = read_json(config.directory/'processes.json')
    if owns_supervisor(state):
        if state.get('config') != asdict(config):
            raise DemoError('This directory already runs another configuration. Stop it explicitly before changing ports or paths.')
        if state.get('status') == 'running' and all(service_health(config).values()):
            return {'result':'already_running', 'urls':config.urls, 'business_state':'preserved'}
        raise DemoError('Owned supervisor is starting or unhealthy. Inspect status/logs, then stop explicitly.')
    prerequisites(config)
    occupied = [p for p in (config.source_port, config.mcp_port, config.host_port, config.ui_port) if not port_free(p)]
    if occupied:
        raise DemoError('Ports occupied: '+', '.join(map(str, occupied))+'. No process was killed or adopted. Select free ports or stop the known owner.')
    # Existing host admission also owns this storage pair, even on different ports.
    with exclusive(Path(config.metadata_dir)/'control-host.lock'):
        pass
    build_env = {k:v for k,v in os.environ.items() if not k.startswith(('OPENAI_', 'VITE_'))}
    build_env.update(MOCK_API_URL=config.urls['source'], CONTROL_HOST_URL=config.urls['host'])
    # Each owned preview has its own compiled output, bound to its actual source URL.
    # Starting another configuration never replaces assets served by an existing demo.
    output = config.directory/'frontend'
    safe_path(output)
    log = config.directory/'build.log'
    safe_path(log)
    with os.fdopen(os.open(log, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as handle:
        built = subprocess.run([shutil.which('npm'), '--prefix', str(PROJECT/'mock_apps_ui'), 'run', 'build', '--',
                                '--outDir', str(output), '--emptyOutDir'], cwd=PROJECT, env=build_env,
                               stdout=handle, stderr=handle, timeout=120)
    if built.returncode:
        raise DemoError('Frontend build failed. Inspect build.log; no services were started.')
    write_json(config.directory/'config.json', asdict(config))
    token = uuid4().hex
    log = config.directory/'supervisor.log'
    safe_path(log)
    with os.fdopen(os.open(log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), 'a') as handle:
        child = subprocess.Popen([sys.executable, '-m', 'program_coordinator.control_host.demo_harness', '--state-dir', config.state_dir,
                                  '_serve', '--ownership-token', token], cwd=PROJECT,
                                 env={**os.environ, 'PYTHONPATH':str(PROJECT/'src')+os.pathsep+str(PROJECT)},
                                 stdin=subprocess.DEVNULL, stdout=handle, stderr=handle, start_new_session=True)
    deadline = time.monotonic()+75
    while time.monotonic() < deadline:
        state = read_json(config.directory/'processes.json')
        if state.get('token') == token:
            if state.get('status') == 'running':
                return {'result':'started', 'urls':config.urls, 'business_state':'preserved', 'log_directory':config.state_dir}
            if state.get('status') == 'failed': raise DemoError(state['error'])
        if child.poll() is not None: raise DemoError('Supervisor exited before readiness. Inspect supervisor.log.')
        time.sleep(.2)
    if child.poll() is None: child.terminate()
    raise DemoError('Startup timed out; owned supervisor was asked to stop. Inspect status before retrying.')


def stop(config):
    state = read_json(config.directory/'processes.json')
    if not owns_supervisor(state):
        if state.get('status') in ('starting','running'):
            raise DemoError('Recorded supervisor ownership no longer matches. No process was signaled. Inspect saved PIDs and logs manually.')
        return {'result':'already_stopped', 'business_state':'preserved'}
    if state.get('config', {}).get('state_dir') != config.state_dir:
        raise DemoError('Supervisor belongs to another state directory. No process was signaled.')
    os.kill(state['pid'], signal.SIGTERM)
    deadline = time.monotonic()+75
    while time.monotonic() < deadline:
        now = read_json(config.directory/'processes.json')
        if now.get('status') in ('stopped','failed'):
            return {'result':'stopped', 'business_state':'preserved'}
        time.sleep(.2)
    raise DemoError('Owned shutdown has not completed. Inspect supervisor.log; arbitrary processes were not killed.')


def status(config):
    health = service_health(config)
    base = config.urls['host']
    baseline = request(base+'/control-api/demo/verify?scope=full', timeout=60) if health['control_host'] else None
    controls = request(base+'/control-api/demo') if health['control_host'] else None
    autonomous = request(base+'/control-api/demo/autonomous', headers={'X-Stratos-Demo-Profile':'automation'}) if health['control_host'] else None
    ready = request(base+'/control-api/readiness') if health['control_host'] else None
    systems = request(base+'/control-api/operations/health', timeout=30, headers={'X-Stratos-Demo-Profile':'automation'}) if health['control_host'] else None
    cases = request(base+'/control-api/cases/CR-017', timeout=30) if health['control_host'] else None
    state = read_json(config.directory/'processes.json')
    summaries = {x['change_id']: {'state':x['state_label'], 'source_available':x['source_available']} for x in (cases or {}).get('case_summaries', [])}
    stale = [x['id'] for x in (cases or {}).get('decision_summaries', []) if x['status'] in ('stale','partial_failure','verification_required')]
    sources = {x['system']:x['status'] == 'Available' for x in systems or []}
    running = (ready or {}).get('active_workflows', [])
    model = (ready or {}).get('model_configuration', {'status':'unavailable'})
    background = (ready or {}).get('background_execution', {})
    checks = {'services_available':all(health.values()), 'source_apps_reachable':all(sources.get(s) for s in SYSTEMS),
              'baseline_valid':(baseline or {}).get('baseline_valid') is True,
              'canonical_cases_present':all(summaries.get(c, {}).get('source_available') for c in CASES),
              'no_stale_executable_proposal':isinstance(cases, dict) and not stale,
              'no_running_work':ready is not None and not running and not ready.get('active_host_tasks') and not ready.get('active_concierge_turns'),
              'reset_consistent':bool(controls and controls.get('enabled') and not controls.get('recovery_required')),
              'concierge_available':bool(ready and ready.get('concierge_route_available')),
              'model_configured':model.get('status') == 'configured' and bool(ready and ready.get('runtime_invocable')),
              'background_inactive':all(background.get(k) == 'not_installed' for k in ('schedulers','event_listeners','condition_evaluators')),
              'owned_services':owns_supervisor(state) and state.get('config') == asdict(config)}
    return {'result':'Demo ready' if all(checks.values()) else 'Not ready', 'checks':checks, 'services':health,
            'source_apps':sources, 'baseline_state':'valid' if checks['baseline_valid'] else 'mutated_or_unavailable',
            'baseline':baseline, 'demo_controls':controls, 'autonomous_opening':autonomous, 'cases':summaries,
            'model_configuration':model, 'background_execution':background, 'running_workflows':running,
            'stale_or_unverified_decisions':stale, 'urls':config.urls, 'supervisor_status':state.get('status','not_started'),
            'model_connectivity_note':'Credential format/presence only; provider access, quota and live behavior are not verified.'}


def reset(config, scope, yes):
    state = read_json(config.directory/'processes.json')
    if not owns_supervisor(state) or state.get('config') != asdict(config):
        raise DemoError('Reset requires the matching owned harness. Start this configuration first.')
    # The sole reset implementation and exact preview/epoch/confirmation remain Phase 09.1.
    from . import demo_cli
    previous, old_demo = sys.argv, os.environ.get('DEMO_MODE')
    sys.argv = ['demo_cli', '--host-url', config.urls['host'], '--ui-origin', config.urls['ui'],
                'reset', '--scope', scope] + (['--yes'] if yes else [])
    os.environ['DEMO_MODE'] = 'true'
    try: demo_cli.main()
    finally:
        sys.argv = previous
        if old_demo is None: os.environ.pop('DEMO_MODE', None)
        else: os.environ['DEMO_MODE'] = old_demo


def initialize(config, yes):
    if not yes: raise DemoError('New database initialization requires --yes. Existing files are never overwritten.')
    if Path(config.source_db).exists(): raise DemoError('Database already exists. Start preserves it; use prepare for an explicit full reset.')
    if owns_supervisor(read_json(config.directory/'processes.json')): raise DemoError('Stop the owned services before initialization.')
    from mock_enterprise.config import Settings
    from mock_enterprise.seed import initialize as seed
    from mock_enterprise.standard_upgrade import install as standard
    from mock_enterprise.delivery_upgrade import install as delivery
    settings = Settings(Path(config.source_db), PROJECT/'.demo', True)
    seed(settings); standard(settings); delivery(settings)
    write_json(config.directory/'config.json', asdict(config))
    return {'result':'initialized_new_database', 'source_db':config.source_db, 'next':'start, then prepare --yes to verify the integrated baseline'}


def emit(value, json_output):
    if json_output:
        print(json.dumps(value, indent=2)); return
    print(value['result'])
    if 'checks' in value:
        for name, valid in value['checks'].items(): print(f'  {"PASS" if valid else "FAIL"}  {name.replace("_", " ")}')
        opening = value.get('autonomous_opening') or {}
        print('Autonomous opening:', opening.get('status','unavailable').replace('_',' ').capitalize())
        print('Baseline:', value['baseline_state'], (value['baseline'] or {}).get('demo_baseline_version','unknown'))
        for detail in (value['baseline'] or {}).get('discrepancies', [])[:8]: print('  '+detail)
        for case in CASES: print(case+':', value['cases'].get(case, {}).get('state', 'unavailable'))
        print('Model:', value['model_configuration'].get('model','unavailable'), value['model_configuration']['status'], '· No paid connectivity check')
        print('Background:', json.dumps(value['background_execution']))
        for system in SYSTEMS: print(system+':', 'reachable' if value['source_apps'].get(system) else 'unavailable')
        for run in value['running_workflows']: print('Running:', run['run_id'])
    for name, url in value.get('urls', {}).items(): print(name+':', url+('/control/overview' if name == 'ui' else '/mcp' if name == 'mcp' else ''))
    if 'next' in value: print(value['next'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', default=str(PROJECT/'.demo/interview'))
    parser.add_argument('--source-db'); parser.add_argument('--metadata-dir')
    for name in ('source','mcp','host','ui'): parser.add_argument('--'+name+'-port', type=int)
    parser.add_argument('--json', action='store_true')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('start','stop','status','check'): sub.add_parser(name)
    for name in ('init','prepare','reset'):
        p = sub.add_parser(name); p.add_argument('--yes', action='store_true')
        if name == 'reset': p.add_argument('--scope', choices=('full', *CASES, 'QE-011'), default='full')
    p = sub.add_parser('_serve', help=argparse.SUPPRESS); p.add_argument('--ownership-token', required=True)
    args = parser.parse_args()
    try:
        config = configuration(args)
        if args.command == '_serve': supervise(config, args.ownership_token); return 0
        if args.command in ('status','check'):
            value = status(config); emit(value, args.json)
            return 0 if args.command == 'status' or value['result'] == 'Demo ready' else 1
        with exclusive(config.directory/'command.lock'):
            if args.command == 'init': value = initialize(config, args.yes)
            elif args.command == 'start': value = start(config)
            elif args.command == 'stop': value = stop(config)
            else:
                if not all(service_health(config).values()): raise DemoError('Required services unavailable. Start them before prepare/reset.')
                reset(config, getattr(args,'scope','full'), args.yes)
                value = status(config)
            emit(value, args.json)
            return 0 if args.command != 'prepare' or value['result'] == 'Demo ready' else 1
    except (DemoError, OSError, ValueError, TypeError, subprocess.TimeoutExpired):
        # Fixed messages only; do not include raw system/library exceptions.
        exc = sys.exception()
        print(str(exc) if isinstance(exc, DemoError) else 'Local harness operation failed. Inspect the owned logs and runbook.', file=sys.stderr)
        return 1


if __name__ == '__main__': raise SystemExit(main())
