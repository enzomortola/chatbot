# src/models/gemini_client.py
import google.generativeai as genai
import streamlit as st
from src.config.settings import GEMINI_MODEL, MAX_TOKENS

class GeminiClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model_name = GEMINI_MODEL
        self.model = None
        self.configure_client()
    
    def configure_client(self):
        """Configurar el cliente de Gemini"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            st.sidebar.success(f"✅ Gemini cargado: {self.model_name}")
        except Exception as e:
            st.sidebar.error(f"❌ Error configurando Gemini: {e}")
            self.model = None
    
    def generate_content(self, prompt, max_words=None):
        """Generar contenido usando Gemini con límite de palabras"""
        try:
            if not self.model:
                return "🔧 El modelo Gemini no está disponible. Por favor, contacta al administrador.", None
            
            # Agregar límite de palabras al prompt si se especificó
            if max_words:
                prompt += f"\n\nIMPORTANTE: Responde en MÁXIMO {max_words} palabras. Sé conciso y directo."
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=MAX_TOKENS,
                    temperature=0.7
                )
            )
            
            respuesta_final = response.text
            
            # Contar palabras para mostrar en el sidebar
            word_count = len(respuesta_final.split())
            st.sidebar.info(f"📝 Palabras en respuesta: {word_count}/{max_words or '∞'}")
            
            return respuesta_final, None  # Para compatibilidad con el código actual
            
        except Exception as e:
            st.sidebar.error(f"❌ Error con Gemini: {e}")
            return "⚠️ Error temporal. Por favor, intenta nuevamente o escribe 'quiero contacto'.", None