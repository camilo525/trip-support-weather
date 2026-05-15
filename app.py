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
    .airport-label { color: #00d4ff; font-size: 0.85em; font-weight: bold; margin-bottom: 15px; }
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

# --- LÓGICA DE DATOS ---
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
                "lat": d.get("location", {}).get("lat"),
                "lon": d.get("location", {}).get("lon")
            }
    except: return None

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
destination_icao = st.sidebar.text_input("ARRIVAL ICAO", value="KOPF").upper()
etd = st.sidebar.text_input("ETD (Internal)", value="12:00")
eta = st.sidebar.text_input("ETA (Internal)", value="15:30")
fase = st.sidebar.selectbox("Assessment Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT MODE", ["Executive (Client)", "Technical (Internal)"])

# --- HEADER ---
LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png"
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"

col_logo, col_title = st.columns([1, 4])
with col_logo: st.image(LOGO_UP_LEFT, width=250)
with col_title: st.markdown('<div class="header-style">Flight Support Team | Hybrid Assessment</div>', unsafe_allow_html=True)

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
    # ALERTAS: Vis < 3, Viento > 20, Techo < 1000
    is_crit = (vis < 3 or wind > 20 or ceiling < 1000 or any(x in raw for x in ["TS", "SN", "FG"]))
    return is_crit, {"vis": vis, "wind": wind, "ceiling": ceiling}

# --- EJECUCIÓN ---
if st.button("Run Advanced Assessment"):
    info_o = get_airport_static_data(origin_icao)
    info_d = get_airport_static_data(destination_icao)
    wx_o = get_weather_data(origin_icao, fase)
    wx_d = get_weather_data(destination_icao, fase)

    if wx_o and wx_d:
        # Mapa
        if info_o and info_d:
            lats, lons = [info_o["lat"], info_d["lat"]], [info_o["lon"], info_d["lon"]]
            fig = go.Figure(go.Scattergeo(lat=lats, lon=lons, mode='lines+markers', line=dict(width=2, color='#00d4ff')))
            fig.update_layout(geo=dict(showland=True, landcolor="#0a0a0a", bgcolor="rgba(0,0,0,0)"), height=300, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

        risk_o, stats_o = evaluate_risk(wx_o)
        risk_d, stats_d = evaluate_risk(wx_d)

        if tipo_reporte == "Executive (Client)":
            name_o = info_o["name"] if info_o else origin_icao
            name_d = info_d["name"] if info_d else destination_icao
            msg_o = "Unstable weather detected. Expect coordination." if risk_o else "Weather is ideal and stable for departure."
            msg_d = "Monitoring meteorological activity at destination." if risk_d else "Favorable forecast for a seamless arrival."
            
            st.markdown(f"""
            <div class="executive-card">
                <h2>{name_o} ➔ {name_d}</h2>
                <p><b>Departure:</b> {msg_o}</p>
                <p><b>Arrival:</b> {msg_d}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### 🛠 OPS Hybrid Technical Assessment")
            t1, t2 = st.columns(2)
            
            # ORIGIN
            with t1:
                lbl_o = '<b style="color:#ff3333;">🔴 CRITICAL</b>' if risk_o else '<b style="color:#00ff00;">🟢 NOMINAL</b>'
                name_o = info_o["name"] if info_o else origin_icao
                st.markdown(f"""
                <div class="tech-card-origin">
                    <h4 style="color:#00d4ff; margin:0;">{name_o}</h4>
                    <p style="font-size:0.8em; color:#aaa;">{etd}Z | Status: {lbl_o}</p>
                    <div class="raw-code">{wx_o.get("raw_text")}</div>
                    <p style="margin-top:10px; font-size:0.9em;">
                        <b>Vis:</b> {stats_o['vis']} SM | 
                        <b>Wind:</b> {stats_o['wind']} KTS | 
                        <b>Ceiling:</b> {stats_o['ceiling']} FT
                    </p>
                </div>
                """, unsafe_allow_html=True)

            # DESTINATION
            with t2:
                lbl_d = '<b style="color:#ff3333;">🔴 CRITICAL</b>' if risk_d else '<b style="color:#00ff00;">🟢 NOMINAL</b>'
                name_d = info_d["name"] if info_d else destination_icao
                st.markdown(f"""
                <div class="tech-card-dest">
                    <h4 style="color:#a855f7; margin:0;">{name_d}</h4>
                    <p style="font-size:0.8em; color:#aaa;">{eta}Z | Status: {lbl_d}</p>
                    <div class="raw-code">{wx_d.get("raw_text")}</div>
                    <p style="margin-top:10px; font-size:0.9em;">
                        <b>Vis:</b> {stats_d['vis']} SM | 
                        <b>Wind:</b> {stats_d['wind']} KTS | 
                        <b>Ceiling:</b> {stats_d['ceiling']} FT
                    </p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error("No meteorological data found. Check ICAO codes.")

# --- FOOTER ---
st.markdown(f'<div class="footer-container"><img src="{LOGO_BOTTOM_CENTER}" width="160"><p style="font-size:0.7em; margin-top:10px; color:#333;">SYSTEM TIME: {datetime.utcnow().strftime("%H:%M")}Z</p></div>', unsafe_allow_html=True)
