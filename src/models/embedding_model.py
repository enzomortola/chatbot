# src/models/embedding_model.py
import streamlit as st
from sentence_transformers import SentenceTransformer
from src.config.settings import EMBEDDING_MODEL

@st.cache_resource
def load_embedding_model():
    """Cargar modelo de embeddings (con cache)"""
    try:
        st.sidebar.info("🔄 Cargando modelo de embeddings...")
        model = SentenceTransformer(EMBEDDING_MODEL)
        st.sidebar.success("✅ Modelo de embeddings cargado")
        return model
    except Exception as e:
        st.sidebar.error(f"❌ Error cargando embeddings: {e}")
        return None