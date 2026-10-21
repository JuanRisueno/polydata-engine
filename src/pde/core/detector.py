import magic
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from charset_normalizer import from_bytes


# ==============================================================================
# ESQUEMAS DE SALIDA (Pydantic)
# ==============================================================================

class DetectionResult(BaseModel):
    """
    Modelo de salida estricto con la metadata analizada del archivo.
    """
    filename: str = Field(..., description="Nombre original del archivo cargado")
    mime_type: str = Field(..., description="Tipo MIME real detectado por firmas binarias")
    encoding: Optional[str] = Field(None, description="Codificación de texto detectada")
    dataset_type: str = Field(..., description="Tipo de dataset: csv, tsv, json, arff, parquet, zip, unknown")
    file_size_bytes: int = Field(..., description="Tamaño real del archivo en bytes")
    is_text: bool = Field(..., description="Indica si el contenido es interpretable como texto")


# ==============================================================================
# MOTOR DE DETECCIÓN POLIMÓRFICO
# ==============================================================================

class FileDetector:
    """
    Motor de inspección de archivos sin confiar en la extensión enviada por el usuario.
    """

    # Límite por defecto para prevenir DoS por agotamiento de RAM (100 MB)
    DEFAULT_MAX_BYTES: int = 100 * 1024 * 1024

    def __init__(self, max_allowed_bytes: int = DEFAULT_MAX_BYTES):
        self.max_allowed_bytes = max_allowed_bytes
        self._mime_detector = magic.Magic(mime=True)

    def analyze_bytes(self, content: bytes, filename: str = "unknown") -> DetectionResult:
        """
        Analiza un buffer de bytes en memoria aplicando controles de seguridad previos.
        """
        size_bytes = len(content)

        # 1. CONTROL DE SEGURIDAD: Rechazo de archivos vacíos
        if size_bytes == 0:
            raise ValueError("El archivo está vacío (0 bytes). Operación denegada.")

        # 2. CONTROL DE SEGURIDAD: Prevención de DoS por tamaño excesivo
        if size_bytes > self.max_allowed_bytes:
            raise ValueError(
                f"El archivo excede el tamaño máximo permitido de {self.max_allowed_bytes} bytes."
            )

        # Muestra inicial para análisis de firma binaria (8 KB)
        sample = content[:8192]

        # A. Identificación de tipo MIME real por magic bytes
        mime_type = self._mime_detector.from_buffer(sample) or "application/octet-stream"

        # B. Comprobación de naturaleza textual
        is_text = mime_type.startswith("text/") or mime_type in [
            "application/json",
            "application/xml",
            "text/csv"
        ]

        # C. Identificación de encoding
        encoding = None
        if is_text:
            matches = from_bytes(sample)
            best_match = matches.best()
            if best_match:
                encoding = best_match.encoding

        # D. Clasificación del dataset
        dataset_type = self._resolve_dataset_type(mime_type, sample, Path(filename).suffix.lower())

        return DetectionResult(
            filename=filename,
            mime_type=mime_type,
            encoding=encoding,
            dataset_type=dataset_type,
            file_size_bytes=size_bytes,
            is_text=is_text
        )

    def _resolve_dataset_type(self, mime_type: str, sample: bytes, suffix: str) -> str:
        """
        Determina la estructura interna del dataset.
        """
        if sample.startswith(b"PAR1") or "parquet" in mime_type:
            return "parquet"

        if mime_type in ["application/zip", "application/x-zip-compressed"] or sample.startswith(b"PK\x03\x04"):
            return "zip"

        if mime_type == "application/json" or suffix == ".json":
            stripped = sample.strip()
            if stripped.startswith(b"{") or stripped.startswith(b"["):
                return "json"

        if suffix == ".arff" or b"@relation" in sample.lower() or b"@attribute" in sample.lower():
            return "arff"

        if mime_type in ["text/csv", "application/csv"] or suffix in [".csv", ".tsv"]:
            if b"\t" in sample and b"," not in sample:
                return "tsv"
            return "csv"

        if mime_type.startswith("text/"):
            return "csv"

        return "unknown"