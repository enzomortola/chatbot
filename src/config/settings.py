# src/config/settings.py
import streamlit as st

# Configuración de la página
PAGE_CONFIG = {
    "page_title": "Asistente de Ventas ESET",
    "page_icon": "🤖",
    "layout": "wide"
}

# Límites y configuraciones
MAX_TOKENS = 500
CHUNK_SIZE = 500
TOP_K_SEARCH = 5

# Modelo de Gemini
GEMINI_MODEL = "gemini-2.0-flash-exp"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Carpetas
DOCUMENTS_FOLDER = "documentos"
CHROMA_PERSIST_DIR = "./chroma_db_drive"

# Palabras clave para detectar intención de contacto
CONTACT_KEYWORDS = [
    'contacto', 'contactarme', 'dejar mis datos', 'llámenme', 'escribanme',
    'quiero que me contacten', 'datos de contacto', 'hablar con un ejecutivo',
    'asesor comercial', 'agendar reunión', 'cotización', 'presupuesto', 'me interesa',
    'precio', 'costo', 'cotiz', 'compra', 'licencia', 'demo', 'contratar', 'adquirir',
    'comprar', 'venta', 'vendedor', 'comercial', 'asesor', 'cotización', 'presupuesto'
]

# Configuración de Google Sheets
GOOGLE_SHEETS_SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SHEET_NAME = "leads_eset"

# Obtener secrets de Streamlit
def get_secret(key, default=None):
    try:
        return st.secrets[key]
    except KeyError:
        return default

# API Keys
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GOOGLE_SHEETS_CREDENTIALS = get_secret("google_sheets")