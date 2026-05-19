import io
import pandas as pd
from typing import List, Dict, Any
from fastapi import HTTPException, status

class ExcelService:
    @staticmethod
    def process_sales_excel(file_bytes: bytes) -> List[Dict[str, Any]]:
        """Procesa un archivo Excel binario de compras/ventas, filtrando

        y limpiando dinámicamente las hojas mensuales.
        """
        processed_sheets = []

        try:
            # Cargamos el archivo directamente desde memoria (Bytes)
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error al abrir el archivo Excel: {str(e)}"
            )

        # Columnas objetivo que exige nuestro DTO
        target_columns = ["FACT. N°", "CLIENTE", "RUT", "VALOR NETO", "IVA", "TOTAL FACTURA"]

        for sheet_name in excel_file.sheet_names:
            # Filtro defensivo: Solo procesamos hojas mensuales
            sheet_name_upper = sheet_name.strip().upper()
            meses_validos = [
                "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
            ]
            
            if not any(mes in sheet_name_upper for mes in meses_validos):
                continue  # Salta automáticamente BALANCE ANUAL, SUELDOS, etc.

            # Leer la hoja cruda sin cabecera
            df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

            # 1. Localizar la fila de cabecera de forma dinámica
            header_row_idx = None
            for idx, row in df_raw.iterrows():
                row_str = [str(cell).strip().upper() for cell in row]
                if any("CLIENTE" in s for s in row_str) and any("VALOR NETO" in s for s in row_str):
                    header_row_idx = idx
                    break

            if header_row_idx is None:
                continue  

            # 2. Recortar el DataFrame desde la cabecera identificada
            df_sales = df_raw.iloc[header_row_idx:].copy()
            
            # Forzamos que los nombres de las columnas del DataFrame queden limpios en mayúsculas desde YA
            df_sales.columns = [str(c).strip().upper() for c in df_sales.iloc[0]]
            df_sales = df_sales.iloc[1:]  # Quitamos la fila que usamos como cabecera

            # =================================================================
            # 3. Mapear y renombrar columnas existentes (Búsqueda Flexible Sin Duplicados)
            # =================================================================
            column_mapping = {}
            # Llevamos un registro de qué DTOs ya asignamos para no repetirlos
            assigned_targets = set()

            for c in df_sales.columns:
                c_upper = str(c).strip().upper()
                target = None
                
                if ("FACT" in c_upper or "N°" in c_upper or "NUMERO" in c_upper or "FOLIO" in c_upper) and "FACT. N°" not in assigned_targets:
                    target = "FACT. N°"
                elif ("CLIENTE" in c_upper or "RAZON" in c_upper) and "CLIENTE" not in assigned_targets:
                    target = "CLIENTE"
                elif ("RUT" in c_upper or "RECEPTOR" in c_upper) and "RUT" not in assigned_targets:
                    target = "RUT"
                elif "NETO" in c_upper and "VALOR NETO" not in assigned_targets:
                    target = "VALOR NETO"
                elif "IVA" in c_upper and "IVA" not in assigned_targets:
                    target = "IVA"
                elif "TOTAL" in c_upper and "TOTAL FACTURA" not in assigned_targets:
                    target = "TOTAL FACTURA"

                if target:
                    column_mapping[c] = target
                    assigned_targets.add(target)

            # Verificación de seguridad crítica
            if "CLIENTE" not in column_mapping.values() or "RUT" not in column_mapping.values():
                continue  

            # Filtramos el DataFrame con las columnas únicas encontradas
            df_sales = df_sales[list(column_mapping.keys())]
            # Las renombramos al estándar exacto que pide el DTO
            df_sales = df_sales.rename(columns=column_mapping)

            # 4. Limpieza profunda de filas basura
            df_sales = df_sales.dropna(subset=["CLIENTE", "RUT"], how="all")
            
            for col in ["CLIENTE", "RUT"]:
                df_sales = df_sales[
                    df_sales[col].astype(str).str.strip().str.upper().notna() & 
                    (~df_sales[col].astype(str).str.strip().str.upper().isin(["NAN", "NONE", ""]))
                ]

            df_sales = df_sales[
                ~df_sales["CLIENTE"].astype(str).str.contains("TOTAL|SUB TOTAL|SUBTOTAL|SALDO", case=False, na=False)
            ]

            # 5. Formatear tipos de datos finales para cumplir con Pydantic
            if "FACT. N°" in df_sales.columns:
                fact_numeric = pd.to_numeric(df_sales["FACT. N°"], errors='coerce').fillna(0)
                df_sales["FACT. N°"] = fact_numeric.astype(int).astype(str)
                df_sales["FACT. N°"] = df_sales["FACT. N°"].replace("0", "")
            else:
                df_sales["FACT. N°"] = ""

            for col in ["CLIENTE", "RUT"]:
                if col in df_sales.columns:
                    df_sales[col] = df_sales[col].astype(str).str.strip()
                else:
                    df_sales[col] = ""

            for col in ["VALOR NETO", "IVA", "TOTAL FACTURA"]:
                if col in df_sales.columns:
                    df_sales[col] = pd.to_numeric(df_sales[col], errors='coerce').fillna(0.0)
                else:
                    df_sales[col] = 0.0

            # Convertir las filas a colecciones de diccionarios
            records = df_sales.to_dict(orient="records")

            processed_sheets.append({
                "sheet_name": sheet_name,
                "records_count": len(records),
                "data": records
            })

        return processed_sheets