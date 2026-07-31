"""
Objetos de Transferencia de Datos (DTOs) para Métricas Analíticas y Visualización.

Este módulo define los esquemas de Pydantic V2 utilizados para estructurar las
respuestas de los endpoints de métricas financieras y operacionales. Diseñados
específicamente para alimentar idioms de visualización de datos (gráficos de flujo, 
barras de densidad, etc.).
"""

from pydantic import BaseModel


# DTO para el Idiom 1: Flujo de caja mensual
class MonthlyFlowResponse(BaseModel):
    """
    Objeto de Transferencia de Datos (DTO) para el Flujo de Caja Mensual (Idiom 1).

    Estructura el comportamiento financiero acumulado por periodo u hoja, permitiendo
    analizar la relación entre las ventas brutas, el impacto de las notas de crédito
    y el dinero neto efectivamente ingresado.

    Atributos:
        sheet_name (str): Nombre de la hoja, mes o periodo contable analizado.
        ventas_brutas (float): Total bruto acumulado de ventas/facturas emitidas.
        notas_credito (float): Monto total descontado o anulado mediante notas de crédito.
        recaudacion_real (float): Flujo neto real percibido (`ventas_brutas` - `notas_credito`).
    """
    sheet_name: str
    ventas_brutas: float
    notas_credito: float
    recaudacion_real: float

    # Configuración de Pydantic V2 para mapear atributos directamente desde objetos/modelos ORM
    model_config = {"from_attributes": True}


# DTO para el Idiom 3: Densidad Operativa (Barras alineadas)
class OperationalDensityResponse(BaseModel):
    """
    Objeto de Transferencia de Datos (DTO) para la Densidad Operativa (Idiom 3).

    Diseñado para alimentaciones gráficas de barras alineadas u ordenadas,
    permitiendo comparar el volumen transaccional (cantidad de facturas)
    frente a la carga o densidad financiera total alcanzada por periodo o categoría.

    Atributos:
        sheet_name (str): Nombre de la hoja, categoría o periodo analizado.
        cantidad_facturas (int): Cantidad total de documentos/facturas procesados.
        total_recaudado (float): Monto total financiero acumulado en la categoría/periodo.
    """
    sheet_name: str
    cantidad_facturas: int
    total_recaudado: float

    # Configuración de Pydantic V2 para mapear atributos directamente desde objetos/modelos ORM
    model_config = {"from_attributes": True}