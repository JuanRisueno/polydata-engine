import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.pde.core.detector import DetectionResult, FileDetector
from src.pde.core.explorer import DatasetExplorer, DatasetSummary
from src.pde.core.parser import DatasetParser

load_dotenv()

# ==============================================================================
# CONFIGURACIÓN Y CONSTANTES DE SEGURIDAD (alineadas con .env)
# ==============================================================================

_DEFAULT_MAX_BYTES = 100 * 1024 * 1024
MAX_UPLOAD_SIZE_BYTES: int = int(
    os.getenv("MAX_ALLOWED_BYTES", str(_DEFAULT_MAX_BYTES))
)
MAX_UPLOAD_SIZE_MB: int = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)

_DEFAULT_CORS = (
    "http://localhost:8501,http://127.0.0.1:8501,"
    "http://localhost:8000,http://127.0.0.1:8000"
)
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _DEFAULT_CORS).split(",")
    if origin.strip()
]

# Instancias globales de los motores del Bloque 1
detector = FileDetector(max_allowed_bytes=MAX_UPLOAD_SIZE_BYTES)
parser = DatasetParser(max_allowed_memory_mb=MAX_UPLOAD_SIZE_MB)
explorer = DatasetExplorer()


# ==============================================================================
# MIDDLEWARE DE SEGURIDAD CUSTOMIZADO (Security Headers)
# ==============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware que inyecta cabeceras de seguridad HTTP adaptadas
    para mitigar vulnerabilidades web y permitir la carga de Swagger UI.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com;"
        )
        
        return response


# ==============================================================================
# INICIALIZACIÓN DE LA APLICACIÓN FASTAPI
# ==============================================================================

app = FastAPI(
    title="PolyData Engine (PDE)",
    description=(
        "Motor polimórfico de alta seguridad para la ingesta, validación "
        "y procesamiento heterogéneo de datasets."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


# ==============================================================================
# ENDPOINTS DE CONTROL Y SALUD DEL SISTEMA
# ==============================================================================

@app.get(
    "/",
    summary="Información de estado del servicio",
    tags=["System"]
)
async def root():
    return {
        "status": "online",
        "service": "PolyData Engine (PDE)",
        "security_level": "enhanced",
        "version": "0.1.0"
    }


@app.get(
    "/health",
    summary="Health check para orquestadores y Docker",
    tags=["System"]
)
async def health_check():
    return {"status": "healthy"}


# ==============================================================================
# ENDPOINTS DEL MOTOR DE DETECCIÓN Y ANÁLISIS (EDA BLOQUE 1)
# ==============================================================================

@app.post(
    "/detect",
    response_model=DetectionResult,
    status_code=status.HTTP_200_OK,
    summary="Analizar y detectar las propiedades de un archivo",
    tags=["Detection Engine"],
    description=(
        "Recibe un archivo enviado mediante un formulario multipart/form-data, "
        "inspecciona sus firmas binarias en memoria, determina su tipo MIME real, "
        "su codificación de texto (encoding) y su estructura de dataset. "
        "Si es un ZIP, cataloga todos sus sub-archivos internos."
    )
)
async def detect_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        result = detector.analyze_bytes(
            content=content,
            filename=file.filename or "unknown"
        )
        return result

    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )

    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno durante la inspección del archivo: {str(err)}"
        )


@app.post(
    "/extract-and-detect",
    response_model=DetectionResult,
    status_code=status.HTTP_200_OK,
    summary="Extraer un archivo específico dentro de un ZIP y analizarlo",
    tags=["Detection Engine"],
    description=(
        "Recibe un contenedor ZIP y el nombre del sub-archivo objetivo. "
        "Extrae el archivo seleccionado en memoria (Zero-Disk-I/O) y ejecuta "
        "la inspección y clasificación binaria completa sobre él."
    )
)
async def extract_and_detect_file(
    file: UploadFile = File(...),
    target_filename: str = Form(...)
):
    try:
        content = await file.read()
        
        # 1. Extraer el sub-archivo específico del ZIP en RAM
        extracted_bytes = detector.extract_zip_entry(
            content=content,
            target_filename=target_filename
        )

        # 2. Analizar el buffer del sub-archivo extraído
        result = detector.analyze_bytes(
            content=extracted_bytes,
            filename=target_filename
        )
        return result

    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )

    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al extraer y analizar el archivo del ZIP: {str(err)}"
        )


@app.post(
    "/api/v1/datasets/analyze",
    response_model=DatasetSummary,
    status_code=status.HTTP_200_OK,
    summary="Ingesta, parsing y análisis exploratorio completo (Bloque 1 EDA)",
    tags=["EDA Engine"],
    description=(
        "Ejecuta la canalización completa del Bloque 1: detecta la firma del archivo, "
        "aplica sanitización de fórmulas, parsea el contenido en memoria y devuelve "
        "el diagnóstico estructural completo (dimensiones, dtypes, nulos, vistas previas y estadísticas)."
    )
)
async def analyze_dataset(file: UploadFile = File(...)):
    try:
        content = await file.read()
        filename = file.filename or "unknown_dataset"

        # 1. Detección binaria
        detection = detector.analyze_bytes(content=content, filename=filename)

        # 2. Parsing y sanitización
        parsed_dataset = parser.parse(content=content, detection=detection)

        # 3. Análisis exploratorio en memoria
        summary = explorer.analyze(parsed_dataset.dataframe, preview_rows=5)

        return summary

    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en la validación/parsing del dataset: {str(val_err)}"
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al procesar el dataset: {str(err)}"
        )