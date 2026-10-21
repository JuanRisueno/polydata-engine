"""
Funciones auxiliares de formateo de datos.
Ubicación: frontend/utils/formatters.py
"""

def format_bytes(size_in_bytes: int) -> str:
    """Convierte un tamaño en bytes a una cadena legible (KB, MB, GB)."""
    if size_in_bytes == 0:
        return "0 Bytes"
    size = float(size_in_bytes)
    for unit in ['Bytes', 'KB', 'MB', 'GB']:
        if abs(size) < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"