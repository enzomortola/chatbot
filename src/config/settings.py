# src/config/settings.py
import streamlit as st
import os

# CONFIGURACION BASICA
PAGE_CONFIG = {
    "page_title": "Asistente de Ventas ESET",
    "page_icon": "🤖",
    "layout": "wide"
}

# LIMITES DE LA APLICACION
MAX_TOKENS = 4000
MAX_RESPONSE_WORDS = 150
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
TOP_K_SEARCH = 7

# MODELOS - CONFIGURACION PRINCIPAL
GEMINI_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# CARPETAS
DOCUMENTS_FOLDER = "documentos"
CHROMA_PERSIST_DIR = "./chroma_db_drive"

# PALABRAS CLAVE PARA DETECTAR INTENCION DE CONTACTO
CONTACT_KEYWORDS = [
    'contacto', 'contactarme', 'cotizacion', 'presupuesto', 'demo', 
    'asesor', 'hablar con ejecutivo', 'dejar mis datos', 'comprar', 'precio'
]

# GOOGLE SHEETS
GOOGLE_SHEETS_SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SHEET_NAME = "leads_eset"

# FUNCION DE SEGURIDAD PARA API KEYS
def get_secret(key, default=None):
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, default)

# INICIALIZACION DE CLAVES
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")

# VALIDACION SIMPLE (sin assert para evitar errores de ejecucion)
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY no encontrada. La app fallara al usar Gemini.")
