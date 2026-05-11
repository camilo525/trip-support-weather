import streamlit as st
import requests
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Flight Support Team Weather Tool", page_icon="✈️", layout="wide")

# --- DISEÑO PRO: NEÓN Y CONTRASTE ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    .header-style {
        font-size: 24px; font-weight: bold;
        background: -webkit-linear-gradient(#00d4ff, #005fcc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    
    /* RECUADRO ORIGEN: Azul Neón */
    .tech-card-origin { 
        padding: 20px; border-radius: 15px; 
        border: 2px solid #00d4ff; /* Borde Azul */
        background-color: rgba(0, 212, 255, 0.05); margin-bottom: 20px; 
    }
    
    /* RECUADRO DESTINO: Violeta/Púrpura Neón (Cambiado para evitar confusión con alerta) */
    .tech-card-dest { 
        padding: 20px; border-radius: 15px; 
        border: 2px solid #a855f7; /* Borde Violeta */
        background-color: rgba(168, 85, 247, 0.05); margin-bottom: 20px; 
    }

    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: transparent; font-size: 1.1em; line-height: 1.5; }
    
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important;
        font-weight: bold; border: none; border-radius: 10px; height: 3.5em;
        transition: 0.3s; text-transform: uppercase; letter-spacing: 2px;
    }
    
    .executive-card {
        background: rgba(255,255,255,0.03); 
        padding: 35px; border-radius: 20px; border-left: 6px solid #00d4ff;
    }

    /* Colores de estatus interno */
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
        return r.json()["data"][0] if r.json().get("results", 0) > 0 else None
    except: return None

# Lógica de texto cliente
def generate_client_text(wx, icao, type="dep"):
    raw = wx.get("raw_text", "").upper()
    vis = wx.get("visibility", {}).get("miles_float", 10)
    is_critical = any(x in raw for x in ["TS", "SN", "FG", "DZ", "RA", "SQ"]) or vis < 3
    if type == "dep":
        if is_critical: return f"Our latest meteorological assessment for your departure at {icao} shows active weather systems in the vicinity. To prioritize your safety and ensure a smooth operation, we are evaluating the most efficient departure window for your day of travel."
        else: return f"Current weather analysis for your departure at {icao} indicates ideal flying conditions. We anticipate an on-time departure as scheduled for your day of travel."
    else:
        if is_critical: return f"The terminal forecast for your arrival at {icao} currently indicates weather activity near your arrival time. Our Dispatch Team is already working on optimized routing."
        else: return f"The terminal forecast for your arrival at {icao} remains favorable. Our team confirms clear skies for your day of arrival."

# 5. BOTÓN Y LÓGICA
if st.button("Run Mission Assessment"):
    wx_org = get_wx(origin, fase)
    wx_dst = get_wx(destination, fase)

    if wx_org and wx_dst:
        if tipo_reporte == "Executive (Client)":
            st.markdown(f"""
            <div class="executive-card">
                <h2 style="color:#00d4ff; margin-top:0;">Flight Briefing: {origin} ➔ {destination}</h2>
                <p><b>Departure:</b> {generate_client_text(wx_org, origin, "dep")}</p>
                <p><b>Arrival:</b> {generate_client_text(wx_dst, destination, "arr")}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### 🛠 Internal Support Intelligence")
            c1, c2 = st.columns(2)
            
            # --- ORIGEN ---
            with c1:
                vis_o = wx_org.get("visibility", {}).get("miles_float", 10)
                is_crit_o = any(x in wx_org.get("raw_text", "").upper() for x in ["TS", "SN", "FG", "SQ"]) or vis_o < 3
                status_o = '<span class="status-alert">🔴 Alert</span>' if is_crit_o else '<span class="status-stable">🟢 Stable</span>'
                st.markdown(f"""<div class="tech-card-origin"><h4 style="color:#00d4ff;">{origin} @ {etd}Z</h4><p class="raw-code">{wx_org.get("raw_text", "")}</p><hr style="border: 0.5px solid #333;"><p><b>Vis:</b> {vis_o} SM | <b>Status:</b> {status_o}</p></div>""", unsafe_allow_html=True)

            # --- DESTINO ---
            with c2:
                vis_d = wx_dst.get("visibility", {}).get("miles_float", 10)
                is_crit_d = any(x in wx_dst.get("raw_text", "").upper() for x in ["TS", "SN", "FG", "SQ"]) or vis_d < 3
                status_d = '<span class="status-alert">🔴 Alert</span>' if is_crit_d else '<span class="status-stable">🟢 Stable</span>'
                st.markdown(f"""<div class="tech-card-dest"><h4 style="color:#a855f7;">{destination} @ {eta}Z</h4><p class="raw-code">{wx_dst.get("raw_text", "")}</p><hr style="border: 0.5px solid #333;"><p><b>Vis:</b> {vis_d} SM | <b>Status:</b> {status_d}</p></div>""", unsafe_allow_html=True)
    else:
        st.error("ICAO not found.")

# 6. FOOTER
st.markdown(f"""<div class="footer-container"><img src="{LOGO_BOTTOM_CENTER}" width="180"><p style="color:#555; font-size:0.8em; margin-top:10px;">Dir. Operations & Standards</p><p style="color:#333; font-size:0.7em;">SYSTEM TIME: {datetime.utcnow().strftime('%H:%M')}Z</p></div>""", unsafe_allow_html=True)
