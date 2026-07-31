"""
Servicio de Cálculo de Métricas Analíticas y Financieras.

Este módulo provee la lógica de negocio para procesar y consolidar la información
de ventas almacenada en la base de datos, generando agregaciones estructuradas para
diagramas de flujo mensual, matrices de perfil de riesgo de clientes y densidad operacional.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.Services.sales_service import SalesService

# Diccionario auxiliar para garantizar que los gráficos rendericen los meses en orden
MESES_ORDEN = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
    "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
}


class MetricsService:
    """
    Servicio encargado de transformar y agregar registros de ventas en indicadores analíticos.
    """

    @staticmethod
    def get_monthly_flow_metrics(
        db: Session,
        rut: Optional[str] = None,
        min_neto: Optional[float] = None,
        max_neto: Optional[float] = None,
        segmentos: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calcula las métricas de flujo de caja mensual (ventas brutas, notas de crédito y recaudación real).

        Proceso:
        1. Consulta las ventas filtradas a través de `SalesService`.
        2. Agrupa los montos por mes (`sheet_name`) diferenciando entre ventas y notas de crédito.
        3. Calcula la recaudación real (`ventas_brutas` - `notas_credito`).
        4. Ordena el resultado de forma cronológica utilizando `MESES_ORDEN`.

        Args:
            db (Session): Sesión activa de SQLAlchemy.
            rut (Optional[str]): Filtro opcional por RUT de cliente. Default: `None`.
            min_neto (Optional[float]): Filtro opcional de valor neto mínimo. Default: `None`.
            max_neto (Optional[float]): Filtro opcional de valor neto máximo. Default: `None`.
            segmentos (Optional[List[str]]): Filtro opcional por lista de segmentos comerciales. Default: `None`.

        Returns:
            List[Dict[str, Any]]: Lista de diccionarios ordenada por mes con la estructura de `MonthlyFlowResponse`.
        """
        # Obtenemos los registros filtrados desde la capa de persistencia
        sales = SalesService.get_sales_with_filters(
            db, min_neto=min_neto, max_neto=max_neto, rut=rut, segmentos=segmentos
        )
        if not sales:
            return []

        # Agregación por periodo/mes
        meses: Dict[str, Dict[str, float]] = {}
        for s in sales:
            mes = str(s.sheet_name)
            val_neto = float(s.valor_neto or 0.0)

            if mes not in meses:
                meses[mes] = {"ventas_brutas": 0.0, "notas_credito": 0.0}

            if s.tipo_documento == "NOTA_CREDITO":
                meses[mes]["notas_credito"] += val_neto
            else:
                meses[mes]["ventas_brutas"] += val_neto

        # Construcción de la respuesta calculando la recaudación real
        resultado = [
            {
                "sheet_name": mes,
                "ventas_brutas": data["ventas_brutas"],
                "notas_credito": data["notas_credito"],
                "recaudacion_real": data["ventas_brutas"] - data["notas_credito"],
            }
            for mes, data in meses.items()
        ]
        
        # Ordenamos cronológicamente según el diccionario auxiliar
        resultado.sort(key=lambda x: MESES_ORDEN.get(str(x["sheet_name"]).upper(), 99))
        return resultado

    @staticmethod
    def get_client_risk_metrics(
        db: Session,
        min_neto: Optional[float] = None,
        max_neto: Optional[float] = None,
        rut: Optional[str] = None,
        segmentos: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calcula la matriz de perfil de riesgo y comportamiento comercial por cliente.

        Proceso:
        1. Consulta las ventas filtradas a través de `SalesService`.
        2. Agrupa por RUT del cliente acumulando recurrencia (cantidad de facturas), ventas brutas y monto de notas de crédito.
        3. Calcula el ticket promedio (`ventas_brutas` / `recurrencia`) y la tasa de riesgo (% de notas de crédito respecto al total).

        Args:
            db (Session): Sesión activa de SQLAlchemy.
            min_neto (Optional[float]): Filtro opcional de valor neto mínimo. Default: `None`.
            max_neto (Optional[float]): Filtro opcional de valor neto máximo. Default: `None`.
            rut (Optional[str]): Filtro opcional por RUT de cliente. Default: `None`.
            segmentos (Optional[List[str]]): Filtro opcional por lista de segmentos comerciales. Default: `None`.

        Returns:
            List[Dict[str, Any]]: Lista de diccionarios con la estructura de `ClientRiskProfileResponse`.
        """
        # Obtenemos los registros filtrados desde la capa de persistencia
        sales = SalesService.get_sales_with_filters(
            db, min_neto=min_neto, max_neto=max_neto, rut=rut, segmentos=segmentos
        )
        if not sales:
            return []

        # Agregación por cliente (RUT)
        clientes: Dict[str, Dict[str, Any]] = {}
        for s in sales:
            client_rut = str(s.rut) if s.rut else "SIN_RUT"
            val_neto = float(s.valor_neto or 0.0)

            if client_rut not in clientes:
                clientes[client_rut] = {
                    "cliente": str(s.cliente),
                    "recurrencia": 0,
                    "ventas_brutas": 0.0,
                    "monto_nc": 0.0,
                }

            if s.tipo_documento == "NOTA_CREDITO":
                clientes[client_rut]["monto_nc"] += val_neto
            else:
                clientes[client_rut]["recurrencia"] += 1
                clientes[client_rut]["ventas_brutas"] += val_neto

        # Cálculo de indicadores por cliente (tasa de riesgo y ticket promedio)
        result = []
        for client_rut, data in clientes.items():
            count = int(data["recurrencia"])
            ventas = float(data["ventas_brutas"])
            nc = float(data["monto_nc"])

            tasa_riesgo = (nc / ventas * 100.0) if ventas > 0 else (100.0 if nc > 0 else 0.0)
            ticket_promedio = (ventas / count) if count > 0 else 0.0

            result.append({
                "rut": client_rut,
                "cliente": data["cliente"],
                "recurrencia": count,
                "ticket_promedio": ticket_promedio,
                "ventas_totales": ventas,
                "tasa_riesgo": round(tasa_riesgo, 2),
            })
        return result

    @staticmethod
    def get_operational_density_metrics(
        db: Session,
        min_neto: Optional[float] = None,
        max_neto: Optional[float] = None,
        rut: Optional[str] = None,
        segmentos: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calcula las métricas de densidad operativa (cantidad de facturas y total recaudado por periodo).

        Proceso:
        1. Consulta las ventas filtradas a través de `SalesService`.
        2. Agrupa por mes (`sheet_name`) contando la cantidad de facturas emitidas y restando notas de crédito del neto acumulado.
        3. Ordena el resultado cronológicamente mediante `MESES_ORDEN`.

        Args:
            db (Session): Sesión activa de SQLAlchemy.
            min_neto (Optional[float]): Filtro opcional de valor neto mínimo. Default: `None`.
            max_neto (Optional[float]): Filtro opcional de valor neto máximo. Default: `None`.
            rut (Optional[str]): Filtro opcional por RUT de cliente. Default: `None`.
            segmentos (Optional[List[str]]): Filtro opcional por lista de segmentos comerciales. Default: `None`.

        Returns:
            List[Dict[str, Any]]: Lista de diccionarios ordenada por mes con la estructura de `OperationalDensityResponse`.
        """
        # Obtenemos los registros filtrados desde la capa de persistencia
        sales = SalesService.get_sales_with_filters(
            db, 
            min_neto=min_neto, 
            max_neto=max_neto, 
            rut=rut, 
            segmentos=segmentos
        )
        if not sales:
            return []

        # Agregación de cantidad de documentos y recaudación neta por mes
        meses: Dict[str, Dict[str, Any]] = {}
        for s in sales:
            mes = str(s.sheet_name)
            val_neto = float(s.valor_neto or 0.0)

            if mes not in meses:
                meses[mes] = {"cantidad": 0, "neto_recaudado": 0.0}

            if s.tipo_documento == "VENTA":
                meses[mes]["cantidad"] += 1
                meses[mes]["neto_recaudado"] += val_neto
            else:
                meses[mes]["neto_recaudado"] -= val_neto

        # Construcción de la respuesta estructurada
        resultado = [
            {
                "sheet_name": mes,
                "cantidad_facturas": int(data["cantidad"]),
                "total_recaudado": float(data["neto_recaudado"]),
            }
            for mes, data in meses.items()
        ]
        
        # Ordenamos cronológicamente
        resultado.sort(key=lambda x: MESES_ORDEN.get(str(x["sheet_name"]).upper(), 99))
        return resultado