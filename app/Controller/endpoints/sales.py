from fastapi import APIRouter, UploadFile, File, status, HTTPException
from typing import List
from app.Services.excel_service import ExcelService
from app.DTOs.sales_dto import SheetProcessResponse

router = APIRouter(prefix="/sales", tags=["Procesamiento de Ventas"])

@router.post(
    "/upload-excel", 
    response_model=List[SheetProcessResponse], 
    status_code=status.HTTP_200_OK,
    summary="Cargar y procesar libro Excel de ventas"
)
async def upload_sales_excel(file: UploadFile = File(..., description="Archivo .xlsx de Compras/Ventas")):
    """
    Sube un archivo Excel consolidado de compras y ventas. El sistema filtrará 
    exclusivamente las hojas de los meses y extraerá los registros limpios.
    """
    # Validación básica de extensión (.csproj / FluentValidation style)
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extensión de archivo no soportada. Debe ser .xlsx o .xls"
        )
    
    # Leemos los bytes en memoria de forma asíncrona
    file_bytes = await file.read()
    
    # Invocamos la lógica de negocio
    resultado = ExcelService.process_sales_excel(file_bytes)
    
    return resultado