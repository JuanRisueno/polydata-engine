"""
===============================================================================
PolyData Engine (PDE) - Módulo de Normalización y Parsing de Datasets
===============================================================================
Ubicación: src/pde/core/parser.py

Descripción:
    Motor de parsing polimórfico encargado de deserializar y estandarizar 
    buffers binarios o de texto en Pandas DataFrames limpios en memoria.

Funcionalidades Principales (Bloque 1 Ingesta & Parsing):
    - Parsing heterogéneo por formato: lectura de CSV, TSV, JSON/JSONL, 
      ARFF (Weka) y Parquet (PyArrow).
    - Autodetección de delimitadores (coma, punto y coma, tabulador) y soporte
      de opciones avanzadas de carga[cite: 5].
    - Security by Design & Sanitización: neutralización de prefijos de inyección 
      de fórmulas (CSV Injection) en cabeceras y celdas, y normalización de 
      nombres de columnas (caracteres especiales, minúsculas y duplicados).
    - Gestión estricta de recursos: control del consumo de memoria en RAM 
      (memory_usage) para evitar saturación de recursos.

Principios de Diseño:
    - Zero-Disk-I/O: procesamiento 100% en memoria mediante io.BytesIO e io.StringIO.
    - Transformación robusta con gestión de fallos en filas malformadas.
===============================================================================
"""
import io
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import arff
import pandas as pd

from src.pde.core.detector import DetectionResult


@dataclass
class ParsedDataset:
    """
    Estructura de datos que almacena el DataFrame parseado y los metadatos
    asociados a la sanitización y estructura del dataset.
    """
    dataframe: pd.DataFrame
    shape: tuple[int, int]
    columns: List[str]
    column_types: Dict[str, str]
    memory_usage_bytes: int
    sanitized_columns_count: int


class DatasetParser:
    """
    Motor de parsing polimórfico encargado de convertir buffers binarios/texto
    en un Pandas DataFrame estandarizado y sanitizado en memoria.
    """

    # Caracteres peligrosos al inicio de celdas/cabeceras que pueden desencadenar
    # ataques de Inyección de Fórmulas (CSV Injection) en hojas de cálculo.
    DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

    def __init__(self, max_allowed_memory_mb: int = 100):
        """
        :param max_allowed_memory_mb: Límite máximo en MB que puede ocupar
                                      el DataFrame resultante en RAM.
        """
        self.max_allowed_memory_bytes = max_allowed_memory_mb * 1024 * 1024

    def parse(self, content: bytes, detection: DetectionResult) -> ParsedDataset:
        """
        Punto de entrada principal para el parsing polimórfico en función
        del resultado de la detección.
        """
        dataset_type = detection.dataset_type.lower()

        if dataset_type in ["csv", "tsv"]:
            df = self._parse_csv_tsv(content, detection)
        elif dataset_type == "json":
            df = self._parse_json(content, detection)
        elif dataset_type == "arff":
            df = self._parse_arff(content, detection)
        elif dataset_type == "parquet":
            df = self._parse_parquet(content)
        else:
            raise ValueError(f"Tipo de dataset no soportado para parsing: '{dataset_type}'")

        # Sanitización de seguridad y normalización de estructura
        df, sanitized_count = self._sanitize_dataframe(df)

        # Control de consumo de recursos en memoria RAM
        mem_bytes = int(df.memory_usage(deep=True).sum())
        if mem_bytes > self.max_allowed_memory_bytes:
            raise ValueError(
                f"El dataset parseado ocupa {mem_bytes / (1024 * 1024):.2f} MB en RAM, "
                f"superando el límite de {self.max_allowed_memory_bytes / (1024 * 1024):.2f} MB."
            )

        # Inferencia de tipos de datos de las columnas
        column_types = {str(col): str(dtype) for col, dtype in df.dtypes.items()}

        return ParsedDataset(
            dataframe=df,
            shape=df.shape,
            columns=[str(col) for col in df.columns],
            column_types=column_types,
            memory_usage_bytes=mem_bytes,
            sanitized_columns_count=sanitized_count
        )

    def _parse_csv_tsv(self, content: bytes, detection: DetectionResult) -> pd.DataFrame:
        """Parseo de archivos tabulares delimitados por texto con autodetección de separador."""
        encoding = detection.encoding or "utf-8"
        text_stream = io.StringIO(content.decode(encoding, errors="replace"))

        # Si el tipo detectado es TSV forzamos tabulación; si es CSV, pasamos sep=None
        # para que Pandas autodetecte si el delimitador es coma, punto y coma, etc.
        sep = "\t" if detection.dataset_type.lower() == "tsv" else None

        return pd.read_csv(
            text_stream,
            sep=sep,
            engine="python",
            on_bad_lines="skip"  # Previene caídas por filas malformadas
        )

    def _parse_json(self, content: bytes, detection: DetectionResult) -> pd.DataFrame:
        """Parseo de archivos JSON estructurados o JSON Lines (JSONL)."""
        encoding = detection.encoding or "utf-8"
        text_data = content.decode(encoding, errors="replace")
        text_stream = io.StringIO(text_data)

        try:
            # Intento de lectura en formato estándar (orientado a objetos/registros)
            return pd.read_json(text_stream)
        except ValueError:
            # Reintento con formato JSON Lines (una entidad JSON por línea)
            text_stream.seek(0)
            return pd.read_json(text_stream, lines=True)

    def _parse_arff(self, content: bytes, detection: DetectionResult) -> pd.DataFrame:
        """Parseo de datasets en formato ARFF (Weka)."""
        encoding = detection.encoding or "utf-8"
        text_data = content.decode(encoding, errors="replace")

        parsed_arff = arff.loads(text_data)
        attributes = [attr[0] for attr in parsed_arff["attributes"]]
        data = parsed_arff["data"]

        return pd.DataFrame(data, columns=attributes)

    def _parse_parquet(self, content: bytes) -> pd.DataFrame:
        """Parseo binario de tablas en formato Apache Parquet mediante PyArrow."""
        binary_stream = io.BytesIO(content)
        return pd.read_parquet(binary_stream, engine="pyarrow")

    def _sanitize_dataframe(self, df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        """
        Aplica reglas sanitarias estrictas a los nombres de columna y valores de texto:
        1. Limpieza de nombres de columna (caracteres especiales, minúsculas, guiones bajos).
        2. Neutralización de prefijos peligrosos de inyección de fórmulas.
        """
        original_cols = list(df.columns)
        new_cols: List[str] = []
        sanitized_count = 0

        for i, raw_col in enumerate(original_cols):
            col_str = str(raw_col).strip() if raw_col is not None else f"col_{i}"

            # Desinfectar prefijos de inyección de fórmulas en la cabecera
            if col_str.startswith(self.DANGEROUS_PREFIXES):
                col_str = "'" + col_str
                sanitized_count += 1

            # Normalizar: minúsculas y reemplazar no-alfanuméricos por '_'
            col_sanitized = re.sub(r"[^\w]+", "_", col_str.lower()).strip("_")
            if not col_sanitized:
                col_sanitized = f"unnamed_col_{i}"

            new_cols.append(col_sanitized)

        # Garantizar que las columnas sean únicas agregando sufijos si hay duplicados
        unique_cols: List[str] = []
        seen: Dict[str, int] = {}
        for col in new_cols:
            if col in seen:
                seen[col] += 1
                unique_cols.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                unique_cols.append(col)

        df.columns = unique_cols

        # Desinfectar valores de texto en las celdas del DataFrame
        string_cols = df.select_dtypes(include=["object", "string"]).columns
        for s_col in string_cols:
            # Reemplazar valores que inicien con prefijos de fórmulas por comilla simple prepuesta
            mask = df[s_col].astype(str).str.startswith(self.DANGEROUS_PREFIXES)
            if mask.any():
                df.loc[mask, s_col] = "'" + df.loc[mask, s_col].astype(str)
                sanitized_count += int(mask.sum())

        return df, sanitized_count