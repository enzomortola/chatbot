# src/models/gemini_client.py
import google.generativeai as genai
import streamlit as st
from src.config.settings import GEMINI_MODEL, MAX_TOKENS
from src.utils.token_calculator import calcular_tokens_y_costo

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
    
    def generate_content(self, prompt):
        """Generar contenido usando Gemini y devolver respuesta + uso"""
        try:
            if not self.model:
                return "🔧 El modelo Gemini no está disponible. Por favor, contacta al administrador.", None
            
            # Generar respuesta
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=MAX_TOKENS,
                    temperature=0.7
                )
            )
            respuesta_final = response.text
            
            # Calcular tokens usados
            uso = calcular_tokens_y_costo(prompt, respuesta_final, self.model_name)
            
            return respuesta_final, uso
            
        except Exception as e:
            st.sidebar.error(f"❌ Error con Gemini: {e}")
            error_msg = "⚠️ Error temporal con Gemini 2.0. Por favor, intenta nuevamente o escribe 'quiero contacto' para hablar con un especialista."
            return error_msg, None