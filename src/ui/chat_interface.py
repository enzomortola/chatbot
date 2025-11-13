# src/ui/chat_interface.py
import streamlit as st
from src.services.chroma_service import search_similar_documents
from src.services.intent_detector import extract_contact_intent
from src.models.gemini_client import GeminiClient
from src.config.settings import GEMINI_API_KEY, MAX_RESPONSE_WORDS
from src.utils.session_manager import SessionStateManager
from src.utils.validators import sanitize_input

def generate_contextual_response(query, context_documents):
    """Generar respuesta contextual con límite de palabras"""
    try:
        client = GeminiClient(GEMINI_API_KEY)
        if not client.model:
            return "🔧 El modelo no está disponible.", None
        
        # Si hay muchos documentos, resumir contexto para ahorrar tokens
        if context_documents:
            # Tomar solo los 3 más relevantes y resumirlos si son muy largos
            context = "\n\n".join(context_documents[:3])
            if len(context.split()) > 300:
                context = " ".join(context.split()[:300]) + "..."
            
            prompt = f"""Eres un experto vendedor de ESET. Usa esta información:

{context}

Pregunta: {query}

Responde como un vendedor profesional."""
        else:
            prompt = f"""Eres un vendedor experto de ESET. Responde a esta pregunta:

Pregunta: {query}

Respuesta:"""
        
        # Llamar con límite de palabras configurable
        response, _ = client.generate_content(prompt, max_words=MAX_RESPONSE_WORDS)
        
        return response
    except Exception as e:
        st.sidebar.error(f"❌ Error generando respuesta: {e}")
        return "⚠️ Error temporal. Por favor, intenta nuevamente."

def procesar_mensaje(prompt):
    """Procesar un mensaje del usuario con detección de 2 niveles"""
    # Sanitizar entrada
    prompt = sanitize_input(prompt)
    st.session_state.last_query = prompt
    SessionStateManager.add_message("user", prompt)
    
    # Detectar intención con 2 niveles
    intencion = extract_contact_intent(prompt)
    
    if intencion == "DIRECTO":
        # ACTIVA FORMULARIO DIRECTAMENTE
        contact_response = """¡Perfecto! Para ofrecerte la mejor atención personalizada, completa este formulario.

Un especialista te contactará en menos de 24 horas para:
- ✅ Analizar tus necesidades específicas
- ✅ Proporcionarte una demostración personalizada
- ✅ Entregarte una cotización detallada

👇 Completa el formulario a continuación:"""
        
        SessionStateManager.add_message("assistant", contact_response)
        st.session_state.awaiting_form = True
        return contact_response
        
    elif intencion == "SUGERENCIA":
        # SUGIERE contacto pero no fuerza
        suggestion_response = """¡Me alegra que estés interesado! 

Para ofrecerte información más detallada y una cotización personalizada, puedo conectarte con uno de nuestros especialistas.

💡 **¿Querés que te contactemos?** Simplemente escribí: *"quiero dejar mis datos"* y te ayudo con el proceso.

¿En qué más puedo ayudarte mientras tanto?"""
        
        SessionStateManager.add_message("assistant", suggestion_response)
        return suggestion_response
    
    else:
        # Sin intención detectada → búsqueda normal en documentos
        with st.spinner("Buscando información..."):
            relevant_docs = search_similar_documents(prompt, top_k=3)
            response = generate_contextual_response(prompt, relevant_docs)
            
            SessionStateManager.add_message("assistant", response)
            
            # Sugerir contacto solo si es relevante
            if any(word in prompt.lower() for word in ['precio', 'cotiz', 'comprar']):
                response += "\n\n💡 **¿Cotización?** Escribe 'quiero dejar mis datos'."
            
            return response
