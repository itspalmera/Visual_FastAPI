from fastapi import APIRouter, UploadFile, File, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.Services.excel_service import ExcelService
from app.DTOs.sales_dto import SaleResponse
from app.Models.sale import Sale
from app.Database.connection import get_db

# Esta es la variable exacta que router.py necesita importar
router = APIRouter()

# -----------------------------------------------------------------
# 1. POST: Cargar y procesar libro Excel
# -----------------------------------------------------------------
@router.post(
    "/upload-excel", 
    status_code=status.HTTP_200_OK,
    summary="Subir libro contable en Excel y guardar ventas"
)
async def upload_sales_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Debe subir un archivo .xlsx o .xls")
        
    file_bytes = await file.read()
    ventas_procesadas = ExcelService.process_sales_excel(file_bytes)
    nuevas_ventas = [Sale(**venta) for venta in ventas_procesadas]
    
    try:
        db.bulk_save_objects(nuevas_ventas)
        db.commit()
        return {
            "status": "success",
            "message": f"Se procesaron e indexaron exitosamente {len(nuevas_ventas)} registros históricos."
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}

# -----------------------------------------------------------------
# 2. GET ALL: Listado histórico completo
# -----------------------------------------------------------------
@router.get(
    "/", 
    response_model=List[SaleResponse], 
    status_code=status.HTTP_200_OK,
    summary="Obtener todas las facturas guardadas"
)
def get_all_sales(db: Session = Depends(get_db)):
    return ExcelService.get_all_sales(db)

# -----------------------------------------------------------------
# 3. GET SEARCH: Filtrar por cliente o mes
# -----------------------------------------------------------------
@router.get(
    "/search", 
    response_model=List[SaleResponse], 
    status_code=status.HTTP_200_OK,
    summary="Filtrar facturas por cliente o mes"
)
def get_filtered_sales(
    cliente: Optional[str] = Query(None, description="Parte del nombre del cliente"),
    sheet_name: Optional[str] = Query(None, description="Mes exacto (Ej: ENERO)"),
    db: Session = Depends(get_db)
):
    return ExcelService.get_sales_with_filters(db, cliente=cliente, sheet_name=sheet_name)

# -----------------------------------------------------------------
# 4. GET BY ID: Factura específica
# -----------------------------------------------------------------
@router.get(
    "/{sale_id}", 
    response_model=SaleResponse, 
    status_code=status.HTTP_200_OK,
    summary="Obtener una factura por su ID"
)
def get_sale_by_id(sale_id: int, db: Session = Depends(get_db)):
    venta = ExcelService.get_sale_by_id(db, sale_id)
    if not venta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"No se encontró la factura con ID {sale_id}"
        )
    return venta