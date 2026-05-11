import streamlit as st
import requests
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Flight Support Team Weather Tool", page_icon="✈️", layout="wide")

# --- FORZAR MODO OSCURO TOTAL (BLACK BACKGROUND) ---
st.markdown("""
    <style>
    /* Fondo negro para toda la aplicación */
    .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }
    
    /* Forzar que todos los textos sean blancos o grises claros */
    .stMarkdown, p, h1, h2, h3, h4, span, label, .stSelectbox, .stTextInput {
        color: #FFFFFF !important;
    }

    /* Estilo de los campos de entrada (Input Boxes) */
    input {
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
    }

    /* Estilo de la Sidebar (Barra Lateral) en negro */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #222222;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* Botón Principal estilo Neón/Aeronáutico */
    .stButton>button {
        background-color: #004a99 !important;
        color: white !important;
        font-weight: bold;
        width: 100%;
        border-radius: 8px;
        border: 1px solid #005fcc;
        height: 3.5em;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        background-color: #005fcc !important;
        border: 1px solid #007fff;
    }
    
    /* Caja de reporte del cliente (Gris muy oscuro para contraste) */
    .main-card {
        padding: 25px;
        border-radius: 12px;
        background-color: #111111 !important;
        border: 1px solid #222222;
        color: #e0e0e0 !important;
    }

    /* Footer */
    .footer-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px 0px;
        margin-top: 50px;
        border-top: 1px solid #222222;
    }
    
    /* Estilo para los bloques de código técnico */
    code {
        background-color: #1a1a1a !important;
        color: #00ff00 !important; /* Verde terminal para el equipo técnico */
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN DE LOGOS (USA TUS LINKS AQUÍ) ---
LOGO_PRINCIPAL = "TU_LINK_AQUI" 
LOGO_FOOTER = "TU_OTRO_LINK_AQUI"

API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# 2. ENCABEZADO
col_header_1, col_header_2 = st.columns([1, 8])
with col_header_1:
    if LOGO_PRINCIPAL != "TU_LINK_AQUI":
        st.image(LOGO_PRINCIPAL, width=80)
with col_header_2:
    st.title("Flight Support Team Weather Tool")

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
    with st.spinner('Synchronizing with Aviation Servers...'):
        wx_org = get_wx(origin, fase)
        wx_dst = get_wx(destination, fase)

        if wx_org and wx_dst:
            org_raw = wx_org.get("raw_text", "")
            dst_raw = wx_dst.get("raw_text", "")
            
            if tipo_reporte == "Executive (Client)":
                st.subheader("Client Executive Briefing")
                report = f"""
                <div class="main-card">
                <b style="color:#4dabf7">DEPARTURE: {origin} (Scheduled {etd}Z)</b><br>
                • Analysis indicates favorable conditions for departure. Visibility is optimal.<br><br>
                <b style="color:#4dabf7">ARRIVAL: {destination} (Scheduled {eta}Z)</b><br>
                • Destination weather is within operational limits. No significant delays expected.
                </div>
                """
                st.markdown(report, unsafe_allow_html=True)
            else:
                st.subheader("Internal Technical Brief")
                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"**ORIGIN: {origin}**")
                    st.code(org_raw)
                with c2:
                    st.info(f"**DESTINATION: {destination}**")
                    st.code(dst_raw)
        else:
            st.error("Data not found. Verify ICAO codes.")

# 5. FOOTER
st.markdown(f"""
    <div class="footer-container">
        {"<img src='" + LOGO_FOOTER + "' width='150'>" if LOGO_FOOTER != "TU_OTRO_LINK_AQUI" else ""}
        <p style="margin-top:20px; color:#555555; font-size: 0.9em; letter-spacing: 2px;">
            FLIGHT SUPPORT TEAM | AI DIVISION<br>
            UTC TIME: {datetime.utcnow().strftime('%H:%M')}Z
        </p>
    </div>
    """, unsafe_allow_html=True)
