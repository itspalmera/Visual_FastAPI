from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.Services.excel_service import ExcelService
from app.DTOs.client_dto import ClientRiskProfileResponse
from app.Database.connection import get_db

router = APIRouter()

@router.get(
    "/risk-matrix", 
    response_model=List[ClientRiskProfileResponse], 
    status_code=status.HTTP_200_OK,
    summary="Matriz de Clientes: Recurrencia, Ticket Promedio y Tasa de Riesgo"
)
def get_client_risk_matrix(db: Session = Depends(get_db)):
    """Responde al Idiom 2: Diagrama de dispersión de riesgo por cliente."""
    return ExcelService.get_client_risk_metrics(db)