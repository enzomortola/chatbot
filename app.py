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

ADMIN_PASSWORD = "eset_admin_ciceEnzo"  # Agregar esta línea

def mostrar_dashboard_admin():
    st.title("🔧 Dashboard de Administración - ESET")
    st.markdown("---")
    
    # Métricas de uso
    if "uso_tokens" in st.session_state and st.session_state.uso_tokens:
        datos = st.session_state.uso_tokens
        
        total_tokens = sum([x['total_tokens'] for x in datos])
        total_consultas = len(datos)
        avg_tokens = total_tokens / total_consultas if total_consultas > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Consultas", total_consultas)
        col2.metric("Total Tokens", f"{total_tokens:,}")
        col3.metric("Promedio Tokens/Consulta", f"{avg_tokens:.0f}")
        
        # Últimas consultas
        st.subheader("📊 Últimas Consultas")
        if len(datos) > 0:
            df = pd.DataFrame(datos[-10:])  # Últimas 10
            st.dataframe(df[['prompt_tokens', 'completion_tokens', 'total_tokens', 'modelo']])
    
    # Estadísticas de conversación
    st.subheader("💬 Estadísticas de Chat")
    if "messages" in st.session_state:
        total_mensajes = len(st.session_state.messages)
        mensajes_usuario = len([m for m in st.session_state.messages if m["role"] == "user"])
        mensajes_asistente = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Mensajes", total_mensajes)
        col2.metric("Mensajes Usuario", mensajes_usuario)
        col3.metric("Mensajes Asistente", mensajes_asistente)
    
    # Configuración
    st.subheader("⚙️ Configuración Actual")
    st.info(f"**Modelo:** google/gemini-2.0-flash-exp:free")
    st.info(f"**Límite tokens/respuesta:** 1,024")
    st.info(f"**PDFs cargados:** {len(PDF_FILES)}")
    
    # Botón para limpiar datos
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

# Configuración de rutas de documentos
DOCUMENTS_FOLDER = "documentos"

# Lista de PDFs en la carpeta local (sin URLs)
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

# Palabras clave para detectar interés en contacto
CONTACT_KEYWORDS = [
    'contacto', 'contactarme', 'dejar mis datos', 'llámenme', 'escribanme',
    'quiero que me contacten', 'datos de contacto', 'hablar con un ejecutivo',
    'asesor comercial', 'agendar reunión', 'cotización', 'presupuesto', 'me interesa'
]

# ===========================
# CLIENTE OPENROUTER
# ===========================

class OpenRouterClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://asistente-eset.streamlit.app",
            "X-Title": "Asistente ESET"
        }

    def generate_content(self, prompt):
        """Generar contenido usando OpenRouter API"""
        try:
            payload = {
                "model": "google/gemini-2.0-flash-exp:free",  # Modelo gratuito
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            response = requests.post(
                self.base_url, 
                headers=self.headers, 
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_msg = f"❌ Error OpenRouter: {response.status_code}"
                if response.status_code == 402:
                    error_msg += " - Límite alcanzado"
                elif response.status_code == 429:
                    error_msg += " - Demasiadas solicitudes"
                st.sidebar.error(error_msg)
                return "Lo siento, hubo un error temporal. Por favor, intenta nuevamente en un momento."
                
        except requests.exceptions.Timeout:
            st.sidebar.error("❌ Timeout en OpenRouter")
            return "El servicio está respondiendo lentamente. Por favor, intenta nuevamente."
        except Exception as e:
            st.sidebar.error(f"❌ Excepción OpenRouter: {e}")
            return "En este momento tengo dificultades técnicas. Por favor, intenta nuevamente o escribe 'quiero contacto' para hablar con un especialista."

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
# FUNCIONES DE MODELO CON DEBUG
# ===========================

@st.cache_resource
def load_embedding_model():
    st.sidebar.info("🔄 Cargando modelo de embeddings...")
    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

@st.cache_resource
def load_openrouter_model():
    """Cargar cliente de OpenRouter"""
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
        client = OpenRouterClient(api_key)
        st.sidebar.success("✅ OpenRouter configurado")
        return client
    except Exception as e:
        st.sidebar.error(f"❌ Error configurando OpenRouter: {e}")
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
        model = load_openrouter_model()
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
# FUNCIONES PDF CON DEBUG
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
        model = load_openrouter_model()
        if not model:
            return f"Como especialista en ESET, puedo ayudarte con información sobre nuestros productos de ciberseguridad. Para tu pregunta sobre '{query}', te recomiendo contactar con nuestro equipo de ventas."
        
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
        return f"Como especialista en ESET, puedo ayudarte con información sobre nuestros productos de ciberseguridad. Para tu pregunta sobre '{query}', te recomiendo contactar con nuestro equipo de ventas."

@st.cache_resource
def initialize_knowledge_base():
    """Carga PDFs desde carpeta local y crea la base de conocimiento"""
    st.sidebar.info("🔄 Inicializando base de conocimiento...")
    
    embedding_model = load_embedding_model()
    chroma_client, collection = init_chroma_db()
    
    # Verificar si ya existe data
    if collection.count() > 0:
        st.sidebar.success(f"✅ Base lista: {collection.count()} fragmentos")
        return True
    
    # Verificar carpeta de documentos
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
    
    # Interfaz limpia y profesional
    st.title("🤖 Asistente de Ventas ESET")
    st.markdown("### Especialista en productos de ciberseguridad")
    st.markdown("---")
    
    # Sidebar con información para el cliente Y debug
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
        
        # ==== BOTÓN SOLO PARA TI (cuando accedes por URL secreta) ====
        if st.session_state.get('admin_authenticated', False):
            st.divider()
            if st.button("📊 Panel de Control Admin"):
                st.session_state.show_admin = True

    # Inicializar base de conocimiento CON DEBUG
    knowledge_loaded = initialize_knowledge_base()
    
    # Inicializar session state
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "¡Hola! Soy tu especialista en ventas de ESET. ¿En qué puedo ayudarte con nuestros productos de ciberseguridad?"}
        ]
    
    if "awaiting_form" not in st.session_state:
        st.session_state.awaiting_form = False
    
    # Mostrar historial de mensajes
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # MOSTRAR FORMULARIO SI ESTÁ ACTIVO
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
            
            # Mostrar resumen de la conversación
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
                # Validaciones
                if not nombre or not email or not telefono:
                    st.error("❌ Por favor completa todos los campos obligatorios (*)")
                elif interes == "Selecciona una opción":
                    st.error("❌ Por favor selecciona tu interés principal")
                elif "@" not in email or "." not in email:
                    st.error("❌ Por favor ingresa un email válido")
                else:
                    # Preparar datos
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
                    
                    # Guardar SOLO en Google Sheets
                    if guardar_lead_sheets(form_data):
                        st.success("✅ ¡Datos enviados correctamente!")
                        st.balloons()
                        
                        # Agregar mensaje de confirmación
                        confirmation_msg = f"""✅ ¡Perfecto {nombre}! He registrado tus datos de contacto. 

**Resumen de tu interés:**
{resumen_interes}

Un especialista de ESET te contactará en las próximas 24 horas para:
- ✅ Analizar tus necesidades específicas
- ✅ Proporcionarte una demostración personalizada  
- ✅ Entregarte una cotización detallada

¡Estamos aquí para ayudarte! 🚀"""
                        
                        st.session_state.messages.append({"role": "assistant", "content": confirmation_msg})
                        
                        # Desactivar formulario
                        st.session_state.awaiting_form = False
                        
                        # Recargar después de enviar
                        st.rerun()
                    else:
                        st.error("❌ Hubo un error al guardar tus datos. Por favor intenta nuevamente.")
    
    # Input del usuario - SOLO si NO hay formulario activo
    if not st.session_state.awaiting_form:
        if prompt := st.chat_input("Escribe tu pregunta sobre productos ESET..."):
            # Guardar último query
            st.session_state.last_query = prompt
            
            # Agregar mensaje del usuario
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Mostrar mensaje del usuario inmediatamente
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Verificar intención de contacto
            is_contact_intent = extract_contact_intent(prompt)
            
            if is_contact_intent:
                # Activar formulario
                contact_response = """¡Excelente! Veo que estás interesado en nuestros productos de ESET. 

Para ofrecerte la mejor atención personalizada y una cotización adaptada a tus necesidades, me gustaría contar con algunos datos.

**Por favor completa el formulario que aparece a continuación** 👇

Un especialista se pondrá en contacto contigo en un máximo de 24 horas para:
- ✅ Analizar tus necesidades específicas
- ✅ Proporcionarte una demostración personalizada  
- ✅ Entregarte una cotización detallada

¡Estamos aquí para ayudarte! 🚀"""
                
                st.session_state.messages.append({"role": "assistant", "content": contact_response})
                
                # Mostrar respuesta del asistente inmediatamente
                with st.chat_message("assistant"):
                    st.markdown(contact_response)
                
                st.session_state.awaiting_form = True
                
                # Recargar para mostrar el formulario
                st.rerun()
            
            else:
                # Búsqueda normal
                with st.chat_message("assistant"):
                    with st.spinner("Buscando información..."):
                        try:
                            relevant_docs = search_similar_documents(prompt, top_k=5)
                            response = generate_contextual_response(prompt, relevant_docs)
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            
                            # Sugerir contacto si es relevante
                            if any(word in prompt.lower() for word in ['precio', 'costo', 'cotiz', 'compra', 'licencia', 'demo']):
                                st.info("💡 **¿Te interesa una cotización personalizada?** Escribe 'quiero dejar mis datos' y te ayudo con el proceso.")
                        
                        except Exception as e:
                            error_msg = f"En este momento tengo dificultades técnicas. Para tu pregunta sobre '{prompt}', te recomiendo escribir 'quiero contacto' para que un especialista te atienda personalmente."
                            st.markdown(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})

    # MOSTRAR DASHBOARD ADMIN SOLO SI ESTÁ ACTIVADO
    if st.session_state.get('show_admin', False):
        mostrar_dashboard_admin()

if __name__ == "__main__":
    main()
