from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.Services.excel_service import ExcelService
from app.DTOs.metrics_dto import MonthlyFlowResponse, OperationalDensityResponse
from app.Database.connection import get_db

router = APIRouter()

@router.get(
    "/monthly-flow", 
    response_model=List[MonthlyFlowResponse], 
    status_code=status.HTTP_200_OK,
    summary="Evolución del Flujo de Caja"
)
def get_monthly_flow(
    min_neto: Optional[float] = Query(None, description="Filtro mínimo de valor neto (Outliers)"),
    max_neto: Optional[float] = Query(None, description="Filtro máximo de valor neto (Outliers)"),
    db: Session = Depends(get_db)
): 
    return ExcelService.get_monthly_flow_metrics(db, min_neto=min_neto, max_neto=max_neto)


@router.get(
    "/operational-density", 
    response_model=List[OperationalDensityResponse], 
    status_code=status.HTTP_200_OK,
    summary="Densidad Operativa"
)
def get_operational_density(
    min_neto: Optional[float] = Query(None, description="Filtro mínimo de valor neto (Outliers)"),
    max_neto: Optional[float] = Query(None, description="Filtro máximo de valor neto (Outliers)"),
    db: Session = Depends(get_db)
): 
    return ExcelService.get_operational_density_metrics(db, min_neto=min_neto, max_neto=max_neto)