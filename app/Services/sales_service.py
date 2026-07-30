from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.Models.sale import Sale


class SalesService:
    @staticmethod
    def get_all_sales(db: Session) -> List[Sale]:
        return db.query(Sale).all()

    @staticmethod
    def get_sale_by_id(db: Session, sale_id: int) -> Optional[Sale]:
        return db.query(Sale).filter(Sale.id == sale_id).first()

    @staticmethod
    def get_sales_with_filters(
        db: Session,
        cliente: Optional[str] = None,
        rut: Optional[str] = None,
        sheet_name: Optional[str] = None,
        min_neto: Optional[float] = None,
        max_neto: Optional[float] = None,
        segmentos: Optional[List[str]] = None,
    ) -> List[Sale]:
        query = db.query(Sale)
        if cliente:
            query = query.filter(Sale.cliente.ilike(f"%{cliente}%"))
        if rut:
            query = query.filter(Sale.rut == rut.strip())
        if sheet_name:
            query = query.filter(func.upper(Sale.sheet_name) == sheet_name.strip().upper())
        if min_neto is not None:
            query = query.filter(Sale.valor_neto >= min_neto)
        if max_neto is not None:
            query = query.filter(Sale.valor_neto <= max_neto)
        if segmentos:
            query = query.filter(Sale.segmento.in_(segmentos))
        return query.all()