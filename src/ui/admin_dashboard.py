# src/ui/admin_dashboard.py - Dashboard puro sin login
import streamlit as st
import pandas as pd
from src.utils.session_manager import SessionStateManager
from src.config.settings import GEMINI_MODEL, MAX_TOKENS
from src.config.pdf_manifest import PDF_FILES
from src.utils.validators import validate_pdf_files

def mostrar_dashboard_admin():
    """Dashboard de administración (solo accesible si está autenticado)"""
    st.title("🔧 Dashboard de Administración - ESET")
    st.markdown("---")
    
    # Métricas de tokens
    if "uso_tokens" in st.session_state and st.session_state.uso_tokens:
        datos = st.session_state.uso_tokens
        total_tokens = sum([x['total_tokens'] for x in datos])
        total_consultas = len(datos)
        avg_tokens = total_tokens / total_consultas if total_consultas > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Consultas", total_consultas)
        col2.metric("Total Tokens", f"{total_tokens:,}")
        col3.metric("Promedio Tokens/Consulta", f"{avg_tokens:.0f}")
        
        st.subheader("📊 Últimas Consultas")
        if len(datos) > 0:
            df = pd.DataFrame(datos[-10:])
            st.dataframe(df[['timestamp', 'prompt_tokens', 'completion_tokens', 'total_tokens', 'modelo']])
    else:
        st.info("📝 Aún no hay datos de consultas.")
    
    # Estadísticas de chat
    st.subheader("💬 Estadísticas de Chat")
    if "messages" in st.session_state:
        total_mensajes = len(st.session_state.messages)
        mensajes_usuario = len([m for m in st.session_state.messages if m["role"] == "user"])
        mensajes_asistente = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Mensajes", total_mensajes)
        col2.metric("Mensajes Usuario", mensajes_usuario)
        col3.metric("Mensajes Asistente", mensajes_asistente)
    
    # Configuración
    st.subheader("⚙️ Configuración Actual")
    st.info(f"**Modelo:** {GEMINI_MODEL}")
    st.info(f"**Límite tokens:** {MAX_TOKENS}")
    st.info(f"**PDFs cargados:** {len(PDF_FILES)}")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🗑️ Limpiar Métricas", use_container_width=True):
            SessionStateManager.reset_metrics()
            st.rerun()
    
    with col2:
        if st.button("🔒 Cerrar Sesión Admin", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.query_params.clear()
            st.rerun()