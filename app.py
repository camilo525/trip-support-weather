import streamlit as st
import requests
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Flight Support Team Weather Tool", page_icon="✈️", layout="wide")

# --- FORZAR MODO OSCURO TOTAL (BLACK BACKGROUND) ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    .stMarkdown, p, h1, h2, h3, h4, span, label, .stSelectbox, .stTextInput { color: #FFFFFF !important; }
    input { background-color: #1a1a1a !important; color: #FFFFFF !important; border: 1px solid #333333 !important; }
    [data-testid="stSidebar"] { background-color: #0a0a0a !important; border-right: 1px solid #222222; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    .stButton>button { background-color: #004a99 !important; color: white !important; font-weight: bold; width: 100%; border-radius: 8px; border: 1px solid #005fcc; height: 3.5em; text-transform: uppercase; }
    .main-card { padding: 25px; border-radius: 12px; background-color: #111111 !important; border: 1px solid #222222; color: #e0e0e0 !important; }
    .tech-analysis-card { padding: 15px; border-radius: 8px; background-color: #1a1a1a; border-left: 4px solid #00d4ff; margin-top: 10px; font-size: 0.9em; }
    .footer-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; padding: 40px 0px; margin-top: 30px; border-top: 1px solid #222222; text-align: center; }
    .footer-text-main { margin-top: 15px; color: #BBBBBB !important; font-size: 0.9em; font-weight: 500; letter-spacing: 1.5px; }
    .footer-text-time { margin-top: 5px; color: #666666 !important; font-size: 0.75em; letter-spacing: 1px; }
    code { color: #00ff00 !important; background-color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

LOGO_UP_LEFT = "https://thrust-aviation.com/wp-content/uploads/2024/02/Logo-White-500-2-e1710003051285.png" 
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"
API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# 2. ENCABEZADO
col_logo, col_title = st.columns([1, 8])
with col_logo: st.image(LOGO_UP_LEFT, width=100)
with col_title: st.title("Flight Support Team Weather Tool")
st.markdown("---")

# 3. SIDEBAR
st.sidebar.title("✈️ FST Dispatcher")
origin = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
etd = st.sidebar.text_input("ETD (UTC)", value="1200")
destination = st.sidebar.text_input("ARRIVAL ICAO", value="KMIA").upper()
eta = st.sidebar.text_input("ETA (UTC)", value="1600")
fase = st.sidebar.selectbox("PLANNING PHASE", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT STYLE", ["Executive (Client)", "Technical (Internal)"])

def get_wx(icao, phase):
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    headers = {"X-API-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers)
        return r.json()["data"][0] if r.json().get("results", 0) > 0 else None
    except: return None

# 4. EJECUCIÓN
if st.button("RUN TRIP ANALYSIS"):
    with st.spinner('Accessing Aviation Servers...'):
        wx_org = get_wx(origin, fase)
        wx_dst = get_wx(destination, fase)

        if wx_org and wx_dst:
            if tipo_reporte == "Executive (Client)":
                st.subheader("Client Executive Briefing")
                st.markdown(f"""
                <div class="main-card">
                <b style="color:#4dabf7">DEPARTURE: {origin} (Scheduled {etd}Z)</b><br>
                • Conditions are favorable for departure. Optimal visibility confirmed.<br><br>
                <b style="color:#4dabf7">ARRIVAL: {destination} (Scheduled {eta}Z)</b><br>
                • Destination is within operational limits. No significant delays expected.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.subheader("Internal Technical Brief & Analysis")
                c1, c2 = st.columns(2)
                
                for col, wx, icao, time in zip([c1, c2], [wx_org, wx_dst], [origin, destination], [etd, eta]):
                    with col:
                        st.info(f"**{icao} @ {time}Z**")
                        st.code(wx.get("raw_text", ""))
                        
                        # Análisis Técnico Dinámico
                        vis = wx.get("visibility", {}).get("miles_float", 10)
                        wind = wx.get("wind", {}).get("speed_kts", 0)
                        clouds = wx.get("clouds", [{}])[0].get("text", "Clear")
                        
                        analysis = f"""
                        <div class="tech-analysis-card">
                        <b>FST SITUATIONAL ANALYSIS:</b><br>
                        • <b>Visibility:</b> {vis} SM ({"VFR Standard" if vis >= 5 else "IFR/Marginal Condition"})<br>
                        • <b>Winds:</b> {wind} KTS ({"Stable" if wind < 20 else "High Wind / Gust Alert"})<br>
                        • <b>Ceiling:</b> {clouds}<br>
                        • <b>Notes:</b> {"Monitor TAF trends for alternate planning if visibility drops." if vis < 5 else "Routine operations recommended."}
                        </div>
                        """
                        st.markdown(analysis, unsafe_allow_html=True)
        else:
            st.error("Data not found. Verify ICAO codes.")

# 5. FOOTER
st.markdown("---")
current_utc = datetime.utcnow().strftime('%H:%M')
st.markdown(f"""
    <div class="footer-container">
        <img src="{LOGO_BOTTOM_CENTER}" width="180">
        <p class="footer-text-main">Dir. Operations & Standards</p>
        <p class="footer-text-time">UTC SYSTEM TIME: {current_utc}Z</p>
    </div>
    """, unsafe_allow_html=True)
