# app.py - VERSION CON SIDEBAR SOLO PARA ADMIN
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
    
    # Detectar si es admin por URL
    try:
        query_params = st.query_params
    except AttributeError:
        query_params = st.experimental_get_query_params()
    
    is_admin_url = "admin" in query_params and query_params["admin"] == ["true"]
    
    # SIDEBAR SOLO PARA ADMIN AUTENTICADO
    if st.session_state.get('admin_authenticated', False) and is_admin_url:
        mostrar_sidebar_admin()
    
    # LÓGICA PRINCIPAL
    if is_admin_url and not st.session_state.get('admin_authenticated'):
        mostrar_login_admin()
    elif st.session_state.get('admin_authenticated') and is_admin_url:
        mostrar_dashboard_admin()
    else:
        mostrar_chat_publico()  # Usuarios normales: NO sidebar

def mostrar_sidebar_admin():
    """Sidebar SOLO para admin autenticado"""
    with st.sidebar:
        st.header("🔧 Panel de Admin")
        
        # Muestra uso de tokens
        if st.session_state.get('uso_tokens'):
            total_consultas = len(st.session_state.uso_tokens)
            st.metric("Consultas", total_consultas)
        
        if st.button("📊 Dashboard"):
            st.session_state.show_admin = True
            st.rerun()
        
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.admin_authenticated = False
            st.session_state.show_admin = False
            try:
                st.query_params.clear()
            except:
                st.experimental_set_query_params()
            st.rerun()

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
            try:
                st.query_params.clear()
            except:
                st.experimental_set_query_params()
            st.rerun()

def mostrar_chat_publico():
    """Chat público: SIN sidebar, SIN opciones de admin"""
    # Header
    st.title("🤖 Asistente de Ventas ESET")
    st.markdown("### Especialista en productos de ciberseguridad")
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
