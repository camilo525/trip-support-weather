import streamlit as st
import requests
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Flight Support Team Weather Tool", page_icon="✈️", layout="wide")

# --- DISEÑO PRO: NEÓN Y CONTRASTE ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    
    /* Títulos con degradado */
    .header-style {
        font-size: 24px;
        font-weight: bold;
        background: -webkit-linear-gradient(#00d4ff, #005fcc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }

    /* Tarjetas técnicas sin fondo gris pesado - Estilo Neón */
    .tech-card-origin {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #00d4ff;
        background-color: rgba(0, 212, 255, 0.05);
        margin-bottom: 20px;
    }
    
    .tech-card-dest {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #ff007a;
        background-color: rgba(255, 0, 122, 0.05);
        margin-bottom: 20px;
    }

    /* Código RAW - Limpio sobre negro */
    .raw-code {
        font-family: 'Courier New', monospace;
        color: #00ff00;
        background: transparent;
        font-size: 1.1em;
        line-height: 1.5;
    }

    /* Botón PRO con degradado */
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff);
        color: white !important;
        font-weight: bold;
        border: none;
        border-radius: 10px;
        height: 3.5em;
        transition: 0.3s;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .stButton>button:hover {
        box-shadow: 0px 0px 15px #00d4ff;
        transform: scale(1.02);
    }

    /* Inputs estilizados */
    input {
        background-color: #0a0a0a !important;
        border: 1px solid #333333 !important;
        color: #00d4ff !important;
    }

    /* Footer */
    .footer-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        padding: 40px 0px;
        margin-top: 30px;
        border-top: 1px solid #222222;
    }
    </style>
    """, unsafe_allow_html=True)

LOGO_UP_LEFT = "https://ibb.co/XkrRXFhZ.png" 
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"
API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# 2. ENCABEZADO
col_logo, col_title = st.columns([1, 8])
with col_logo: st.image(LOGO_UP_LEFT, width=100)
with col_title: st.markdown('<div class="header-style">Operations Team </div>', unsafe_allow_html=True)

# 3. SIDEBAR
st.sidebar.title("Thrust Aviation Trip")
origin = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
etd = st.sidebar.text_input("ETD (UTC)", value="1200")
destination = st.sidebar.text_input("ARRIVAL ICAO", value="KMIA").upper()
eta = st.sidebar.text_input("ETA (UTC)", value="1600")
fase = st.sidebar.selectbox("Type of Assessment", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("MODE", ["Executive (Client)", "Technical (Internal)"])

def get_wx(icao, phase):
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    headers = {"X-API-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers)
        return r.json()["data"][0] if r.json().get("results", 0) > 0 else None
    except: return None

# 4. BOTÓN Y LÓGICA
if st.button("Run Assessment"):
    wx_org = get_wx(origin, fase)
    wx_dst = get_wx(destination, fase)

    if wx_org and wx_dst:
        if tipo_reporte == "Executive (Client)":
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 30px; border-radius: 20px; border-left: 5px solid #00d4ff;">
                <h3 style="color:#00d4ff;">Trip Briefing: {origin} ➔ {destination}</h3>
                <p><b>Departure:</b> Conditions at {etd}Z are favorable for operation.</p>
                <p><b>Arrival:</b> Weather at {eta}Z is within safety standards. No delays expected.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### 🛠 Internal Support Intelligence")
            col1, col2 = st.columns(2)
            
            # ORIGEN (AZUL NEÓN)
            with col1:
                vis_o = wx_org.get("visibility", {}).get("miles_float", 10)
                st.markdown(f"""
                <div class="tech-card-origin">
                    <h4 style="color:#00d4ff;">{origin} @ {etd}Z</h4>
                    <p class="raw-code">{wx_org.get("raw_text", "")}</p>
                    <hr style="border: 0.5px solid #333;">
                    <p><b>Vis:</b> {vis_o} SM | <b>Analysis:</b> {"🟢 Stable" if vis_o >= 5 else "🔴 Low Vis Alert"}</p>
                </div>
                """, unsafe_allow_html=True)

            # DESTINO (ROSA/MAGENTA NEÓN)
            with col2:
                vis_d = wx_dst.get("visibility", {}).get("miles_float", 10)
                st.markdown(f"""
                <div class="tech-card-dest">
                    <h4 style="color:#ff007a;">{destination} @ {eta}Z</h4>
                    <p class="raw-code">{wx_dst.get("raw_text", "")}</p>
                    <hr style="border: 0.5px solid #333;">
                    <p><b>Vis:</b> {vis_d} SM | <b>Analysis:</b> {"🟢 Stable" if vis_d >= 5 else "🔴 Low Vis Alert"}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error("Access denied or ICAO not found.")

# 5. FOOTER
st.markdown(f"""
    <div class="footer-container">
        <img src="{LOGO_BOTTOM_CENTER}" width="180">
        <p style="color:#555; font-size:0.8em; margin-top:10px;">Dir. Operations & Standards</p>
        <p style="color:#333; font-size:0.7em;">SYSTEM TIME: {datetime.utcnow().strftime('%H:%M')}Z</p>
    </div>
    """, unsafe_allow_html=True)
