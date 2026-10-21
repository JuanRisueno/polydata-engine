"""
Inyección de estilos CSS para la interfaz de Streamlit.
Ubicación: frontend/styles/theme.py
"""
import streamlit as st

def apply_custom_css() -> None:
    st.markdown("""
        <style>
        .stApp {
            max-width: 900px;
            margin: 0 auto;
        }
        .pde-card {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }
        .pde-label {
            font-size: 0.8rem;
            color: #94a3b8;
            margin-bottom: 0.25rem;
        }
        .pde-value {
            font-family: monospace;
            font-size: 1.1rem;
            font-weight: 600;
            color: #f8fafc;
            word-break: break-all;
        }
        </style>
    """, unsafe_allow_html=True)