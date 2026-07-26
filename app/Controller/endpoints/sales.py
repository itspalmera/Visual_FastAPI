from fastapi import APIRouter, UploadFile, File, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.Services.excel_service import ExcelService
from app.DTOs.sales_dto import SaleResponse  # Importación limpia
from app.Database.connection import get_db
from app.Models.sale import Sale

router = APIRouter()

@router.post("/upload-excel", status_code=status.HTTP_200_OK)
async def upload_sales_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Debe subir un archivo .xlsx o .xls")
    
    file_bytes = await file.read()
    lista_ventas = ExcelService.process_sales_excel(file_bytes)
    
    if not lista_ventas:
        return {"status": "success", "message": "Se procesaron 0 registros."}
        
    for venta_dict in lista_ventas:
        db_sale = Sale(**venta_dict)
        db.add(db_sale)
    db.commit()
    
    return {"status": "success", "message": f"Se indexaron {len(lista_ventas)} registros."}


# --- GET ALL ---
@router.get("/", response_model=List[SaleResponse], status_code=status.HTTP_200_OK)
def get_all_sales(db: Session = Depends(get_db)):
    """Obtiene el listado histórico completo de la base de datos."""
    return ExcelService.get_all_sales(db)


# --- GET CON FILTROS ---
@router.get("/search", response_model=List[SaleResponse], status_code=status.HTTP_200_OK)
def get_filtered_sales(
    cliente: Optional[str] = Query(None, description="Nombre o parte del cliente"),
    sheet_name: Optional[str] = Query(None, description="Mes en mayúsculas (Ej: ENERO)"),
    db: Session = Depends(get_db)
):
    """Filtra los registros guardados por nombre de cliente o mes de origen."""
    return ExcelService.get_sales_with_filters(db, cliente=cliente, sheet_name=sheet_name)


# --- GET BY ID ---
@router.get("/{sale_id}", response_model=SaleResponse, status_code=status.HTTP_200_OK)
def get_sale_by_id(sale_id: int, db: Session = Depends(get_db)):
    """Recupera una factura única usando su ID de base de datos."""
    venta = ExcelService.get_sale_by_id(db, sale_id)
    if not venta:
        raise HTTPException(status_code=404, detail=f"No se encontró la factura con ID {sale_id}")
    return venta