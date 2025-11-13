# src/utils/token_calculator.py
import datetime

def calcular_tokens_y_costo(prompt, response, model_used):
    """Estimar tokens usados (versión mejorada)"""
    # Contar palabras y estimar tokens (más preciso que antes)
    prompt_words = len(prompt.split())
    response_words = len(response.split())
    
    # En español, aproximadamente 1 token = 0.75 palabras
    prompt_tokens = int(prompt_words * 1.33)
    response_tokens = int(response_words * 1.33)
    
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": response_tokens,
        "total_tokens": prompt_tokens + response_tokens,
        "modelo": model_used,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
    }