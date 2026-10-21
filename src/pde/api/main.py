from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.pde.core.detector import DetectionResult, FileDetector
from src.pde.core.explorer import DatasetExplorer, DatasetSummary
from src.pde.core.parser import DatasetParser

# ==============================================================================
# CONFIGURACIÓN Y CONSTANTES DE SEGURIDAD
# ==============================================================================

# Límite global de tamaño para archivos subidos (50 MB)
MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024

# Instancias globales de los motores del Bloque 1
detector = FileDetector(max_allowed_bytes=MAX_UPLOAD_SIZE_BYTES)
parser = DatasetParser(max_allowed_memory_mb=100)
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
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
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
        "su codificación de texto (encoding) y su estructura de dataset."
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