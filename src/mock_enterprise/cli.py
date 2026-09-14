import argparse
import sys
import uvicorn
from .config import Settings
from .seed import initialize


def main():
    parser = argparse.ArgumentParser(description='Local synthetic enterprise; no AI runtime.')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init-demo')
    sub.add_parser('upgrade-downstream', help='Add CR-017 downstream tables to a stopped owned demo; preserve all records')
    sub.add_parser('install-standard-case', help='Add CR-019 and its bounded intake contract to a stopped owned demo; preserve existing records')
    sub.add_parser('install-delivery-case', help='Add DR-009 delivery commitment contracts to a stopped owned demo')
    sub.add_parser('install-quality-case', help='Add QE-004 and bounded quality recovery contracts to a stopped owned demo')
    sub.add_parser('install-quality-knowledge', help='Add three controlled quality documents to a stopped owned demo; preserve all operational records')
    reset = sub.add_parser('reset-demo')
    reset.add_argument('--yes', action='store_true', help='Explicitly confirm destructive demo reset')
    serve = sub.add_parser('serve')
    serve.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    try:
        settings = Settings.environment()
        if args.command == 'init-demo':
            initialize(settings)
            print('Synthetic demo initialized.')
        elif args.command == 'upgrade-downstream':
            from .downstream_upgrade import upgrade
            upgrade(settings)
            print('Downstream tables installed; existing records preserved.')
        elif args.command == 'install-standard-case':
            from .standard_upgrade import install
            install(settings)
            print('Standard CR-019 case and intake tables installed; existing records preserved.')
        elif args.command == 'install-delivery-case':
            from .delivery_upgrade import install
            install(settings)
        elif args.command == 'install-quality-case':
            from .quality_upgrade import install
            install(settings)
            print('Quality QE-004 installed; existing source records preserved.')
        elif args.command == 'install-quality-knowledge':
            from .quality_knowledge import install
            added = install(settings)
            print(f'Quality knowledge installed: {len(added)} new documents; operational records preserved.')
        elif args.command == 'reset-demo':
            confirmed = args.yes or (sys.stdin.isatty() and input('Reset the local demo and erase generated records? Type RESET: ') == 'RESET')
            initialize(settings, reset=True, confirmed=confirmed)
            print('Synthetic demo reset to original fixture state.')
        else:
            from .app import create_app
            uvicorn.run(create_app(settings), host='127.0.0.1', port=args.port, workers=1, access_log=False)
    except (ValueError, FileExistsError) as exc:
        # Only our bounded local setup errors are displayed; no credentials/config dump.
        parser.exit(1, f'{exc}\n')


if __name__ == '__main__':
    main()
