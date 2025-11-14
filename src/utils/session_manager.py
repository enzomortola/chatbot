# src/utils/session_manager.py
import streamlit as st

class SessionStateManager:
    """Manejador centralizado del estado de la sesión"""
    
    @staticmethod
    def initialize():
        """Inicializar todos los estados necesarios"""
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "🛡️ Asesor de Ciberseguridad ESET. ¿Sobre qué producto querés info? Si querés una demo, escribí 'quiero dejar mis datos' y un especialista se va a contactar a la brevedad."}
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
