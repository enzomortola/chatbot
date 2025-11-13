# setup_kb.py - VERSIÓN FINAL
import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Cargar secrets manualmente para setup
def load_secrets_for_setup():
    """Cargar secrets desde archivo para ejecutar fuera de Streamlit"""
    secrets_path = os.path.join(PROJECT_ROOT, ".streamlit", "secrets.toml")
    secrets = {}
    
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            content = f.read()
            # Parse simple de TOML (para este caso básico)
            for line in content.splitlines():
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    secrets[key.strip()] = value.strip().strip('"')
    return secrets

# Mock secrets para setup
secrets = load_secrets_for_setup()
GEMINI_API_KEY = secrets.get("GEMINI_API_KEY", "")

# Reemplazar la función get_secret temporalmente
import src.config.settings as settings
settings.GEMINI_API_KEY = GEMINI_API_KEY
settings.get_secret = lambda key, default=None: secrets.get(key, default)

# Ahora importar los módulos
from src.services.chroma_service import init_chroma_db
from src.services.pdf_processor import get_pdf_path, extract_text_from_pdf, split_text
from src.config.pdf_manifest import PDF_FILES
from src.models.embedding_model import load_embedding_model

def print_log(msg, level="info"):
    """Función para imprimir sin Streamlit"""
    if level == "info":
        print(f"ℹ️ {msg}")
    elif level == "success":
        print(f"✅ {msg}")
    elif level == "error":
        print(f"❌ {msg}")

def main():
    print_log("Inicializando base de conocimiento...")
    
    embedding_model = load_embedding_model()
    chroma_client, collection = init_chroma_db()
    
    if not collection:
        print_log("No se pudo inicializar la base de datos", "error")
        return
    
    if collection.count() > 0:
        print_log(f"Base ya existe: {collection.count()} fragmentos")
        print_log("Si quieres recrearla, borra la carpeta 'chroma_db_drive' y ejecuta de nuevo.")
        return
    
    all_chunks = []
    all_embeddings = []
    all_metadata = []
    processed_files = 0
    
    for pdf_filename in PDF_FILES:
        pdf_path = get_pdf_path(pdf_filename)
        if pdf_path and os.path.exists(pdf_path):
            print_log(f"Procesando: {pdf_filename}...")
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
                print_log(f"Procesado: {pdf_filename} ({len(chunks)} chunks)", "success")
            else:
                print_log(f"Texto insuficiente: {pdf_filename}", "error")
        else:
            print_log(f"No encontrado: {pdf_path}", "error")
    
    if all_chunks:
        collection.add(
            embeddings=all_embeddings,
            documents=all_chunks,
            metadatas=all_metadata,
            ids=[f"doc_{i}" for i in range(len(all_chunks))]
        )
        print_log(f"Base creada: {processed_files} PDFs, {len(all_chunks)} fragmentos", "success")
    else:
        print_log("No se pudo crear la base de conocimiento", "error")

if __name__ == "__main__":
    main()