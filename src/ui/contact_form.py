# src/ui/contact_form.py
import streamlit as st
import datetime
from src.services.google_sheets_service import guardar_lead_sheets
from src.utils.session_manager import SessionStateManager
from src.utils.validators import validate_email, validate_phone

def generar_resumen_interes(historial_conversacion, interes_seleccionado):
    """Generar resumen de interés del cliente"""
    try:
        from src.models.gemini_client import GeminiClient
        from src.config.settings import GEMINI_API_KEY
        
        if not GEMINI_API_KEY:
            return f"Cliente interesado en {interes_seleccionado}. Conversación: {historial_conversacion[-500:]}"
        
        client = GeminiClient(GEMINI_API_KEY)
        
        prompt = f"""
        Eres un asistente de ventas de ESET. Analiza la siguiente conversación y genera un resumen conciso (máximo 150 palabras) sobre los intereses específicos del cliente en productos ESET.

        INTERÉS SELECCIONADO POR EL CLIENTE: {interes_seleccionado}

        HISTORIAL DE CONVERSACIÓN:
        {historial_conversacion}

        El resumen debe incluir:
        1. Productos o servicios específicos mencionados
        2. Necesidades o preocupaciones del cliente
        3. Características que le interesan
        4. Contexto de uso (empresa, tamaño, sector si se menciona)

        Resumen:
        """
        
        response, _ = client.generate_content(prompt)
        return response.strip()
    except Exception as e:
        st.sidebar.error(f"❌ Error generando resumen: {e}")
        return f"Cliente interesado en {interes_seleccionado}. Conversación: {historial_conversacion[-500:]}"

def mostrar_formulario_contacto():
    """Mostrar y manejar el formulario de contacto"""
    st.markdown("---")
    st.subheader("📝 Formulario de Contacto")
    st.info("👇 Completa tus datos y un especialista te contactará en menos de 24 horas")
    
    with st.form(key="contact_form_main", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre completo*", placeholder="Ej: Juan Pérez")
            email = st.text_input("Email*", placeholder="juan@empresa.com")
            telefono = st.text_input("Teléfono*", placeholder="+54 11 1234-5678")
        
        with col2:
            empresa = st.text_input("Empresa", placeholder="Nombre de tu empresa")
            interes = st.selectbox(
                "Principal interés*",
                ["Selecciona una opción", "ESET PROTECT Elite", "ESET PROTECT Enterprise", "ESET PROTECT Complete", 
                 "ESET PROTECT Advanced", "ESET PROTECT Entry", "Detección y Respuesta", "Seguridad para Endpoints", "Otro"],
                index=0
            )
        
        st.subheader("📋 Resumen de tu consulta")
        conversacion_texto = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
        resumen_interes = generar_resumen_interes(conversacion_texto, interes)
        st.info(resumen_interes)
        
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            submitted = st.form_submit_button("🚀 Enviar mis datos", use_container_width=True)
        
        with col_btn2:
            cancelled = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if cancelled:
            st.session_state.awaiting_form = False
            st.rerun()
        
        if submitted:
            if not nombre or not email or not telefono:
                st.error("❌ Por favor completa todos los campos obligatorios (*)")
            elif interes == "Selecciona una opción":
                st.error("❌ Por favor selecciona tu interés principal")
            elif not validate_email(email):
                st.error("❌ Por favor ingresa un email válido")
            elif not validate_phone(telefono):
                st.error("❌ Por favor ingresa un teléfono válido (mínimo 8 dígitos)")
            else:
                form_data = {
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'nombre': nombre.strip(),
                    'email': email.strip().lower(),
                    'telefono': telefono.strip(),
                    'empresa': empresa.strip() if empresa else "No especificada",
                    'interes': interes,
                    'consulta_original': st.session_state.get('last_query', '')[:200],
                    'resumen_interes': resumen_interes
                }
                
                if guardar_lead_sheets(form_data):
                    st.success("✅ ¡Datos enviados correctamente!")
                    st.balloons()
                    
                    confirmation_msg = f"""✅ ¡Perfecto {nombre}! He registrado tus datos de contacto.

**Resumen de tu interés:**
{resumen_interes}

Un especialista de ESET te contactará en las próximientos 24 horas para:
- ✅ Analizar tus necesidades específicas
- ✅ Proporcionarte una demostración personalizada
- ✅ Entregarte una cotización detallada

¡Estamos aquí para ayudarte! 🚀"""
                    
                    SessionStateManager.add_message("assistant", confirmation_msg)
                    st.session_state.awaiting_form = False
                    st.rerun()
                else:
                    st.error("❌ Hubo un error al guardar tus datos. Por favor intenta nuevamente.")