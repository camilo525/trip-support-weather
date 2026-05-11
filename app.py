import streamlit as st
import requests
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Flight Support Team Weather Tool", page_icon="✈️", layout="wide")

# --- FORZAR MODO OSCURO TOTAL (BLACK BACKGROUND) ---
st.markdown("""
    <style>
    /* Fondo negro absoluto para toda la aplicación */
    .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }
    
    /* Forzar que todos los textos sean blancos */
    .stMarkdown, p, h1, h2, h3, h4, span, label, .stSelectbox, .stTextInput {
        color: #FFFFFF !important;
    }

    /* Estilo de los campos de entrada (Input Boxes) */
    input {
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
    }

    /* Estilo de la Sidebar (Barra Lateral) en negro */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #222222;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* Botón Principal estilo Aeronáutico */
    .stButton>button {
        background-color: #004a99 !important;
        color: white !important;
        font-weight: bold;
        width: 100%;
        border-radius: 8px;
        border: 1px solid #005fcc;
        height: 3.5em;
        text-transform: uppercase;
    }
    
    /* Caja de reporte del cliente */
    .main-card {
        padding: 25px;
        border-radius: 12px;
        background-color: #111111 !important;
        border: 1px solid #222222;
        color: #e0e0e0 !important;
    }

    /* Contenedor del Logo Inferior */
    .footer-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        padding: 50px 0px;
        margin-top: 50px;
        border-top: 1px solid #222222;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ESPACIOS PARA TUS LOGOS ---
# REEMPLAZA LOS LINKS ENTRE COMILLAS CON TUS ENLACES DIRECTOS (IMG BB O GITHUB)
LOGO_UP_LEFT = "TU_LINK_DE_LOGO_SUPERIOR_AQUI" 
LOGO_BOTTOM_CENTER = "TU_LINK_DE_LOGO_INFERIOR_AQUI"

API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# 2. ENCABEZADO CON LOGO SUPERIOR IZQUIERDO
col_logo, col_title = st.columns([1, 8])
with col_logo:
    # Si el link no ha sido cambiado, mostramos un placeholder de avión
    if LOGO_UP_LEFT == "TU_LINK_DE_LOGO_SUPERIOR_AQUI":
        st.write("✈️") 
    else:
        st.image(LOGO_UP_LEFT, width=100)

with col_title:
    st.title("Flight Support Team Weather Tool")

st.markdown("---")

# 3. SIDEBAR (CONFIGURACIÓN)
st.sidebar.title("✈️ FST Dispatcher")
origin = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
etd = st.sidebar.text_input("ETD (UTC)", value="1200")
destination = st.sidebar.text_input("ARRIVAL ICAO",
