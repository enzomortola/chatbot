# src/models/embedding_model.py - VERSIÓN MÁS ESTABLE
import streamlit as st
from sentence_transformers import SentenceTransformer
from src.config.settings import EMBEDDING_MODEL

@st.cache_resource(show_spinner=False)  # Ocultar spinner molesto
def load_embedding_model():
    """Cargar modelo de embeddings con mejor manejo de errores"""
    try:
        st.sidebar.info("🔄 Cargando modelo...")
        
        # Intentar cargar modelo local si existe, sino descargar
        model = SentenceTransformer(EMBEDDING_MODEL)
        
        st.sidebar.success("✅ Modelo cargado")
        return model
        
    except Exception as e:
        st.sidebar.error(f"❌ Error cargando modelo: {e}")
        st.sidebar.warning("⚠️ Usando respuestas sin contexto")
        return None
