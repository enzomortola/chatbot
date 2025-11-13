# src/ui/chat_interface.py
import streamlit as st
from src.services.chroma_service import search_similar_documents
from src.services.intent_detector import extract_contact_intent
from src.models.gemini_client import GeminiClient
from src.config.settings import GEMINI_API_KEY
from src.utils.session_manager import SessionStateManager
from src.utils.validators import sanitize_input

def generate_contextual_response(query, context_documents):
    """Generar respuesta contextual con Gemini"""
    try:
        client = GeminiClient(GEMINI_API_KEY)
        if not client.model:
            return "🔧 El modelo Gemini no está disponible. Por favor, escribe 'quiero contacto' para hablar con un especialista."

        if context_documents:
            context = "\n\n".join(context_documents[:3])
            prompt = f"""Eres un experto vendedor de ESET con acceso a toda la información de productos y técnicas de ventas.

INFORMACIÓN RELEVANTE DE NUESTROS DOCUMENTOS:
{context}

PREGUNTA DEL CLIENTE: {query}

Responde como un vendedor profesional de ESET usando la información proporcionada.

RESPUESTA:"""
        else:
            prompt = f"""Eres un vendedor experto de ESET. Responde a esta pregunta de manera profesional y útil.

PREGUNTA: {query}

RESPUESTA:"""
        
        # ESTA ES LA LÍNEA CLAVE - Ahora devuelve (response, usage)
        response, usage = client.generate_content(prompt)
        
        if usage:
            SessionStateManager.add_token_usage(usage)
        
        return response
    except Exception as e:
        st.sidebar.error(f"❌ Error generando respuesta: {e}")
        return "⚠️ Error temporal con Gemini 2.0. Por favor, intenta nuevamente o escribe 'quiero contacto' para hablar con un especialista."

def procesar_mensaje(prompt):
    """Procesar un mensaje del usuario"""
    # Sanitizar entrada
    prompt = sanitize_input(prompt)
    
    # Guardar última consulta
    st.session_state.last_query = prompt
    
    # Agregar mensaje del usuario
    SessionStateManager.add_message("user", prompt)
    
    # Verificar intención de contacto
    is_contact_intent = extract_contact_intent(prompt)
    
    if is_contact_intent:
        contact_response = """¡Excelente! Veo que estás interesado en nuestros productos de ESET.

Para ofrecerte la mejor atención personalizada y una cotización adaptada a tus necesidades, me gustaría contar con algunos datos.

**Por favor completa el formulario que aparece a continuación** 👇

Un especialista se pondrá en contacto contigo en un máximo de 24 horas para:
- ✅ Analizar tus necesidades específicas
- ✅ Proporcionarte una demostración personalizada
- ✅ Entregarte una cotización detallada

¡Estamos aquí para ayudarte! 🚀"""
        
        SessionStateManager.add_message("assistant", contact_response)
        st.session_state.awaiting_form = True
        return contact_response
    
    # Buscar información relevante
    with st.spinner("Buscando información..."):
        relevant_docs = search_similar_documents(prompt, top_k=5)
        response = generate_contextual_response(prompt, relevant_docs)
        
        SessionStateManager.add_message("assistant", response)
        
        # Sugerir contacto si es relevante
        if any(word in prompt.lower() for word in ['precio', 'cotiz', 'compra', 'demo', 'contratar']):
            response += "\n\n💡 **¿Te interesa una cotización personalizada?** Escribe 'quiero dejar mis datos' y te ayudo con el proceso."
        
        return response