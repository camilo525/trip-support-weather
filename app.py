import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Flight Support Team Weather Tool", page_icon="✈️", layout="wide")

# --- DISEÑO ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    .header-style {
        font-size: 24px; font-weight: bold;
        background: -webkit-linear-gradient(#00d4ff, #005fcc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .tech-card-origin { padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; background-color: rgba(0, 212, 255, 0.05); margin-bottom: 20px; }
    .tech-card-dest { padding: 20px; border-radius: 15px; border: 2px solid #a855f7; background-color: rgba(168, 85, 247, 0.05); margin-bottom: 20px; }
    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: transparent; font-size: 1.1em; line-height: 1.5; }
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important;
        font-weight: bold; border: none; border-radius: 10px; height: 3.5em; width: 100%;
    }
    .executive-card { background: rgba(255,255,255,0.03); padding: 35px; border-radius: 20px; border-left: 6px solid #00d4ff; }
    .status-stable { color: #00ff00; font-weight: bold; }
    .status-alert { color: #ff0000; font-weight: bold; text-decoration: underline; }
    input { background-color: #0a0a0a !important; border: 1px solid #333333 !important; color: #00d4ff !important; }
    .footer-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; padding: 40px 0px; margin-top: 30px; border-top: 1px solid #222222; }
    </style>
    """, unsafe_allow_html=True)

LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png" 
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"
API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# 2. ENCABEZADO
col_logo, col_title = st.columns([1, 8])
with col_logo: st.image(LOGO_UP_LEFT, width=300)
with col_title: st.markdown('<div class="header-style">Flight Support Team | Trip Assessment</div>', unsafe_allow_html=True)

# 3. SIDEBAR
st.sidebar.title("Trip Details")
origin = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
etd = st.sidebar.text_input("ETD (UTC Internal)", value="1200")
destination = st.sidebar.text_input("ARRIVAL ICAO", value="KMIA").upper()
eta = st.sidebar.text_input("ETA (UTC Internal)", value="1600")
fase = st.sidebar.selectbox("Assessment Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT MODE", ["Executive (Client)", "Technical (Internal)"])

def get_wx(icao, phase):
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    headers = {"X-API-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        return data["data"][0] if data.get("results", 0) > 0 else None
    except: return None

def generate_client_text(wx, icao, type="dep"):
    raw = wx.get("raw_text", "").upper()
    vis = wx.get("visibility", {}).get("miles_float", 10)
    is_critical = any(x in raw for x in ["TS", "SN", "FG", "DZ", "RA", "SQ"]) or vis < 3
    if type == "dep":
        if is_critical: return f"Our latest meteorological assessment for your departure at {icao} shows active weather systems in the vicinity. We are evaluating the most efficient departure window for your day of travel."
        else: return f"Current weather analysis for your departure at {icao} indicates ideal flying conditions for your day of travel."
    else:
        if is_critical: return f"The terminal forecast for your arrival at {icao} currently indicates weather activity. Our Dispatch Team is already working on optimized routing."
        else: return f"The terminal forecast for your arrival at {icao} remains favorable for your day of arrival."

# 5. BOTÓN Y LÓGICA
if st.button("Run Mission Assessment"):
    wx_org = get_wx(origin, fase)
    wx_dst = get_wx(destination, fase)

    if wx_org and wx_dst:
        # MAPA
        try:
            o_lat, o_lon = wx_org['station']['geometry']['coordinates'][1], wx_org['station']['geometry']['coordinates'][0]
            d_lat, d_lon = wx_dst['station']['geometry']['coordinates'][1], wx_dst['station']['geometry']['coordinates'][0]
            fig = go.Figure(go.Scattergeo(lon=[o_lon, d_lon], lat=[o_lat, d_lat], mode='lines+markers', line=dict(width=2, color='#00d4ff'), marker=dict(size=8, color=['#00d4ff', '#a855f7'])))
            fig.update_layout(geo=dict(scope='world', projection_type='orthographic', showland=True, landcolor="#111", bgcolor="rgba(0,0,0,0)", showocean=True, oceancolor="#050505"), margin=dict(l=0,r=0,t=0,b=0), height=350, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        except: st.warning("Map coordinates unavailable.")

        # REPORTES
        if tipo_reporte == "Executive (Client)":
            st.markdown(f'<div class="executive-card"><h2 style="color:#00d4ff;">Flight Briefing: {origin} ➔ {destination}</h2><p><b>Departure:</b> {generate_client_text(wx_org, origin, "dep")}</p><p><b>Arrival:</b> {generate_client_text(wx_dst, destination, "arr")}</p></div>', unsafe_allow_html=True)
        else:
            c1, c2 = st.columns(2)
            for col, wx, icao, time, color, css in zip([c1, c2], [wx_org, wx_dst], [origin, destination], [etd, eta], ["#00d4ff", "#a855f7"], ["tech-card-origin", "tech-card-dest"]):
                with col:
                    vis = wx.get("visibility", {}).get("miles_float", 10)
                    is_crit = any(x in wx.get("raw_text", "").upper() for x in ["TS", "SN", "FG", "SQ"]) or vis < 3
                    status = '<span class="status-alert">🔴 Alert</span>' if is_crit else '<span class="status-stable">🟢 Stable</span>'
                    st.markdown(f'<div class="{css}"><h4 style="color:{color};">{icao} @ {time}Z</h4><p class="raw-code">{wx["raw_text"]}</p><hr style="border: 0.5px solid #333;"><p><b>Vis:</b> {vis} SM | <b>Status:</b> {status}</p></div>', unsafe_allow_html=True)
    else: st.error("ICAO not found.")

# 6. FOOTER
st.markdown(f'<div class="footer-container"><img src="{LOGO_BOTTOM_CENTER}" width="180"><p style="color:#555; font-size:0.8em; margin-top:10px;">Dir. Operations & Standards</p><p style="color:#333; font-size:0.7em;">SYSTEM TIME: {datetime.utcnow().strftime("%H:%M")}Z</p></div>', unsafe_allow_html=True)
