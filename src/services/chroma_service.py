# src/services/chroma_service.py
import chromadb
from chromadb.config import Settings
import streamlit as st
from src.config.settings import CHROMA_PERSIST_DIR
from src.models.embedding_model import load_embedding_model

@st.cache_resource
def init_chroma_db():
    """Inicializar cliente de ChromaDB"""
    try:
        client = chromadb.Client(Settings(
            persist_directory=CHROMA_PERSIST_DIR,
            is_persistent=True
        ))
        
        try:
            collection = client.get_collection("drive_documents")
            st.sidebar.success(f"✅ DB cargada: {collection.count()} fragmentos")
        except:
            collection = client.create_collection("drive_documents")
            st.sidebar.info("🆕 Nueva base de datos creada")
        
        return client, collection
    except Exception as e:
        st.sidebar.error(f"❌ Error inicializando ChromaDB: {e}")
        return None, None

def search_similar_documents(query, top_k=5):
    """Buscar documentos similares en la base de datos"""
    try:
        embedding_model = load_embedding_model()
        chroma_client, collection = init_chroma_db()
        
        if not embedding_model or not collection:
            return []
        
        st.sidebar.info(f"🔍 Buscando: '{query}'")
        query_embedding = embedding_model.encode(query).tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        documentos_encontrados = len(results['documents'][0]) if results['documents'] else 0
        st.sidebar.info(f"📄 Encontrados: {documentos_encontrados} documentos")
        
        return results['documents'][0] if results['documents'] else []
    except Exception as e:
        st.sidebar.error(f"❌ Error en búsqueda: {e}")
        return []