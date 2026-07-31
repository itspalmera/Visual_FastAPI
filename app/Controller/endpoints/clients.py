from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.Services.metrics_service import MetricsService
from app.DTOs.client_dto import ClientRiskProfileResponse
from app.Database.connection import get_db

# Inicialización del router de FastAPI para agrupar endpoints relacionados
router = APIRouter()


@router.get(
    "/risk-matrix", 
    response_model=List[ClientRiskProfileResponse], 
    status_code=status.HTTP_200_OK,
    summary="Matriz de Clientes: Recurrencia, Ticket Promedio y Tasa de Riesgo"
)
def get_client_risk_matrix(
    min_neto: Optional[float] = Query(None, description="Filtro mínimo de valor neto"),
    max_neto: Optional[float] = Query(None, description="Filtro máximo de valor neto"),
    db: Session = Depends(get_db)
):
    """
    Obtiene la matriz de perfil de riesgo y métricas operativas de los clientes.

    Esta ruta calcula y retorna indicadores clave para cada cliente, incluyendo:
    - **Recurrencia:** Frecuencia de transacciones realizadas.
    - **Ticket Promedio:** Valor promedio de facturación por cliente.
    - **Tasa de Riesgo:** Nivel de riesgo asignado según el comportamiento comercial.

    Permite acotar el análisis mediante un rango opcional de montos netos (`min_neto` y `max_neto`).

    ### Parámetros de Consulta (Query Parameters):
    - **min_neto** *(float, opcional)*: Límite inferior para filtrar métricas por valor neto. Default: `None`.
    - **max_neto** *(float, opcional)*: Límite superior para filtrar métricas por valor neto. Default: `None`.

    ### Inyección de Dependencias:
    - **db** *(Session)*: Sesión activa de SQLAlchemy administrada por el generador `get_db`.

    ### Respuestas:
    - **200 OK**: Retorna una lista de objetos `ClientRiskProfileResponse` con la matriz calculada.
    """
    # Delega la lógica de negocio y consulta de base de datos a la capa de servicios (MetricsService)
    return MetricsService.get_client_risk_metrics(db, min_neto=min_neto, max_neto=max_neto)