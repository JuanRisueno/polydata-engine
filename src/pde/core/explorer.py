"""
===============================================================================
PolyData Engine (PDE) - Módulo de Exploración y Análisis Estructural (EDA)
===============================================================================
Ubicación: src/pde/core/explorer.py

Descripción:
    Motor de inspección y diagnóstico estructural para DataFrames en memoria.
    Transforma la exploración inicial de datos en reportes estructurados y 
    serializables para la API de FastAPI.

Funcionalidades Principales (Bloque 1 EDA):
    - Inspección de metadatos y dimensiones: shape, columns, dtypes[cite: 5].
    - Muestreo y vistas previas: extracción de registros head() y tail()[cite: 5].
    - Diagnóstico de completitud: conteo (sum) y porcentaje (mean) de valores 
    nulos o faltantes por columna (isna)[cite: 6].
    - Resumen estadístico multivariable: describe() desglosado para columnas 
    numéricas y categóricas/texto[cite: 5].

Principios de Diseño:
    - Zero-Disk-I/O: operaciones 100% en memoria sobre DataFrames de Pandas.
    - Exportación limpia compatible con esquemas de Pydantic y respuestas JSON.
===============================================================================
"""
from dataclasses import dataclass
from typing import Any, Dict, List
import pandas as pd


@dataclass
class DatasetSummary:
    """Estructura con el reporte de exploración inicial del dataset."""
    shape: tuple[int, int]
    columns: List[str]
    dtypes: Dict[str, str]
    head_preview: List[Dict[str, Any]]
    tail_preview: List[Dict[str, Any]]
    missing_values_count: Dict[str, int]
    missing_values_pct: Dict[str, float]
    numeric_describe: Dict[str, Dict[str, float]]
    categorical_describe: Dict[str, Dict[str, Any]]


class DatasetExplorer:
    """
    Motor de inspección y análisis estructural para DataFrames en PDE.
    Implementa los métodos de consulta y resumen del Bloque 1.
    """

    def analyze(self, df: pd.DataFrame, preview_rows: int = 5) -> DatasetSummary:
        """Genera un diagnóstico completo del DataFrame."""
        total_rows = len(df)
        
        # 1. Atributos directos de estructura
        shape = df.shape
        columns = [str(c) for c in df.columns]
        dtypes = {str(col): str(dtype) for col, dtype in df.dtypes.items()}

        # 2. Vistas previas (head y tail)
        head_preview = df.head(preview_rows).to_dict(orient="records")
        tail_preview = df.tail(preview_rows).to_dict(orient="records")

        # 3. Métricas de valores nulos
        missing_count = df.isna().sum().to_dict()
        missing_pct = (
            (df.isna().mean() * 100).round(2).to_dict()
            if total_rows > 0 else {col: 0.0 for col in columns}
        )

        # 4. Resumen estadístico (numérico)
        numeric_df = df.select_dtypes(include=["number"])
        numeric_desc = (
            numeric_df.describe().to_dict() if not numeric_df.empty else {}
        )

        # 5. Resumen estadístico (texto / categórico)
        categorical_df = df.select_dtypes(include=["object", "category", "string"])
        categorical_desc = (
            categorical_df.describe().to_dict() if not categorical_df.empty else {}
        )

        return DatasetSummary(
            shape=shape,
            columns=columns,
            dtypes=dtypes,
            head_preview=head_preview,
            tail_preview=tail_preview,
            missing_values_count={str(k): int(v) for k, v in missing_count.items()},
            missing_values_pct={str(k): float(v) for k, v in missing_pct.items()},
            numeric_describe={
                str(col): {str(k): float(v) for k, v in metrics.items()}
                for col, metrics in numeric_desc.items()
            },
            categorical_describe={
                str(col): {str(k): v for k, v in metrics.items()}
                for col, metrics in categorical_desc.items()
            }
        )