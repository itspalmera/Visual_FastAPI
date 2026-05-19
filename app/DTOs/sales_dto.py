from pydantic import BaseModel, Field
from typing import List, Optional

class SaleRecord(BaseModel):
    factura_n: Optional[str] = Field(None, alias="FACT. N°")
    cliente: str = Field(..., alias="CLIENTE")
    rut: str = Field(..., alias="RUT")
    valor_neto: Optional[float] = Field(None, alias="VALOR NETO")
    iva: Optional[float] = Field(None, alias="IVA")
    total_factura: Optional[float] = Field(None, alias="TOTAL FACTURA")

    class Config:
        populate_by_name = True

class SheetProcessResponse(BaseModel):
    sheet_name: str
    records_count: int
    data: List[SaleRecord]