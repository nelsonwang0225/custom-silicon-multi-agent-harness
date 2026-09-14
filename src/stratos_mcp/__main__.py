"""Local CLI. Configuration is explicit; environment files are never loaded."""

import argparse
import json
import logging

from pydantic import ValidationError
import uvicorn

from enterprise_api import ClientConfig, Scope
from .catalog import TOOLS
from .config import ServerConfig
from .server import create_app


def configure_logging():
    # Library debug/error prose may contain supplied arguments or network details.
    # This service emits only its own small, fixed-field event records.
    logging.basicConfig(level=logging.CRITICAL + 1, force=True)
    for name in ("mcp", "httpx", "httpcore", "httpx2", "httpcore2", "uvicorn", "sse_starlette"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.setLevel(logging.CRITICAL + 1)
    logger = logging.getLogger("stratos_mcp")
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "Invalid CLI arguments; use --help for supported local MCP settings.\n")


def main():
    parser = SafeParser(description="Local read-only Stratos Streamable HTTP MCP; no model or API key.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    parser.add_argument("--program-id", default="PRG-A17")
    parser.add_argument("--customer-id", default="CUST-FML01")
    parser.add_argument("--reader-identity", default="demo-reader-local-only")
    parser.add_argument("--connect-timeout", type=float, default=2)
    parser.add_argument("--read-timeout", type=float, default=10)
    parser.add_argument("--max-retries", type=int, default=2)
    args = parser.parse_args()
    try:
        config = ServerConfig(host=args.host, port=args.port, enterprise=ClientConfig(
            base_url=args.backend_url, scope=Scope(program_id=args.program_id, customer_id=args.customer_id),
            reader_identity=args.reader_identity, connect_timeout=args.connect_timeout,
            read_timeout=args.read_timeout, max_retries=args.max_retries))
    except ValidationError:
        parser.exit(2, "Invalid local MCP configuration; check loopback address, port, reader scope and timeout bounds.\n")
    configure_logging()
    logger = logging.getLogger("stratos_mcp")
    logger.info(json.dumps({"event": "starting", "url": config.origin + "/mcp", "tools": len(TOOLS),
                            "read_only": True, "program_id": config.enterprise.scope.program_id,
                            "customer_id": config.enterprise.scope.customer_id}))
    try:
        uvicorn.run(create_app(config), host=config.bind_host, port=config.port, workers=1,
                    access_log=False, log_config=None, proxy_headers=False, timeout_graceful_shutdown=180)
    except (OSError, SystemExit):
        logger.error('{"event":"startup_failed","code":"LOCAL_SERVER_UNAVAILABLE"}')
        return 1
    finally:
        logger.info('{"event":"stopped"}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
