"""
===============================================================================
PolyData Engine (PDE) - Pruebas de Integración End-to-End (Bloque 1)
===============================================================================
Ubicación: tests/test_integration_block1.py

Descripción:
    Suite de pruebas de integración para validar la cadena de procesamiento
    completa del Bloque 1 de PDE:
    FileDetector -> DatasetParser -> DatasetExplorer

Funcionalidades Evaluadas:
    - Identificación automática de MIME type, encoding y delimitadores de texto (;, ,).
    - Deserialización, desinfección de inyección de fórmulas y control de RAM.
    - Extracción de métricas estructurales, resumen estadístico y diagnóstico de nulos.
===============================================================================
"""
import pytest
from src.pde.core.detector import FileDetector
from src.pde.core.parser import DatasetParser
from src.pde.core.explorer import DatasetExplorer, DatasetSummary


def test_block1_pipeline_e2e_csv_spanish_format():
    """
    Valida el flujo completo con un dataset CSV en formato europeo/español
    (delimitador por punto y coma ';', prefijos de fórmulas e inyección de nulos).
    """
    # 1. Buffer de datos simulado de entrada
    raw_csv_content = (
        b"ID_Cliente;=Importe_EUR;Categoria;Puntuacion\n"
        b"101;150.50;Electrica;4.5\n"
        b"102;@999.99;Hogar;3.8\n"
        b"103;200.00;Electrica;\n"
        b"104;+50.00;;5.0\n"
    )
    filename = "ventas_raw.csv"

    # 2. Etapa 1: Detección binaria y MIME
    detector = FileDetector()
    detection_result = detector.analyze_bytes(raw_csv_content, filename=filename)

    assert detection_result.dataset_type == "csv"
    assert detection_result.is_text is True
    assert detection_result.file_size_bytes == len(raw_csv_content)

    # 3. Etapa 2: Parsing, autodetección de separador y sanitización
    parser = DatasetParser(max_allowed_memory_mb=10)
    parsed_dataset = parser.parse(raw_csv_content, detection_result)

    assert parsed_dataset.shape == (4, 4)
    assert parsed_dataset.sanitized_columns_count > 0
    
    df = parsed_dataset.dataframe
    assert "id_cliente" in df.columns
    assert "categoria" in df.columns

    # 4. Etapa 3: Análisis Exploratorio de Datos (EDA Bloque 1)
    explorer = DatasetExplorer()
    summary = explorer.analyze(df, preview_rows=2)

    assert isinstance(summary, DatasetSummary)
    assert summary.shape == (4, 4)
    assert summary.columns == ["id_cliente", "importe_eur", "categoria", "puntuacion"]
    
    # Comprobar métricas de completitud y nulos
    assert summary.missing_values_count["puntuacion"] == 1
    assert summary.missing_values_pct["puntuacion"] == 25.0
    assert summary.missing_values_count["categoria"] == 1
    
    # Comprobar muestras e inspección estadística
    assert len(summary.head_preview) == 2
    assert len(summary.tail_preview) == 2
    assert "puntuacion" in summary.numeric_describe


def test_block1_pipeline_e2e_json_format():
    """
    Valida el flujo completo con una estructura JSON orientada a registros.
    """
    raw_json_content = (
        b'[\n'
        b'  {"id": 1, "nombre": "Juan", "rol": "Admin"},\n'
        b'  {"id": 2, "nombre": "Tina", "rol": "User"}\n'
        b']'
    )
    filename = "usuarios.json"

    # Detección
    detector = FileDetector()
    detection_result = detector.analyze_bytes(raw_json_content, filename=filename)
    assert detection_result.dataset_type == "json"

    # Parsing
    parser = DatasetParser()
    parsed_dataset = parser.parse(raw_json_content, detection_result)
    assert parsed_dataset.shape == (2, 3)

    # Exploración
    explorer = DatasetExplorer()
    summary = explorer.analyze(parsed_dataset.dataframe)
    assert summary.shape == (2, 3)
    assert "nombre" in summary.columns