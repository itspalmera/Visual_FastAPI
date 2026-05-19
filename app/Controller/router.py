from fastapi import APIRouter
from app.Controller.endpoints.sales import router as sales_router

# Creamos el enrutador global
router = APIRouter(prefix="/api")

# Inclusión de sub-módulos (puedes colgar más enrutadores aquí abajo)
router.include_router(sales_router)