# src/ui/chat_interface.py - SIN FORMATO DE FUENTE GRANDE
import streamlit as st
from src.services.chroma_service import search_similar_documents
from src.services.intent_detector import extract_contact_intent
from src.models.gemini_client import GeminiClient
from src.config.settings import GEMINI_API_KEY, MAX_RESPONSE_WORDS
from src.utils.session_manager import SessionStateManager
from src.utils.validators import sanitize_input

# CONFIGURACIÓN DE CONTACTO
WHATSAPP_NUMBER = "541140000000"  # <--- CAMBIA ESTO
WHATSAPP_MESSAGE = "Hola, me contacto desde el asistente de ESET. Necesito información comercial."
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}?text={WHATSAPP_MESSAGE.replace(' ', '%20')}"

def generate_contextual_response(query, context_documents):
    """Genera respuesta con TONO y BREVEDAD controlados"""
    try:
        client = GeminiClient(GEMINI_API_KEY)
        if not client.model:
            return "🔧 El modelo no está disponible."
        
        # Preparar contexto
        context_text = ""
        if context_documents:
            context_text = "\n\n".join(context_documents[:3])
            if len(context_text.split()) > 300:
                context_text = " ".join(context_text.split()[:300]) + "..."
        
        # INSTRUCCIONES DEL USUARIO
        system_instructions = """Instrucciones de comportamiento:
- Trabajás para CICE, líder Cristian Sánchez y Enzo Mórtola (ventas ESET)
- Tu función es mostrar productos y convertir: vender o capturar contacto
- Para precios/cotizaciones, INSISTÍ en que deben contactarse
- Respuestas potentes pero concisas (máx 3-4 líneas)
- TONO: profesional, empático, confiado
- Para empresas: enfoque en productividad, protección, reputación, ahorro
- Para usuarios: enfoque en tranquilidad, simplicidad, soporte
- NO agregues invitaciones de contacto al final (eso lo controla el sistema)"""

        prompt = f"""{system_instructions}

Información para responder:
{context_text}

Pregunta del usuario: {query}

Respuesta concisa y profesional:"""

        response, _ = client.generate_content(prompt, max_words=MAX_RESPONSE_WORDS)
        return response
    except Exception as e:
        st.sidebar.error(f"❌ Error: {e}")
        return "⚠️ Error temporal. Intenta nuevamente."

def procesar_mensaje(prompt):
    """Procesa mensaje: BUSCA → RESPONDE → INCENTIVO ÚNICO"""
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
    
    # Paso 3: Agregar incentivo ÚNICO en una sola línea
    if not st.session_state.awaiting_form:
        incentivo = f"\n\n💬 **¿Querés información comercial directa?** 📧 enzo@cice.ar | 💬 [WhatsApp]({WHATSAPP_URL}) | 📝 *Escribí 'quiero dejar mis datos'*"
        response += incentivo
    
    # Guardar en historial
    SessionStateManager.add_message("assistant", response)
    
    return response
