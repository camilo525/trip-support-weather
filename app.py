import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Ops Assessment Tool v3.2", page_icon="✈️", layout="wide")

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

# --- FUNCIONES DE RESCATE ---
def get_mock_weather(icao):
    """Genera datos de respaldo si la API falla"""
    return {
        "raw_text": f"{icao} 151453Z 16009KT 10SM FEW025 22/14 A3012 RMK AO2",
        "visibility": {"miles_float": 10.0},
        "wind": {"speed_kts": 9},
        "clouds": [{"code": "FEW", "base_feet_agl": 2500}]
    }

def get_weather(icao, phase):
    icao = icao.strip().upper()
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    headers = {"X-API-Key": CHECKWX_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if data.get("results", 0) > 0:
            return data["data"][0]
    except:
        return None
    return None

def get_airport_static(icao):
    icao = icao.strip().upper()
    url = f"https://aerodatabox.p.rapidapi.com/airports/icao/{icao}"
    headers = {"X-RapidAPI-Key": AERODATA_KEY, "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {"name": d.get("name", icao), "city": d.get("municipalityName", "City"), 
                    "lat": d.get("location", {}).get("lat"), "lon": d.get("location", {}).get("lon")}
    except:
        return {"name": icao, "city": "Unknown", "lat": 25.79, "lon": -80.28}
    return None

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
with col_title: st.markdown('<div class="header-style">Flight Support | Mission Assessment 3.2</div>', unsafe_allow_html=True)

# --- RIESGO ---
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
    with st.spinner("Analyzing Global Ops Data..."):
        # Intentar clima real, si falla usar Mock
        wx_o = get_weather(origin_icao, fase) or get_mock_weather(origin_icao)
        wx_d = get_weather(destination_icao, fase) or get_mock_weather(destination_icao)
        info_o = get_airport_static(origin_icao)
        info_d = get_airport_static(destination_icao)

    # MAPA
    lats, lons = [info_o["lat"], info_d["lat"]], [info_o["lon"], info_d["lon"]]
    fig = go.Figure(go.Scattergeo(lat=lats, lon=lons, mode='lines+markers', line=dict(width=2, color='#00d4ff')))
    fig.update_layout(geo=dict(showland=True, landcolor="#0a0a0a", bgcolor="rgba(0,0,0,0)"), height=300, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

    risk_o, stats_o = evaluate_risk(wx_o)
    risk_d, stats_d = evaluate_risk(wx_d)

    if tipo_reporte == "Executive (Client)":
        msg_o = "Unstable weather. Coordination required." if risk_o else "Weather is ideal for departure."
        msg_d = "Activity detected. Ops Team monitoring." if risk_d else "Favorable forecast for arrival."
        st.markdown(f'<div class="executive-card"><h2>{info_o["name"]} ➔ {info_d["name"]}</h2><p><b>Departure:</b> {msg_o}</p><p><b>Arrival:</b> {msg_d}</p></div>', unsafe_allow_html=True)
    else:
        st.markdown("### 🛠 OPS Technical Assessment")
        t1, t2 = st.columns(2)
        with t1:
            lbl = '<b style="color:#ff3333;">🔴 CRITICAL</b>' if risk_o else '<b style="color:#00ff00;">🟢 NOMINAL</b>'
            st.markdown(f'<div class="tech-card-origin"><h4>{info_o["name"]}</h4><p>{etd}Z | Status: {lbl}</p><div class="raw-code">{wx_o["raw_text"]}</div><p>Vis: {stats_o["vis"]} SM | Wind: {stats_o["wind"]} KTS | Ceiling: {stats_o["ceiling"]} FT</p></div>', unsafe_allow_html=True)
        with t2:
            lbl = '<b style="color:#ff3333;">🔴 CRITICAL</b>' if risk_d else '<b style="color:#00ff00;">🟢 NOMINAL</b>'
            st.markdown(f'<div class="tech-card-dest"><h4>{info_d["name"]}</h4><p>{eta}Z | Status: {lbl}</p><div class="raw-code">{wx_d["raw_text"]}</div><p>Vis: {stats_d["vis"]} SM | Wind: {stats_d["wind"]} KTS | Ceiling: {stats_d["ceiling"]} FT</p></div>', unsafe_allow_html=True)
