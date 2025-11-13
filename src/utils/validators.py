# src/utils/validators.py
import os
import re

# Usar imports relativos en lugar de absolutos
try:
    from ..config.settings import DOCUMENTS_FOLDER
    from ..config.pdf_manifest import PDF_FILES
except ImportError:
    # Si falla, usar imports absolutos
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from src.config.settings import DOCUMENTS_FOLDER
    from src.config.pdf_manifest import PDF_FILES

def validate_email(email):
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validar que el teléfono tenga al menos 8 dígitos"""
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 8

def validate_pdf_files():
    """Verificar que todos los PDFs existan"""
    missing = []
    for pdf_file in PDF_FILES:
        pdf_path = os.path.join(DOCUMENTS_FOLDER, pdf_file)
        if not os.path.exists(pdf_path):
            missing.append(pdf_file)
    
    return len(missing) == 0, missing

def sanitize_input(text):
    """Limpiar entrada de texto para prevenir inyección"""
    text = re.sub(r'[<>\"\'%;()&+]', '', text)
    return text.strip()