import json
import logging
import sqlite3
import traceback
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from starlette.exceptions import HTTPException

from .config import Settings
from .core import BusinessError, header_id, identity, new_id
from .db import connect, read_store
from .domains import engineering, validation, manufacturing, erp, planner, downstream, standard_change, quality, delivery
from .http import record_denial
from .portfolio_views import router as portfolio_router
from starlette.middleware.gzip import GZipMiddleware
from .schemas import AuditEvent, ErrorResponse, Items
from .seed import check_marker, lifecycle_lock


def create_app(settings=None):
    settings = settings or Settings.environment()
    settings.validate(existing=True)

    @asynccontextmanager
    async def lifespan(app):
        with lifecycle_lock(settings):
            con = connect(settings.db_path)
            try:
                check_marker(con)
            finally:
                con.close()
            yield

    app = FastAPI(title='Synthetic Semiconductor Enterprise', version='1.0.0', lifespan=lifespan,
                  description='Local deterministic demo. Public mock role selectors are not production authentication. Scheduling does not execute tests or imply acceptance.',
                  redoc_url=None)
    app.state.settings = settings
    app.add_middleware(GZipMiddleware, minimum_size=2000)

    @app.middleware('http')
    async def request_context(request, call_next):
        request.state.request_id = new_id('request')
        request.state.correlation_id = header_id(request.headers.get('x-correlation-id'))
        request.state.actor = None
        try:
            response = await call_next(request)
        except Exception as exc:
            logging.getLogger('mock_enterprise').error('Request failed: type=%s frames=%s request_id=%s',
                type(exc).__name__, [(Path(f.filename).name, f.name, f.lineno) for f in traceback.extract_tb(exc.__traceback__)], request.state.request_id)
            # Never emit exception/body/header content: it could contain user-supplied text.
            record_denial(request, 'INTERNAL_ERROR', failed=True)
            response = JSONResponse({'error': {'code': 'INTERNAL_ERROR', 'message': 'Request failed; no success is asserted. Retry or read back using the original key.', 'details': {}}, 'correlation_id': request.state.correlation_id}, status_code=500)
        response.headers['X-Request-ID'] = request.state.request_id
        response.headers['X-Correlation-ID'] = request.state.correlation_id
        return response

    @app.exception_handler(BusinessError)
    async def business_error(request, exc):
        record_denial(request, exc.code, failed=exc.status >= 500)
        return JSONResponse({'error': {'code': exc.code, 'message': exc.message, 'details': exc.details},
                             'correlation_id': request.state.correlation_id}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        # Error types/locations only, never input values or exception context.
        try:
            identity(request)
        except BusinessError as auth_error:
            return await business_error(request, auth_error)
        record_denial(request, 'INVALID_REQUEST')
        return JSONResponse({'error': {'code': 'INVALID_REQUEST', 'message': 'Request does not match the documented schema.',
                                      'details': {'errors': [{'type': e['type'], 'location': [str(x) for x in e['loc'][:2]]} for e in exc.errors()]}},
                             'correlation_id': request.state.correlation_id}, status_code=422)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        try:
            identity(request)
        except BusinessError:
            pass
        code = 'NOT_FOUND' if exc.status_code == 404 else 'METHOD_NOT_ALLOWED'
        return await business_error(request, BusinessError(exc.status_code, code, 'No such business operation.'))

    errors = {status: {'model': ErrorResponse} for status in (401, 403, 404, 409, 422, 500, 503)}
    security = HTTPBearer(auto_error=False, description='Public local-only role selector. Use the documented demo identity values; no real credentials.')
    for router in (engineering.router, validation.router, manufacturing.router, erp.router, planner.router, portfolio_router, downstream.router, standard_change.router, quality.router, delivery.router):
        app.include_router(router, prefix='/api/v1', dependencies=[Depends(security)], responses=errors)

    @app.get('/health', operation_id='health', response_model=dict[str, bool | str])
    def health():
        with read_store(settings.db_path) as store:
            check_marker(store.con)
        return {'status': 'ready', 'synthetic': True}

    @app.get('/api/v1/audit/events', response_model=Items[AuditEvent], tags=['Audit'], operation_id='list_audit_events',
             dependencies=[Depends(security)], responses=errors)
    def events(change_id: str, request: Request):
        with read_store(settings.db_path) as store:
            actor = identity(request)
            kind = 'manufacturing.quality_exception' if change_id == 'QE-004' and quality.exists(store) else 'engineering.change'
            if change_id == 'DR-009': kind = 'erp.delivery_request'
            change = store.get(kind, change_id, actor)
            rows = store.con.execute('SELECT sequence,data FROM audit_events WHERE program_id=? AND change_id=? ORDER BY sequence', (change['program_id'], change_id)).fetchall()
            return {'items': [{'sequence': r['sequence'], **json.loads(r['data'])} for r in rows]}

    # Headers are shared by all POSTs and explicitly documented in the generated schema.
    original_openapi = app.openapi

    def openapi():
        schema = original_openapi()
        for path in schema['paths'].values():
            for method, operation in path.items():
                if method == 'post':
                    parameters = operation.setdefault('parameters', [])
                    for name, required in [('Idempotency-Key', True), ('X-Correlation-ID', False)]:
                        if not any(p['name'] == name for p in parameters):
                            parameters.append({'in': 'header', 'name': name, 'required': required,
                                               'schema': {'type': 'string', 'minLength': 1, 'maxLength': 100}})
        return schema
    app.openapi = openapi

    # Local administrative maintenance is separate from all business handlers.
    # A nonblocking shared lease covers each complete HTTP request; the explicit
    # host reset takes an exclusive lease against this same configured file.
    from .demo_management import maintenance_lock, storage_id, VERSION
    @app.middleware('http')
    async def demo_maintenance(request, call_next):
        try:
            with maintenance_lock(settings):
                with read_store(settings.db_path) as store:
                    epoch = store.meta.get('demo_epoch', 'initial')
                    pending_reset = store.meta.get('demo_reset_pending', False)
                if pending_reset and request.method not in {'GET','HEAD'}:
                    return JSONResponse({'error': {'code':'DEMO_RESET_RECONCILIATION_REQUIRED',
                        'message':'Demo reset is incomplete. Retry from Demo controls before business actions.', 'details':{}}}, status_code=503)
                if request.method not in {'GET','HEAD'} and request.headers.get('x-stratos-demo-epoch',epoch) != epoch:
                    return JSONResponse({'error': {'code':'DEMO_STATE_CHANGED',
                        'message':'The demo was reset. Refresh before creating a new request.', 'details':{}}}, status_code=409,
                        headers={'X-Stratos-Demo-Epoch':epoch})
                response = await call_next(request)
                response.headers['X-Stratos-Demo-Epoch'] = epoch
                if request.url.path == '/health':
                    response.headers['X-Stratos-Demo-Storage'] = storage_id(settings)
                    response.headers['X-Stratos-Demo-Protocol'] = VERSION
                return response
        except ValueError:
            return JSONResponse({'error': {'code': 'DEMO_MAINTENANCE_BUSY',
                'message': 'Demo maintenance is in progress; retry after reset.', 'details': {}}}, status_code=503)
    return app
