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
    Cliente encargado de consumir los endpoints de inspección del backend FastAPI.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or Config.PDE_API_URL).rstrip("/")
        self.detect_url = Config.DETECT_ENDPOINT if not base_url else f"{self.base_url}/detect"
        self.extract_detect_url = (
            Config.EXTRACT_DETECT_ENDPOINT
            if not base_url
            else f"{self.base_url}/extract-and-detect"
        )

    def detect_file(self, file_bytes: bytes, filename: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Envia un buffer de bytes al endpoint /detect.
        """
        try:
            files = {'file': (filename, file_bytes)}
            response = requests.post(self.detect_url, files=files, timeout=60)

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

    def extract_and_detect_file(self, file_bytes: bytes, zip_filename: str, target_filename: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Envia el ZIP y el nombre del sub-archivo seleccionado al endpoint /extract-and-detect.
        """
        try:
            files = {'file': (zip_filename, file_bytes)}
            data = {'target_filename': target_filename}
            response = requests.post(self.extract_detect_url, files=files, data=data, timeout=60)

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