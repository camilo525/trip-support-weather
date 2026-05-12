import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Flight Support VIP Tool", page_icon="✈️", layout="wide")

# --- DISEÑO DE LA APP ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    .header-style {
        font-size: 24px; font-weight: bold;
        background: -webkit-linear-gradient(#00d4ff, #005fcc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    input { background-color: #0a0a0a !important; border: 1px solid #333333 !important; color: #00d4ff !important; }
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important;
        font-weight: bold; border: none; border-radius: 10px; height: 3.5em; width: 100%;
    }
    .footer-container { display: flex; flex-direction: column; align-items: center; padding: 40px 0px; border-top: 1px solid #222222; }
    </style>
    """, unsafe_allow_html=True)

LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png" 
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"
API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# --- HEADER ---
col_logo, col_title = st.columns([1, 8])
with col_logo: st.image(LOGO_UP_LEFT, width=300)
with col_title: st.markdown('<div class="header-style">Flight Support Team | VIP Milestone Manager</div>', unsafe_allow_html=True)

# --- SIDEBAR: GESTIÓN DE ETAPAS ---
st.sidebar.title("🛠 Trip Management")
etapa = st.sidebar.selectbox("FLIGHT MILESTONE (Etapa del Vuelo)", [
    "1. Trip Sheet Update (Confirmación de Datos)",
    "2. Crew & Tail Info (Itinerario Final)",
    "3. Positioning & Weather (Día del Vuelo/Ferry)",
    "4. Aircraft Ready & FBO (Pre-Despegue)",
    "5. Pushing Back (Iniciando Rodaje)"
])

origin = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
destination = st.sidebar.text_input("ARRIVAL ICAO", value="KMIA").upper()
etd = st.sidebar.text_input("ETD (UTC)", value="12:00")
eta = st.sidebar.text_input("ETA (UTC)", value="16:00")
tail = st.sidebar.text_input("TAIL NUMBER", value="N123VIP")

# --- LÓGICA DE CLIMA ---
def get_wx(icao):
    url = f"https://api.checkwx.com/metar/{icao}/decoded"
    try:
        r = requests.get(url, headers={"X-API-Key": API_KEY})
        data = r.json()
        return data["data"][0] if data.get("results", 0) > 0 else None
    except: return None

def generate_client_text(wx, icao, type="dep"):
    if not wx: return "Weather monitoring is active."
    raw = wx.get("raw_text", "").upper()
    vis = wx.get("visibility", {}).get("miles_float", 10)
    is_crit = any(x in raw for x in ["TS", "SN", "FG"]) or vis < 3
    if type == "dep":
        return f"Current conditions at {icao} are favorable for departure." if not is_crit else f"We are monitoring some weather activity at {icao} for your departure window."
    return f"Skies are clear for your arrival at {icao}." if not is_crit else f"Our team is tracking local activity at {icao} to ensure a smooth arrival."

# --- GENERADOR DE NEWSLETTER VIP ---
def generate_vip_card(etapa, origin, destination, etd, eta, tail, wx_org, wx_dst):
    # Textos dinámicos según etapa
    title = "FLIGHT STATUS UPDATE"
    main_msg = ""
    weather_section = ""

    if "1." in etapa:
        title = "TRIP SHEET UPDATED"
        main_msg = "Hemos recibido sus detalles (Pax/Equipaje). Adjunto encontrará el Trip Sheet actualizado con los detalles confirmados para su revisión."
    elif "2." in etapa:
        title = "FINAL ITINERARY CONFIRMED"
        main_msg = f"Detalles finales listos. Su aeronave con matrícula <b>{tail}</b> y la tripulación asignada se encuentran confirmadas para su misión."
    elif "3." in etapa:
        title = "POSITIONING & WEATHER"
        dep_w = generate_client_text(wx_org, origin, "dep")
        arr_w = generate_client_text(wx_dst, destination, "arr")
        main_msg = f"El avión <b>{tail}</b> está iniciando su reposicionamiento. Todo marcha según lo previsto para su salida."
        weather_section = f"""<div style='background:#f9f9f9; padding:15px; border-radius:10px; margin-top:15px;'>
                                <p style='color:#555; font-size:13px;'><b>Weather Departure:</b> {dep_w}</p>
                                <p style='color:#555; font-size:13px;'><b>Weather Arrival:</b> {arr_w}</p>
                              </div>"""
    elif "4." in etapa:
        title = "AIRCRAFT READY & FBO"
        main_msg = f"<b>Good News:</b> El avión {tail} ya se encuentra listo en plataforma, con combustible cargado y todos los chequeos de seguridad completados. El personal del FBO los estará esperando a su llegada para recibirlos y asistirles con el abordaje."
    elif "5." in etapa:
        title = "PUSHING BACK / TAXI"
        main_msg = f"Iniciando rodaje en {origin}. El tiempo estimado de vuelo es de {eta} (ETA). Nuestro equipo de Flight Support estará monitoreando su ruta en tiempo real hasta su destino."

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 550px; border: 1px solid #eee; border-radius: 15px; overflow: hidden; background-color: #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <div style="background-color: #000; padding: 25px; text-align: center;">
            <img src="{LOGO_UP_LEFT}" width="160">
            <h2 style="color: #00d4ff; font-size: 16px; letter-spacing: 3px; margin: 15px 0 0 0;">{title}</h2>
        </div>
        <div style="padding: 25px; text-align: center;">
            <p style="font-size: 28px; font-weight: bold; color: #333; margin: 0;">{origin} <span style="color:#00d4ff;">✈️</span> {destination}</p>
            <p style="color: #888; font-size: 13px; margin: 5px 0 20px 0;">TAIL: {tail} | ETD: {etd}Z</p>
            <p style="color: #444; line-height: 1.6; font-size: 15px; text-align: left;">{main_msg}</p>
            {weather_section}
        </div>
        <div style="background-color: #000; padding: 15px; text-align: center; color: #666; font-size: 10px;">
            VERIFIED BY FLIGHT SUPPORT TEAM | OPS & STANDARDS
        </div>
    </div>
    """
    return html

# --- BOTÓN DE ACCIÓN ---
if st.button("Generate VIP Milestone Briefing"):
    wx_org = get_wx(origin)
    wx_dst = get_wx(destination)
    
    st.markdown("### 📧 Gmail Preview (VIP Design)")
    card_html = generate_vip_card(etapa, origin, destination, etd, eta, tail, wx_org, wx_dst)
    
    # Vista previa
    st.components.v1.html(card_html, height=550)
    
    st.info("💡 **INSTRUCCIONES:**
