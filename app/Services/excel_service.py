import io
import pandas as pd
from typing import List, Dict, Any
from fastapi import HTTPException, status


class ExcelService:
    @staticmethod
    def _clean_float(val: Any) -> float:
        num = pd.to_numeric(val, errors="coerce")
        if pd.isna(num):
            return 0.0
        return float(num)

    @staticmethod
    def process_sales_excel(file_bytes: bytes) -> List[Dict[str, Any]]:
        processed_records: List[Dict[str, Any]] = []

        try:
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error al abrir el archivo Excel: {str(e)}",
            )

        meses_validos = [
            "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
            "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE",
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
                if any("CLIENTE" in s or "TOTAL" in s for s in row_str):
                    indices_posibles = [i for i, s in enumerate(row_str) if "CLIENTE" in s]
                    if indices_posibles:
                        header_row_idx = int(idx)
                        idx_cliente = indices_posibles[0]
                        break

            if header_row_idx is None or idx_cliente is None:
                continue

            df_sales = df_raw.iloc[header_row_idx:].copy()
            inicio_ventas_col = max(0, idx_cliente - 1)
            df_sales = df_sales.iloc[:, inicio_ventas_col:]

            df_sales.columns = [str(c).strip().upper() for c in df_sales.iloc[0]]
            df_sales = df_sales.iloc[1:]

            column_mapping: Dict[str, str] = {}
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

                val_neto = ExcelService._clean_float(row.get("VALOR NETO"))
                val_iva = ExcelService._clean_float(row.get("IVA"))
                val_total = ExcelService._clean_float(row.get("TOTAL FACTURA"))

                if val_total == 0.0 and val_neto > 0:
                    val_total = val_neto + val_iva

                # Lógica de negocio inferida para Segmentos
                if val_total >= 15000000:
                    segmento = "Grandes Proyectos"
                elif val_total >= 5000000:
                    segmento = "Servicios Comerciales"
                else:
                    segmento = "Mantenciones Ocasionales"

                processed_records.append({
                    "sheet_name": sheet_name,
                    "fact_number": fact_numeric,
                    "cliente": str(row["CLIENTE"]).strip(),
                    "rut": str(row.get("RUT", "")).strip() if not pd.isna(row.get("RUT")) else "",
                    "tipo_documento": current_doc_type,
                    "valor_neto": val_neto,
                    "iva": val_iva,
                    "total_factura": val_total,
                    "segmento": segmento,
                })

        return processed_records