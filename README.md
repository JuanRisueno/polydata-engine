# PolyData Engine (PDE)

Motor polimórfico de alta seguridad desarrollado en Python y FastAPI para la ingesta, validación, detección de tipos y procesamiento heterogéneo de datasets (CSV, TSV, JSON, ARFF, Parquet) bajo principios de **Security by Design** e I/O en memoria.

---

## 🚀 Características Principales

* **Detección Polimórfica de Archivos:** Identificación precisa del tipo MIME real, codificación (*encoding*) y formato mediante firmas binarias (`libmagic` / `charset-normalizer`), evitando la suplantación de extensiones falsas.
* **Security by Design:** Middleware de cabeceras HTTP de seguridad estrictamente configuradas (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` y `Content-Security-Policy` ajustada para Swagger UI).
* **Procesamiento Seguro:** Prevención de ataques DoS mediante límites de tamaño por petición (50 MB) y gestión directa de buffers en RAM (*Zero-Disk-I/O*).
* **Infraestructura Contenerizada:** Orquestación mediante Docker y Docker Compose para entornos de producción y desarrollo aislados.

---

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.11+
* **Framework Web:** FastAPI / Uvicorn
* **Contenerización:** Docker / Docker Compose
* **Análisis de Datos:** Pandas, NumPy, PyArrow, Liac-ARFF
* **Motor de Inspección:** `python-magic` (`libmagic`), `charset-normalizer`
* **Testing & Calidad:** Pytest, HTTPX

---

## 📁 Estructura del Proyecto

```text
polydata-engine/
├── src/
│   └── pde/
│       ├── api/
│       │   └── main.py          # Aplicación FastAPI, Middlewares y Endpoints
│       └── core/
│           ├── detector.py      # Motor de detección polimórfica binaria
│           └── parser.py        # Normalización y parsing seguro de datasets
├── tests/
│   ├── test_detector.py         # Pruebas unitarias del detector
│   └── test_parser.py           # Pruebas unitarias del parser
├── Dockerfile                   # Configuración de imagen Docker
├── docker-compose.yml           # Orquestación de servicios
├── requirements.txt             # Dependencias del proyecto
├── pytest.ini                   # Configuración global de pruebas
└── README.md
```

---

## ⚙️ Instalación y Configuración Local

### Requisitos Previos

* Sistema Operativo Linux (CachyOS / Arch Linux recomendado).
* Python 3.11+
* Docker y Docker Compose
* Librería de sistema `file` (`libmagic`):
  ```bash
  sudo pacman -S --needed file
  ```

### 1. Clonar el Repositorio

```bash
git clone [https://github.com/tu-usuario/polydata-engine.git](https://github.com/tu-usuario/polydata-engine.git)
cd polydata-engine
```

### 2. Configurar el Entorno Virtual

**En Fish Shell (CachyOS / Arch Linux):**
```fish
python -m venv ~/.venvs/polydata-engine
source ~/.venvs/polydata-engine/bin/activate.fish
pip install --upgrade pip
pip install -r requirements.txt
```

**En Bash / Zsh:**
```bash
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🐳 Despliegue con Docker Compose

Para construir y levantar el servicio en segundo plano (*detached mode*):

```bash
docker compose up -d --build
```

### Acceso a la Documentación Interactiva

* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

### Comandos Útiles de Gestión

* **Estado del contenedor:** `docker compose ps`
* **Logs en tiempo real:** `docker compose logs -f`
* **Reiniciar el servicio:** `docker compose restart`
* **Detener la infraestructura:** `docker compose down`

---

## 🧪 Ejecución de Pruebas Automatizadas

La suite de pruebas valida la detección de firmas binarias, el control de límites de tamaño y la sanitización de inyecciones de fórmulas.

**En el entorno virtual local:**
```bash
pytest
```

**Dentro del contenedor Docker:**
```bash
docker compose exec api pytest
```

---

## 📌 Endpoints de la API

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/` | Estado operativo del servicio y nivel de seguridad. |
| `GET` | `/health` | Healthcheck para orquestadores y balanceadores de carga. |
| `POST` | `/detect` | Inspección y detección polimórfica de archivos (`multipart/form-data`). |

---

## 📄 Licencia

Proyecto distribuido bajo la Licencia MIT.