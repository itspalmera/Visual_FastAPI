from pydantic import BaseModel

# DTO para el Idiom 2: Diagrama de Dispersión / Matriz de Riesgo
class ClientRiskProfileResponse(BaseModel):
    rut: str
    cliente: str
    recurrencia: int          # Cantidad de facturas emitidas (Eje X)
    ticket_promedio: float     # Promedio neto por factura (Eje Y)
    ventas_totales: float      # Área de la marca (Tamaño)
    tasa_riesgo: float         # % o ratio de Notas de Crédito (Color)

    model_config = {"from_attributes": True}