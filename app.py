import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ops Assessment Tool v3.1", page_icon="✈️", layout="wide")

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
    .tech-card-origin { padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; background-color: rgba(0, 212, 255, 0.05); margin-bottom: 20px; }
    .tech-card-dest { padding: 20px; border-radius: 15px; border: 2px solid #a855f7; background-color: rgba(168, 85, 247, 0.05); margin-bottom: 20px; }
    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: #0a0a0a; padding: 10px; border-radius: 5px; font-size: 0.85em; border: 1px solid #222; margin-top: 10px; }
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important;
        font-weight: bold; border: none; border-radius: 10px; height: 3.5em; width: 100%;
    }
    .executive-card { background: #ffffff; padding: 35px; border-radius: 20px; border-left: 8px solid #00d4ff; color: #111; }
    .footer-container { display: flex; flex-direction: column; align-items: center; padding: 40px 0; border-top: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

# --- API KEYS ---
CHECKWX_KEY = "1b89b9a703e34d8596a1b932c0d30a82"
AERODATA_KEY = "d6ae47d1-8477-42c4-9f26-dc4e7939a81b"

# --- FUNCIONES DE DATOS BLINDADAS ---
def get_airport_static(icao):
    icao = icao.strip().upper()
    if len(icao) < 3: return None
    url = f"https://aerodatabox.p.rapidapi.com/airports/icao/{icao}"
    headers = {"X-RapidAPI-Key": AERODATA_KEY, "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            d = r.json()
            return {
                "name": d.get("name", icao),
                "city": d.get("municipalityName", "Unknown City"),
                "lat": d.get("location", {}).get("lat"),
                "lon": d.get("location", {}).get("lon")
            }
    except: return None
    return None

def get_weather(icao, phase):
    icao = icao.strip().upper()
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    headers = {"X-API-Key": CHECKWX_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        data = r.json()
        if data.get("results", 0) > 0:
            return data["data"][0]
    except: return None
    return None

# --- SIDEBAR ---
st.sidebar.title("Trip Configuration")
origin_icao = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").strip().upper()
destination_icao = st.sidebar.text_input("ARRIVAL ICAO", value="KMIA").strip().upper()
etd = st.sidebar.text_input("ETD (Internal)", value="12:00")
eta = st.sidebar.text_input("ETA (Internal)", value="15:30")
fase = st.sidebar.selectbox("Assessment Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT MODE", ["Executive (Client)", "Technical (Internal)"])

# --- HEADER ---
LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png"
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"

col_logo, col_title = st.columns([1, 4])
with col_logo: st.image(LOGO_UP_LEFT, width=250)
with col_title: st.markdown('<div class="header-style">Flight Support Team | Mission Assessment 3.1</div>', unsafe_allow_html=True)

# --- LÓGICA DE RIESGO ---
def evaluate_risk(wx):
    if not wx: return False, {"vis": "N/A", "wind": "N/A", "ceiling": "N/A"}
    vis = wx.get("visibility", {}).get("miles_float", 10)
    wind = wx.get("wind", {}).get("speed_kts", 0)
    raw = wx.get("raw_text", "").upper()
    ceiling = 10000
    for layer in wx.get("clouds", []):
        if layer.get("code") in ["BKN", "OVC"]:
            ceiling = min(ceiling, layer.get("base_feet_agl", 10000))
    is_crit = (vis < 3 or wind > 20 or ceiling < 1000 or any(x in raw for x in ["TS", "SN", "FG", "RA"]))
    return is_crit, {"vis": vis, "wind": wind, "ceiling": ceiling}

# --- EJECUCIÓN ---
if st.button("RUN MISSION ASSESSMENT"):
    with st.spinner("Fetching global aviation data..."):
        info_o = get_airport_static(origin_icao)
        info_d = get_airport_static(destination_icao)
        wx_o = get_weather(origin_icao, fase)
        wx_d = get_weather(destination_icao, fase)

    if wx_o and wx_d:
        # Mapa (Solo si hay coordenadas)
        if info_o and info_d and info_o.get("lat") and info_d.get("lat"):
            lats, lons = [info_o["lat"], info_d["lat"]], [info_o["lon"], info_d["lon"]]
            fig = go.Figure(go.Scattergeo(lat=lats, lon=lons, mode='lines+markers', line=dict(width=2, color='#00d4ff')))
            fig.update_layout(geo=dict(showland=True, landcolor="#0a0a0a", bgcolor="rgba(0,0,0,0)"), height=300, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

        risk_o, stats_o = evaluate_risk(wx_o)
        risk_d, stats_d = evaluate_risk(wx_d)

        name_o = info_o["name"] if info_o else origin_icao
        name_d = info_d["name"] if info_d else destination_icao

        if tipo_reporte == "Executive (Client)":
            msg_o = "Unstable conditions. Operations monitoring." if risk_o else "Weather is ideal and stable."
            msg_d = "Activity detected. Expect coordination." if risk_d else "Favorable forecast for a seamless arrival."
            st.markdown(f'<div class="executive-card"><h2>{name_o} ➔ {name_d}</h2><p><b>Departure:</b> {msg_o}</p><p><b>Arrival:</b> {msg_d}</p></div>', unsafe_allow_html=True)
        else:
            st.markdown("### 🛠 OPS Advanced Technical Assessment")
            t1, t2 = st.columns(2)
            # Origin
            with t1:
                lbl = '<b style="color:#ff3333;">🔴 CRITICAL</b>' if risk_o else '<b style="color:#00ff00;">🟢 NOMINAL</b>'
                st.markdown(f'<div class="tech-card-origin"><h4>{name_o}</h4><p>{etd}Z | Status: {lbl}</p><div class="raw-code">{wx_o.get("raw_text")}</div><p>Vis: {stats_o["vis"]} SM | Wind: {stats_o["wind"]} KTS | Ceiling: {stats_o["ceiling"]} FT</p></div>', unsafe_allow_html=True)
            # Destination
            with t2:
                lbl = '<b style="color:#ff3333;">🔴 CRITICAL</b>' if risk_d else '<b style="color:#00ff00;">🟢 NOMINAL</b>'
                st.markdown(f'<div class="tech-card-dest"><h4>{name_d}</h4><p>{eta}Z | Status: {lbl}</p><div class="raw-code">{wx_d.get("raw_text")}</div><p>Vis: {stats_d["vis"]} SM | Wind: {stats_d["wind"]} KTS | Ceiling: {stats_d["ceiling"]} FT</p></div>', unsafe_allow_html=True)
    else:
        st.error(f"Error: Could not retrieve weather for {origin_icao} or {destination_icao}. Verify codes.")

# --- FOOTER ---
st.markdown(f'<div class="footer-container"><img src="{LOGO_BOTTOM_CENTER}" width="160"><p style="font-size:0.7em; margin-top:10px; color:#333;">SYSTEM TIME: {datetime.utcnow().strftime("%H:%M")}Z</p></div>', unsafe_allow_html=True)
