from fastapi import APIRouter, UploadFile, File, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.Services.excel_service import ExcelService
from app.Services.sales_service import SalesService
from app.DTOs.sales_dto import SaleResponse
from app.Models.sale import Sale
from app.Database.connection import get_db

router = APIRouter()


@router.post(
    "/upload-excel",
    status_code=status.HTTP_200_OK,
    summary="Subir libro contable en Excel y guardar ventas"
)
async def upload_sales_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Debe subir un archivo .xlsx o .xls")

    file_bytes = await file.read()
    ventas_procesadas = ExcelService.process_sales_excel(file_bytes)
    nuevas_ventas = [Sale(**venta) for venta in ventas_procesadas]

    try:
        db.bulk_save_objects(nuevas_ventas)
        db.commit()
        return {
            "status": "success",
            "message": f"Se procesaron e indexaron exitosamente {len(nuevas_ventas)} registros."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/",
    response_model=List[SaleResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtener todas las ventas con filtros opcionales"
)
def get_sales(
    cliente: Optional[str] = Query(None),
    sheet_name: Optional[str] = Query(None),
    min_neto: Optional[float] = Query(None),
    max_neto: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    return SalesService.get_sales_with_filters(
        db, cliente=cliente, sheet_name=sheet_name, min_neto=min_neto, max_neto=max_neto
    )


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener una venta por ID"
)
def get_sale_by_id(sale_id: int, db: Session = Depends(get_db)):
    sale = SalesService.get_sale_by_id(db, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return sale