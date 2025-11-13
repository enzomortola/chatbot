# src/services/intent_detector.py
from src.config.settings import CONTACT_KEYWORDS

def extract_contact_intent(message):
    """Detectar si el usuario quiere dejar datos de contacto"""
    message_lower = message.lower()
    
    # Frases de alto peso (detectan intención inmediata)
    high_weight_phrases = [
        'quiero contacto', 'dejar mis datos', 'formulario', 'cotizacion', 
        'presupuesto', 'me llaman', 'me contactan', 'hablar con ejecutivo',
        'quiero que me contacten', 'datos de contacto', 'asesor comercial'
    ]
    
    for phrase in high_weight_phrases:
        if phrase in message_lower:
            return True
    
    # Palabras individuales
    return any(keyword in message_lower for keyword in CONTACT_KEYWORDS)