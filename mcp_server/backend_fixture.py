"""TEST BOOTSTRAP ONLY, run with the original backend environment.

The MCP runtime never imports this module. Temporary database setup/fingerprints
belong here; every business interaction under test still crosses real HTTP.
"""

import argparse
import hashlib
from pathlib import Path
import sqlite3

from mock_enterprise.app import create_app
from mock_enterprise.config import PROJECT, Settings
from mock_enterprise.seed import initialize
import uvicorn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--storage", type=Path, required=True)
    parser.add_argument("--port", type=int)
    parser.add_argument("--fingerprint", action="store_true")
    parser.add_argument("--standard", action="store_true")
    parser.add_argument("--quality", action="store_true")
    parser.add_argument("--delivery", action="store_true")
    args = parser.parse_args()
    storage = args.storage.absolute()
    if not storage.is_relative_to(PROJECT / ".cache"):
        parser.exit(2, "Test storage must be under the project cache.\n")
    settings = Settings(storage / "enterprise.sqlite3", storage, True)
    settings.validate(existing=args.fingerprint)
    if args.fingerprint:
        # All persisted tables, including audit/idempotency, without returning rows.
        with sqlite3.connect(f"file:{settings.db_path}?mode=ro", uri=True) as con:
            digest = hashlib.sha256("\n".join(con.iterdump()).encode()).hexdigest()
        print(digest)
        return
    initialize(settings)
    if args.standard:
        from mock_enterprise.standard_upgrade import install
        install(settings)
    if args.quality:
        from mock_enterprise.quality_upgrade import install
        install(settings)
    if args.delivery:
        from mock_enterprise.delivery_upgrade import install
        install(settings)
    uvicorn.run(create_app(settings), host="127.0.0.1", port=args.port, access_log=False, log_level="warning")


if __name__ == "__main__":
    main()
