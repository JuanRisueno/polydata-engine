"""
===============================================================================
PolyData Engine (PDE) - Pruebas Unitarias para DatasetExplorer
===============================================================================
Ubicación: tests/test_explorer.py
"""
import pandas as pd
import numpy as np
from src.pde.core.explorer import DatasetExplorer, DatasetSummary


def test_explorer_summary_analysis():
    # DataFrame de prueba con datos numéricos, categóricos y nulos
    data = {
        "edad": [25, 30, np.nan, 45, 50],
        "salario": [1500.0, 2200.0, 3100.0, np.nan, 4000.0],
        "categoria": ["A", "B", "A", "B", "A"]
    }
    df = pd.DataFrame(data)

    explorer = DatasetExplorer()
    summary = explorer.analyze(df, preview_rows=2)

    assert isinstance(summary, DatasetSummary)
    assert summary.shape == (5, 3)
    assert summary.columns == ["edad", "salario", "categoria"]
    
    # Verificación de metadatos e inspección
    assert len(summary.head_preview) == 2
    assert len(summary.tail_preview) == 2

    # Verificación de análisis de valores faltantes (isna)
    assert summary.missing_values_count["edad"] == 1
    assert summary.missing_values_count["salario"] == 1
    assert summary.missing_values_count["categoria"] == 0
    assert summary.missing_values_pct["edad"] == 20.0

    # Verificación de resúmenes estadísticos (describe)
    assert "edad" in summary.numeric_describe
    assert "salario" in summary.numeric_describe
    assert "categoria" in summary.categorical_describe
    assert summary.categorical_describe["categoria"]["unique"] == 2