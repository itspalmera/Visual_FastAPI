from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.Database.connection import Base  # Tu configuración de base de datos

class Sale(Base):
    __tablename__ = "sales_registry"

    id = Column(Integer, primary_key=True, index=True)
    sheet_name = Column(String, index=True)       # Ejemplo: "ENERO", "FEBRERO"
    fact_number = Column(Integer, index=True)     # Folio de la Factura
    cliente = Column(String)
    rut = Column(String)
    valor_neto = Column(Float)
    iva = Column(Float)
    total_factura = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tipo_documento = Column(String, default="VENTA")  # "VENTA" o "NOTA_CREDITO"