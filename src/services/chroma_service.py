# src/services/chroma_service.py - VERSIÓN AUTO-REPARACIÓN PARA PRODUCCIÓN
import chromadb
from chromadb.config import Settings
import streamlit as st
from src.config.settings import CHROMA_PERSIST_DIR
from src.models.embedding_model import load_embedding_model
import os

@st.cache_resource
def init_chroma_db():
    """Inicializar cliente de ChromaDB con auto-reparación"""
    try:
        client = chromadb.Client(Settings(
            persist_directory=CHROMA_PERSIST_DIR,
            is_persistent=True
        ))
        
        try:
            collection = client.get_collection("drive_documents")
            st.sidebar.success(f"✅ DB cargada: {collection.count()} fragmentos")
        except Exception as e:
            st.sidebar.warning(f"⚠️ Base de datos incompatible o corrupta: {e}")
            st.sidebar.info("🔄 Creando nueva base de datos...")
            
            # ELIMINAR carpeta corrupta y crear nueva
            if os.path.exists(CHROMA_PERSIST_DIR):
                import shutil
                shutil.rmtree(CHROMA_PERSIST_DIR)
                st.sidebar.info("🗑️ Carpeta corrupta eliminada")
            
            # Crear cliente limpio
            client = chromadb.Client(Settings(
                persist_directory=CHROMA_PERSIST_DIR,
                is_persistent=True
            ))
            collection = client.create_collection("drive_documents")
            st.sidebar.success("🆕 Nueva base de datos creada")
        
        return client, collection
        
    except Exception as e:
        st.sidebar.error(f"❌ Error crítico: {e}")
        st.sidebar.warning("🔧 Usando modo sin base de datos")
        return None, None

def search_similar_documents(query, top_k=5):
    """Buscar documentos similares (modo seguro)"""
    try:
        embedding_model = load_embedding_model()
        chroma_client, collection = init_chroma_db()
        
        if not embedding_model or not collection:
            st.sidebar.warning("⚠️ Búsqueda deshabilitada temporalmente")
            return []
        
        st.sidebar.info(f"🔍 Buscando: '{query}'")
        query_embedding = embedding_model.encode(query).tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, 3)  # Máximo 3 para ahorrar tokens
        )
        
        documentos = results['documents'][0] if results['documents'] else []
        st.sidebar.info(f"📄 Encontrados: {len(documentos)} documentos")
        
        return documentos
        
    except Exception as e:
        st.sidebar.error(f"❌ Error en búsqueda: {e}")
        return []
