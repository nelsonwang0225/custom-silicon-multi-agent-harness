"""Owned loopback source and MCP servers for offline integration probes."""
from contextlib import contextmanager
from threading import Thread
import socket
import time
import uvicorn
from mock_enterprise.app import create_app as source_app
from stratos_mcp.server import create_app as mcp_app
from stratos_mcp.config import ServerConfig
from enterprise_api import ClientConfig, Scope


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]

@contextmanager
def serving(app,port):
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error',access_log=False))
    thread=Thread(target=server.run,daemon=True);thread.start()
    for _ in range(200):
        if server.started:break
        if not thread.is_alive():raise RuntimeError('Isolated server stopped')
        time.sleep(.01)
    else:raise RuntimeError('Isolated server did not start')
    try:yield
    finally:
        server.should_exit=True;thread.join(10)
        if thread.is_alive():raise RuntimeError('Isolated server did not stop')

@contextmanager
def network(settings,source_port=None,mcp_port=None):
    source_port=source_port or free_port();mcp_port=mcp_port or free_port()
    source_url=f'http://127.0.0.1:{source_port}'
    mcp_config=ServerConfig(port=mcp_port,enterprise=ClientConfig(base_url=source_url,scope=Scope(customer_id='CUST-FML01',program_id='PRG-A17')))
    with serving(source_app(settings),source_port),serving(mcp_app(mcp_config),mcp_port):
        yield source_url,f'http://127.0.0.1:{mcp_port}/mcp'
