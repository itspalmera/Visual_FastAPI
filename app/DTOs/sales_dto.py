"""
Objetos de Transferencia de Datos (DTOs) para la Gestión de Ventas.

Este módulo define los esquemas de Pydantic V2 utilizados tanto para la ingesta
y parseo de planillas Excel (mapeo con alias de columnas) como para la persistencia,
creación y serialización de registros de ventas provenientes de la base de datos.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ==========================================
# DTOs PARA EL POST (Procesamiento por Hojas)
# ==========================================
class SaleRecord(BaseModel):
    """
    Representa un registro o fila individual extraída de una planilla Excel.

    Utiliza alias (`Field(..., alias=...)`) para mapear directamente los encabezados
    originales del libro contable en Excel a nombres de atributos estandarizados en Python.

    Atributos:
        factura_n (Optional[str]): Número de la factura (Columna: 'FACT. N°'). Default: `None`.
        cliente (str): Nombre o razón social del cliente (Columna: 'CLIENTE'). Requerido.
        rut (str): Identificador tributario (Columna: 'RUT'). Requerido.
        valor_neto (Optional[float]): Monto neto sin impuestos (Columna: 'VALOR NETO'). Default: `None`.
        iva (Optional[float]): Impuesto al Valor Agregado (Columna: 'IVA'). Default: `None`.
        total_factura (Optional[float]): Monto total facturado (Columna: 'TOTAL FACTURA'). Default: `None`.
    """
    factura_n: Optional[str] = Field(None, alias="FACT. N°")
    cliente: str = Field(..., alias="CLIENTE")
    rut: str = Field(..., alias="RUT")
    valor_neto: Optional[float] = Field(None, alias="VALOR NETO")
    iva: Optional[float] = Field(None, alias="IVA")
    total_factura: Optional[float] = Field(None, alias="TOTAL FACTURA")

    # Permite instanciar el modelo usando tanto el alias del Excel como el nombre del atributo en Python
    model_config = {"populate_by_name": True}


class SheetProcessResponse(BaseModel):
    """
    Respuesta estructurada del procesamiento de una hoja individual del libro Excel.

    Atributos:
        sheet_name (str): Nombre de la pestaña u hoja procesada.
        records_count (int): Cantidad total de registros extraídos en la hoja.
        data (List[SaleRecord]): Lista con los registros parseados de la hoja.
    """
    sheet_name: str
    records_count: int
    data: List[SaleRecord]


# ==========================================
# DTOs PARA EL GET (Consulta a Base de Datos)
# ==========================================
class SaleCreate(BaseModel):
    """
    Esquema base para la creación y persistencia de un registro de venta en la base de datos.

    Atributos:
        sheet_name (str): Nombre de la hoja o categoría de origen.
        fact_number (int): Número correlativo numérico de la factura.
        cliente (str): Nombre o razón social del cliente.
        rut (str): Identificador tributario (RUT).
        tipo_documento (str): Tipo de documento emitido. Default: `"VENTA"`.
        valor_neto (float): Monto neto de la transacción.
        iva (float): Monto correspondiente al IVA.
        total_factura (float): Monto total facturado.
        segmento (str): Clasificación comercial asignada. Default: `"Mantenciones Ocasionales"`.
    """
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
    """
    Esquema de respuesta para la consulta de ventas almacenadas.

    Hereda la estructura completa de `SaleCreate` e incorpora la clave primaria
    autogenerada por la base de datos.

    Atributos:
        id (int): Identificador único (`ID`) de la venta en la base de datos.
    """
    id: int

    # Configuración limpia de Pydantic V2 para leer modelos ORM de SQLAlchemy
    model_config = {"from_attributes": True}