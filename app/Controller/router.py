from fastapi import APIRouter
from app.Controller.endpoints.sales import router as sales_router
from app.Controller.endpoints.clients import router as clients_router
#from app.Controller.endpoints.metrics import router as metrics_router

# Router central de la API
router = APIRouter()

# Registramos cada controlador con su prefijo y etiqueta para Swagger
router.include_router(sales_router, prefix="/api/v1/sales", tags=["Gestión de Facturas"])
router.include_router(clients_router, prefix="/api/v1/clients", tags=["Análisis de Clientes"])
#router.include_router(metrics_router, prefix="/api/v1/metrics", tags=["Métricas Financieras"])