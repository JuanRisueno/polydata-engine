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
    API_BASE_URL: str = os.getenv("PDE_API_URL", "http://localhost:8000")
    DETECT_ENDPOINT: str = f"{API_BASE_URL}/detect"
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024