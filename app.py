import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ops Assessment Tool v3.0", page_icon="✈️", layout="wide")

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
    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: #0a0a0a; padding: 10px; border-radius: 5px; font-size: 0.85em; line-height: 1.4; border: 1px solid #222; margin: 10px 0; }
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important;
        font-weight: bold; border: none; border-radius: 10px; height: 3.5em; width: 100%;
    }
    .executive-card { background: #ffffff; padding: 35px; border-radius: 20px; border-left: 8px solid #00d4ff; color: #111; }
    .data-row { display: flex; justify-content: space-between; font-size: 0.9em; margin-bottom: 4px; border-bottom: 1px solid #222; padding-bottom: 2px; }
    .footer-container { display: flex; flex-direction: column; align-items: center; padding: 40px 0; margin-top: 30px; border-top: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

# --- API KEYS ---
CHECKWX_KEY = "1b89b9a703e34d8596a1b932c0d30a82"
AERODATA_KEY = "d6ae47d1-8477-42c4-9f26-dc4e7939a81b"

# --- LÓGICA HÍBRIDA ---
def get_airport_static_data(icao):
    if not icao or len(icao) < 3: return None
    url = f"https://aerodatabox.p.rapidapi.com/airports/icao/{icao}"
    headers = {"X-RapidAPI-Key": AERODATA_KEY, "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            d = r.json()
            return {
                "name": d.get("name", icao),
                "city": d.get("municipalityName", "Unknown City"),
                "tz": d.get("timeZone", "UTC"),
                "coords": [d.get("location", {}).get("lat"), d.get("location", {}).get("lon")]
            }
    except: return None
    return None

def get_weather_data(icao, phase):
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    headers = {"X-API-Key": CHECKWX_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        return data["data"][0] if data.get("results", 0) > 0 else None
    except: return None

# --- SIDEBAR ---
st.sidebar.title("Trip Configuration")
origin_icao = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
info_o = get_airport_static_data(origin_icao)
if info_o: st.sidebar.markdown(f'<div class="airport-label">✈️ {info_o["name"]}</div>', unsafe_allow_html=True)

destination_icao = st.sidebar.text_input("ARRIVAL ICAO", value="KOPF").upper()
info_d = get_airport_static_data(destination_icao)
if info_d: st.sidebar.markdown(f'<div class="airport-label">✈️ {info_d["name"]}</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
etd = st.sidebar.text_input("ETD (Internal)", value="12:00")
eta = st.sidebar.text_input("ETA (Internal)", value="15:30")
fase = st.sidebar.selectbox("Assessment Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT MODE", ["Executive (Client)", "Technical (Internal)"])

# --- HEADER ---
LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png"
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"

col_logo, col_title = st.columns([1, 4])
with col_logo: st.image(LOGO_UP_LEFT, width=250)
with col_title: st.markdown('<div class="header-style">Flight Support Team | Hybrid Mission Assessment</div>', unsafe_allow_html=True)

# --- LÓGICA DE RIESGO ---
def evaluate_risk(wx):
    if not wx: return False, {}
    vis = wx.get("visibility", {}).get("miles_float", 10)
    wind_spd = wx.get("wind", {}).get("speed_kts", 0)
    raw = wx.get("raw_text", "").upper()
    ceiling = 10000
    for layer in wx.get("clouds", []):
        if layer.get("code") in ["BKN", "OVC"]:
            ceiling = min(ceiling, layer.get("base_feet_agl", 10000))
    is_crit = (vis < 3 or wind_spd > 20 or ceiling < 1000 or any(x in raw for x in ["TS", "SN", "FG", "SQ"]))
    return is_crit, {"vis": vis, "wind": wind_spd, "ceiling": ceiling}

# --- EJECUCIÓN ---
if st.button("Run Hybrid Assessment"):
    wx_o = get_weather_data(origin_icao, fase)
    wx_d = get_weather_data(destination_icao, fase)

    if wx_o and wx_d and info_o and info_d:
        # MAPA
        fig = go.Figure(go.Scattergeo(
            lon=[info_o["coords"][1], info_d["coords"][1]], 
            lat=[info_o["coords"][0], info_d["coords"][0]], 
            mode='lines+markers', line=dict(width=2, color='#00d4ff'),
            marker=dict(size=10, color=['#00d4ff
