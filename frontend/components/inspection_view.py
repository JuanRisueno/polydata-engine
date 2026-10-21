"""
Componente de UI para renderizar los resultados del análisis.
Ubicación: frontend/components/inspection_view.py
"""
import streamlit as st
from typing import Dict, Any, Callable, Optional
from frontend.utils.formatters import format_bytes


def render_inspection_results(
    result: Dict[str, Any], 
    on_clear_callback: Callable[[], None],
    on_select_subfile_callback: Optional[Callable[[str], None]] = None,
    parent_zip_name: Optional[str] = None
) -> None:
    st.success("Análisis completado")

    # Cabecera con título y botón de borrado
    col_header, col_clear = st.columns([3, 1])
    with col_header:
        st.subheader("Resultado de la Inspección")
    with col_clear:
        if st.button("🗑️ Limpiar", use_container_width=True, help="Borra el dataset cargado"):
            on_clear_callback()

    # Destacado del tipo de dataset
    dataset_type_str = result['dataset_type'].upper()
    st.markdown(
        f"**Estructura:** <span style='color: #38bdf8; font-weight: bold; font-family: monospace;'>{dataset_type_str}</span>", 
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # Grilla de métricas principales
    col1, col2 = st.columns(2)

    with col1:
        parent_info = f"<br><span style='font-size: 0.75rem; color: #38bdf8;'>📦 Extraído de: {parent_zip_name}</span>" if parent_zip_name else ""
        st.markdown(f"""
            <div class="pde-card">
                <div class="pde-label">Nombre del archivo</div>
                <div class="pde-value">{result['filename']}{parent_info}</div>
            </div>
            <div class="pde-card">
                <div class="pde-label">Tipo MIME</div>
                <div class="pde-value">{result['mime_type']}</div>
            </div>
            <div class="pde-card">
                <div class="pde-label">Codificación</div>
                <div class="pde-value">{result['encoding'] or 'N/A (Binario)'}</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        human_size = format_bytes(result['file_size_bytes'])
        st.markdown(f"""
            <div class="pde-card">
                <div class="pde-label">Tipo de Dataset</div>
                <div class="pde-value">{result['dataset_type']}</div>
            </div>
            <div class="pde-card">
                <div class="pde-label">Tamaño Real</div>
                <div class="pde-value">{human_size} <span style="font-size: 0.8rem; font-weight: normal; color: #94a3b8;">({result['file_size_bytes']:,} B)</span></div>
            </div>
            <div class="pde-card">
                <div class="pde-label">¿Es Texto Plano?</div>
                <div class="pde-value">{'Sí' if result['is_text'] else 'No'}</div>
            </div>
        """, unsafe_allow_html=True)

    # SECCIÓN ESPECIAL: Inspección de archivos dentro de contenedores ZIP
    if result.get("is_container") and result.get("contained_files"):
        st.divider()
        st.info("📦 **Contenedor ZIP detectado:** Selecciona el archivo interno que deseas extraer y analizar.")

        contained_files = result["contained_files"]
        
        # Mapeo de opciones para el selector
        file_map = {}
        options = []
        default_index = 0

        for idx, item in enumerate(contained_files):
            fname = item["filename"]
            fsize = format_bytes(item["file_size_bytes"])
            is_cand = item["is_dataset_candidate"]

            # Etiqueta visual clara
            label = f"📊 [DATASET RECOMENDADO] {fname} ({fsize})" if is_cand else f"📄 [ARCHIVO] {fname} ({fsize})"
            options.append(label)
            file_map[label] = fname

            if fname == result.get("recommended_file"):
                default_index = idx

        selected_label = st.selectbox(
            "Archivos encontrados dentro del ZIP:",
            options=options,
            index=default_index
        )

        target_file = file_map[selected_label]

        if st.button("🔍 Extraer y analizar archivo seleccionado", use_container_width=True):
            if on_select_subfile_callback:
                on_select_subfile_callback(target_file)

    with st.expander("Ver payload RAW de la API (JSON)"):
        st.json(result)