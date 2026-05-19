from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.Services.excel_service import ExcelService
from app.Models.sale import Sale
from app.Database.connection import get_db  

router = APIRouter()

@router.post("/upload-excel")
async def upload_sales_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_bytes = await file.read()
    
    # 1. Procesamos el Excel con los filtros inteligentes que armamos
    ventas_procesadas = ExcelService.process_sales_excel(file_bytes)
    
    # 2. Mapeamos los diccionarios al modelo SQLAlchemy
    nuevas_ventas = [Sale(**venta) for venta in ventas_procesadas]
    
    try:
        # 3. Guardamos todo masivamente en la Base de Datos
        db.bulk_save_objects(nuevas_ventas)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Se procesaron e indexaron exitosamente {len(nuevas_ventas)} registros históricos."
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}