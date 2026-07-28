from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.Services.sales_service import SalesService


class MetricsService:
    @staticmethod
    def get_monthly_flow_metrics(
        db: Session,
        min_neto: Optional[float] = None,
        max_neto: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        sales = SalesService.get_sales_with_filters(db, min_neto=min_neto, max_neto=max_neto)
        if not sales:
            return []

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

        return [
            {
                "sheet_name": mes,
                "ventas_brutas": data["ventas_brutas"],
                "notas_credito": data["notas_credito"],
                "recaudacion_real": data["ventas_brutas"] - data["notas_credito"],
            }
            for mes, data in meses.items()
        ]

    @staticmethod
    def get_client_risk_metrics(
        db: Session,
        min_neto: Optional[float] = None,
        max_neto: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        sales = SalesService.get_sales_with_filters(db, min_neto=min_neto, max_neto=max_neto)
        if not sales:
            return []

        clientes: Dict[str, Dict[str, Any]] = {}
        for s in sales:
            rut = str(s.rut) if s.rut else "SIN_RUT"
            val_neto = float(s.valor_neto or 0.0)

            if rut not in clientes:
                clientes[rut] = {
                    "cliente": str(s.cliente),
                    "recurrencia": 0,
                    "ventas_brutas": 0.0,
                    "monto_nc": 0.0,
                }

            if s.tipo_documento == "NOTA_CREDITO":
                clientes[rut]["monto_nc"] = float(clientes[rut]["monto_nc"]) + val_neto
            else:
                clientes[rut]["recurrencia"] = int(clientes[rut]["recurrencia"]) + 1
                clientes[rut]["ventas_brutas"] = float(clientes[rut]["ventas_brutas"]) + val_neto

        result = []
        for rut, data in clientes.items():
            count = int(data["recurrencia"])
            ventas = float(data["ventas_brutas"])
            nc = float(data["monto_nc"])

            tasa_riesgo = (nc / ventas * 100.0) if ventas > 0 else (100.0 if nc > 0 else 0.0)
            ticket_promedio = (ventas / count) if count > 0 else 0.0

            result.append({
                "rut": rut,
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
    ) -> List[Dict[str, Any]]:
        sales = SalesService.get_sales_with_filters(db, min_neto=min_neto, max_neto=max_neto)
        if not sales:
            return []

        meses: Dict[str, Dict[str, Any]] = {}
        for s in sales:
            mes = str(s.sheet_name)
            val_neto = float(s.valor_neto or 0.0)

            if mes not in meses:
                meses[mes] = {"cantidad": 0, "neto_recaudado": 0.0}

            if s.tipo_documento == "VENTA":
                meses[mes]["cantidad"] = int(meses[mes]["cantidad"]) + 1
                meses[mes]["neto_recaudado"] = float(meses[mes]["neto_recaudado"]) + val_neto
            else:
                meses[mes]["neto_recaudado"] = float(meses[mes]["neto_recaudado"]) - val_neto

        return [
            {
                "sheet_name": mes,
                "cantidad_facturas": int(data["cantidad"]),
                "total_recaudado": float(data["neto_recaudado"]),
            }
            for mes, data in meses.items()
        ]