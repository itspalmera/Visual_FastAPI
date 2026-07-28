from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.Services.metrics_service import MetricsService
from app.DTOs.metrics_dto import MonthlyFlowResponse, OperationalDensityResponse
from app.Database.connection import get_db

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
    db: Session = Depends(get_db)
):
    return MetricsService.get_monthly_flow_metrics(db, min_neto=min_neto, max_neto=max_neto)


@router.get(
    "/operational-density",
    response_model=List[OperationalDensityResponse],
    status_code=status.HTTP_200_OK,
    summary="Métricas de Densidad Operacional"
)
def get_operational_density(
    min_neto: Optional[float] = Query(None, description="Filtro mínimo de valor neto"),
    max_neto: Optional[float] = Query(None, description="Filtro máximo de valor neto"),
    db: Session = Depends(get_db)
):
    return MetricsService.get_operational_density_metrics(db, min_neto=min_neto, max_neto=max_neto)