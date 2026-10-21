"""
===============================================================================
PolyData Engine (PDE) - Pruebas Unitarias para DatasetParser
===============================================================================
Ubicación: tests/test_parser.py
"""
import pytest
import pandas as pd
from src.pde.core.detector import DetectionResult
from src.pde.core.parser import DatasetParser, ParsedDataset


def test_parse_csv_basic():
    csv_bytes = b"nombre,edad,salario\nJuan,30,2500.50\nTina,28,2800.00"
    detection = DetectionResult(
        filename="test.csv",
        mime_type="text/csv",
        encoding="utf-8",
        dataset_type="csv",
        file_size_bytes=len(csv_bytes),
        is_text=True
    )
    
    parser = DatasetParser(max_allowed_memory_mb=10)
    result = parser.parse(csv_bytes, detection)

    assert isinstance(result, ParsedDataset)
    assert result.shape == (2, 3)
    assert "nombre" in result.columns
    assert "edad" in result.columns
    assert result.sanitized_columns_count == 0


def test_parse_tsv_basic():
    tsv_bytes = b"producto\tprecio\tstock\nLaptop\t1200\t5\nMouse\t25\t50"
    detection = DetectionResult(
        filename="datos.tsv",
        mime_type="text/plain",
        encoding="utf-8",
        dataset_type="tsv",
        file_size_bytes=len(tsv_bytes),
        is_text=True
    )

    parser = DatasetParser()
    result = parser.parse(tsv_bytes, detection)

    assert result.shape == (2, 3)
    assert "producto" in result.columns
    assert "precio" in result.columns


def test_parse_json_basic():
    json_bytes = b'[{"id": 1, "usuario": "Juan"}, {"id": 2, "usuario": "Tina"}]'
    detection = DetectionResult(
        filename="users.json",
        mime_type="application/json",
        encoding="utf-8",
        dataset_type="json",
        file_size_bytes=len(json_bytes),
        is_text=True
    )

    parser = DatasetParser()
    result = parser.parse(json_bytes, detection)

    assert result.shape == (2, 2)
    assert "usuario" in result.columns


def test_parse_arff_basic():
    arff_bytes = (
        b"@relation test_db\n"
        b"@attribute edad numeric\n"
        b"@attribute clase {A,B}\n"
        b"@data\n"
        b"25,A\n"
        b"40,B\n"
    )
    detection = DetectionResult(
        filename="data.arff",
        mime_type="text/plain",
        encoding="utf-8",
        dataset_type="arff",
        file_size_bytes=len(arff_bytes),
        is_text=True
    )

    parser = DatasetParser()
    result = parser.parse(arff_bytes, detection)

    assert result.shape == (2, 2)
    assert "edad" in result.columns
    assert "clase" in result.columns


def test_formula_injection_sanitization():
    # Inyección de fórmula en columna (=cmd) y en celda (@SUM)
    csv_bytes = b"=formula_col,valor\n@cmd|' /C calc'!A0,100\n+34600112233,200"
    detection = DetectionResult(
        filename="malicious.csv",
        mime_type="text/csv",
        encoding="utf-8",
        dataset_type="csv",
        file_size_bytes=len(csv_bytes),
        is_text=True
    )

    parser = DatasetParser()
    result = parser.parse(csv_bytes, detection)

    # Las fórmulas deben neutralizarse anteponiendo comilla simple "'"
    assert result.sanitized_columns_count > 0
    df = result.dataframe
    assert df.iloc[0, 0].startswith("'")
    assert df.iloc[1, 0].startswith("'")


def test_memory_limit_exceeded():
    csv_bytes = b"col1,col2\n" + b"a,1\n" * 50000
    detection = DetectionResult(
        filename="big.csv",
        mime_type="text/csv",
        encoding="utf-8",
        dataset_type="csv",
        file_size_bytes=len(csv_bytes),
        is_text=True
    )

    # Configurar límite intencionadamente bajo para forzar excepción de RAM
    parser = DatasetParser(max_allowed_memory_mb=0)

    with pytest.raises(ValueError, match="superando el límite"):
        parser.parse(csv_bytes, detection)