"""
Modelo ORM de Entidad: Venta (Sale).

Este módulo define la tabla 'sales' en la base de datos utilizando la sintaxis
moderna de SQLAlchemy 2.0 (Mapped y mapped_column). Mapea cada registro de venta
o factura procesada desde el libro contable.
"""

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer
from app.Database.connection import Base


class Sale(Base):
    """
    Modelo ORM que representa un registro de venta en la tabla 'sales'.

    Almacena el detalle financiero y operativo de cada documento o factura emitida,
    así como datos del cliente, segmentación comercial y la hoja de origen.

    Atributos:
        id (int): Clave primaria autoincremental e indexada de la transacción.
        sheet_name (str): Nombre de la hoja o periodo del libro contable de origen.
        fact_number (int): Número correlativo de la factura.
        cliente (str): Nombre o razón social del cliente.
        rut (str): Identificador tributario (RUT) del cliente.
        tipo_documento (str): Tipo de documento emitido (ej. "VENTA", "NOTA DE CRÉDITO").
        valor_neto (float): Monto neto de la factura sin impuestos. Default: `0.0`.
        iva (float): Monto por concepto de Impuesto al Valor Agregado. Default: `0.0`.
        total_factura (float): Monto total del documento (`valor_neto` + `iva`). Default: `0.0`.
        segmento (str): Categorización comercial del cliente o tipo de servicio. Default: `"Mantenciones Ocasionales"`.
    """
    # Nombre explícito de la tabla en la base de datos
    __tablename__ = "sales"

    # Clave primaria e identificador único indexado
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Identificación y origen de la transacción
    sheet_name: Mapped[str] = mapped_column(String)
    fact_number: Mapped[int] = mapped_column(Integer)
    cliente: Mapped[str] = mapped_column(String)
    rut: Mapped[str] = mapped_column(String)
    tipo_documento: Mapped[str] = mapped_column(String)
    
    # Valores financieros (con valores por defecto en 0.0)
    valor_neto: Mapped[float] = mapped_column(Float, default=0.0)
    iva: Mapped[float] = mapped_column(Float, default=0.0)
    total_factura: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Segmentación comercial del registro
    segmento: Mapped[str] = mapped_column(String, default="Mantenciones Ocasionales")