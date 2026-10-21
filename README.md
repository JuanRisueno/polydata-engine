# PolyData Engine (PDE)

Motor polimórfico de alta seguridad desarrollado en Python y FastAPI para la ingesta, validación, detección de tipos y procesamiento heterogéneo de datasets (CSV, TSV, JSON, ARFF, Parquet) bajo principios de **Security by Design** e I/O en memoria, junto con una interfaz web interactiva en Streamlit.

---

## 🚀 Características Principales

* **Detección Polimórfica de Archivos:** Identificación precisa del tipo MIME real, codificación (*encoding*) y formato mediante firmas binarias (`libmagic` / `charset-normalizer`) e inspección de buffer, evitando la suplantación por extensiones falsas.
* **Interfaz Web Modular:** Panel interactivo desarrollado en Streamlit desacoplado de la API, estructurado modularmente (`components`, `services`, `styles`, `utils`), con soporte para arrastrar/soltar datasets, visualización de métricas sin truncamiento y limpieza en caliente.
* **Security by Design:** Middleware de cabeceras HTTP de seguridad estrictamente configuradas (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` y `Content-Security-Policy` ajustada para Swagger UI).
* **Procesamiento Seguro:** Prevención de ataques DoS mediante límites de tamaño por petición (configurable, 100 MB por defecto) y gestión directa de buffers en RAM (*Zero-Disk-I/O*).
* **Infraestructura Contenerizada:** Orquestación mediante Docker y Docker Compose aislando los servicios de backend (`api`) y frontend (`frontend`) en una red privada interna.

---

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.11+
* **Backend Framework:** FastAPI / Uvicorn (ASGI)
* **Frontend Framework:** Streamlit
* **Contenerización & Redes:** Docker / Docker Compose
* **Análisis de Datos:** Pandas, NumPy, PyArrow, Liac-ARFF
* **Motor de Inspección Binaria:** `python-magic` (`libmagic`), `charset-normalizer`
* **Testing & Calidad:** Pytest, HTTPX

---

## 📁 Estructura del Proyecto

```text
polydata-engine/
├── data/                       # Almacenamiento temporal/local de datos
├── datasets/                   # Datasets de prueba y validación
│   ├── raw/                    # Datasets sin procesar
│   └── samples/                # Muestras de prueba (JSON, TXT, etc.)
│       ├── prueba.json
│       └── prueba.txt
├── frontend/                   # Interfaz de usuario en Streamlit (Modular)
│   ├── components/             # Componentes de renderizado de interfaz
│   │   ├── __init__.py
│   │   └── inspection_view.py  # Renderizado de métricas y tarjetas
│   ├── services/               # Clientes de comunicación HTTP
│   │   ├── __init__.py
│   │   └── api_client.py       # Consumo del backend FastAPI
│   ├── styles/                 # Inyección aislada de CSS
│   │   ├── __init__.py
│   │   └── theme.py
│   ├── utils/                  # Auxiliares de formateo y lógica pura
│   │   ├── __init__.py
│   │   └── formatters.py
│   ├── __init__.py
│   ├── app.py                  # Orquestador principal de Streamlit
│   └── config.py               # Configuración del frontend
├── src/                        # Código fuente del backend
│   └── pde/
│       ├── __init__.py
│       ├── api/                # Endpoints y controladores FastAPI
│       │   ├── __init__.py
│       │   └── main.py
│       ├── core/               # Motores principales de procesamiento
│       │   ├── __init__.py
│       │   ├── detector.py      # Detección polimórfica y firmas binarias
│       │   ├── explorer.py      # Inspección estructural de datasets
│       │   └── parser.py        # Normalización y parsing seguro
│       └── fetchers/            # Módulos de ingesta y conectores de datos
│           └── __init__.py
├── tests/                      # Suite de pruebas automatizadas
│   ├── test_detector.py         # Pruebas unitarias del detector binario
│   ├── test_explorer.py         # Pruebas unitarias del explorador
│   ├── test_integration_block1.py # Pruebas de integración de extremo a extremo
│   └── test_parser.py           # Pruebas unitarias del parser
├── .env                        # Variables de entorno del proyecto
├── Dockerfile                   # Construcción de la imagen Docker
├── docker-compose.yml           # Orquestación de servicios (api + frontend)
├── pytest.ini                   # Configuración global de pytest
├── README.md                    # Documentación principal del proyecto
└── requirements.txt             # Dependencias unificadas de Python
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
git clone https://github.com/tu-usuario/polydata-engine.git
cd polydata-engine
```

### 2. Configurar Variables de Entorno

Asegúrate de tener un archivo `.env` en la raíz del proyecto:

```env
PDE_API_URL=http://localhost:8000
MAX_FILE_SIZE_MB=100
MAX_ALLOWED_BYTES=104857600
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501,http://localhost:8000,http://127.0.0.1:8000
```

> Copia `.env-ejemplo` a `.env` y ajusta si hace falta. Backend y frontend leen los mismos límites y orígenes CORS.

### 3. Configurar el Entorno Virtual (Ejecución local)

```bash
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🐳 Despliegue con Docker Compose

Para construir y levantar los contenedores (`pde_api` y `pde_frontend`):

```bash
docker compose up -d --build
```

### Accesos a los Servicios

* **Interfaz Web (Streamlit Frontend):** `http://localhost:8501`
* **API Backend (FastAPI):** `http://localhost:8000`
* **Documentación OpenAPI (Swagger UI):** `http://localhost:8000/docs`
* **Documentación ReDoc:** `http://localhost:8000/redoc`

### Comandos Útiles de Gestión

* **Estado de los contenedores:** `docker compose ps`
* **Logs del frontend en tiempo real:** `docker compose logs -f frontend`
* **Logs de la API en tiempo real:** `docker compose logs -f api`
* **Reiniciar el servicio frontend:** `docker compose restart frontend`
* **Detener la infraestructura:** `docker compose down`

---

## 🧪 Ejecución de Pruebas Automatizadas

La suite de pruebas valida la detección de firmas binarias, el control de límites de tamaño, la exploración y la sanitización.

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