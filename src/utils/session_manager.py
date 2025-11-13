# src/utils/session_manager.py
import streamlit as st

class SessionStateManager:
    """Manejador centralizado del estado de la sesión"""
    
    @staticmethod
    def initialize():
        """Inicializar todos los estados necesarios"""
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "¡Hola! Soy tu especialista en ventas de ESET. ¿En qué puedo ayudarte con nuestros productos de ciberseguridad?"}
            ]
        
        if "uso_tokens" not in st.session_state:
            st.session_state.uso_tokens = []
        
        if "awaiting_form" not in st.session_state:
            st.session_state.awaiting_form = False
        
        if "admin_authenticated" not in st.session_state:
            st.session_state.admin_authenticated = False
        
        if "show_admin" not in st.session_state:
            st.session_state.show_admin = False
        
        if "last_query" not in st.session_state:
            st.session_state.last_query = ""
    
    @staticmethod
    def reset_metrics():
        """Limpiar métricas"""
        st.session_state.uso_tokens = []
    
    @staticmethod
    def add_message(role, content):
        """Agregar mensaje al chat"""
        st.session_state.messages.append({"role": role, "content": content})
    
    @staticmethod
    def add_token_usage(usage):
        """Agregar uso de tokens"""
        st.session_state.uso_tokens.append(usage)