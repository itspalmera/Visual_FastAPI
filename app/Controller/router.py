"""
Módulo Central de Enrutamiento de la API (Aggregator Router).

Este archivo consolida y centraliza los distintos controladores de la aplicación.
Se encarga de estructurar el versionado de la API (/api/v1/...) y organizar la 
documentación interactiva (Swagger UI / ReDoc) mediante prefijos y etiquetas (tags).
"""

from fastapi import APIRouter

# Importación de los routers específicos de cada dominio
from app.Controller.endpoints.sales import router as sales_router
from app.Controller.endpoints.clients import router as clients_router
from app.Controller.endpoints.metrics import router as metrics_router

# Router central de la API que agrupa la totalidad de los endpoints
router = APIRouter()

# -----------------------------------------------------------------------------
# REGISTRO Y CONFIGURACIÓN DE RUTAS DE LA API (v1)
# -----------------------------------------------------------------------------

# Módulo para la carga, filtrado y consulta de ventas/facturas
router.include_router(
    sales_router, 
    prefix="/api/v1/sales", 
    tags=["Gestión de Facturas"]
)

# Módulo para el análisis del perfil de riesgo y recurrencia de clientes
router.include_router(
    clients_router, 
    prefix="/api/v1/clients", 
    tags=["Análisis de Clientes"]
)

# Módulo para el cálculo de flujo mensual y densidad operacional
router.include_router(
    metrics_router, 
    prefix="/api/v1/metrics", 
    tags=["Métricas Financieras"]
)