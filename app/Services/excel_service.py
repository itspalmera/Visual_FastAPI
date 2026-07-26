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
        processed_sheets = []

        try:
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error al abrir el archivo Excel: {str(e)}"
            )

        for sheet_name in excel_file.sheet_names:
            sheet_name_upper = sheet_name.strip().upper()
            meses_validos = [
                "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
            ]
            
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

            df_sales = df_sales.dropna(subset=["CLIENTE"], how="all")
            
            if "RUT" in df_sales.columns:
                df_sales = df_sales[df_sales["RUT"].astype(str).str.strip().str.upper().notna()]
                
            df_sales = df_sales[
                df_sales["CLIENTE"].astype(str).str.strip().str.upper().notna() & 
                (~df_sales["CLIENTE"].astype(str).str.strip().str.upper().isin(["NAN", "NONE", "", "0", "0.0"]))
            ]

            df_sales = df_sales[
                ~df_sales["CLIENTE"].astype(str).str.contains("TOTAL|SUB TOTAL|SUBTOTAL|SALDO|ELECTRONICAS", case=False, na=False)
            ]

            if "FACT. N°" in df_sales.columns:
                df_sales["FACT. N°"] = df_sales["FACT. N°"].astype(str).str.replace(".0", "", regex=False).str.strip()
            else:
                df_sales["FACT. N°"] = "0"

            if "RUT" not in df_sales.columns:
                df_sales["RUT"] = ""

            for col in ["VALOR NETO", "IVA", "TOTAL FACTURA"]:
                if col in df_sales.columns:
                    df_sales[col] = pd.to_numeric(df_sales[col], errors='coerce').fillna(0.0)
                else:
                    df_sales[col] = 0.0

            for _, row in df_sales.iterrows():
                fact_str = str(row["FACT. N°"]).strip()
                fact_numeric = int(fact_str) if fact_str.isdigit() else 0

                processed_sheets.append({
                    "sheet_name": sheet_name,
                    "fact_number": fact_numeric,
                    "cliente": str(row["CLIENTE"]).strip(),
                    "rut": str(row["RUT"]).strip(),
                    "valor_neto": float(row["VALOR NETO"]),
                    "iva": float(row["IVA"]),
                    "total_factura": float(row["TOTAL FACTURA"])
                })

        return processed_sheets

    # -----------------------------------------------------------------
    # CONSULTAS BÁSICAS CRUD
    # -----------------------------------------------------------------
    @staticmethod
    def get_all_sales(db: Session) -> List[Sale]:
        return db.query(Sale).all()

    @staticmethod
    def get_sale_by_id(db: Session, sale_id: int) -> Optional[Sale]:
        return db.query(Sale).filter(Sale.id == sale_id).first()

    @staticmethod
    def get_sales_with_filters(db: Session, cliente: Optional[str] = None, sheet_name: Optional[str] = None) -> List[Sale]:
        query = db.query(Sale)
        if cliente:
            query = query.filter(Sale.cliente.ilike(f"%{cliente}%"))
        if sheet_name:
            query = query.filter(func.upper(Sale.sheet_name) == sheet_name.strip().upper())
        return query.all()

    # -----------------------------------------------------------------
    # MÉTODOS DE ANALÍTICA PARA EL DASHBOARD (METRICS & CLIENTS)
    # -----------------------------------------------------------------
    @staticmethod
    def get_monthly_flow_metrics(db: Session) -> List[Dict[str, Any]]:
        """Calcula el Flujo de Caja por Mes (Idiom 1)."""
        sales = db.query(Sale).all()
        if not sales:
            return []

        meses = {}
        for s in sales:
            mes = s.sheet_name
            if mes not in meses:
                meses[mes] = {"ventas_brutas": 0.0, "notas_credito": 0.0}
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
    def get_client_risk_metrics(db: Session) -> List[Dict[str, Any]]:
        """Calcula el Perfil de Riesgo por Cliente (Idiom 2)."""
        sales = db.query(Sale).all()
        if not sales:
            return []

        clientes = {}
        for s in sales:
            rut = s.rut
            if rut not in clientes:
                clientes[rut] = {
                    "cliente": s.cliente,
                    "facturas": 0,
                    "ventas_totales": 0.0
                }
            clientes[rut]["facturas"] += 1
            clientes[rut]["ventas_totales"] += s.valor_neto

        result = []
        for rut, data in clientes.items():
            count = data["facturas"]
            tot = data["ventas_totales"]
            result.append({
                "rut": rut,
                "cliente": data["cliente"],
                "recurrencia": count,
                "ticket_promedio": tot / count if count > 0 else 0.0,
                "ventas_totales": tot,
                "tasa_riesgo": 0.0
            })
        return result

    @staticmethod
    def get_operational_density_metrics(db: Session) -> List[Dict[str, Any]]:
        """Calcula la Densidad Operativa (Idiom 3)."""
        sales = db.query(Sale).all()
        if not sales:
            return []

        meses = {}
        for s in sales:
            mes = s.sheet_name
            if mes not in meses:
                meses[mes] = {"cantidad": 0, "total": 0.0}
            meses[mes]["cantidad"] += 1
            meses[mes]["total"] += s.valor_neto

        return [
            {
                "sheet_name": mes,
                "cantidad_facturas": data["cantidad"],
                "total_recaudado": data["total"]
            }
            for mes, data in meses.items()
        ]