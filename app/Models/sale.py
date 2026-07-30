from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer
from app.Database.connection import Base


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sheet_name: Mapped[str] = mapped_column(String)
    fact_number: Mapped[int] = mapped_column(Integer)
    cliente: Mapped[str] = mapped_column(String)
    rut: Mapped[str] = mapped_column(String)
    tipo_documento: Mapped[str] = mapped_column(String)
    valor_neto: Mapped[float] = mapped_column(Float, default=0.0)
    iva: Mapped[float] = mapped_column(Float, default=0.0)
    total_factura: Mapped[float] = mapped_column(Float, default=0.0)
    segmento: Mapped[str] = mapped_column(String, default="Mantenciones Ocasionales")