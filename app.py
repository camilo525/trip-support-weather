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
    .airport-label { color: #00d4ff; font-size: 0.85em; font-weight: bold; margin-bottom: 15px; line-height: 1.2; }
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
    if not icao or len(icao) < 3: return None
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    headers = {"X-API-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        return data["data"][0] if data.get("results", 0) > 0 else None
    except: return None

# --- SIDEBAR & FETCH ---
st.sidebar.title("Trip Configuration")

# ORIGIN
origin_icao = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
wx_org_sidebar = get_wx(origin_icao, "Flight Day (Live)")
if wx_org_sidebar:
    name_o = wx_org_sidebar.get("station", {}).get("name", "")
    if name_o:
        st.sidebar.markdown(f'<div class="airport-label">✈️ {name_o}</div>', unsafe_allow_html=True)

# DESTINATION
destination_icao = st.sidebar.text_input("ARRIVAL ICAO", value="KOPF").upper()
wx_dst_sidebar = get_wx(destination_icao, "Flight Day (Live)")
if wx_dst_sidebar:
    name_d = wx_dst_sidebar.get("station", {}).get("name", "")
    if name_d:
        st.sidebar.markdown(f'<div class="airport-label">✈️ {name_d}</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
etd = st.sidebar.text_input("ETD (UTC)", value="12:00")
eta = st.sidebar.text_input("ETA (UTC)", value="15:3
