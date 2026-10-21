"""
===============================================================================
PolyData Engine (PDE) - Configuración del Frontend
===============================================================================
Ubicación: frontend/config.py
"""
import os
from dotenv import load_dotenv

# Carga las variables del archivo .env en la raíz
load_dotenv()


class Config:
    """Configuración alineada con las variables de entorno del proyecto."""

    PDE_API_URL: str = os.getenv("PDE_API_URL", "http://localhost:8000").rstrip("/")
    DETECT_ENDPOINT: str = f"{PDE_API_URL}/detect"
    EXTRACT_DETECT_ENDPOINT: str = f"{PDE_API_URL}/extract-and-detect"
    ANALYZE_ENDPOINT: str = f"{PDE_API_URL}/api/v1/datasets/analyze"

    # Debe coincidir con MAX_ALLOWED_BYTES del backend (mismo valor en MB)
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    # Alias por compatibilidad con código que use API_BASE_URL
    API_BASE_URL: str = PDE_API_URL
