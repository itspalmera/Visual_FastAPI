from pydantic import BaseModel

# DTO para el Idiom 1: Flujo de caja mensual
class MonthlyFlowResponse(BaseModel):
    sheet_name: str
    ventas_brutas: float
    notas_credito: float
    recaudacion_real: float

    model_config = {"from_attributes": True}


# DTO para el Idiom 3: Densidad Operativa (Barras alineadas)
class OperationalDensityResponse(BaseModel):
    sheet_name: str
    cantidad_facturas: int
    total_recaudado: float

    model_config = {"from_attributes": True}