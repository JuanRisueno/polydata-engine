# ==============================================================================
# FASE DE CONSTRUCCIÓN Y SEGURIDAD DEL CONTENEDOR
# ==============================================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r pdeuser && useradd -r -g pdeuser -s /bin/false pdeuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN chown -R pdeuser:pdeuser /app

USER pdeuser

# Puertos expuestos: 8000 (FastAPI API) y 8501 (Streamlit Frontend)
EXPOSE 8000 8501

CMD ["uvicorn", "src.pde.api.main:app", "--host", "0.0.0.0", "--port", "8000"]