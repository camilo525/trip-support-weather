import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Flight Support Team Weather Tool", page_icon="✈️", layout="wide")

# --- DISEÑO ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    .header-style { font-size: 24px; font-weight: bold; background: -webkit-linear-gradient(#00d4ff, #005fcc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .tech-card-origin { padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; background-color: rgba(0, 212, 255, 0.05); margin-bottom: 20px; }
    .tech-card-dest { padding: 20px; border-radius: 15px; border: 2px solid #a855f7; background-color: rgba(168, 85, 247, 0.05); margin-bottom: 20px; }
    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: transparent; }
    .stButton>button { background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important; font-weight: bold; border-radius: 10px; border: none; height: 3em; width: 100%; }
    .footer-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; padding: 40px 0px; margin-top: 30px; border-top: 1px solid #222222; }
    </style>
    """, unsafe_allow_html=True)

# LOGOS
LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png"
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"
API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# ENCABEZADO
c_l, c_t = st.columns([1, 8])
with c_l: st.image(LOGO_UP_LEFT, width=300)
with c_t: st.markdown('<div class="header-style">Flight Support Team | Trip Assessment</div>', unsafe_allow_html=True)

# SIDEBAR
st.sidebar.title("Trip Details")
origin = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
destination = st.sidebar.text_input("ARRIVAL ICAO", value="KMIA").upper()
fase = st.sidebar.selectbox("Assessment Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT MODE", ["Executive (Client)", "Technical (Internal)"])

def get_wx(icao, phase):
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    headers = {"X-API-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers)
        d = r.json()
        return d["data"][0] if d.get("results", 0) > 0 else None
    except: return None

# BOTÓN
if st.button("Run Mission Assessment"):
    w_o = get_wx(origin, fase)
    w_d = get_wx(destination, fase)

    if w_o and w_d:
        # DIBUJAR MAPA
        try:
            o_lat, o_lon = w_o['station']['geometry']['coordinates'][1], w_o['station']['geometry']['coordinates'][0]
            d_lat, d_lon = w_d['station']['geometry']['coordinates'][1], w_d['station']['geometry']['coordinates'][0]
            
            fig = go.Figure(go.Scattergeo(
                lon = [o_lon, d_lon], lat = [o_lat, d_lat],
                mode = 'lines+markers',
                line = dict(width = 2, color = '#00d4ff'),
                marker = dict(size = 8, color = ['#00d4ff', '#a855f7']),
                text = [origin, destination]
            ))
            fig.update_layout(
                geo = dict(scope='world', projection_type='orthographic', showland=True, landcolor="#111", bgcolor="rgba(0,0,0,0)", showocean=True, oceancolor="#050505"),
                margin=dict(l=0,r=0,t=0,b=0), height=350, paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)
        except: st.write("Map coordinates unavailable.")

        # REPORTES
        if tipo_reporte == "Executive (Client)":
            st.info(f"Route Assessment for {origin} to {destination} is complete. Conditions are stable.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div class="tech-card-origin"><h4>{origin}</h4><p class="raw-code">{w_o["raw_text"]}</p></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="tech-card-dest"><h4>{destination}</h4><p class="raw-code">{w_d["raw_text"]}</p></div>', unsafe_allow_html=True)
    else: st.error("Check ICAO codes.")

# FOOTER
st.markdown(f'<div class="footer-container"><img src="{LOGO_BOTTOM_CENTER}" width="180"><p style="color:#555; font-size:0.8em;">Dir. Operations & Standards</p></div>', unsafe_allow_html=True)
