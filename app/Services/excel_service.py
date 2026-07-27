import io
import pandas as pd
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.Models.sale import Sale


class ExcelService:
    @staticmethod
    def process_sales_excel(file_bytes: bytes) -> List[Dict[str, Any]]:
        processed_records = []

        try:
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error al abrir el archivo Excel: {str(e)}"
            )

        meses_validos = [
            "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
            "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
        ]

        for sheet_name in excel_file.sheet_names:
            sheet_name_upper = sheet_name.strip().upper()
            if not any(mes in sheet_name_upper for mes in meses_validos):
                continue

            df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

            header_row_idx = None
            idx_cliente = None
            
            for idx, row in df_raw.iterrows():
                row_str = [str(cell).strip().upper() for cell in row]
                if "CLIENTE" in row_str or "TOTAL FACTURA" in row_str:
                    indices_posibles = [i for i, s in enumerate(row_str) if "CLIENTE" in s]
                    if indices_posibles:
                        header_row_idx = idx
                        idx_cliente = indices_posibles[0]
                        break

            if header_row_idx is None or idx_cliente is None:
                continue  

            df_sales = df_raw.iloc[header_row_idx:].copy()
            inicio_ventas_col = max(0, idx_cliente - 1)
            df_sales = df_sales.iloc[:, inicio_ventas_col:]

            df_sales.columns = [str(c).strip().upper() for c in df_sales.iloc[0]]
            df_sales = df_sales.iloc[1:]

            column_mapping = {}
            assigned_targets = set()

            for c in df_sales.columns:
                if ("FACT" in c or "N°" in c or "NUMERO" in c or "FOLIO" in c) and "FACT. N°" not in assigned_targets:
                    column_mapping[c] = "FACT. N°"
                    assigned_targets.add("FACT. N°")
                elif ("CLIENTE" in c or "RAZON" in c) and "CLIENTE" not in assigned_targets:
                    column_mapping[c] = "CLIENTE"
                    assigned_targets.add("CLIENTE")
                elif ("RUT" in c or "RECEPTOR" in c) and "RUT" not in assigned_targets:
                    column_mapping[c] = "RUT"
                    assigned_targets.add("RUT")
                elif "NETO" in c and "VALOR NETO" not in assigned_targets:
                    column_mapping[c] = "VALOR NETO"
                    assigned_targets.add("VALOR NETO")
                elif "IVA" in c and "IVA" not in assigned_targets:
                    column_mapping[c] = "IVA"
                    assigned_targets.add("IVA")
                elif "TOTAL" in c and "TOTAL FACTURA" not in assigned_targets:
                    column_mapping[c] = "TOTAL FACTURA"
                    assigned_targets.add("TOTAL FACTURA")

            if "CLIENTE" not in column_mapping.values():
                continue

            df_sales = df_sales[list(column_mapping.keys())].rename(columns=column_mapping)

            current_doc_type = "VENTA"

            for _, row in df_sales.iterrows():
                cliente_str = str(row["CLIENTE"]).strip().upper()

                if "NOTA DE CREDITO" in cliente_str or "NOTAS DE CREDITO" in cliente_str:
                    current_doc_type = "NOTA_CREDITO"
                    continue

                if cliente_str in ["NAN", "NONE", "", "0", "0.0"]:
                    continue

                if any(kw in cliente_str for kw in ["TOTAL", "SUB TOTAL", "SUBTOTAL", "SALDO", "ELECTRONICAS"]):
                    continue

                fact_str = str(row.get("FACT. N°", "0")).replace(".0", "").strip()
                fact_numeric = int(fact_str) if fact_str.isdigit() else 0

                val_neto = pd.to_numeric(row.get("VALOR NETO"), errors='coerce') or 0.0
                val_iva = pd.to_numeric(row.get("IVA"), errors='coerce') or 0.0
                val_total = pd.to_numeric(row.get("TOTAL FACTURA"), errors='coerce') or 0.0

                processed_records.append({
                    "sheet_name": sheet_name,
                    "fact_number": fact_numeric,
                    "cliente": str(row["CLIENTE"]).strip(),
                    "rut": str(row.get("RUT", "")).strip(),
                    "tipo_documento": current_doc_type,
                    "valor_neto": float(val_neto),
                    "iva": float(val_iva),
                    "total_factura": float(val_total)
                })

        return processed_records

    # -----------------------------------------------------------------
    # CONSULTAS Y FILTROS CRUD
    # -----------------------------------------------------------------
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
        sheet_name: Optional[str] = None,
        min_neto: Optional[float] = None,
        max_neto: Optional[float] = None
    ) -> List[Sale]:
        query = db.query(Sale)
        if cliente:
            query = query.filter(Sale.cliente.ilike(f"%{cliente}%"))
        if sheet_name:
            query = query.filter(func.upper(Sale.sheet_name) == sheet_name.strip().upper())
        if min_neto is not None:
            query = query.filter(Sale.valor_neto >= min_neto)
        if max_neto is not None:
            query = query.filter(Sale.valor_neto <= max_neto)
        return query.all()

    # -----------------------------------------------------------------
    # MÉTODOS DE ANALÍTICA (IDIOMS 1, 2 Y 3)
    # -----------------------------------------------------------------
    @staticmethod
    def get_monthly_flow_metrics(
        db: Session, 
        min_neto: Optional[float] = None, 
        max_neto: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        sales = ExcelService.get_sales_with_filters(db, min_neto=min_neto, max_neto=max_neto)
        if not sales:
            return []

        meses = {}
        for s in sales:
            mes = s.sheet_name
            if mes not in meses:
                meses[mes] = {"ventas_brutas": 0.0, "notas_credito": 0.0}
            
            if s.tipo_documento == "NOTA_CREDITO":
                meses[mes]["notas_credito"] += s.valor_neto
            else:
                meses[mes]["ventas_brutas"] += s.valor_neto

        result = []
        for mes, data in meses.items():
            bruto = data["ventas_brutas"]
            nc = data["notas_credito"]
            result.append({
                "sheet_name": mes,
                "ventas_brutas": bruto,
                "notas_credito": nc,
                "recaudacion_real": bruto - nc
            })
        return result

    @staticmethod
    def get_client_risk_metrics(
        db: Session, 
        min_neto: Optional[float] = None, 
        max_neto: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        sales = ExcelService.get_sales_with_filters(db, min_neto=min_neto, max_neto=max_neto)
        if not sales:
            return []

        clientes = {}
        for s in sales:
            rut = s.rut if s.rut else "SIN_RUT"
            if rut not in clientes:
                clientes[rut] = {
                    "cliente": s.cliente,
                    "recurrencia": 0,
                    "ventas_brutas": 0.0,
                    "monto_nc": 0.0
                }
            
            if s.tipo_documento == "NOTA_CREDITO":
                clientes[rut]["monto_nc"] += s.valor_neto
            else:
                clientes[rut]["recurrencia"] += 1
                clientes[rut]["ventas_brutas"] += s.valor_neto

        result = []
        for rut, data in clientes.items():
            count = data["recurrencia"]
            ventas = data["ventas_brutas"]
            nc = data["monto_nc"]
            
            tasa_riesgo = (nc / ventas * 100.0) if ventas > 0 else (100.0 if nc > 0 else 0.0)
            ticket_promedio = (ventas / count) if count > 0 else 0.0

            result.append({
                "rut": rut,
                "cliente": data["cliente"],
                "recurrencia": count,
                "ticket_promedio": ticket_promedio,
                "ventas_totales": ventas,
                "tasa_riesgo": round(tasa_riesgo, 2)
            })
        return result

    @staticmethod
    def get_operational_density_metrics(
        db: Session, 
        min_neto: Optional[float] = None, 
        max_neto: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        sales = ExcelService.get_sales_with_filters(db, min_neto=min_neto, max_neto=max_neto)
        if not sales:
            return []

        meses = {}
        for s in sales:
            mes = s.sheet_name
            if mes not in meses:
                meses[mes] = {"cantidad": 0, "neto_recaudado": 0.0}
            
            if s.tipo_documento == "VENTA":
                meses[mes]["cantidad"] += 1
                meses[mes]["neto_recaudado"] += s.valor_neto
            else:
                meses[mes]["neto_recaudado"] -= s.valor_neto

        return [
            {
                "sheet_name": mes,
                "cantidad_facturas": data["cantidad"],
                "total_recaudado": data["neto_recaudado"]
            }
            for mes, data in meses.items()
        ]