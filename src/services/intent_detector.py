# src/services/intent_detector.py - VERSION CON DOS NIVELES DE RESPUESTA
from src.config.settings import CONTACT_KEYWORDS

def extract_contact_intent(message):
    """Detecta intención con DOS niveles: INMEDIATO vs SUGERENCIA"""
    if not message:
        return "NINGUNA"
        
    message_lower = message.lower()
    
    # NIVEL 1: Frases de ALTO PESO (llevan DIRECTO al formulario)
    high_weight_phrases = [
        'quiero dejar mis datos', 'dejar mis datos', 'quiero contacto',
        'hablar con ejecutivo', 'que me contacten', 'quiero que me llamen',
        'quiero una demo', 'necesito un asesor', 'quiero cotizar',
        'quiero comprar', 'quiero contratar', 'dejar datos', 'formulario',
        'quiero hablar con alguien', 'me pueden llamar', 'escribanme'
    ]
    
    # Si encuentra frase de ALTO PESO → ACTIVA FORMULARIO DIRECTAMENTE
    for phrase in high_weight_phrases:
        if phrase in message_lower:
            return "DIRECTO"  # Lleva al formulario
    
    # NIVEL 2: Palabras de interés medio (sugiere contacto)
    medium_interest_words = [
        'me interesa', 'interesado', 'interesante', 'me gustaría', 'me intereza',
        'cuánto cuesta', 'precio', 'costo', 'valor', 'cotización',
        'presupuesto', 'información sobre precios', 'cuánto sale',
        'me interesa el producto', 'me interesa saber', 'quiero saber más'
    ]
    
    # Si encuentra interés medio → SUGIERE contacto
    if any(word in message_lower for word in medium_interest_words):
        return "SUGERENCIA"  # Sugiere dejar datos
    
    # NIVEL 3: Palabras básicas del config (respaldo)
    if any(keyword in message_lower for keyword in CONTACT_KEYWORDS):
        return "SUGERENCIA"  # Sugiere también
    
    # Sin intención detectada
    return "NINGUNA"
