from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.Services.metrics_service import MetricsService
from app.DTOs.metrics_dto import MonthlyFlowResponse, OperationalDensityResponse
from app.Database.connection import get_db

# Inicialización del router de FastAPI para los endpoints de métricas
router = APIRouter()


@router.get(
    "/monthly-flow",
    response_model=List[MonthlyFlowResponse],
    status_code=status.HTTP_200_OK,
    summary="Métricas de Flujo Mensual"
)
def get_monthly_flow(
    min_neto: Optional[float] = Query(None, description="Filtro mínimo de valor neto"),
    max_neto: Optional[float] = Query(None, description="Filtro máximo de valor neto"),
    rut: Optional[str] = Query(None, description="Filtrar por RUT de cliente"),
    segmentos: Optional[List[str]] = Query(None, description="Filtra por uno o múltiples segmentos"),
    db: Session = Depends(get_db)
):
    """
    Obtiene el desglose histórico y consolidado de las métricas de flujo mensual.

    Calcula la evolución temporal de las operaciones y volumen financiero acumulado
    mes a mes. Admite filtrado por montos netos, identificación del cliente (RUT) y
    múltiples segmentos comerciales.

    ### Parámetros de Consulta (Query Parameters):
    - **min_neto** *(float, opcional)*: Límite inferior para filtrar por valor neto. Default: `None`.
    - **max_neto** *(float, opcional)*: Límite superior para filtrar por valor neto. Default: `None`.
    - **rut** *(str, opcional)*: Identificador único (RUT) de cliente. Default: `None`.
    - **segmentos** *(List[str], opcional)*: Lista de segmentos comerciales a considerar. Default: `None`.

    ### Inyección de Dependencias:
    - **db** *(Session)*: Sesión activa de SQLAlchemy entregada por `get_db`.

    ### Respuestas:
    - **200 OK**: Retorna una lista de objetos `MonthlyFlowResponse` con las métricas del periodo.
    """
    # Consulta de métricas de flujo mensual delegada a la capa de servicios
    return MetricsService.get_monthly_flow_metrics(db, 
                                                   min_neto=min_neto, 
                                                   max_neto=max_neto, 
                                                   rut=rut,
                                                   segmentos=segmentos)


@router.get(
    "/operational-density",
    response_model=List[OperationalDensityResponse],
    status_code=status.HTTP_200_OK,
    summary="Métricas de Densidad Operacional"
)
def get_operational_density(
    min_neto: Optional[float] = Query(None, description="Filtro mínimo de valor neto"),
    max_neto: Optional[float] = Query(None, description="Filtro máximo de valor neto"),
    rut: Optional[str] = Query(None, description="Filtrar por RUT de cliente"),
    segmentos: Optional[List[str]] = Query(None, description="Filtra por uno o múltiples segmentos"),
    db: Session = Depends(get_db)
):
    """
    Obtiene los indicadores de densidad operacional y concentración de actividad.

    Permite analizar la frecuencia e intensidad operativa para identificar patrones
    de carga de trabajo o volumen transaccional según los filtros aplicados.

    ### Parámetros de Consulta (Query Parameters):
    - **min_neto** *(float, opcional)*: Límite inferior para filtrar por valor neto. Default: `None`.
    - **max_neto** *(float, opcional)*: Límite superior para filtrar por valor neto. Default: `None`.
    - **rut** *(str, opcional)*: Identificador único (RUT) de cliente. Default: `None`.
    - **segmentos** *(List[str], opcional)*: Lista de segmentos comerciales a considerar. Default: `None`.

    ### Inyección de Dependencias:
    - **db** *(Session)*: Sesión activa de SQLAlchemy entregada por `get_db`.

    ### Respuestas:
    - **200 OK**: Retorna una lista de objetos `OperationalDensityResponse` con el cálculo de densidad.
    """
    # Consulta de densidad operacional delegada a la capa de servicios
    return MetricsService.get_operational_density_metrics(db, 
                                                          min_neto=min_neto, 
                                                          max_neto=max_neto, 
                                                          rut=rut,
                                                          segmentos=segmentos)