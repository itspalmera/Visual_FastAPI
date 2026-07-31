from pydantic import BaseModel


class ClientRiskProfileResponse(BaseModel):
    """
    Objeto de Transferencia de Datos (DTO) para la Matriz de Riesgo de Clientes.

    Diseñado para alimentar visualizaciones avanzadas (ej. Diagrama de Dispersión / Scatter Plot),
    mapeando métricas clave de comportamiento comercial a canales de representación visual.

    Atributos:
        rut (str): Identificador único o RUT del cliente.
        cliente (str): Nombre o razón social del cliente.
        recurrencia (int): Cantidad total de facturas emitidas (Eje X en la gráfica).
        ticket_promedio (float): Promedio del valor neto por factura (Eje Y en la gráfica).
        ventas_totales (float): Volumen total de ventas acumuladas (Área / Tamaño del punto).
        tasa_riesgo (float): Ratio o porcentaje de Notas de Crédito asociadas (Color del punto).
    """
    rut: str
    cliente: str
    recurrencia: int          # Cantidad de facturas emitidas (Eje X)
    ticket_promedio: float     # Promedio neto por factura (Eje Y)
    ventas_totales: float      # Área de la marca (Tamaño)
    tasa_riesgo: float         # % o ratio de Notas de Crédito (Color)

    # Permite a Pydantic mapear campos directamente desde atributos de modelos ORM (SQLAlchemy)
    model_config = {"from_attributes": True}