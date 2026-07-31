"""
Servicio de Procesamiento e Ingesta de Archivos Excel.

Este módulo provee la lógica de lectura, parsing, normalización y extracción
de datos contables desde libros de Excel (.xlsx / .xls) utilizando Pandas.
Maneja dinámicamente la detección de encabezados, mapeo flexible de columnas,
identificación de Notas de Crédito y clasificación comercial por segmentos.
"""

import io
import pandas as pd
from typing import List, Dict, Any
from fastapi import HTTPException, status


class ExcelService:
    """
    Servicio encargado de procesar la estructura física y lógica de planillas Excel de ventas.
    """

    @staticmethod
    def _clean_float(val: Any) -> float:
        """
        Limpia y convierte un valor a tipo float de manera segura.

        Args:
            val (Any): Valor extraído de la celda de Pandas (puede ser string, NaN, int, etc.).

        Returns:
            float: Valor numérico parseado. Retorna 0.0 si el valor es nulo o no numérico.
        """
        num = pd.to_numeric(val, errors="coerce")
        if pd.isna(num):
            return 0.0
        return float(num)

    @staticmethod
    def process_sales_excel(file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Lee el contenido binario de un archivo Excel, filtra las pestañas correspondientes a meses
        válidos, detecta la fila del encabezado y extrae las transacciones normalizadas.

        Proceso de procesamiento:
        1. Carga del archivo Excel en memoria mediante `io.BytesIO`.
        2. Filtrado de hojas cuyo nombre contenga un mes del año (ej. "ENERO", "FEBRERO").
        3. Búsqueda dinámica de la fila de encabezado que contiene la columna "CLIENTE".
        4. Recorte de la matriz de datos y mapeo inteligente de nombres de columna flexibles a claves estándar.
        5. Iteración de filas identificando cambio de tipo de documento (VENTA vs. NOTA DE CRÉDITO).
        6. Limpieza de montos y cálculo del segmento comercial según el total facturado.

        Args:
            file_bytes (bytes): Contenido en bytes del archivo Excel cargado.

        Returns:
            List[Dict[str, Any]]: Lista de diccionarios con la estructura de cada venta procesada.

        Raises:
            HTTPException: Si el archivo está corrupto o no se puede abrir como libro Excel (Status 400).
        """
        processed_records: List[Dict[str, Any]] = []

        # Intentar cargar el archivo binario Excel
        try:
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error al abrir el archivo Excel: {str(e)}",
            )

        # Meses válidos para identificar pestañas contables relevantes
        meses_validos = [
            "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
            "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE",
        ]

        # Iterar sobre cada hoja del libro Excel
        for sheet_name in excel_file.sheet_names:
            sheet_name_upper = sheet_name.strip().upper()
            
            # Omitir pestañas que no correspondan a un mes válido
            if not any(mes in sheet_name_upper for mes in meses_validos):
                continue

            # Lectura sin encabezados iniciales para detectar la fila real de datos
            df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

            header_row_idx = None
            idx_cliente = None

            # Detección dinámica de la fila que contiene el encabezado de la tabla
            for idx, row in df_raw.iterrows():
                row_str = [str(cell).strip().upper() for cell in row]
                if any("CLIENTE" in s or "TOTAL" in s for s in row_str):
                    indices_posibles = [i for i, s in enumerate(row_str) if "CLIENTE" in s]
                    if indices_posibles:
                        header_row_idx = int(idx)
                        idx_cliente = indices_posibles[0]
                        break

            # Si no se encuentra una fila válida con la columna "CLIENTE", se omite la hoja
            if header_row_idx is None or idx_cliente is None:
                continue

            # Recorte del DataFrame desde la fila de encabezado encontrada
            df_sales = df_raw.iloc[header_row_idx:].copy()
            inicio_ventas_col = max(0, idx_cliente - 1)
            df_sales = df_sales.iloc[:, inicio_ventas_col:]

            # Asignación de la primera fila como nombres de columna y limpieza del DataFrame
            df_sales.columns = [str(c).strip().upper() for c in df_sales.iloc[0]]
            df_sales = df_sales.iloc[1:]

            # Mapeo flexible de columnas para tolerar variaciones en los nombres del Excel
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

            # Verificar que exista la columna obligatoria 'CLIENTE'
            if "CLIENTE" not in column_mapping.values():
                continue

            # Filtrar e renombrar el DataFrame con las columnas identificadas
            df_sales = df_sales[list(column_mapping.keys())].rename(columns=column_mapping)

            # Estado inicial para el tipo de documento en la hoja
            current_doc_type = "VENTA"

            # Iterar registro por registro procesando la información contable
            for _, row in df_sales.iterrows():
                cliente_str = str(row["CLIENTE"]).strip().upper()

                # Cambio de contexto a NOTA DE CRÉDITO si se detecta la fila divisoria
                if "NOTA DE CREDITO" in cliente_str or "NOTAS DE CREDITO" in cliente_str:
                    current_doc_type = "NOTA_CREDITO"
                    continue

                # Ignorar filas vacías o nulas
                if cliente_str in ["NAN", "NONE", "", "0", "0.0"]:
                    continue

                # Ignorar filas de sumatorias o totales acumulados
                if any(kw in cliente_str for kw in ["TOTAL", "SUB TOTAL", "SUBTOTAL", "SALDO", "ELECTRONICAS"]):
                    continue

                # Extraer y limpiar número de factura
                fact_str = str(row.get("FACT. N°", "0")).replace(".0", "").strip()
                fact_numeric = int(fact_str) if fact_str.isdigit() else 0

                # Extraer y limpiar valores financieros
                val_neto = ExcelService._clean_float(row.get("VALOR NETO"))
                val_iva = ExcelService._clean_float(row.get("IVA"))
                val_total = ExcelService._clean_float(row.get("TOTAL FACTURA"))

                # Autocalcular total si falta pero existe valor neto
                if val_total == 0.0 and val_neto > 0:
                    val_total = val_neto + val_iva

                # Lógica de negocio inferida para asignación de Segmento Comercial
                if val_total >= 15000000:
                    segmento = "Grandes Proyectos"
                elif val_total >= 5000000:
                    segmento = "Servicios Comerciales"
                else:
                    segmento = "Mantenciones Ocasionales"

                # Construcción del diccionario estructurado para la base de datos / DTO
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