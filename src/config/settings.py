# src/config/settings.py
import streamlit as st

# Configuración de la página
PAGE_CONFIG = {
    "page_title": "Asistente de Ventas ESET",
    "page_icon": "🤖",
    "layout": "wide"
}

# LÍMITES CONFIGURABLES - FÁCIL DE MODIFICAR
MAX_TOKENS = 500                    # Límite de tokens de Gemini
MAX_RESPONSE_WORDS = 150            # LÍMITE DE PALABRAS EN RESPUESTAS - ¡CAMBIA ESTO!
CHUNK_SIZE = 500                    # Tamaño de chunks de PDFs
TOP_K_SEARCH = 5                    # Documentos a buscar

# Modelos
GEMINI_MODEL = "gemini-2.0-flash"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Carpetas
DOCUMENTS_FOLDER = "documentos"
CHROMA_PERSIST_DIR = "./chroma_db_drive"

# Palabras clave de contacto (reducidas para ser más específicas)
CONTACT_KEYWORDS = [
    'contacto', 'contactarme', 'cotizacion', 'presupuesto', 'demo', 
    'asesor', 'hablar con ejecutivo', 'dejar mis datos'
]

# Configuración de Google Sheets
GOOGLE_SHEETS_SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SHEET_NAME = "leads_eset"

def get_secret(key, default=None):
    """Obtener secret de Streamlit o variable de entorno"""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, default)

import os
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
