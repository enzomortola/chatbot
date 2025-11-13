# src/services/pdf_processor.py
import os
from PyPDF2 import PdfReader
from src.config.settings import DOCUMENTS_FOLDER

def get_pdf_path(filename):
    """Obtener ruta completa del PDF"""
    return os.path.join(DOCUMENTS_FOLDER, filename)

def extract_text_from_pdf(pdf_path):
    """Extraer texto de un archivo PDF"""
    try:
        pdf_reader = PdfReader(pdf_path, strict=False)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text if text.strip() else None
    except Exception as e:
        print(f"Error leyendo PDF {pdf_path}: {e}")
        return None

def split_text(text, chunk_size=500):
    """Dividir texto en chunks"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks