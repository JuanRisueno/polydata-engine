import pytest
from src.pde.core.detector import FileDetector


@pytest.fixture
def detector():
    """Fixture que proporciona una instancia del detector con límite de 1 MB."""
    return FileDetector(max_allowed_bytes=1024 * 1024)


def test_detect_csv_bytes(detector):
    """Verifica que el detector identifique correctamente un buffer CSV en UTF-8."""
    csv_data = b"id,nombre,valor\n1,Alpha,10.5\n2,Beta,20.0"
    
    result = detector.analyze_bytes(csv_data, filename="datos.csv")

    assert result.is_text is True
    assert result.dataset_type == "csv"
    assert result.encoding.lower() in ["utf-8", "ascii"]
    assert result.file_size_bytes == len(csv_data)


def test_detect_json_bytes(detector):
    """Verifica la detección de un archivo con estructura JSON."""
    json_data = b'{"status": "ok", "items": [1, 2, 3]}'
    
    result = detector.analyze_bytes(json_data, filename="config.json")

    assert result.is_text is True
    assert result.dataset_type == "json"


def test_detect_empty_file_raises_error(detector):
    """Verifica que el control de seguridad rechace archivos vacíos (0 bytes)."""
    empty_data = b""

    with pytest.raises(ValueError, match="El archivo está vacío"):
        detector.analyze_bytes(empty_data, filename="vacio.txt")


def test_detect_file_exceeds_size_limit():
    """Verifica la prevención de DoS bloqueando archivos que superen el tamaño máximo."""
    # Instanciamos con un límite muy pequeño (10 bytes) para la prueba
    strict_detector = FileDetector(max_allowed_bytes=10)
    large_data = b"Este buffer supera los 10 bytes permitidos."

    with pytest.raises(ValueError, match="excede el tamaño máximo permitido"):
        strict_detector.analyze_bytes(large_data, filename="pesado.txt")