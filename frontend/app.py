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

# Ocultar menú superior y footer de Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header[data-testid="stHeader"] {
        visibility: hidden;
        height: 0rem;
    }
    footer {visibility: hidden;}
    .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Encabezado principal
st.title("PolyData Engine (PDE)")
st.caption("Inspección Binaria y Clasificación Polimórfica de Datasets")
st.divider()

# 3. Inicialización del Estado y Servicios
api_client = PDEApiClient()

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

if "extracted_result" not in st.session_state:
    st.session_state["extracted_result"] = None

if "parent_zip_name" not in st.session_state:
    st.session_state["parent_zip_name"] = None


def clear_uploader():
    """Resetea completamente la interfaz y el estado de la sesión."""
    st.session_state["uploader_key"] += 1
    st.session_state["extracted_result"] = None
    st.session_state["parent_zip_name"] = None
    st.rerun()


# 4. Componente Dropzone
uploaded_file = st.file_uploader(
    "Arrastra o selecciona un archivo para analizar",
    type=None,
    help=f"Tamaño máximo permitido: {Config.MAX_FILE_SIZE_MB} MB",
    key=f"uploader_{st.session_state['uploader_key']}"
)

# Reseteo automático del estado extraído si se elimina/cambia el archivo subido
if uploaded_file is None:
    st.session_state["extracted_result"] = None
    st.session_state["parent_zip_name"] = None

# 5. Flujo de Control Principal
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    
    if len(file_bytes) > Config.MAX_FILE_SIZE_BYTES:
        st.error(f"El archivo supera el límite máximo de {Config.MAX_FILE_SIZE_MB} MB.")
    else:
        # Callback para manejar la extracción de sub-archivos dentro de un ZIP
        def handle_subfile_selection(target_filename: str):
            with st.spinner(f"Extrayendo y analizando '{target_filename}' en memoria..."):
                success, result, error_msg = api_client.extract_and_detect_file(
                    file_bytes=file_bytes,
                    zip_filename=uploaded_file.name,
                    target_filename=target_filename
                )
                if success and result:
                    st.session_state["extracted_result"] = result
                    st.session_state["parent_zip_name"] = uploaded_file.name
                    st.rerun()
                else:
                    st.error(error_msg)

        # Si ya se ha analizado un sub-archivo extraído, mostramos su resultado
        if st.session_state["extracted_result"] is not None:
            render_inspection_results(
                result=st.session_state["extracted_result"],
                on_clear_callback=clear_uploader,
                parent_zip_name=st.session_state["parent_zip_name"]
            )
        else:
            # Inspección estándar del archivo cargado (o catálogo del ZIP)
            with st.spinner("Analizando firmas binarias y estructura interna..."):
                success, result, error_msg = api_client.detect_file(file_bytes, uploaded_file.name)

            if success and result:
                render_inspection_results(
                    result=result,
                    on_clear_callback=clear_uploader,
                    on_select_subfile_callback=handle_subfile_selection
                )
            else:
                st.error(error_msg)