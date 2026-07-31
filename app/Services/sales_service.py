"""
Servicio de Consulta y Acceso a Datos de Ventas (SalesService).

Este módulo encapsula las operaciones de lectura directamente sobre la base de datos
utilizando SQLAlchemy ORM. Provee métodos para obtener ventas individuales, listados
completos y consultas complejas con filtros dinámicos (búsqueda insensible a mayúsculas,
rangos numéricos, coincidencias exactas y listas de segmentos).
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.Models.sale import Sale


class SalesService:
    """
    Servicio de capa de acceso a datos para la entidad ORM `Sale`.
    """

    @staticmethod
    def get_all_sales(db: Session) -> List[Sale]:
        """
        Recupera la totalidad de los registros de ventas almacenados en la base de datos sin aplicar filtros.

        Args:
            db (Session): Sesión activa de SQLAlchemy.

        Returns:
            List[Sale]: Lista completa de objetos ORM `Sale`.
        """
        return db.query(Sale).all()

    @staticmethod
    def get_sale_by_id(db: Session, sale_id: int) -> Optional[Sale]:
        """
        Busca y retorna un registro de venta específico por su clave primaria (`ID`).

        Args:
            db (Session): Sesión activa de SQLAlchemy.
            sale_id (int): Identificador único de la venta.

        Returns:
            Optional[Sale]: Instancia del objeto `Sale` si existe, o `None` si no es encontrado.
        """
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
        """
        Consulta y filtra registros de ventas construyendo dinámicamente una consulta en SQLAlchemy.

        Los filtros se combinan mediante cláusulas `AND` si son proporcionados:
        - **cliente**: Búsqueda parcial e insensible a mayúsculas/minúsculas (`ILIKE`).
        - **rut**: Coincidencia exacta eliminando espacios laterales.
        - **sheet_name**: Coincidencia exacta insensible a mayúsculas usando `func.upper`.
        - **min_neto / max_neto**: Filtrado por rango del atributo `valor_neto`.
        - **segmentos**: Coincidencia dentro de una lista de categorías/segmentos (`IN`).

        Args:
            db (Session): Sesión activa de SQLAlchemy.
            cliente (Optional[str]): Coincidencia parcial con el nombre o razón social del cliente. Default: `None`.
            rut (Optional[str]): Identificador tributario (RUT) del cliente. Default: `None`.
            sheet_name (Optional[str]): Nombre de la hoja/mes contable de origen. Default: `None`.
            min_neto (Optional[float]): Mínimo valor neto requerido. Default: `None`.
            max_neto (Optional[float]): Máximo valor neto permitido. Default: `None`.
            segmentos (Optional[List[str]]): Lista de segmentos comerciales autorizados. Default: `None`.

        Returns:
            List[Sale]: Lista de objetos `Sale` que cumplen con todos los criterios aplicados.
        """
        # Inicialización de la consulta base sobre la entidad Sale
        query = db.query(Sale)

        # Filtro por cliente (búsqueda parcial insensitivecase)
        if cliente:
            query = query.filter(Sale.cliente.ilike(f"%{cliente}%"))
            
        # Filtro por RUT exacto
        if rut:
            query = query.filter(Sale.rut == rut.strip())
            
        # Filtro por hoja/mes ignorando diferencias entre mayúsculas y minúsculas
        if sheet_name:
            query = query.filter(func.upper(Sale.sheet_name) == sheet_name.strip().upper())
            
        # Filtros por rango numérico en valor_neto
        if min_neto is not None:
            query = query.filter(Sale.valor_neto >= min_neto)
        if max_neto is not None:
            query = query.filter(Sale.valor_neto <= max_neto)
            
        # Filtro por pertenencia a una lista de segmentos
        if segmentos:
            query = query.filter(Sale.segmento.in_(segmentos))

        # Ejecución de la consulta y retorno de resultados
        return query.all()