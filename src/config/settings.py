# src/config/settings.py
import streamlit as st
import os

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================
PAGE_CONFIG = {
    "page_title": "Asistente de Ventas ESET",
    "page_icon": "🤖",
    "layout": "wide"
}

# ============================================================================
# LÍMITES INTELIGENTES (AJUSTADOS PARA 300+ PÁGINAS)
# ============================================================================
MAX_TOKENS = 4000                    # Gemini 2.5-flash: hasta 8192 tokens
MAX_RESPONSE_WORDS = 150            # Mantiene respuestas concisas de ventas
CHUNK_SIZE = 1000                   # ⬆️ MÁS GRANDE: menos chunks, mejor contexto
CHUNK_OVERLAP = 100                 # ⭐ NUEVO: superposición para contexto continuo
TOP_K_SEARCH = 7                    # ⬆️ MÁS RESULTADOS: 7 chunks para 300 páginas

# ============================================================================
# MODELOS - CONFIGURACIÓN CLARA
# ============================================================================
# Modelo generativo (tu LLM principal)
GEMINI_MODEL = "gemini-2.5-flash"    # Confirmado por usuario

# Modelo de embeddings (motor de búsqueda inteligente - NO es secundario)
# Este modelo hace que la búsqueda sea 1000x más eficiente que leer todo
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dimensiones, ultra rápido

# ============================================================================
# ALMACENAMIENTO
# ============================================================================
DOCUMENTS_FOLDER = "documentos"
CHROMA_PERSIST_DIR = "./chroma_db_drive"

# ============================================================================
# LÓGICA DE NEGOCIO
# ============================================================================
# Palabras clave que activan captura de leads
CONTACT_KEYWORDS = [
    'contacto', 'contactarme', 'cotizacion', 'presupuesto', 'demo', 
    'asesor', 'hablar con ejecutivo', 'dejar mis datos', 'comprar', 'precio'
]

# ============================================================================
# INTEGRACIONES
# ============================================================================
GOOGLE_SHEETS_SCOPE = [
    "https://www
