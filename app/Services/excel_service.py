import io
import pandas as pd
from typing import List, Dict, Any
from fastapi import HTTPException, status

class ExcelService:
    @staticmethod
    def process_sales_excel(file_bytes: bytes) -> List[Dict[str, Any]]:
        """Procesa un archivo Excel de Libro de Compras/Ventas aislando

        la sección de ventas mediante coordenadas físicas de la planilla.
        """
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
                continue  # Ignora BALANCE ANUAL, SUELDOS, etc.

            # Leer la hoja cruda completa sin procesar cabeceras
            df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

            # -----------------------------------------------------------------
            # 1. LOCALIZAR LA CABECERA Y EL MURO DE VENTAS
            # -----------------------------------------------------------------
            header_row_idx = None
            idx_cliente = None
            
            for idx, row in df_raw.iterrows():
                row_str = [str(cell).strip().upper() for cell in row]
                if "CLIENTE" in row_str and "RUT" in row_str:
                    header_row_idx = idx
                    idx_cliente = row_str.index("CLIENTE")
                    break

            # Si no encuentra las palabras clave en la hoja, la salta de forma segura
            if header_row_idx is None or idx_cliente is None:
                continue  

            # -----------------------------------------------------------------
            # 2. AISLAR LA TABLA DE VENTAS (Corte por Coordenadas Físicas)
            # -----------------------------------------------------------------
            # Cortamos verticalmente desde la fila de la cabecera hacia abajo
            df_sales = df_raw.iloc[header_row_idx:].copy()
            
            # Cortamos horizontalmente: Nos quedamos SOLO desde la columna 'CLIENTE' hacia la izquierda y derecha de ventas
            # Retrocedemos una columna para capturar obligatoriamente el 'FACT. N°' que está justo antes de 'CLIENTE'
            inicio_ventas_col = max(0, idx_cliente - 1)
            df_sales = df_sales.iloc[:, inicio_ventas_col:]

            # Asignamos la primera fila recortada como los nuevos nombres de columnas
            df_sales.columns = [str(c).strip().upper() for c in df_sales.iloc[0]]
            df_sales = df_sales.iloc[1:]  # Eliminamos la fila de cabecera repetida

            # -----------------------------------------------------------------
            # 3. MAPEO INTELIGENTE UNITARIO
            # -----------------------------------------------------------------
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

            # Si por algún motivo el mapeo básico falla, protegemos la ejecución
            if "CLIENTE" not in column_mapping.values() or "RUT" not in column_mapping.values():
                continue

            # Filtramos y renombramos de inmediato
            df_sales = df_sales[list(column_mapping.keys())]
            df_sales = df_sales.rename(columns=column_mapping)

            # -----------------------------------------------------------------
            # 4. LIMPIEZA PROFUNDA DE FILAS BASURA (Subtotales / Celdas vacías)
            # -----------------------------------------------------------------
            df_sales = df_sales.dropna(subset=["CLIENTE", "RUT"], how="all")

            for col in ["CLIENTE", "RUT"]:
                df_sales = df_sales[
                    df_sales[col].astype(str).str.strip().str.upper().notna() & 
                    (~df_sales[col].astype(str).str.strip().str.upper().isin(["NAN", "NONE", "", "0", "0.0"]))
                ]

            # Quitamos filas que sumen subtotales o contengan cierres de mes
            df_sales = df_sales[
                ~df_sales["CLIENTE"].astype(str).str.contains("TOTAL|SUB TOTAL|SUBTOTAL|SALDO|ELECTRONICAS", case=False, na=False)
            ]

            # -----------------------------------------------------------------
            # 5. FORMATEO DE TIPOS DE DATOS FINALES PARA LA BASE DE DATOS
            # -----------------------------------------------------------------
            if "FACT. N°" in df_sales.columns:
                df_sales["FACT. N°"] = df_sales["FACT. N°"].astype(str).str.replace(".0", "", regex=False).str.strip()
            else:
                df_sales["FACT. N°"] = "0"

            for col in ["CLIENTE", "RUT"]:
                df_sales[col] = df_sales[col].astype(str).str.strip()

            for col in ["VALOR NETO", "IVA", "TOTAL FACTURA"]:
                if col in df_sales.columns:
                    df_sales[col] = pd.to_numeric(df_sales[col], errors='coerce').fillna(0.0)
                else:
                    df_sales[col] = 0.0

            # -----------------------------------------------------------------
            # 6. CONVERSIÓN A DICCIONARIOS PARA PERSISTENCIA MASIVA
            # -----------------------------------------------------------------
            for _, row in df_sales.iterrows():
                fact_str = str(row["FACT. N°"]).strip()
                fact_numeric = int(fact_str) if fact_str.isdigit() else 0

                processed_sheets.append({
                    "sheet_name": sheet_name,
                    "fact_number": fact_numeric,
                    "cliente": str(row["CLIENTE"]),
                    "rut": str(row["RUT"]),
                    "valor_neto": float(row["VALOR NETO"]),
                    "iva": float(row["IVA"]),
                    "total_factura": float(row["TOTAL FACTURA"])
                })

        return processed_sheets