"""Read-only customer commitments and approved incremental rates."""
from fastapi import APIRouter, Request
from ..core import at, identity
from ..db import read_store
from ..schemas import Order, Rate, Items

router = APIRouter(prefix='/erp', tags=['Commercial ERP'])


@router.get('/orders', response_model=Items[Order], operation_id='list_customer_orders')
def orders(request: Request, program_id: str | None = None):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        return {'items': store.list('erp.order', actor, **({"program_id": program_id} if program_id else {}))}


@router.get('/orders/{order_id}', response_model=Order, operation_id='get_customer_order')
def order(order_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        return store.get('erp.order', order_id, identity(request))


@router.get('/cost-rates', response_model=Items[Rate], operation_id='list_cost_rates')
def rates(program_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        records = store.list('erp.rate', identity(request), program_id=program_id)
        return {'items': [r for r in records if r['status'] == 'approved' and at(r['effective_from']) <= at(store.now) < at(r['effective_to'])]}
