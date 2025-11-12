import streamlit as st
import requests
import json
import os
import re
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import numpy as np
import datetime
import pandas as pd
from pathlib import Path
import io
import gspread
from google.oauth2.service_account import Credentials

# Configurar página - PRIMERO
st.set_page_config(
    page_title="Asistente de Ventas ESET",
    page_icon="🤖",
    layout="wide"
)

ADMIN_PASSWORD = "eset_admin_ciceEnzo"
MAX_TOKENS = 500

def calcular_tokens_y_costo(prompt, response, model_used):
    prompt_tokens_est = len(prompt.split()) * 1.3
    response_tokens_est = len(response.split()) * 1.3
    return {
        "prompt_tokens": int(prompt_tokens_est),
        "completion_tokens": int(response_tokens_est),
        "total_tokens": int(prompt_tokens_est + response_tokens_est),
        "modelo": model_used,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
    }

def mostrar_dashboard_admin():
    st.title("🔧 Dashboard de Administración - ESET")
    st.markdown("---")
    if "uso_tokens" in st.session_state and st.session_state.uso_tokens:
        datos = st.session_state.uso_tokens
        total_tokens = sum([x['total_tokens'] for x in datos])
        total_consultas = len(datos)
        avg_tokens = total_tokens / total_consultas if total_consultas > 0 else 0
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Consultas", total_consultas)
        col2.metric("Total Tokens", f"{total_tokens:,}")
        col3.metric("Promedio Tokens/Consulta", f"{avg_tokens:.0f}")
        st.subheader("📊 Últimas Consultas")
        if len(datos) > 0:
            df = pd.DataFrame(datos[-10:])
            st.dataframe(df[['timestamp', 'prompt_tokens', 'completion_tokens', 'total_tokens', 'modelo']])
    else:
        st.info("📝 Aún no hay datos de consultas")
    st.subheader("💬 Estadísticas de Chat")
    if "messages" in st.session_state:
        total_mensajes = len(st.session_state.messages)
        mensajes_usuario = len([m for m in st.session_state.messages if m["role"] == "user"])
        mensajes_asistente = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Mensajes", total_mensajes)
        col2.metric("Mensajes Usuario", mensajes_usuario)
        col3.metric("Mensajes Asistente", mensajes_asistente)
    st.subheader("⚙️ Configuración Actual")
    st.info(f"**Modelo:** google/gemini-2.0-flash-exp:free")
    st.info(f"**Límite tokens/respuesta:** {MAX_TOKENS}")
    st.info(f"**PDFs cargados:** 12")
    if st.button("🗑️ Limpiar Métricas", type="secondary"):
        if "uso_tokens" in st.session_state:
            st.session_state.uso_tokens = []
        st.rerun()

DOCUMENTS_FOLDER = "documentos"
PDF_FILES = [
    "ESET_DRA_Service_Specification.pdf", "ESET_PROTECT_Elite_brochure-ES.pdf", 
    "ESET_PROTECT_Enterprise_brochure-ES.pdf", "ESET_PSE_Service_Specification.pdf",
    "How-to-Win-Friends-and-Influence-People-Dale-Carnegie_-editorial-consultant_-Dorothy-Carnegie_-_-WeL.pdf", 
    "INSTRUCCIONES DE COMPORTAMIENTO GENERALES.pdf", "Objections-The-Ultimate-Guide-for-Mastering-The-Art-and-Blount_-Jeb_-Hunter_-Mark-_-WeLib.org-_.pdf", 
    "Overview-ESET-PROTECT-Advanced.pdf", "Overview-ESET-PROTECT-Complete.pdf", "Overview-ESET-PROTECT-Entry.pdf",
    "Thank You for Arguing - What Aristotle, Lincoln, and Homer -- Heinrichs, Jay -- ( WeLib.org ).pdf",
    "The Psychology of Selling - Increase Your Sales Faster and -- Brian Tracy -- ( WeLib.org ).pdf"
]

CONTACT_KEYWORDS = [
    'contacto', 'contactar', 'contactarme', 'llamar', 'llámenme', 'escribir', 'escribanme', 
    'datos de contacto', 'hablar con asesor', 'ejecutivo', 'asesor', 'reunión', 'cita', 
    'cotización', 'presupuesto', 'quiero que me contacten', 'deseo contacto', 'me interesa contacto',
    'agendar', 'coordinar'
]

class OpenRouterClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json", "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://asistente-eset.streamlit.app", "X-Title": "Asistente ESET"
        }
    def generate_content(self, prompt):
        try:
            payload = {
                "model": "google/gemini-2.0-flash-exp:free", "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7, "max_tokens": MAX_TOKENS
            }
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                respuesta_final = result["choices"][0]["message"]["content"]
                uso = calcular_tokens_y_costo(prompt, respuesta_final, payload["model"])
                if "uso_tokens" not in st.session_state: st.session_state.uso_tokens = []
                st.session_state.uso_tokens.append(uso)
                return respuesta_final
            else: return "Lo siento, hubo un error temporal. Por favor, intenta nuevamente."
        except Exception as e: return "En este momento tengo dificultades técnicas. Por favor, intenta nuevamente."

def setup_google_sheets():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials_dict = st.secrets["google_sheets"]
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e: return None

def get_leads_sheet(client, sheet_name="leads_eset"):
    try:
        sheet = client.open(sheet_name).sheet1
        return sheet
    except gspread.SpreadsheetNotFound:
        try:
            sheet = client.create(sheet_name)
            worksheet = sheet.sheet1
            headers = ["timestamp", "nombre", "email", "telefono", "empresa", "interes", "consulta_original", "resumen_interes"]
            worksheet.append_row(headers)
            return worksheet
        except Exception as e: return None
    except Exception as e: return None

def guardar_lead_sheets(form_data):
    try:
        client = setup_google_sheets()
        if not client: return False
        sheet = get_leads_sheet(client)
        if not sheet: return False
        row = [form_data['timestamp'], form_data['nombre'] or "No especificado", form_data['email'] or "No especificado", 
               form_data['telefono'], form_data['empresa'] or "No especificado", form_data['interes'] or "No especificado",
               form_data['consulta_original'] or "No especificada", form_data['resumen_interes'] or "No especificado"]
        sheet.append_row(row)
        return True
    except Exception as e: return False

@st.cache_resource
def load_embedding_model():
    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

@st.cache_resource
def load_openrouter_model():
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
        client = OpenRouterClient(api_key)
        return client
    except Exception as e: return None

@st.cache_resource
def init_chroma_db():
    client = chromadb.Client(Settings(persist_directory="./chroma_db_drive", is_persistent=True))
    try: collection = client.get_collection("drive_documents")
    except: collection = client.create_collection("drive_documents")
    return client, collection

def extract_contact_intent(message):
    message_lower = message.lower().strip()
    import string
    message_clean = message_lower.translate(str.maketrans('', '', string.punctuation))
    contact_interest_keywords = [
        'contacto', 'contactar', 'contactarme', 'llamar', 'llámenme', 'escribir', 'escribanme', 
        'datos de contacto', 'hablar con asesor', 'ejecutivo', 'asesor', 'reunión', 'cita', 
        'cotización', 'presupuesto', 'quiero que me contacten', 'deseo contacto', 'me interesa contacto',
        'agendar', 'coordinar'
    ]
    has_contact_interest = any(keyword in message_clean for keyword in contact_interest_keywords)
    if message_clean in ['sí', 'si', 'ok', 'dale', 'perfecto']:
        if st.session_state.messages and len(st.session_state.messages) > 0:
            last_assistant_msg = st.session_state.messages[-1]["content"] if st.session_state.messages[-1]["role"] == "assistant" else ""
            if "¿Te gustaría que un especialista te contacte" in last_assistant_msg: return True
    return has_contact_interest

def generar_resumen_interes(historial_conversacion, interes_seleccionado):
    try:
        model = load_openrouter_model()
        if not model: return f"Cliente interesado en {interes_seleccionado}"
        prompt = f"Resume en MÁXIMO 50 palabras los intereses del cliente:\nInterés: {interes_seleccionado}\nConversación: {historial_conversacion[-300:]}\nResumen ultra-breve:"
        response = model.generate_content(prompt)
        return response.strip()
    except Exception as e: return f"Interesado en {interes_seleccionado}"

def get_pdf_from_local(filename):
    pdf_path = os.path.join(DOCUMENTS_FOLDER, filename)
    return pdf_path if os.path.exists(pdf_path) else None

def extract_text_from_pdf(pdf_path):
    try:
        pdf_reader = PdfReader(pdf_path, strict=False)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text: text += page_text + "\n"
        return text if text.strip() else None
    except Exception as e: return None

def split_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def search_similar_documents(query, top_k=3):
    try:
        embedding_model = load_embedding_model()
        chroma_client, collection = init_chroma_db()
        query_embedding = embedding_model.encode(query).tolist()
        results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
        return results['documents'][0] if results['documents'] else []
    except Exception as e: return []

def generate_contextual_response(query, context_documents):
    try:
        model = load_openrouter_model()
        if not model: return "¡Te recomiendo contactar a nuestro equipo de ventas! 😊"
        if context_documents:
            context = "\n".join(context_documents[:2])
            prompt = f"Responde en MÁXIMO 2 oraciones. Sé breve y amigable.\nCONTEXTO: {context}\nPREGUNTA: {query}\nRESPUESTA BREVE:"
        else: prompt = f"Responde en 1-2 oraciones máximo. Sé breve y directo.\nPREGUNTA: {query}\nRESPUESTA CONCISA:"
        response = model.generate_content(prompt)
        sentences = response.split('. ')
        if len(sentences) > 2: response = '. '.join(sentences[:2]) + '.'
        if len(response) > 300: response = response[:300] + "..."
        return response
    except Exception as e: return "¡Perfecto! Te recomiendo contactar a nuestro equipo para más detalles. 😊"

def generate_quick_response(query):
    quick_responses = {
        'precio': "¡Los precios varían según tus necesidades! ¿Te gustaría una cotización personalizada? 😊",
        'costo': "¡Claro! Los costos dependen del producto y cantidad. ¿Para cuántos equipos necesitas protección?",
        'catálogo': "¡Tenemos un catálogo completo! ¿Te interesa conocer las opciones disponibles?",
        'catalogo': "¡Claro! Tenemos soluciones para todos los needs. ¿Qué tipo de protección buscas?",
        'opciones': "¡Tenemos varias opciones! ¿Es para uso personal o empresarial?",
        'contacto': "¡Perfecto! ¿Te gustaría que un especialista te contacte? 😊",
        'sí': "¡Excelente! Vamos a registrar tus datos para contactarte. 📞", 'si': "¡Excelente! Vamos a registrar tus datos para contactarte. 📞",
    }
    query_lower = query.lower()
    for key, response in quick_responses.items():
        if key in query_lower: return response
    return None

@st.cache_resource
def initialize_knowledge_base():
    embedding_model = load_embedding_model()
    chroma_client, collection = init_chroma_db()
    if collection.count() > 0: return True
    if not os.path.exists(DOCUMENTS_FOLDER): return False
    all_chunks, all_embeddings, all_metadata = [], [], []
    for pdf_filename in PDF_FILES:
        pdf_path = get_pdf_from_local(pdf_filename)
        if pdf_path and os.path.exists(pdf_path):
            text = extract_text_from_pdf(pdf_path)
            if text and len(text.strip()) > 100:
                chunks = split_text(text)
                for i, chunk in enumerate(chunks):
                    embedding = embedding_model.encode(chunk).tolist()
                    all_chunks.append(chunk)
                    all_embeddings.append(embedding)
                    all_metadata.append({"file_name": pdf_filename, "chunk_id": i, "total_chunks": len(chunks)})
    if all_chunks:
        collection.add(embeddings=all_embeddings, documents=all_chunks, metadatas=all_metadata, ids=[f"doc_{i}" for i in range(len(all_chunks))])
        return True
    else: return False

def main():
    query_params = st.experimental_get_query_params()
    if "admin" in query_params and query_params["admin"][0] == "eset2024":
        st.session_state.admin_authenticated = True
        st.session_state.show_admin = True
    if "awaiting_form" not in st.session_state: st.session_state.awaiting_form = False
    if "messages" not in st.session_state: st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Soy tu especialista en ventas de ESET. ¿En qué puedo ayudarte con nuestros productos de ciberseguridad?"}]
    if "last_query" not in st.session_state: st.session_state.last_query = ""
    if "admin_authenticated" not in st.session_state: st.session_state.admin_authenticated = False
    if "show_admin" not in st.session_state: st.session_state.show_admin = False
    if "uso_tokens" not in st.session_state: st.session_state.uso_tokens = []
    
    st.title("🤖 Asistente de Ventas ESET")
    st.markdown("### Especialista en productos de ciberseguridad")
    st.markdown("---")
    
    with st.sidebar:
        st.header("💬 Chat ESET")
        st.markdown("**¿En qué puedo ayudarte?**\n- Información sobre productos\n- Características y beneficios\n- Comparación de soluciones\n- Cotizaciones personalizadas\n*Escribe tu consulta en el chat*")
        st.divider()
        st.markdown("**📞 Contacto**\n📧 enzo@cice.ar")
        st.divider()
        st.markdown("**🔧 Estado del Sistema**")
        if st.session_state.get('admin_authenticated', False):
            st.divider()
            if st.button("📊 Panel de Control Admin"): st.session_state.show_admin = True

    initialize_knowledge_base()
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])
    
    if st.session_state.awaiting_form:
        st.markdown("---")
        st.subheader("📝 Formulario de Contacto Rápido")
        st.info("👇 **Solo tu teléfono es necesario** - Te contactaremos en menos de 24 horas")
        with st.form(key="contact_form_main", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                telefono = st.text_input("Teléfono*", placeholder="+54 11 1234-5678")
                nombre = st.text_input("Nombre (opcional)", placeholder="Ej: Juan Pérez")
                email = st.text_input("Email (opcional)", placeholder="juan@empresa.com")
            with col2:
                empresa = st.text_input("Empresa (opcional)", placeholder="Nombre de tu empresa")
                interes = st.selectbox("Principal interés (opcional)", ["No especificado", "ESET PROTECT Elite", "ESET PROTECT Enterprise", "ESET PROTECT Complete", "ESET PROTECT Advanced", "ESET PROTECT Entry", "Detección y Respuesta", "Seguridad para Endpoints", "Otro"], index=0)
            st.subheader("📋 Resumen de tu consulta")
            conversacion_texto = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages[-4:]])
            resumen_interes = generar_resumen_interes(conversacion_texto, interes)
            st.info(resumen_interes)
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1: submitted = st.form_submit_button("📞 ¡Que me llamen!", use_container_width=True)
            with col_btn2: cancelled = st.form_submit_button("❌ Cancelar", use_container_width=True)
            if cancelled:
                st.session_state.awaiting_form = False
                st.rerun()
            if submitted:
                if not telefono or not telefono.strip(): st.error("❌ Por favor ingresa tu teléfono")
                else:
                    form_data = {
                        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'nombre': nombre.strip() if nombre else "No especificado",
                        'email': email.strip().lower() if email else "No especificado",
                        'telefono': telefono.strip(), 'empresa': empresa.strip() if empresa else "No especificado",
                        'interes': interes, 'consulta_original': st.session_state.get('last_query', '')[:200],
                        'resumen_interes': resumen_interes
                    }
                    if guardar_lead_sheets(form_data):
                        st.success("✅ ¡Perfecto! Hemos recibido tus datos")
                        st.balloons()
                        if nombre and nombre.strip():
                            confirmation_msg = f"✅ ¡Gracias {nombre.strip()}!\n**Hemos registrado tu solicitud:**\n📞 **Teléfono:** {telefono}\nUn especialista te contactará en 24 horas. ¡Estamos aquí para ayudarte! 🚀"
                        else: confirmation_msg = f"✅ ¡Perfecto!\n**Hemos registrado tu solicitud:**\n📞 **Teléfono:** {telefono}\nUn especialista te contactará en 24 horas. ¡Estamos aquí para ayudarte! 🚀"
                        st.session_state.messages.append({"role": "assistant", "content": confirmation_msg})
                        st.session_state.awaiting_form = False
                        st.rerun()
                    else: st.error("❌ Error al guardar. Por favor intenta nuevamente.")
    
    if not st.session_state.awaiting_form:
        if prompt := st.chat_input("Escribe tu pregunta sobre productos ESET..."):
            st.session_state.last_query = prompt
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            shows_contact_interest = extract_contact_intent(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Buscando información..."):
                    try:
                        quick_response = generate_quick_response(prompt)
                        if quick_response: response_text = quick_response
                        else:
                            relevant_docs = search_similar_documents(prompt, top_k=3)
                            response_text = generate_contextual_response(prompt, relevant_docs)
                        st.markdown(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                        if shows_contact_interest:
                            st.markdown("---")
                            invitation_msg = "**¿Te gustaría que un especialista te contacte personalmente?**\n\nPodemos:\n- 📞 Llamarte para resolver tus dudas\n- ✉️ Enviarte una cotización detallada\n- 🎯 Asesorarte según tus necesidades\n\n**Solo dime \"sí\" o escribe \"contacto\".** 😊"
                            st.markdown(invitation_msg)
                            st.session_state.messages.append({"role": "assistant", "content": invitation_msg})
                        elif any(word in prompt.lower() for word in ['precio', 'costo', 'cotiz', 'catálogo', 'catalogo']):
                            st.info("💡 **¿Te interesa una cotización personalizada?** Solo dime *sí* 📞")
                    except Exception as e:
                        error_msg = "¡Te recomiendo contactar a nuestro equipo para la mejor atención! 📞"
                        st.markdown(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    if st.session_state.get('show_admin', False): mostrar_dashboard_admin()

if __name__ == "__main__":
    main()
