from fastapi import APIRouter, UploadFile, File, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.Services.excel_service import ExcelService
from app.Services.sales_service import SalesService
from app.DTOs.sales_dto import SaleResponse
from app.Models.sale import Sale
from app.Database.connection import get_db

# Inicialización del router de FastAPI para endpoints relacionados con la gestión de ventas
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
    """
    Procesa y carga masivamente registros de ventas desde un archivo Excel (.xlsx o .xls).

    El flujo realiza las siguientes operaciones:
    1. Valida la extensión del archivo subido.
    2. Lee el archivo en memoria y lo transforma en objetos del modelo ORM `Sale` mediante `ExcelService`.
    3. Realiza la inserción masiva (`bulk_save_objects`) en la base de datos dentro de una transacción.

    ### Parámetros:
    - **file** *(UploadFile)*: Archivo Excel que contiene la planilla de ventas (`.xlsx` o `.xls`).

    ### Inyección de Dependencias:
    - **db** *(Session)*: Sesión activa de base de datos administrada por `get_db`.

    ### Respuestas:
    - **200 OK**: Objeto JSON con el estado de la operación y la cantidad de registros ingresados.
    - **400 Bad Request**: El archivo no tiene una extensión permitida (`.xlsx` o `.xls`).
    - **500 Internal Server Error**: Fallo durante la inserción en base de datos (se ejecuta un rollback automático).
    """
    # Validación del formato del archivo adjunto
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Debe subir un archivo .xlsx o .xls")

    # Lectura del contenido binario del archivo
    file_bytes = await file.read()
    
    # Procesamiento del libro Excel a través de la capa de servicios
    ventas_procesadas = ExcelService.process_sales_excel(file_bytes)
    nuevas_ventas = [Sale(**venta) for venta in ventas_procesadas]

    # Inserción masiva en la base de datos con manejo de transacciones
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
    """
    Obtiene el listado general de ventas con soporte para múltiples filtros combinables.

    Permite consultar el historial filtrando por coincidencia o rango de valores.

    ### Parámetros de Consulta (Query Parameters):
    - **cliente** *(str, opcional)*: Nombre o razón social del cliente. Default: `None`.
    - **sheet_name** *(str, opcional)*: Nombre de la hoja o categoría del origen del dato. Default: `None`.
    - **min_neto** *(float, opcional)*: Límite inferior para filtrar por valor neto. Default: `None`.
    - **max_neto** *(float, opcional)*: Límite superior para filtrar por valor neto. Default: `None`.

    ### Inyección de Dependencias:
    - **db** *(Session)*: Sesión activa de SQLAlchemy.

    ### Respuestas:
    - **200 OK**: Lista de objetos `SaleResponse` correspondiente a las ventas encontradas.
    """
    # Delegación de la consulta con filtros a la capa de servicios
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
    """
    Recupera los detalles de un registro de venta específico mediante su identificador único.

    ### Parámetros de Ruta (Path Parameters):
    - **sale_id** *(int)*: Identificador único (`ID`) de la venta en la base de datos.

    ### Inyección de Dependencias:
    - **db** *(Session)*: Sesión activa de base de datos.

    ### Respuestas:
    - **200 OK**: Retorna el objeto `SaleResponse` correspondiente a la venta.
    - **404 Not Found**: No existe ninguna venta asociada al `sale_id` especificado.
    """
    # Búsqueda del registro individual a través de la capa de servicios
    sale = SalesService.get_sale_by_id(db, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return sale