"""
PolyData Engine (PDE) - Orquestador Principal
Ubicación: frontend/app.py
"""
import streamlit as st
from frontend.config import Config
from frontend.services.api_client import PDEApiClient
from frontend.styles.theme import apply_custom_css
from frontend.components.inspection_view import render_inspection_results

# 1. Configuración de página e inyección de CSS
st.set_page_config(page_title="PolyData Engine (PDE)", page_icon="🔍", layout="centered")
apply_custom_css()

# 2. Encabezado principal
st.title("PolyData Engine (PDE)")
st.caption("Inspección Binaria y Clasificación Polimórfica de Datasets")
st.divider()

# 3. Estado y Servicios
api_client = PDEApiClient()
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

def clear_uploader():
    st.session_state["uploader_key"] += 1
    st.rerun()

# 4. Componente Dropzone
uploaded_file = st.file_uploader(
    "Arrastra o selecciona un archivo para analizar",
    type=None,
    help=f"Tamaño máximo permitido: {Config.MAX_FILE_SIZE_MB} MB",
    key=f"uploader_{st.session_state['uploader_key']}"
)

# 5. Flujo de Control
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    
    if len(file_bytes) > Config.MAX_FILE_SIZE_BYTES:
        st.error(f"El archivo supera el límite máximo de {Config.MAX_FILE_SIZE_MB} MB.")
    else:
        with st.spinner("Analizando firmas binarias y estructura interna..."):
            success, result, error_msg = api_client.detect_file(file_bytes, uploaded_file.name)

        if success and result:
            render_inspection_results(result, on_clear_callback=clear_uploader)
        else:
            st.error(error_msg)
# frontend/app.py

st.markdown("""
    <style>
    /* Ocultar el menú de tres puntos (Hamburger menu) */
    #MainMenu {visibility: hidden;}
    
    /* Ocultar la barra superior (Header) donde aparece 'Deploy' */
    header[data-testid="stHeader"] {
        visibility: hidden;
        height: 0rem;
    }
    
    /* Ocultar el pie de página por defecto de Streamlit */
    footer {visibility: hidden;}
    
    /* Ajuste de margen superior para compensar la barra oculta */
    .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)