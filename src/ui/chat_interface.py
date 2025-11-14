# src/ui/chat_interface.py - VERSIÓN FINAL CON INCENTIVO AGRESIVO
# src/ui/chat_interface.py - VERSIÓN FINAL CON INCENTIVO ÚNICO Y WHATSAPP
import streamlit as st
from src.services.chroma_service import search_similar_documents
from src.services.intent_detector import extract_contact_intent
from src.models.gemini_client import GeminiClient
from src.config.settings import GEMINI_API_KEY, MAX_RESPONSE_WORDS
from src.utils.session_manager import SessionStateManager
from src.utils.validators import sanitize_input

# CONFIGURACIÓN DEL LINK DE WHATSAPP
# Reemplaza con tu número real en formato internacional sin '+' ni espacios
# Ejemplo: "541112345678" para +54 11 1234-5678
WHATSAPP_NUMBER = "541124797731"  # <--- CAMBIA ESTO POR TU NÚMERO
WHATSAPP_MESSAGE = "Hola, me contacto desde el asistente de ESET. Necesito información comercial."
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}?text={WHATSAPP_MESSAGE.replace(' ', '%20')}"

def generate_contextual_response(query, context_documents):
    """Genera respuesta usando contexto SIN incentivo de contacto"""
    try:
        client = GeminiClient(GEMINI_API_KEY)
        if not client.model:
            return "🔧 El modelo no está disponible."
        
        # Preparar contexto
        if context_documents:
            context = "\n\n".join(context_documents[:3])
            if len(context.split()) > 300:
                context = " ".join(context.split()[:300]) + "..."
            
            prompt = f"""Eres un experto vendedor de ESET. Responde esta pregunta usando la información:

{context}

Pregunta: {query}

Responde de forma profesional, clara y concisa. NO agregues invitaciones a contacto al final."""
        else:
            prompt = f"""Eres un vendedor experto de ESET. Responde a: {query}

Responde de forma profesional. NO agregues invitaciones a contacto al final."""
        
        response, _ = client.generate_content(prompt, max_words=MAX_RESPONSE_WORDS)
        return response
    except Exception as e:
        st.sidebar.error(f"❌ Error: {e}")
        return "⚠️ Error temporal. Intenta nuevamente."

def procesar_mensaje(prompt):
    """Procesa mensaje: BUSCA → RESPONDE → INCENTIVO ÚNICO CON WHATSAPP"""
    # Sanitizar entrada
    prompt = sanitize_input(prompt)
    st.session_state.last_query = prompt
    SessionStateManager.add_message("user", prompt)
    
    # Paso 0: Detectar SOLO frases de contacto DIRECTO
    intencion = extract_contact_intent(prompt)
    
    if intencion == "DIRECTO":
        contact_response = """¡Perfecto! Para ofrecerte la mejor atención personalizada, completa este formulario.

Un especialista te contactará en menos de 24 horas para:
- ✅ Analizar tus necesidades específicas
- ✅ Proporcionarte una demostración personalizada
- ✅ Entregarte una cotización detallada

👇 Completa el formulario a continuación:"""
        SessionStateManager.add_message("assistant", contact_response)
        st.session_state.awaiting_form = True
        return contact_response
    
    # Paso 1: Buscar SIEMPRE en la base de datos
    with st.spinner("Buscando información..."):
        relevant_docs = search_similar_documents(prompt, top_k=5)
    
    # Paso 2: Generar respuesta con contexto
    response = generate_contextual_response(prompt, relevant_docs)
    
    # Paso 3: Agregar incentivo ÚNICO con WhatsApp y formulario
    # SOLO si no se activó el formulario
    if not st.session_state.awaiting_form:
        incentivo = f"""
---
💬 **¿Querés hablar con un especialista ahora?**

Tienes dos opciones rápidas:

1️⃣ **WhatsApp directo**: [Click aquí para chatear]({WHATSAPP_URL})  
2️⃣ **Formulario**: Escribí *"quiero dejar mis datos"* y te contactamos en 24h"""
        
        # Guardar respuesta principal primero
        SessionStateManager.add_message("assistant", response)
        # Luego agregar incentivo como mensaje separado para mejor UX
        response += incentivo
    
    return response
