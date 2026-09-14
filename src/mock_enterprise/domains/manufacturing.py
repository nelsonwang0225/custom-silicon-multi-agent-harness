"""Read-only partner provenance and restrictions."""
from fastapi import APIRouter, Request
from ..core import identity
from ..db import read_store
from ..schemas import Unit, Lot, Items

router = APIRouter(prefix='/manufacturing', tags=['Manufacturing Portal'])


@router.get('/units', response_model=Items[Unit], operation_id='list_manufacturing_units')
def units(request: Request, program_id: str | None = None):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        return {'items': store.list('manufacturing.unit', actor, **({"program_id": program_id} if program_id else {}))}


@router.get('/lots', response_model=Items[Lot], operation_id='list_manufacturing_lots')
def lots(request: Request, program_id: str | None = None):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        return {'items': store.list('manufacturing.lot', actor, **({"program_id": program_id} if program_id else {}))}


@router.get('/units/{unit_id}', response_model=Unit, operation_id='get_manufacturing_unit')
def unit(unit_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        return store.get('manufacturing.unit', unit_id, identity(request))


@router.get('/lots/{lot_id}', response_model=Lot, operation_id='get_manufacturing_lot')
def lot(lot_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        return store.get('manufacturing.lot', lot_id, identity(request))
