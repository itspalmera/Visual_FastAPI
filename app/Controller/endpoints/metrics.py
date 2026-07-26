from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.Services.excel_service import ExcelService
# Corregido: Importamos desde metrics_dto
from app.DTOs.metrics_dto import MonthlyFlowResponse, OperationalDensityResponse
from app.Database.connection import get_db

router = APIRouter()

@router.get(
    "/monthly-flow", 
    response_model=List[MonthlyFlowResponse], 
    status_code=status.HTTP_200_OK,
    summary="Evolución del Flujo de Caja"
)
def get_monthly_flow(db: Session = Depends(get_db)):
    """Responde al Idiom 1: Curvas temporales de brecha financiera."""
    return ExcelService.get_monthly_flow_metrics(db)


@router.get(
    "/operational-density", 
    response_model=List[OperationalDensityResponse], 
    status_code=status.HTTP_200_OK,
    summary="Densidad Operativa"
)
def get_operational_density(db: Session = Depends(get_db)):
    """Responde al Idiom 3: Barras alineadas yuxtapuestas."""
    return ExcelService.get_operational_density_metrics(db)