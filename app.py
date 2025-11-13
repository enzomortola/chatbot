import streamlit as st
import requests
import json
import os
import re
from PyPDF2 import PdfReader
import google.generativeai as genai
import chromadb
from chromadb.config import Settings
import numpy as np
import datetime
import pandas as pd
from pathlib import Path
import io
import gspread
from google.oauth2.service_account import Credentials
import unicodedata

ADMIN_PASSWORD = "eset_admin_ciceEnzo"
MAX_TOKENS = 500

def calcular_tokens_y_costo(prompt, response, model_used):
    """
    Estimar tokens usados y costo aproximado
    """
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
        st.info("📝 Aún no hay datos de consultas. Realiza algunas preguntas en el chat.")
    
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
    st.info(f"**Modelo:** gemini-2.0-flash-exp")
    st.info(f"**Límite tokens/respuesta:** {MAX_TOKENS}")
    st.info(f"**PDFs cargados:** {len(PDF_FILES)}")
    
    if st.button("🗑️ Limpiar Métricas", type="secondary"):
        if "uso_tokens" in st.session_state:
            st.session_state.uso_tokens = []
        st.rerun()

# Configurar página
st.set_page_config(
    page_title="Asistente de Ventas ESET",
    page_icon="🤖",
    layout="wide"
)

DOCUMENTS_FOLDER = "documentos"

PDF_FILES = [
    "ESET_DRA_Service_Specification.pdf",
    "ESET_PROTECT_Elite_brochure-ES.pdf", 
    "ESET_PROTECT_Enterprise_brochure-ES.pdf",
    "ESET_PSE_Service_Specification.pdf",
    "How-to-Win-Friends-and-Influence-People-Dale-Carnegie_-editorial-consultant_-Dorothy-Carnegie_-_-WeL.pdf", 
    "INSTRUCCIONES DE COMPORTAMIENTO GENERALES.pdf",
    "Objections-The-Ultimate-Guide-for-Mastering-The-Art-and-Blount_-Jeb_-Hunter_-Mark-_-WeLib.org-_.pdf", 
    "Overview-ESET-PROTECT-Advanced.pdf", 
    "Overview-ESET-PROTECT-Complete.pdf",
    "Overview-ESET-PROTECT-Entry.pdf",
    "Thank You for Arguing - What Aristotle, Lincoln, and Homer -- Heinrichs, Jay -- ( WeLib.org ).pdf",
    "The Psychology of Selling - Increase Your Sales Faster and -- Brian Tracy -- ( WeLib.org ).pdf"
]

CONTACT_KEYWORDS = [
    'contacto', 'contactarme', 'dejar mis datos', 'llámenme', 'escribanme',
    'quiero que me contacten', 'datos de contacto', 'hablar con un ejecutivo',
    'asesor comercial', 'agendar reunión', 'cotización', 'presupuesto', 'me interesa'
]

# ===========================
# CLIENTE GEMINI 2.0 FLASH
# ===========================

class GeminiClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model_name = "gemini-2.0-flash-exp"
        self.configure_client()
        
    def configure_client(self):
        """Configurar el cliente de Gemini 2.0"""
        try:
            genai.configure(api_key=self.api_key)
            
            # Verificar modelos disponibles
            models = genai.list_models()
            available_models = [model.name for model in models]
            
            st.sidebar.info(f"🔍 Buscando modelo: {self.model_name}")
            
            # Buscar específicamente el modelo 2.0
            target_model = f"models/{self.model_name}"
            if target_model in available_models:
                self.model = genai.GenerativeModel(self.model_name)
                st.sidebar.success(f"✅ Gemini 2.0 Flash cargado: {self.model_name}")
            else:
                available_flash = [m for m in available_models if 'flash' in m.lower()]
                st.sidebar.error(f"❌ Modelo {self.model_name} no disponible")
                st.sidebar.info(f"📋 Modelos Flash disponibles: {[m.split('/')[-1] for m in available_flash]}")
                self.model = None
                return
                
        except Exception as e:
            st.sidebar.error(f"❌ Error configurando Gemini 2.0: {e}")
            self.model = None

    def generate_content(self, prompt):
        """Generar contenido usando Gemini 2.0 Flash"""
        try:
            if not self.model:
                return "🔧 El modelo Gemini 2.0 Flash no está disponible en este momento. Por favor, contacta al administrador."
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=MAX_TOKENS,
                    temperature=0.7
                )
            )
            
            respuesta_final = response.text
            
            # Guardar tokens usados
            uso = calcular_tokens_y_costo(prompt, respuesta_final, self.model_name)
            
            if "uso_tokens" not in st.session_state:
                st.session_state.uso_tokens = []
            
            st.session_state.uso_tokens.append(uso)
            
            return respuesta_final
            
        except Exception as e:
            st.sidebar.error(f"❌ Error Gemini 2.0: {e}")
            return "⚠️ Lo siento, hubo un error con el modelo Gemini 2.0. Por favor, intenta nuevamente o contacta al administrador."

# ===========================
# FUNCIONES GOOGLE SHEETS
# ===========================

def setup_google_sheets():
    """Configurar conexión con Google Sheets"""
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials_dict = st.secrets["google_sheets"]
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.sidebar.error(f"❌ Error Google Sheets: {e}")
        return None

def get_leads_sheet(client, sheet_name="leads_eset"):
    """Obtener o crear la hoja de leads"""
    try:
        sheet = client.open(sheet_name).sheet1
        st.sidebar.success("✅ Conectado a Google Sheets")
        return sheet
    except gspread.SpreadsheetNotFound:
        try:
            sheet = client.create(sheet_name)
            worksheet = sheet.sheet1
            headers = ["timestamp", "nombre", "email", "telefono", "empresa", "interes", "consulta_original", "resumen_interes"]
            worksheet.append_row(headers)
            st.sidebar.success("✅ Nueva hoja creada en Google Sheets")
            return worksheet
        except Exception as e:
            st.sidebar.error(f"❌ Error creando hoja: {e}")
            return None
    except Exception as e:
        st.sidebar.error(f"❌ Error accediendo a Google Sheets: {e}")
        return None

def guardar_lead_sheets(form_data):
    """Guardar lead en Google Sheets"""
    try:
        client = setup_google_sheets()
        if not client:
            return False
        
        sheet = get_leads_sheet(client)
        if not sheet:
            return False
        
        row = [
            form_data['timestamp'],
            form_data['nombre'],
            form_data['email'],
            form_data['telefono'],
            form_data['empresa'],
            form_data['interes'],
            form_data['consulta_original'],
            form_data['resumen_interes']
        ]
        
        sheet.append_row(row)
        st.sidebar.success("✅ Lead guardado en Google Sheets")
        return True
        
    except Exception as e:
        st.sidebar.error(f"❌ Error guardando lead: {e}")
        return False

# ===========================
# FUNCIONES DE EMBEDDINGS Y BASE DE DATOS
# ===========================

from sentence_transformers import SentenceTransformer

@st.cache_resource
def load_embedding_model():
    st.sidebar.info("🔄 Cargando modelo de embeddings...")
    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

@st.cache_resource
def load_gemini_model():
    """Cargar cliente de Gemini 2.0"""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = GeminiClient(api_key)
        return client
    except Exception as e:
        st.sidebar.error(f"❌ Error configurando Gemini 2.0: {e}")
        return None

@st.cache_resource
def init_chroma_db():
    client = chromadb.Client(Settings(
        persist_directory="./chroma_db_drive",
        is_persistent=True
    ))
    
    try:
        collection = client.get_collection("drive_documents")
        st.sidebar.success(f"✅ DB cargada: {collection.count()} fragmentos")
    except:
        collection = client.create_collection("drive_documents")
        st.sidebar.info("🆕 Nueva base de datos creada")
    
    return client, collection

def extract_contact_intent(message):
    """Detectar si el usuario quiere dejar datos de contacto"""
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in CONTACT_KEYWORDS)

def generar_resumen_interes(historial_conversacion, interes_seleccionado):
    """Generar un resumen de lo que el cliente está interesado en comprar"""
    try:
        model = load_gemini_model()
        if not model:
            return f"Cliente interesado en {interes_seleccionado}. Conversación: {historial_conversacion[-500:]}"
        
        prompt = f"""
        Eres un asistente de ventas de ESET. Analiza la siguiente conversación y genera un resumen conciso 
        (máximo 150 palabras) sobre los intereses específicos del cliente en productos ESET.
        
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
        
        response = model.generate_content(prompt)
        return response.strip()
        
    except Exception as e:
        st.sidebar.error(f"❌ Error generando resumen: {e}")
        return f"Cliente interesado en {interes_seleccionado}. Conversación: {historial_conversacion[-500:]}"

# ===========================
# FUNCIONES PDF
# ===========================

def get_pdf_from_local(filename):
    """Obtener ruta del PDF desde la carpeta local"""
    pdf_path = os.path.join(DOCUMENTS_FOLDER, filename)
    if os.path.exists(pdf_path):
        return pdf_path
    else:
        st.sidebar.error(f"❌ No encontrado: {filename}")
        return None

def extract_text_from_pdf(pdf_path):
    try:
        pdf_reader = PdfReader(pdf_path, strict=False)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text if text.strip() else None
    except Exception as e:
        st.sidebar.error(f"❌ Error leyendo PDF: {e}")
        return None

def split_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def search_similar_documents(query, top_k=5):
    try:
        embedding_model = load_embedding_model()
        chroma_client, collection = init_chroma_db()
        
        st.sidebar.info(f"🔍 Buscando: '{query}'")
        
        query_embedding = embedding_model.encode(query).tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        documentos_encontrados = len(results['documents'][0]) if results['documents'] else 0
        st.sidebar.info(f"📄 Encontrados: {documentos_encontrados} documentos")
        
        return results['documents'][0] if results['documents'] else []
    except Exception as e:
        st.sidebar.error(f"❌ Error en búsqueda: {e}")
        return []

def generate_contextual_response(query, context_documents):
    try:
        model = load_gemini_model()
        if not model:
            return "🔧 El modelo Gemini 2.0 no está disponible en este momento. Por favor, escribe 'quiero contacto' para hablar con un especialista humano."
        
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
        
        response = model.generate_content(prompt)
        return response
        
    except Exception as e:
        st.sidebar.error(f"❌ Error generando respuesta: {e}")
        return "⚠️ Error temporal con Gemini 2.0. Por favor, intenta nuevamente o escribe 'quiero contacto' para hablar con un especialista."

@st.cache_resource
def initialize_knowledge_base():
    """Carga PDFs desde carpeta local y crea la base de conocimiento"""
    st.sidebar.info("🔄 Inicializando base de conocimiento...")
    
    embedding_model = load_embedding_model()
    chroma_client, collection = init_chroma_db()
    
    if collection.count() > 0:
        st.sidebar.success(f"✅ Base lista: {collection.count()} fragmentos")
        return True
    
    if not os.path.exists(DOCUMENTS_FOLDER):
        st.sidebar.error(f"❌ No existe carpeta: {DOCUMENTS_FOLDER}")
        return False
    
    archivos_encontrados = os.listdir(DOCUMENTS_FOLDER)
    st.sidebar.info(f"📁 Archivos en carpeta: {len(archivos_encontrados)}")
    
    all_chunks = []
    all_embeddings = []
    all_metadata = []
    processed_files = 0
    
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
                    all_metadata.append({
                        "file_name": pdf_filename,
                        "chunk_id": i,
                        "total_chunks": len(chunks)
                    })
                
                processed_files += 1
                st.sidebar.success(f"✅ Procesado: {pdf_filename}")
            else:
                st.sidebar.warning(f"⚠️ Texto insuficiente: {pdf_filename}")
        else:
            st.sidebar.error(f"❌ No encontrado: {pdf_filename}")
    
    if all_chunks:
        collection.add(
            embeddings=all_embeddings,
            documents=all_chunks,
            metadatas=all_metadata,
            ids=[f"doc_{i}" for i in range(len(all_chunks))]
        )
        st.sidebar.success(f"🎉 Base creada: {processed_files} PDFs, {len(all_chunks)} fragmentos")
        return True
    else:
        st.sidebar.error("❌ No se pudo crear la base de conocimiento")
        return False

# ===========================
# INTERFAZ PRINCIPAL
# ===========================

def main():
    query_params = st.experimental_get_query_params()
    if "admin" in query_params and query_params["admin"][0] == "eset2024":
        st.session_state.admin_authenticated = True
        st.session_state.show_admin = True
    
    st.title("🤖 Asistente de Ventas ESET")
    st.markdown("### Especialista en productos de ciberseguridad")
    st.markdown("---")
    
    with st.sidebar:
        st.header("💬 Chat ESET")
        st.markdown("""
        **¿En qué puedo ayudarte?**
        
        - Información sobre productos
        - Características y beneficios
        - Comparación de soluciones
        - Cotizaciones personalizadas
        
        *Escribe tu consulta en el chat*
        """)
        
        st.divider()
        st.markdown("**📞 Contacto**")
        st.markdown("""
        ¿Prefieres hablar con un especialista?
        
        📧 enzo@cice.ar
        """)
        
        st.divider()
        st.markdown("**🔧 Estado del Sistema**")
        
        if st.session_state.get('admin_authenticated', False):
            st.divider()
            if st.button("📊 Panel de Control Admin"):
                st.session_state.show_admin = True

    initialize_knowledge_base()
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "¡Hola! Soy tu especialista en ventas de ESET. ¿En qué puedo ayudarte con nuestros productos de ciberseguridad?"}
        ]
    
    if "awaiting_form" not in st.session_state:
        st.session_state.awaiting_form = False
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if st.session_state.awaiting_form:
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
                    ["Selecciona una opción", "ESET PROTECT Elite", "ESET PROTECT Enterprise", 
                     "ESET PROTECT Complete", "ESET PROTECT Advanced", "ESET PROTECT Entry", 
                     "Detección y Respuesta", "Seguridad para Endpoints", "Otro"],
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
                elif "@" not in email or "." not in email:
                    st.error("❌ Por favor ingresa un email válido")
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

Un especialista de ESET te contactará en las próximas 24 horas para:
- ✅ Analizar tus necesidades específicas
- ✅ Proporcionarte una demostración personalizada  
- ✅ Entregarte una cotización detallada

¡Estamos aquí para ayudarte! 🚀"""
                        
                        st.session_state.messages.append({"role": "assistant", "content": confirmation_msg})
                        st.session_state.awaiting_form = False
                        st.rerun()
                    else:
                        st.error("❌ Hubo un error al guardar tus datos. Por favor intenta nuevamente.")
    
    if not st.session_state.awaiting_form:
        if prompt := st.chat_input("Escribe tu pregunta sobre productos ESET..."):
            st.session_state.last_query = prompt
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
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
                
                st.session_state.messages.append({"role": "assistant", "content": contact_response})
                
                with st.chat_message("assistant"):
                    st.markdown(contact_response)
                
                st.session_state.awaiting_form = True
                st.rerun()
            
            else:
                with st.chat_message("assistant"):
                    with st.spinner("Buscando información..."):
                        try:
                            relevant_docs = search_similar_documents(prompt, top_k=5)
                            response = generate_contextual_response(prompt, relevant_docs)
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            
                            if any(word in prompt.lower() for word in [ 'precio', 'costo', 'cotiz', 'compra', 'licencia', 'demo', 'contratar', 'adquirir', 'comprar', 'venta', 
    'vendedor', 'comercial', 'asesor', 'me gustaría que me contacten', 'quisiera que me llamen', 
    'necesito hablar con alguien', 'busco asesoramiento', 'quiero dejar mis datos para', 'deseo que me cotizen',
    'me pueden asesorar', 'necesito una cotización', 'estoy buscando precios', 'quiero información sobre precios', 
    'me interesa el producto', 'deseo adquirir el servicio', 'presupuesto', 'tarifa', 'pago', 'mensual', 'anual', 
    'plan', 'precios', 'costos', 'cuanto cuesta', 'valor', 'precio final', 'oferta', 'promocion', 'descuento', 
    'caracteristicas', 'especificaciones', 'funciones', 'beneficios', 'comparar', 'vs', 'versus', 'diferencia', 
    'mejor', 'recomendar', 'que me conviene', 'intención de contacto', 'quiero hablar con un representante', 
    'me pueden contactar', 'me gustaría recibir más información', 'quiero comunicarme', 'quiero contacto', 
    'me pueden llamar', 'quiero hablar con un asesor', 'cómo me contacto', 'necesito asistencia', 
    'requiero atención personalizada', 'quiero que me atiendan', 'pueden comunicarse conmigo',
    'me gustaría coordinar una llamada', 'contacto comercial', 'formulario de contacto', 'cotización', 
    'solicitar cotización', 'precio actualizado', 'lista de precios', 'tabla de precios', 'cuánto vale', 
    'me pasan el precio', 'me pueden cotizar', 'cuánto sale', 'me interesa comprar', 'quiero comprar', 
    'cómo pago', 'formas de pago', 'tarifa mensual', 'plan anual', 'precio unitario', 'precio total', 
    'modo de pago', 'pago con tarjeta', 'transferencia', 'cuotas', 'facturación', 'factura', 'recibo', 
    'comprar ahora', 'adquisición', 'comparación', 'comparar con', 'diferencias con', 'qué incluye', 'ventajas', 
    'desventajas', 'beneficios', 'funcionalidades', 'rendimiento', 'características técnicas', 'es la mejor opción', 
    'qué recomiendan', 'qué conviene', 'qué diferencia hay', 'mejor plan', 'más conveniente', 'alternativas', 
    'recomendación', 'review', 'opiniones', 'quiero información', 'me gustaría saber más', 'necesito detalles', 
    'más info', 'cómo funciona', 'de qué se trata', 'documentación', 'brochure', 'ficha técnica', 'manual', 
    'guía', 'tutorial', 'instrucciones', 'folleto', 'catálogo']):
                                st.info("💡 **¿Te interesa una cotización personalizada?** Escribe 'quiero dejar mis datos' y te ayudo con el proceso.")
                        
                        except Exception as e:
                            error_msg = f"En este momento tengo dificultades técnicas. Para tu pregunta sobre '{prompt}', te recomiendo escribir 'quiero contacto' para que un especialista te atienda personalmente."
                            st.markdown(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})

    if st.session_state.get('show_admin', False):
        mostrar_dashboard_admin()

if __name__ == "__main__":
    main()



