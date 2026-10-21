"""
===============================================================================
PolyData Engine (PDE) - Módulo de Detección Polimórfica e Inspección Binaria
===============================================================================
Ubicación: src/pde/core/detector.py

Descripción:
    Motor de inspección y validación polimórfica para la identificación 
    precisa de tipos de archivos, MIME types reales y codificaciones en memoria.

Funcionalidades Principales:
    - Inspección de firmas binarias (magic numbers) mediante libmagic para
    prevenir la suplantación de extensiones falsas (extension spoofing).
    - Detección automática de codificación de caracteres (encoding) mediante
    charset-normalizer.
    - Clasificación polimórfica de formatos heterogéneos de datasets (CSV,
    TSV, JSON, ARFF, Parquet).
    - Inspección y catálogo en memoria de contenedores ZIP (Zero-Disk-I/O).
    - Normalización dinámica del tipo MIME según el contenido real analizado.
    - Validación de límites de tamaño de archivo y prevención de ataques DoS 
    (Security by Design).

Principios de Diseño:
    - Zero-Disk-I/O: análisis 100% en memoria sobre buffers binarios.
    - Salida estructurada y serializable compatible con esquemas de Pydantic.
===============================================================================
"""
import io
import magic
import zipfile
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field
from charset_normalizer import from_bytes


# ==============================================================================
# ESQUEMAS DE SALIDA (Pydantic)
# ==============================================================================

class ContainedFile(BaseModel):
    """
    Información detallada de un archivo contenido dentro de un archivo comprimido.
    """
    filename: str = Field(..., description="Ruta relativa/nombre del archivo dentro del contenedor")
    file_size_bytes: int = Field(..., description="Tamaño descomprimido en bytes")
    extension: str = Field(..., description="Extensión del archivo (ej. .csv, .txt)")
    is_dataset_candidate: bool = Field(..., description="Indica si es un candidato potencial a dataset")
    suggested_type: str = Field(..., description="Tipo de dataset sugerido (csv, json, parquet, etc.)")


class DetectionResult(BaseModel):
    """
    Modelo de salida estricto con la metadata analizada del archivo.
    """
    filename: str = Field(..., description="Nombre original del archivo cargado")
    mime_type: str = Field(..., description="Tipo MIME real detectado y normalizado según el contenido")
    encoding: Optional[str] = Field(None, description="Codificación de texto detectada")
    dataset_type: str = Field(..., description="Tipo de dataset: csv, tsv, json, arff, parquet, zip, unknown")
    file_size_bytes: int = Field(..., description="Tamaño real del archivo en bytes")
    is_text: bool = Field(..., description="Indica si el contenido es interpretable como texto")
    
    # Atributos extendidos para contenedores (ZIP)
    is_container: bool = Field(False, description="Indica si el archivo es un contenedor con sub-archivos")
    contained_files: Optional[List[ContainedFile]] = Field(None, description="Lista de archivos contenidos si es ZIP")
    recommended_file: Optional[str] = Field(None, description="Nombre del archivo candidato recomendado")


# ==============================================================================
# MOTOR DE DETECCIÓN POLIMÓRFICO
# ==============================================================================

class FileDetector:
    """
    Motor de inspección de archivos sin confiar en la extensión enviada por el usuario.
    """

    # Límite por defecto para prevenir DoS por agotamiento de RAM (100 MB)
    DEFAULT_MAX_BYTES: int = 100 * 1024 * 1024

    # Extensiones consideradas candidatos naturales a datasets
    DATASET_EXTENSIONS = {'.csv', '.tsv', '.json', '.arff', '.parquet', '.xlsx'}

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

        # A. Identificación preliminar de tipo MIME por magic bytes
        raw_mime_type = self._mime_detector.from_buffer(sample) or "application/octet-stream"

        # B. Clasificación estructural del dataset
        dataset_type = self._resolve_dataset_type(raw_mime_type, sample, Path(filename).suffix.lower())

        # C. Normalización del tipo MIME según el dataset verificado
        MIME_MAP = {
            "json": "application/json",
            "csv": "text/csv",
            "tsv": "text/tab-separated-values",
            "parquet": "application/x-parquet",
            "arff": "text/x-arff",
            "zip": "application/zip",
        }

        mime_type = MIME_MAP.get(dataset_type, raw_mime_type)

        # D. Comprobación de naturaleza textual
        is_text = mime_type.startswith("text/") or mime_type in [
            "application/json",
            "application/xml",
            "text/csv"
        ] or dataset_type in ["json", "csv", "tsv", "arff"]

        # E. Identificación de encoding
        encoding = None
        if is_text:
            matches = from_bytes(sample)
            best_match = matches.best()
            if best_match:
                encoding = best_match.encoding

        # F. Inspección especializada de contenidos si es un archivo ZIP
        is_container = False
        contained_files = None
        recommended_file = None

        if dataset_type == "zip":
            is_container = True
            contained_files = self.inspect_zip_contents(content)
            
            # Seleccionar el primer candidato recomendado
            for cf in contained_files:
                if cf.is_dataset_candidate:
                    recommended_file = cf.filename
                    break

        return DetectionResult(
            filename=filename,
            mime_type=mime_type,
            encoding=encoding,
            dataset_type=dataset_type,
            file_size_bytes=size_bytes,
            is_text=is_text,
            is_container=is_container,
            contained_files=contained_files,
            recommended_file=recommended_file
        )

    def inspect_zip_contents(self, content: bytes) -> List[ContainedFile]:
        """
        Inspecciona los metadatos internos de un archivo ZIP en memoria (Zero-Disk-I/O).
        """
        contained_files: List[ContainedFile] = []

        try:
            with zipfile.ZipFile(io.BytesIO(content), 'r') as z:
                for file_info in z.infolist():
                    # Ignorar directorios implícitos y archivos ocultos/sistema (macOS, Linux)
                    if file_info.is_dir() or file_info.filename.startswith("__MACOSX/") or Path(file_info.filename).name.startswith("._"):
                        continue

                    fname = file_info.filename
                    fsize = file_info.file_size
                    ext = Path(fname).suffix.lower()

                    is_candidate = ext in self.DATASET_EXTENSIONS
                    suggested_type = ext.replace('.', '') if is_candidate else "desconocido"

                    contained_files.append(
                        ContainedFile(
                            filename=fname,
                            file_size_bytes=fsize,
                            extension=ext,
                            is_dataset_candidate=is_candidate,
                            suggested_type=suggested_type
                        )
                    )
        except zipfile.BadZipFile:
            raise ValueError("El archivo comprimido ZIP está dañado o no es válido.")

        # Ordenar: primero los mejores candidatos a dataset
        contained_files.sort(key=lambda x: x.is_dataset_candidate, reverse=True)
        return contained_files

    def extract_zip_entry(self, content: bytes, target_filename: str) -> bytes:
        """
        Extrae en RAM un archivo específico dentro de un ZIP.
        """
        try:
            with zipfile.ZipFile(io.BytesIO(content), 'r') as z:
                if target_filename not in z.namelist():
                    raise ValueError(f"El archivo '{target_filename}' no existe dentro del contenedor ZIP.")
                return z.read(target_filename)
        except zipfile.BadZipFile:
            raise ValueError("El archivo comprimido ZIP está dañado o no es válido.")

    def _resolve_dataset_type(self, mime_type: str, sample: bytes, suffix: str) -> str:
        """
        Determina la estructura interna del dataset analizando el buffer de muestra.
        """
        stripped = sample.strip()

        # 1. Formato Parquet (firma binaria PAR1)
        if sample.startswith(b"PAR1") or "parquet" in mime_type:
            return "parquet"

        # 2. Formato ZIP (firma binaria PK\x03\x04)
        if mime_type in ["application/zip", "application/x-zip-compressed"] or sample.startswith(b"PK\x03\x04"):
            return "zip"

        # 3. Formato JSON: Detección estructural agnóstica a la extensión o MIME inicial
        if stripped.startswith(b"{") or stripped.startswith(b"[") or mime_type == "application/json" or suffix == ".json":
            return "json"

        # 4. Formato ARFF
        if suffix == ".arff" or b"@relation" in sample.lower() or b"@attribute" in sample.lower():
            return "arff"

        # 5. Formatos de texto estructurado por delimitadores (CSV / TSV)
        if mime_type in ["text/csv", "application/csv"] or suffix in [".csv", ".tsv"]:
            if b"\t" in sample and b"," not in sample:
                return "tsv"
            return "csv"

        if mime_type.startswith("text/"):
            if b"\t" in sample and b"," not in sample:
                return "tsv"
            return "csv"

        return "unknown"