from pydantic import BaseModel, Field
from typing import List, Optional


# ==========================================
# DTOs PARA EL POST (Procesamiento por Hojas)
# ==========================================
class SaleRecord(BaseModel):
    factura_n: Optional[str] = Field(None, alias="FACT. N°")
    cliente: str = Field(..., alias="CLIENTE")
    rut: str = Field(..., alias="RUT")
    valor_neto: Optional[float] = Field(None, alias="VALOR NETO")
    iva: Optional[float] = Field(None, alias="IVA")
    total_factura: Optional[float] = Field(None, alias="TOTAL FACTURA")

    model_config = {"populate_by_name": True}


class SheetProcessResponse(BaseModel):
    sheet_name: str
    records_count: int
    data: List[SaleRecord]


# ==========================================
# DTOs PARA EL GET (Consulta a Base de Datos)
# ==========================================
class SaleCreate(BaseModel):
    sheet_name: str
    fact_number: int
    cliente: str
    rut: str
    tipo_documento: str = "VENTA"
    valor_neto: float
    iva: float
    total_factura: float
    segmento: str = "Mantenciones Ocasionales"


class SaleResponse(SaleCreate):
    id: int

    # Configuración limpia de Pydantic V2 para leer modelos ORM de SQLAlchemy
    model_config = {"from_attributes": True}