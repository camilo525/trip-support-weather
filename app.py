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
    .tech-card-origin { padding: 20px; border-radius: 15px; border: 1px solid #00d4ff; background-color: rgba(0, 212, 255, 0.05); margin-bottom: 20px; }
    .tech-card-dest { padding: 20px; border-radius: 15px; border: 1px solid #ff007a; background-color: rgba(255, 0, 122, 0.05); margin-bottom: 20px; }
    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: transparent; font-size: 1.1em; line-height: 1.5; }
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important;
        font-weight: bold; border: none; border-radius: 10px; height: 3.5em;
        transition: 0.3s; text-transform: uppercase; letter-spacing: 2px;
    }
    .stButton>button:hover { box-shadow: 0px 0px 15px #00d4ff; transform: scale(1.02); }
    input { background-color: #0a0a0a !important; border: 1px solid #333333 !important; color: #00d4ff !important; }
    .footer-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; padding: 40px 0px; margin-top: 30px; border-top: 1px solid #222222; }
    
    /* Tarjeta Ejecutiva */
    .executive-card {
        background: rgba(255,255,255,0.03); 
        padding: 35px; 
        border-radius: 20px; 
        border-left: 6px solid #00d4ff;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png" 
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"
API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# 2. ENCABEZADO
col_logo, col_title = st.columns([1, 8])
with col_logo: st.image(LOGO_UP_LEFT, width=300)
with col_title: st.markdown('<div class="header-style">Flight Support team | Trip Assessment</div>', unsafe_allow_html=True)

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

# 4. LÓGICA DE ANÁLISIS SIN HORAS PARA CLIENTE
def generate_client_text(wx, icao, type="dep"):
    raw = wx.get("raw_text", "").upper()
    vis = wx.get("visibility", {}).get("miles_float", 10)
    
    # Detección de condiciones críticas
    is_critical = any(x in raw for x in ["TS", "SN", "FG", "DZ", "RA", "SQ"]) or vis < 3
    
    if type == "dep":
        if is_critical:
            return f"Our latest meteorological assessment for your departure at {icao} shows active weather systems in the vicinity. To prioritize your safety and ensure a smooth operation, we are evaluating the most efficient departure window for your day of travel and will advise on any necessary adjustments shortly."
        else:
            return f"Current weather analysis for your departure at {icao} indicates ideal flying conditions. We anticipate a seamless boarding process and an on-time departure as scheduled for your day of travel."
    else:
        if is_critical:
            return f"The terminal forecast for your arrival at {icao} currently indicates weather activity near your arrival time. Our Dispatch Team is already working on optimized routing and coordinating with local authorities to minimize any potential inconvenience during your arrival."
        else:
            return f"The terminal forecast for your arrival at {icao} remains favorable. Our team confirms clear skies and stable winds for your day of arrival, ensuring a comfortable and professional arrival experience."

# 5. BOTÓN Y LÓGICA
if st.button("Run Mission Assessment"):
    wx_org = get_wx(origin, fase)
    wx_dst = get_wx(destination, fase)

    if wx_org and wx_dst:
        if tipo_reporte == "Executive (Client)":
            dep_text = generate_client_text(wx_org, origin, "dep")
            arr_text = generate_client_text(wx_dst, destination, "arr")
            
            st.markdown(f"""
            <div class="executive-card">
                <h2 style="color:#00d4ff; margin-top:0;">Flight Briefing: {origin} ➔ {destination}</h2>
                <p style="font-size:1.1em;"><b>Departure Analysis:</b> {dep_text}</p>
                <p style="font-size:1.1em;"><b>Arrival Analysis:</b> {arr_text}</p>
                <p style="color:#888; font-style:italic; margin-top:25px; border-top:1px solid #333; padding-top:15px;">
                Our Operations Team continues to monitor your route in real-time to maintain the highest standards of safety, punctuality, and comfort.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.button("📋 Click to Copy Briefing for Client")
        else:
            st.markdown("### 🛠 Internal Support Intelligence")
            col1, col2 = st.columns(2)
            for col, wx, icao, time, color, css in zip([col1, col2], [wx_org, wx_dst], [origin, destination], [etd, eta], ["#00d4ff", "#ff007a"], ["tech-card-origin", "tech-card-dest"]):
                with col:
                    vis = wx.get("visibility", {}).get("miles_float", 10)
                    st.markdown(f"""<div class="{css}"><h4 style="color:{color};">{icao} @ {time}Z</h4><p class="raw-code">{wx.get("raw_text", "")}</p><hr style="border: 0.5px solid #333;"><p><b>Vis:</b> {vis} SM | <b>Status:</b> {"🟢 Stable" if vis >= 5 else "🔴 Caution"}</p></div>""", unsafe_allow_html=True)
    else:
        st.error("System error: Unable to retrieve aviation data. Check ICAO codes.")

# 6. FOOTER
st.markdown(f"""
    <div class="footer-container">
        <img src="{LOGO_BOTTOM_CENTER}" width="180">
        <p style="color:#555; font-size:0.8em; margin-top:10px;">Dir. Operations & Standards</p>
        <p style="color:#333; font-size:0.7em;">SYSTEM TIME: {datetime.utcnow().strftime('%H:%M')}Z</p>
    </div>
    """, unsafe_allow_html=True)
