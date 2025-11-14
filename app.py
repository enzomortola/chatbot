# app.py - VERSIÓN COMPATIBLE CON STREAMLIT < 1.29
import streamlit as st
from src.config.settings import PAGE_CONFIG
from src.utils.session_manager import SessionStateManager
from src.ui.chat_interface import procesar_mensaje
from src.ui.contact_form import mostrar_formulario_contacto
from src.ui.admin_dashboard import mostrar_dashboard_admin

def main():
    # Configurar página
    st.set_page_config(**PAGE_CONFIG)
    
    # Inicializar estado
    SessionStateManager.initialize()
    
    # Detectar admin por URL (usando experimental para compatibilidad)
    try:
        query_params = st.query_params
    except AttributeError:
        query_params = st.experimental_get_query_params()
    
    is_admin_url = "admin" in query_params and query_params["admin"] == ["true"]
    
    if is_admin_url and not st.session_state.get('admin_authenticated'):
        mostrar_login_admin()
    elif st.session_state.get('admin_authenticated') and is_admin_url:
        mostrar_dashboard_admin()
    else:
        mostrar_chat_publico()

def mostrar_login_admin():
    """Página de login admin oculta"""
    st.title("🔐 Admin Login")
    st.markdown("---")
    
    password = st.text_input("Contraseña", type="password")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Ingresar"):
            from src.config.settings import get_secret
            admin_pass = get_secret("ADMIN_PASSWORD")
            if password == admin_pass:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
    
    with col2:
        if st.button("← Volver al chat"):
            # Limpiar query params
            try:
                st.query_params.clear()
            except AttributeError:
                st.experimental_set_query_params()
            st.rerun()

def mostrar_chat_publico():
    """Chat público sin opciones de admin"""
    # Sidebar limpio
    with st.sidebar:
        st.header("💬 Chat ESET")
        st.markdown("""
        **¿En qué puedo ayudarte?**
        - Información sobre productos
        - Características y beneficios
        - Comparación de soluciones
        
        *Escribe tu consulta en el chat*
        """)
        
        st.divider()
        st.markdown("**📞 +54 9 11 24797731**")
        st.markdown("📧 enzo@cice.ar")
        
        st.divider()
        st.markdown("**🔧 Estado**")
        st.info(f"🤖 {len(st.session_state.messages)-1} mensajes")
    
    # Header
    st.title("🤖 Asesor de Ciberseguridad ESET. Desarrollado por Cice Computación.")
    st.markdown("---")
    
    # Mostrar historial
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Mostrar formulario o input
    if st.session_state.awaiting_form:
        mostrar_formulario_contacto()
    else:
        if prompt := st.chat_input("Escribe tu pregunta..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                response = procesar_mensaje(prompt)
                st.markdown(response)
            
            if st.session_state.awaiting_form:
                st.rerun()

if __name__ == "__main__":
    main()
