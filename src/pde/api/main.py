from fastapi import FastAPI, Request, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.pde.core.detector import FileDetector, DetectionResult

# ==============================================================================
# CONFIGURACIÓN Y CONSTANTES DE SEGURIDAD
# ==============================================================================

# Límite global de tamaño para archivos subidos (50 MB)
MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024

# Instancia global del detector polimórfico
detector = FileDetector(max_allowed_bytes=MAX_UPLOAD_SIZE_BYTES)


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
# ENDPOINT DE INSPECCIÓN Y DETECCIÓN POLIMÓRFICA
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