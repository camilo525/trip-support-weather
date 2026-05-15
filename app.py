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

# --- LÓGICA HÍBRIDA DE DATOS ---

def get_airport_static_data(icao):
    """Obtiene info estática de AeroDataBox"""
    if not icao or len(icao) < 3: return None
    url = f"https://aerodatabox.p.rapidapi.com/airports/icao/{icao}"
    headers = {
        "X-RapidAPI-Key": AERODATA_KEY,
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {
                "name": data.get("name", icao),
                "city": data.get("municipalityName", "Unknown City"),
                "tz": data.get("timeZone", "UTC"),
                "coords": [data.get("location", {}).get("lat"), data.get("location", {}).get("lon")]
            }
    except: return None
    return None

def get_weather_data(icao, phase):
    """Obtiene info climática de CheckWX"""
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

# Origen
origin_icao = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
info_org = get_airport_static_data(origin_icao)
if info_org:
    st.sidebar.markdown(f'<div class="airport-label">✈️ {info_org["name"]}<br>🏙️ {info_org["city"]}</div>', unsafe_allow_html=True)

# Destino
destination_icao = st.sidebar.text_input("ARRIVAL ICAO", value="KOPF").upper()
info_dst = get_airport_static_data(destination_icao)
if info_dst:
    st.sidebar.markdown(f'<div class="airport-label">✈️ {info_dst["name"]}<br>🏙️ {info_dst["city"]}</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
etd = st.sidebar.text_input("ETD (Internal)", value="12:00")
eta = st.sidebar.text_input("ETA (Internal)", value="15:30")
fase = st.sidebar.selectbox("Assessment Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT MODE", ["Executive (Client)", "Technical (Internal)"])

# --- CABECERA ---
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
    wx_org = get_weather_data(origin_icao, fase)
    wx_dst = get_weather_data(destination_icao, fase)

    if wx_org and wx_dst and info_org and info_dst:
        # MAPA
        fig = go.Figure(go.Scattergeo(
            lon=[info_org["coords"][1], info_dst["coords"][1]], 
            lat=[info_org["coords"][0], info_dst["coords"][0]], 
            mode='lines+markers', line=dict(width=2, color='#00d4ff'),
            marker=dict(size=10, color=['#00d4ff', '#a855f7'], symbol='diamond')
        ))
        fig.update_layout(geo=dict(showland=True, landcolor="#0a0a0a", bgcolor="rgba(0,0,0,0)"), margin=dict(l=0, r=0, t=0, b=0), height=300, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        risk_o, stats_o = evaluate_risk(wx_org)
        risk_d, stats_d = evaluate_risk(wx_dst)

        if tipo_reporte == "Executive (Client)":
            exec_html = f'<div class="executive-card"><h2 style="color:#005fcc; margin:0;">{info_org["name"]} ➔ {info_dst["name"]}</h2>'
            exec_html += f'<p style="color:#666; margin-bottom:20px;">{info_org["city"]} to {info_dst["city"]}</p>'
            exec_html += f'<p><b>Departure:</b> ' + ("Unstable conditions detected. Coordination required." if risk_o else "Weather is ideal and stable for departure.") + '</p>'
            exec_html += f'<p><b>Arrival:</b> ' + ("Monitoring meteorological activity at destination."
