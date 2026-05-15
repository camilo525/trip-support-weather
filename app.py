import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ops Assessment Tool", page_icon="✈️", layout="wide")

# --- DISEÑO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    .header-style {
        font-size: 26px; font-weight: bold;
        background: -webkit-linear-gradient(#00d4ff, #005fcc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .airport-label { color: #00d4ff; font-size: 0.85em; font-weight: bold; margin-bottom: 10px; }
    .tech-card-origin { padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; background-color: rgba(0, 212, 255, 0.05); margin-bottom: 20px; }
    .tech-card-dest { padding: 20px; border-radius: 15px; border: 2px solid #a855f7; background-color: rgba(168, 85, 247, 0.05); margin-bottom: 20px; }
    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: transparent; font-size: 0.95em; line-height: 1.4; }
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important;
        font-weight: bold; border: none; border-radius: 10px; height: 3.5em; width: 100%;
    }
    .executive-card { background: #ffffff; padding: 35px; border-radius: 20px; border-left: 8px solid #00d4ff; color: #111; }
    .footer-container { display: flex; flex-direction: column; align-items: center; padding: 40px 0; margin-top: 30px; border-top: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

# --- RECURSOS ---
LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png"
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"
API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# --- LÓGICA DE DATOS ---
def get_wx(icao, phase):
    if not icao: return None
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = "https://api.checkwx.com/" + stype + "/" + icao + "/decoded"
    headers = {"X-API-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        return data["data"][0] if data.get("results", 0) > 0 else None
    except: return None

# --- SIDEBAR & FETCH ---
st.sidebar.title("Trip Configuration")
origin_icao = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
wx_org = get_wx(origin_icao, "Flight Day (Live)") # Fetch rápido para el nombre
if wx_org:
    st.sidebar.markdown(f'<div class="airport-label">📍 {wx_org["station"]["name"]}<br>🏙️ {wx_org["station"]["city"]}</div>', unsafe_allow_html=True)

destination_icao = st.sidebar.text_input("ARRIVAL ICAO", value="KOPF").upper()
wx_dst = get_wx(destination_icao, "Flight Day (Live)") # Fetch rápido para el nombre
if wx_dst:
    st.sidebar.markdown(f'<div class="airport-label">📍 {wx_dst["station"]["name"]}<br>🏙️ {wx_dst["station"]["city"]}</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
etd = st.sidebar.text_input("ETD (UTC)", value="12:00")
eta = st.sidebar.text_input("ETA (UTC)", value="15:30")
fase = st.sidebar.selectbox("Assessment Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT MODE", ["Executive (Client)", "Technical (Internal)"])

# --- CABECERA ---
col_logo, col_title = st.columns([1, 4])
with col_logo: st.image(LOGO_UP_LEFT, width=250)
with col_title: st.markdown('<div class="header-style">Flight Support Team | Trip Assessment</div>', unsafe_allow_html=True)

# --- EJECUCIÓN PRINCIPAL ---
if st.button("Run Mission Assessment"):
    if wx_org and wx_dst:
        # Aquí va el código del mapa que ya tienes...
        # (Omitido por brevedad, pero mantenlo igual)
        
        if tipo_reporte == "Executive (Client)":
            # MEJORA: Incluir nombres completos en el reporte ejecutivo
            exec_html = '<div class="executive-card">'
            exec_html += '<h2 style="color:#005fcc; margin:0;">' + wx_org["station"]["name"] + ' ➔ ' + wx_dst["station"]["name"] + '</h2>'
            exec_html += '<p style="color:#666; font-size:0.9em;">' + wx_org["station"]["city"] + ' to ' + wx_dst["station"]["city"] + '</p><hr>'
            # ... resto de tu lógica de mensajes de clima
            st.markdown(exec_html, unsafe_allow_html=True)
