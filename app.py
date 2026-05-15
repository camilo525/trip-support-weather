import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ops Assessment Tool", page_icon="✈️", layout="wide")

# --- DISEÑO CSS (ESTRUCTURA SEGURA) ---
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
    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: transparent; font-size: 1.0em; line-height: 1.4; }
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important;
        font-weight: bold; border: none; border-radius: 10px; height: 3.5em; width: 100%;
    }
    .tool-container { display: flex; gap: 15px; margin: 25px 0; flex-wrap: wrap; }
    .tool-btn {
        flex: 1; min-width: 200px; padding: 15px; border-radius: 12px;
        text-align: center; text-decoration: none; font-weight: bold; font-size: 0.9em;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .btn-sat { background: rgba(0, 212, 255, 0.1); color: #00d4ff !important; border-color: #00d4ff; }
    .btn-map { background: rgba(168, 85, 247, 0.1); color: #a855f7 !important; border-color: #a855f7; }
    .btn-notam { background: rgba(255, 204, 0, 0.1); color: #ffcc00 !important; border-color: #ffcc00; }
    .executive-card { background: #ffffff; padding: 35px; border-radius: 20px; border-left: 8px solid #00d4ff; color: #111; }
    input { background-color: #0a0a0a !important; border: 1px solid #333 !important; color: #00d4ff !important; }
    .footer-container { display: flex; flex-direction: column; align-items: center; padding: 40px 0; margin-top: 30px; border-top: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

# --- RECURSOS ---
LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png"
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"
API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# --- CABECERA ---
col_logo, col_title = st.columns([1, 4])
with col_logo: 
    st.image(LOGO_UP_LEFT, width=250)
with col_title: 
    # Título segmentado para evitar errores de string
    title_html = '<div class="header-style">Flight Support Team | Trip Assessment</div>'
    st.markdown(title_html, unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("Trip Configuration")
origin = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
etd = st.sidebar.text_input("ETD (UTC)", value="12:00")
destination = st.sidebar.text_input("ARRIVAL ICAO", value="KOPF").upper()
eta = st.sidebar.text_input("ETA (UTC)", value="15:30")
fase = st.sidebar.selectbox("Assessment Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT MODE", ["Executive (Client)", "Technical (Internal)"])

# --- LÓGICA DE DATOS ---
def get_wx(icao, phase):
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    headers = {"X-API-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        if data.get("results", 0) > 0: return data["data"][0]
        return None
    except: return None

def generate_client_text(wx, icao, type="dep"):
    raw = wx.get("raw_text", "").upper()
    vis = wx.get("visibility", {}).get("miles_float", 10)
    is_critical = any(x in raw for x in ["TS", "SN", "FG", "DZ", "RA", "SQ"]) or vis < 3
    if type == "dep":
        if is_critical:
            return f"The Operations Team is analyzing weather conditions for departure from <b>{icao}</b>."
        return f"Meteorological analysis for departure from <b>{icao}</b> indicates ideal conditions."
    else:
        if is_critical:
            return f"The Operations Team is monitoring forecasted activity for arrival at <b>{icao}</b>."
        return f"The terminal forecast for arrival at <b>{icao}</b> remains favorable."

def get_coords(wx):
    try: return wx['station']['geometry']['coordinates'][1], wx['station']['geometry']['coordinates'][0]
    except:
        try: return wx['geometry']['coordinates'][1], wx['geometry']['coordinates'][0]
        except: return None, None

# --- EJECUCIÓN ---
if st.button("Run Mission Assessment"):
    wx_org = get_wx(origin, fase)
    wx_dst = get_wx(destination, fase)

    if wx_org and wx_dst:
        o_lat, o_lon = get_coords(wx_org)
        d_lat, d_lon = get_coords(wx_dst)
        
        if o_lat is not None:
            fig = go.Figure()
            fig.add_trace(go.Scattergeo(
                lon = [o_lon, d_lon], lat = [o_lat, d_lat],
                mode = 'lines+markers', line = dict(width = 2, color = '#00d4ff'),
                marker = dict(size = 10, color = ['#00d4ff', '#a855f7'], symbol = 'diamond')
            ))
            fig.
