"""
===============================================================================
PolyData Engine (PDE) - Cliente HTTP de la API
===============================================================================
Ubicación: frontend/services/api_client.py
"""
import requests
from typing import Tuple, Dict, Any, Optional
from frontend.config import Config


class PDEApiClient:
    """
    Cliente encarado a consumir los endpoints de inspección del backend FastAPI.
    """

    def __init__(self, endpoint_url: str = Config.DETECT_ENDPOINT):
        self.endpoint_url = endpoint_url

    def detect_file(self, file_bytes: bytes, filename: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Envia un buffer de bytes al endpoint /detect.
        """
        try:
            files = {'file': (filename, file_bytes)}
            response = requests.post(self.endpoint_url, files=files, timeout=60)

            if response.status_code == 200:
                return True, response.json(), ""

            detail = "Error en el servidor"
            try:
                detail = response.json().get("detail", detail)
            except Exception:
                pass

            return False, None, f"Error HTTP {response.status_code}: {detail}"

        except requests.exceptions.RequestException as err:
            return False, None, f"Error de conexión con la API: {str(err)}"