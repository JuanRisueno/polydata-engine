# ==============================================================================
# FASE DE CONSTRUCCIÓN Y SEGURIDAD DEL CONTENEDOR
# ==============================================================================

# 1. Imagen base oficial mínima (Debian Slim) para reducir la superficie de ataque
FROM python:3.11-slim

# 2. Variables de entorno de optimización de Python
# - PYTHONDONTWRITEBYTECODE: Evita la creación de ficheros .pyc no necesarios
# - PYTHONUNBUFFERED: Fuerza a Python a enviar logs directamente a stdout/stderr sin buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Instalación de librerías del sistema necesarias
# - libmagic1: Requerido por python-magic para analizar las firmas de archivos en binario
# - Limpieza de caché apt para minimizar el tamaño final de la imagen y reducir vulnerabilidades
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# 4. PRÁCTICA DE SEGURIDAD CRÍTICA: Principio de Mínimo Privilegio (Non-root user)
# Creamos un grupo y un usuario de sistema dedicado ('pdeuser') sin privilegios de administración
RUN groupadd -r pdeuser && useradd -r -g pdeuser -s /bin/false pdeuser

# 5. Establecer directorio de trabajo aislado
WORKDIR /app

# 6. Copia e instalación de dependencias aisladas
# Copiamos primero solo requirements.txt para aprovechar el sistema de capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copia del código fuente del proyecto y ajuste estricto de permisos
COPY src/ /app/src/
RUN chown -R pdeuser:pdeuser /app

# 8. Cambiar al usuario sin privilegios ANTES de ejecutar cualquier proceso
USER pdeuser

# 9. Puerto expuesto por el contenedor
EXPOSE 8000

# 10. Comando de arranque de la aplicación FastAPI
CMD ["uvicorn", "src.pde.api.main:app", "--host", "0.0.0.0", "--port", "8000"]