from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

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
def get_client_risk_matrix(
    min_neto: Optional[float] = Query(None, description="Filtro mínimo de valor neto"),
    max_neto: Optional[float] = Query(None, description="Filtro máximo de valor neto"),
    db: Session = Depends(get_db)
):
    return ExcelService.get_client_risk_metrics(db, min_neto=min_neto, max_neto=max_neto)