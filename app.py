import streamlit as st
import requests
from datetime import datetime

# 1. CONFIGURACIÓN PROFESIONAL
st.set_page_config(page_title="Flight Support Team Weather Tool", page_icon="✈️", layout="wide")

# --- PERSONALIZACIÓN VISUAL (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stButton>button { background-color: #002e5d; color: white; font-weight: bold; width: 100%; border-radius: 8px; }
    .main-card { padding: 25px; border-radius: 12px; background-color: #f8f9fa; border: 1px solid #e0e0e0; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    
    /* Estilo para el logo del Footer */
    .footer-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px 0px;
        margin-top: 50px;
        border-top: 1px solid #eeeeee;
    }
    .footer-logo {
        filter: grayscale(20%);
        opacity: 0.8;
        transition: 0.3s;
    }
    .footer-logo:hover {
        opacity: 1;
        filter: grayscale(0%);
    }
    </style>
    """, unsafe_allow_html=True)

# --- DEFINICIÓN DE LOGOS ---
# REEMPLAZA ESTOS LINKS POR LOS DE TU EMPRESA
LOGO_PRINCIPAL = "https://thrust-aviation.com/wp-content/uploads/2024/02/Logo-White-500-2-e1710003051285.png" # Arriba Izquierda
LOGO_FOOTER = "https://ibb.co/b5bv4Rvv"    # Abajo Centro (Ejemplo genial)

API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# 2. ENCABEZADO CON LOGO ARRIBA A LA IZQUIERDA
col_header_1, col_header_2 = st.columns([1, 8])
with col_header_1:
    st.image(LOGO_PRINCIPAL, width=80)
with col_header_2:
    st.title("Flight Support Team Weather Tool")

st.markdown("---")

# 3. SIDEBAR - DETALLES DEL VUELO
st.sidebar.title("✈️ FST Dispatcher")
origin = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
etd = st.sidebar.text_input("ETD (UTC)", value="1200")
destination = st.sidebar.text_input("ARRIVAL ICAO", value="KMIA").upper()
eta = st.sidebar.text_input("ETA (UTC)", value="1600")

fase = st.sidebar.selectbox("PLANNING PHASE", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT STYLE", ["Executive / Client", "Technical / Support"])

st.markdown(f"**Route Analysis:** {origin} @ {etd}z ➔ {destination} @ {eta}z")

def get_wx(icao, phase):
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    headers = {"X-API-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers)
        return r.json()["data"][0] if r.json().get("results", 0) > 0 else None
    except: return None

# 4. LÓGICA PRINCIPAL
if st.button("EXECUTE MISSION ANALYSIS"):
    with st.spinner('Synchronizing with Global Aviation Weather Centers...'):
        wx_org = get_wx(origin, fase)
        wx_dst = get_wx(destination, fase)

        if wx_org and wx_dst:
            org_raw = wx_org.get("raw_text", "")
            dst_raw = wx_dst.get("raw_text", "")
            
            # Alertas Críticas
            alerts = []
            if any(x in org_raw + dst_raw for x in ["TS", "CB", "SQ"]): alerts.append("⛈️ STORM ACTIVITY DETECTED")
            if any(x in org_raw + dst_raw for x in ["SN", "FZDZ", "FZRA"]): alerts.append("❄️ ICING/SNOW CONDITIONS")
            
            for a in alerts:
                st.error(a)

            if tipo_reporte == "Executive / Client":
                st.subheader("Client Executive Briefing")
                report = f"""
                <div class="main-card">
                <b>DEPARTURE: {origin} (Scheduled {etd}Z)</b><br>
                • Our analysis for your departure time indicates favorable conditions. Visibility is clear.<br><br>
                <b>ARRIVAL: {destination} (Scheduled {eta}Z)</b><br>
                • Conditions at destination are being monitored. No significant weather-related delays expected.
                </div>
                """
                st.markdown(report, unsafe_allow_html=True)
            else:
                st.subheader("Internal Support Briefing")
                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"**ORIGIN: {origin}**")
                    st.text(f"Raw: {org_raw}")
                with c2:
                    st.info(f"**DESTINATION: {destination}**")
                    st.text(f"Raw: {dst_raw}")
        else:
            st.error("Could not fetch data. Please check ICAO codes.")

# 5. FOOTER CON LOGO ABAJO AL CENTRO
st.markdown(f"""
    <div class="footer-container">
        <img src="{LOGO_FOOTER}" width="120" class="footer-logo">
        <p style="margin-top:15px; color:#888888; font-size: 0.8em;">
            Dir. Operations & Standards<br>
            UTC Time: {datetime.utcnow().strftime('%H:%M')}Z
        </p>
    </div>
    """, unsafe_allow_html=True)
