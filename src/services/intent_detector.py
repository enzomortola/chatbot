# src/services/intent_detector.py - VERSIÓN LIMPIA (solo frases directas)
from src.config.settings import CONTACT_KEYWORDS

def extract_contact_intent(message):
    """Detecta SOLO intención de contacto INMEDIATO"""
    if not message:
        return "NINGUNA"
        
    message_lower = message.lower()
    
    # SOLO frases de contacto DIRECTO (alto peso)
    high_weight_phrases = [
        'quiero dejar mis datos', 'dejar mis datos', 'quiero contacto',
        'hablar con ejecutivo', 'que me contacten', 'quiero que me llamen',
        'quiero una demo', 'necesito un asesor', 'quiero cotizar',
        'quiero comprar', 'quiero contratar', 'dejar datos', 'formulario',
        'quiero hablar con alguien', 'me pueden llamar', 'escribanme',
        'agenden contacto', 'solicito contacto', 'requiero contacto',
        'un asesor me contacte', 'un ejecutivo me llame'
    ]
    
    for phrase in high_weight_phrases:
        if phrase in message_lower:
            return "DIRECTO"
    
    # NO detectar palabras sueltas como "productos" o "cotización" aquí
    # Eso se manejará con incentivo después de la respuesta
    
    return "NINGUNA"
