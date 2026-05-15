import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Ops Assessment Tool v3.3", page_icon="✈️", layout="wide")

# --- DISEÑO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    .header-style { font-size: 26px; font-weight: bold; background: -webkit-linear-gradient(#00d4ff, #005fcc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; }
    .tech-card-origin { padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; background-color: rgba(0, 212, 255, 0.05); margin-bottom: 20px; }
    .tech-card-dest { padding: 20px; border-radius: 15px; border: 2px solid #a855f7; background-color: rgba(168, 85, 247, 0.05); margin-bottom: 20px; }
    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: #0a0a0a; padding: 10px; border-radius: 5px; font-size: 0.85em; border: 1px solid #222; margin-top: 10px; }
    .stButton>button { background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important; font-weight: bold; border: none; border-radius: 10px; height: 3.5em; width: 100%; }
    .executive-card { background: #ffffff; padding: 35px; border-radius: 20px; border-left: 8px solid #00d4ff; color: #111; }
    .footer-container { display: flex; flex-direction: column; align-items: center; padding: 40px 0; border-top: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

# --- API KEYS ---
CHECKWX_KEY = "1b89b9a703e34d8596a1b932c0d30a82"
AERODATA_KEY = "d6ae47d1-8477-42c4-9f26-dc4e7939a81b"

# --- FUNCIONES DE RESPALDO ---
def get_mock_weather(icao):
    return {
        "raw_text": f"{icao} 151453Z 16009KT 10SM FEW025 22/14 A3012",
        "visibility": {"miles_float": 10.0},
        "wind": {"speed_kts": 5},
        "clouds": [{"code": "FEW", "base_feet_agl": 3000}]
    }

def get_weather(icao, phase):
    icao = icao.strip().upper()
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    headers = {"X-API-Key": CHECKWX_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        data = r.json()
        if data.get("results", 0) > 0: return data["data"][0]
    except: return None
    return None

def get_airport_static(icao):
    icao = icao.strip().upper()
    url = f"https://aerodatabox.p.rapidapi.com/airports/icao/{icao}"
    headers = {"X-RapidAPI-Key": AERODATA_KEY, "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            d = r.json()
            return {"name": d.get("name", icao), "lat": d.get("location", {}).get("lat"), "lon": d.get("location", {}).get("lon")}
    except: pass
    # Backup si AeroDataBox falla para evitar el TypeError
    return {"name": icao, "lat": 0.0, "lon": 0.0}

# --- SIDEBAR ---
st.sidebar.title("Trip Configuration")
origin_icao = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").strip().upper()
destination_icao = st.sidebar.text_input("ARRIVAL ICAO", value="KMIA").strip().upper()
etd = st.sidebar.text_input("ETD (UTC)", value="12:00")
eta = st.sidebar.text_input("ETA (UTC)", value="15:30")
fase = st.sidebar.selectbox("Assessment Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT MODE", ["Executive (Client)", "Technical (Internal)"])

# --- HEADER ---
col_logo, col_title = st.columns([1, 4])
with col_title: st.markdown('<div class="header-style">Flight Support | Mission Assessment 3.3</div>', unsafe_allow_html=True)

def evaluate_risk(wx):
    if not wx: return False, {"vis": 10, "wind": 0, "ceiling": 10000}
    vis = wx.get("visibility", {}).get("miles_float", 10)
    wind = wx.get("wind", {}).get("speed_kts", 0)
    raw = wx.get("raw_text", "").upper()
    ceiling = 10000
    for layer in wx.get("clouds", []):
        if layer.get("code") in ["BKN", "OVC"]:
            ceiling = min(ceiling, layer.get("base_feet_agl", 10000))
    is_crit = (vis < 3 or wind > 20 or ceiling < 1000 or any(x in raw for x in ["TS", "SN", "FG"]))
    return is_crit, {"vis": vis, "wind": wind, "ceiling": ceiling}

# --- ACCIÓN ---
if st.button("RUN ASSESSMENT"):
    with st.
