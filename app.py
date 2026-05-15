import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ops Assessment Tool", page_icon="✈️", layout="wide")

# --- DISEÑO CSS ---
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
    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: transparent; font-size: 0.95em; line-height: 1.4; }
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important;
        font-weight: bold; border: none; border-radius: 10px; height: 3.5em; width: 100%;
    }
    .tool-container { display: flex; gap: 15px; margin: 25px 0; flex-wrap: wrap; }
    .tool-btn {
        flex: 1; min-width: 180px; padding: 12px; border-radius: 10px;
        text-align: center; text-decoration: none; font-weight: bold; font-size: 0.85em;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .btn-sat { background: rgba(0, 212, 255, 0.1); color: #00d4ff !important; border-color: #00d4ff; }
    .btn-map { background: rgba(168, 85, 247, 0.1); color: #a855f7 !important; border-color: #a855f7; }
    .btn-notam { background: rgba(255, 204, 0, 0.1); color: #ffcc00 !important; border-color: #ffcc00; }
    .executive-card { background: #ffffff; padding: 35px; border-radius: 20px; border-left: 8px solid #00d4ff; color: #111; }
    .footer-container { display: flex; flex-direction: column; align-items: center; padding: 40px 0; margin-top: 30px; border-top: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

# --- RECURSOS ---
LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png"
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"
API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# --- CABECERA (Aquí estaba el error) ---
col_logo, col_title = st.columns([1, 4]) # <-- Definición de las variables
with col_logo:
    st.image(LOGO_UP_LEFT, width=250)
with col_title:
    st.markdown('<div class="header-style">Flight Support Team | Trip Assessment</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("Trip Configuration")
origin = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
etd = st.sidebar.text_input("ETD (UTC)", value="12:00")
destination = st.sidebar.text_input("ARRIVAL ICAO", value="KOPF").upper()
eta = st.sidebar.text_input("ETA (UTC)", value="15:30")
fase = st.sidebar.selectbox("Assessment Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT MODE", ["Executive (Client)", "Technical (Internal)"])

# --- DATA LOGIC ---
def get_wx(icao, phase):
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = "https://api.checkwx.com/" + stype + "/" + icao + "/decoded"
    headers = {"X-API-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        return data["data"][0] if data.get("results", 0) > 0 else None
    except: return None

def get_coords(wx):
    try:
        c = wx.get('station', {}).get('geometry', {}).get('coordinates', [None, None])
        return c[1], c[0]
    except: return None, None

# --- EXECUTION ---
if st.button("Run Mission Assessment"):
    wx_org = get_wx(origin, fase)
    wx_dst = get_wx(destination, fase)

    if wx_org and wx_dst:
        o_lat, o_lon = get_coords(wx_org)
        d_lat, d_lon = get_coords(wx_dst)
        
        if o_lat and d_lat:
            fig = go.Figure(go.Scattergeo(
                lon=[o_lon, d_lon], lat=[o_lat, d_lat],
                mode='lines+markers', line=dict(width=2, color='#00d4ff'),
                marker=dict(size=10, color=['#00d4ff', '#a855f7'])
            ))
            fig.update_layout(geo=dict(showland=True, landcolor="#0a0a0a", bgcolor="rgba(0,0,0,0)"), 
                              margin=dict(l=0, r=0, t=0, b=0), height=400, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        if tipo_reporte == "Executive (Client)":
            raw_o = wx_org.get("raw_text", "").upper()
            vis_o = wx_org.get("visibility", {}).get("miles_float", 10)
            crit_o = any(x in raw_o for x in ["TS", "SN", "FG", "DZ", "RA", "SQ"]) or vis_o < 3
            
            raw_d = wx_dst.get("raw_text", "").upper()
            vis_d = wx_dst.get("visibility", {}).get("miles_float", 10)
            crit_d = any(x in raw_d for x in ["TS", "SN", "FG", "DZ", "RA", "SQ"]) or vis_d < 3

            msg_o = "unstable. Evaluating windows." if crit_o else "ideal. Stable window confirmed."
            msg_d = "under monitoring due to activity." if crit_d else "favorable. Seamless arrival reported."

            exec_html = '<div class="executive-card"><h2 style="color:#005fcc; margin:0;">Flight Briefing: ' + origin + ' ➔ ' + destination + '</h2>'
            exec_html += '<p><b>Departure:</b> Weather analysis for departure from <b>' + origin + '</b> is ' + msg_o + '</p>'
            exec_html += '<p><b>Arrival:</b> Arrival forecast for <b>' + destination + '</b> is ' + msg_d + '</p></div>'
            st.markdown(exec_html, unsafe_allow_html=True)
            
        else:
            st.markdown("### 🛠 OPS Toolkit")
            toolkit = '<div class="tool-container">'
            toolkit += '<a href="https://www.star.nesdis.noaa.gov/GOES/conus_band.php?sat=G16&band=11&length=24" target="_blank" class="tool-btn btn-sat">🛰 LIVE SAT</a>'
            toolkit += '<a href="https://www.weather.gov/forecastmaps/" target="_blank" class="tool-btn btn-map">🗺 NWS MAPS</a>'
            toolkit += '<a href="https://notams.aim.faa.gov/notamSearch/" target="_blank" class="tool-btn btn-notam">🔎 FAA NOTAMS</a></div>'
            st.markdown(toolkit, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                vis = wx_org.get("visibility", {}).get("miles_float", 10)
                status = '🔴 ALERT' if (any(x in wx_org.get("raw_text", "").upper() for x in ["TS", "SN", "FG", "SQ"]) or vis < 3) else '🟢 STABLE'
                card_o = '<div class="tech-card-origin"><h4 style="color:#00d4ff;">' + origin + ' @ ' + etd + 'Z</h4>'
                card_o += '<p class="raw-code">' + wx_org["raw_text"] + '</p>'
                card_o += '<hr style="border:0.5px solid #333;"><p><b>Vis:</b> ' + str(vis) + ' SM | <b>Status:</b> ' + status + '</p></div>'
                st.markdown(card_o, unsafe_allow_html=True)
            with c2:
                vis = wx_dst.get("visibility", {}).get("miles_float", 10)
                status = '🔴 ALERT' if (any(x in wx_dst.get("raw_text", "").upper() for x in ["TS", "SN", "FG", "SQ"]) or vis < 3) else '🟢 STABLE'
                card_d = '<div class="tech-card-dest"><h4 style="color:#a855f7;">' + destination + ' @ ' + eta + 'Z</h4>'
                card_d += '<p class="raw-code">' + wx_dst["raw_text"] + '</p>'
                card_d += '<hr style="border:0.5px solid #333;"><p><b>Vis:</b> ' + str(vis) + ' SM | <b>Status:</b> ' + status + '</p></div>'
                st.markdown(card_d, unsafe_allow_html=True)
    else:
        st.error("ICAO not found. Verify codes and connection.")

# --- FOOTER ---
footer = '<div class="footer-container"><img src="' + LOGO_BOTTOM_CENTER + '" width="160">'
footer += '<p style="color:#555; font-size:0.8em; margin-top:10px;">Dir. Operations & Standards</p>'
footer += '<p style="color:#333; font-size:0.7em;">SYSTEM TIME: ' + datetime.utcnow().strftime("%H:%M") + 'Z</p></div>'
st.markdown(footer, unsafe_allow_html=True)
