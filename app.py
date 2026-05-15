import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ops Assessment Tool", page_icon="✈️", layout="wide")

# --- DISEÑO CSS (BLINDADO) ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    .header-style {
        font-size: 26px; font-weight: bold;
        background: -webkit-linear-gradient(#00d4ff, #005fcc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .airport-label { color: #00d4ff; font-size: 0.85em; font-weight: bold; margin-bottom: 15px; line-height: 1.2; }
    .tech-card-origin { padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; background-color: rgba(0, 212, 255, 0.05); margin-bottom: 20px; }
    .tech-card-dest { padding: 20px; border-radius: 15px; border: 2px solid #a855f7; background-color: rgba(168, 85, 247, 0.05); margin-bottom: 20px; }
    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: #0a0a0a; padding: 10px; border-radius: 5px; font-size: 0.9em; line-height: 1.4; border: 1px solid #222; }
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important;
        font-weight: bold; border: none; border-radius: 10px; height: 3.5em; width: 100%;
    }
    .executive-card { background: #ffffff; padding: 35px; border-radius: 20px; border-left: 8px solid #00d4ff; color: #111; }
    .footer-container { display: flex; flex-direction: column; align-items: center; padding: 40px 0; margin-top: 30px; border-top: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

# --- RECURSOS ---
LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png"
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"
API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# --- LÓGICA DE DATOS ---
def get_wx(icao, phase):
    if not icao or len(icao) < 3: return None
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    headers = {"X-API-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        return data["data"][0] if data.get("results", 0) > 0 else None
    except: return None

def get_coords(wx):
    try:
        coords = wx.get('station', {}).get('geometry', {}).get('coordinates', [None, None])
        return coords[1], coords[0]
    except: return None, None

# --- SIDEBAR ---
st.sidebar.title("Trip Configuration")
origin_icao = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
wx_org_name = get_wx(origin_icao, "Flight Day (Live)")
if wx_org_name:
    st.sidebar.markdown(f'<div class="airport-label">✈️ {wx_org_name.get("station",{}).get("name", "")}</div>', unsafe_allow_html=True)

destination_icao = st.sidebar.text_input("ARRIVAL ICAO", value="KOPF").upper()
wx_dst_name = get_wx(destination_icao, "Flight Day (Live)")
if wx_dst_name:
    st.sidebar.markdown(f'<div class="airport-label">✈️ {wx_dst_name.get("station",{}).get("name", "")}</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
etd = st.sidebar.text_input("ETD (UTC)", value="12:00")
eta = st.sidebar.text_input("ETA (UTC)", value="15:30")
fase = st.sidebar.selectbox("Assessment Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT MODE", ["Executive (Client)", "Technical (Internal)"])

# --- CABECERA ---
col_logo, col_title = st.columns([1, 4])
with col_logo: st.image(LOGO_UP_LEFT, width=250)
with col_title: st.markdown('<div class="header-style">Flight Support Team | Trip Assessment</div>', unsafe_allow_html=True)

# --- EJECUCIÓN PRINCIPAL ---
if st.button("Run Mission Assessment"):
    wx_data_org = get_wx(origin_icao, fase)
    wx_data_dst = get_wx(destination_icao, fase)

    if wx_data_org and wx_data_dst:
        # 1. MAPA DE RUTA
        o_lat, o_lon = get_coords(wx_data_org)
        d_lat, d_lon = get_coords(wx_data_dst)
        if o_lat and d_lat:
            fig = go.Figure(go.Scattergeo(
                lon=[o_lon, d_lon], lat=[o_lat, d_lat],
                mode='lines+markers', line=dict(width=2, color='#00d4ff'),
                marker=dict(size=10, color=['#00d4ff', '#a855f7'], symbol='diamond')
            ))
            fig.update_layout(geo=dict(showland=True, landcolor="#0a0a0a", bgcolor="rgba(0,0,0,0)"), 
                              margin=dict(l=0, r=0, t=0, b=0), height=400, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        # 2. EVALUACIÓN DE REPORTES
        if tipo_reporte == "Executive (Client)":
            def get_client_msg(wx, icao, is_dep=True):
                raw = wx.get("raw_text", "").upper()
                vis = wx.get("visibility", {}).get("miles_float", 10)
                crit = any(x in raw for x in ["TS", "SN", "FG", "DZ", "RA", "SQ"]) or vis < 3
                if is_dep:
                    return f"Weather analysis for departure from <b>{icao}</b> is " + ("unstable. Evaluating windows." if crit else "ideal. Stable window confirmed.")
                return f"Arrival forecast for <b>{icao}</b> is " + ("under monitoring due to activity." if crit else "favorable. Seamless arrival reported.")

            name_o = wx_data_org.get("station", {}).get("name", origin_icao)
            name_d = wx_data_dst.get("station", {}).get("name", destination_icao)
            
            exec_html = f'<div class="executive-card"><h2 style="color:#005fcc; margin:0;">{name_o} ➔ {name_d}</h2>'
            exec_html += f'<p><b>Departure:</b> {get_client_msg(wx_data_org, origin_icao, True)}</p>'
            exec_html += f'<p><b>Arrival:</b> {get_client_msg(wx_data_dst, destination_icao, False)}</p></div>'
            st.markdown(exec_html, unsafe_allow_html=True)
        
        else:
            # --- AQUÍ ESTÁ LA EVALUACIÓN TÉCNICA RECUPERADA ---
            st.markdown("### 🛠 OPS Technical Briefing")
            t1, t2 = st.columns(2)
            
            for col, wx, icao, time, color, css in zip([t1, t2], [wx_data_org, wx_data_dst], [origin_icao, destination_icao], [etd, eta], ["#00d4ff", "#a855f7"], ["tech-card-origin", "tech-card-dest"]):
                with col:
                    raw_text = wx.get("raw_text", "No data")
                    vis = wx.get("visibility", {}).get("miles_float", 10)
                    # Lógica de estatus técnico
                    is_crit = any(x in raw_text.upper() for x in ["TS", "SN", "FG", "SQ"]) or vis < 3
                    status_lbl = '<span style="color:#ff3333; font-weight:bold;">🔴 ALERT</span>' if is_crit else '<span style="color:#00ff00; font-weight:bold;">🟢 STABLE</span>'
                    
                    # Construcción segura del HTML técnico
                    card_html = f'<div class="{css}">'
                    card_html += f'<h4 style="color:{color}; margin-bottom:5px;">{icao} | {time}Z</h4>'
                    card_html += f'<div class="raw-code">{raw_text}</div>'
                    card_html += f'<hr style="border:0.5px solid #333; margin:15px 0;">'
                    card_html += f'<p style="margin:0;"><b>Visibility:</b> {vis} SM</p>'
                    card_html += f'<p style="margin:0;"><b>Ops Status:</b> {status_lbl}</p></div>'
                    st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.error("ICAO not found. Check codes.")

# --- FOOTER ---
st.markdown(f"""
    <div class="footer-container">
        <img src="{LOGO_BOTTOM_CENTER}" width="160">
        <p style="color:#555; font-size:0.8em; margin-top:10px;">Dir. Operations & Standards</p>
        <p style="color:#333; font-size:0.7em;">SYSTEM TIME: {datetime.utcnow().strftime("%H:%M")}Z</p>
    </div>
""", unsafe_allow_html=True)
