# src/services/google_sheets_service.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from src.config.settings import GOOGLE_SHEETS_SCOPE, SHEET_NAME

def setup_google_sheets():
    """Configurar conexión con Google Sheets"""
    try:
        credentials_dict = st.secrets["google_sheets"]
        creds = Credentials.from_service_account_info(credentials_dict, scopes=GOOGLE_SHEETS_SCOPE)
        client = gspread.authorize(creds)
        st.sidebar.success("✅ Google Sheets configurado")
        return client
    except Exception as e:
        st.sidebar.error(f"❌ Error Google Sheets: {e}")
        return None

def get_leads_sheet(client):
    """Obtener o crear la hoja de leads"""
    try:
        sheet = client.open(SHEET_NAME).sheet1
        st.sidebar.success("✅ Conectado a Google Sheets")
        return sheet
    except gspread.SpreadsheetNotFound:
        try:
            sheet = client.create(SHEET_NAME)
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