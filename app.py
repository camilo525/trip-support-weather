import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ops Assessment Tool v2.0", page_icon="✈️", layout="wide")

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
    .airport-label { color: #00d4ff; font-size: 0.85em; font-weight: bold; margin-bottom: 15px; line-height: 1.2; }
    .tech-card-origin { padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; background-color: rgba(0, 212, 255, 0.05); margin-bottom: 20px; }
    .tech-card-dest { padding: 20px; border-radius: 15px; border: 2px solid #a855f7; background-color: rgba(168, 85, 247, 0.05); margin-bottom: 20px; }
    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: #0a0a0a; padding: 10px; border-radius: 5px; font-size: 0.85em; line-height: 1.4; border: 1px solid #222; margin: 10px 0; }
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important;
        font-weight: bold; border: none; border-radius: 10px; height: 3.5em; width: 100%;
    }
    .executive-card { background: #ffffff; padding: 35px; border-radius: 20px; border-left: 8px solid #00d4ff; color: #111; }
    .data-row { display: flex; justify-content: space-between; font-size: 0.9em; margin-bottom: 4px; border-bottom: 1px solid #222; padding-bottom: 2px; }
    .footer-container { display: flex; flex-direction: column; align-items: center; padding: 40px 0; margin-top: 30px; border-top: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

# --- RECURSOS & API ---
LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png"
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"
API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

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
with col_title: st.markdown('<div class="header-style">Flight Support Team | Mission Assessment 2.0</div>', unsafe_allow_html=True)

# --- LOGICA DE EVALUACIÓN PRO ---
def evaluate_risk(wx):
    if not wx: return False, "No Data"
    
    vis = wx.get("visibility", {}).get("miles_float", 10)
    wind_spd = wx.get("wind", {}).get("speed_kts", 0)
    raw = wx.get("raw_text", "").upper()
    
    # Análisis de nubes (Ceiling)
    clouds = wx.get("clouds", [])
    # Buscamos la capa más baja que sea BKN o OVC
    ceiling = 10000 # Default alto
    for layer in clouds:
        if layer.get("code") in ["BKN", "OVC"]:
            ceiling = min(ceiling, layer.get("base_feet_agl", 10000))
            
    # CRITERIOS DE ALERTA
    is_crit = (
        vis < 3 or                  # Visibilidad baja
        wind_spd > 20 or            # Viento fuerte
        ceiling < 1000 or           # Techo bajo (LIFR/IFR)
        any(x in raw for x in ["TS", "SN", "FG", "SQ", "VCTS"]) # Fenómenos peligrosos
    )
    
    return is_crit, {"vis": vis, "wind": wind_spd, "ceiling": ceiling}

# --- EJECUCIÓN ---
if st.button("Run Advanced Mission Assessment"):
    wx_data_org = get_wx(origin_icao, fase)
    wx_data_dst = get_wx(destination_icao, fase)

    if wx_data_org and wx_data_dst:
        # Mapa (Mismo código anterior)
        o_lat, o_lon = wx_data_org['station']['geometry']['coordinates'][1], wx_data_org['station']['geometry']['coordinates'][0]
        d_lat, d_lon = wx_data_dst['station']['geometry']['coordinates'][1], wx_data_dst['station']['geometry']['coordinates'][0]
        fig = go.Figure(go.Scattergeo(lon=[o_lon, d_lon], lat=[o_lat, d_lat], mode='lines+markers', line=dict(width=2, color='#00d4ff')))
        fig.update_layout(geo=dict(showland=True, landcolor="#0a0a0a", bgcolor="rgba(0,0,0,0)"), margin=dict(l=0, r=0, t=0, b=0), height=300, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        risk_org, stats_org = evaluate_risk(wx_data_org)
        risk_dst, stats_dst = evaluate_risk(wx_data_dst)

        if tipo_reporte == "Executive (Client)":
            exec_html = f'<div class="executive-card"><h2 style="color:#005fcc; margin:0;">{origin_icao} ➔ {destination_icao}</h2>'
            exec_html += f'<p><b>Departure:</b> Weather is ' + ("under close monitoring. Expect coordination." if risk_org else "stable and favorable for departure.") + '</p>'
            exec_html += f'<p><b>Arrival:</b> Forecast is ' + ("showing activity. Ops Team monitoring." if risk_dst else "clear. Seamless arrival reported.") + '</p></div>'
            st.markdown(exec_html, unsafe_allow_html=True)
        
        else:
            st.markdown("### 🛠 OPS Advanced Technical Assessment")
            t1, t2 = st.columns(2)
            
            for col, wx, icao, time, color, css, risk, stats in zip(
                [t1, t2], [wx_data_org, wx_data_dst], [origin_icao, destination_icao], 
                [etd, eta], ["#00d4ff", "#a855f7"], ["tech-card-origin", "tech-card-dest"],
                [risk_org, risk_dst], [stats_org, stats_dst]
            ):
                with col:
                    status_lbl = '<span style="color:#ff3333; font-weight:bold;">🔴 CRITICAL</span>' if risk else '<span style="color:#00ff00; font-weight:bold;">🟢 NOMINAL</span>'
                    card_html = f'<div class="{css}">'
                    card_html += f'<h4 style="color:{color}; margin-bottom:5px;">{icao} | {time}Z</h4>'
                    card_html += f'<div class="raw-code">{wx.get("raw_text")}</div>'
                    card_html += f'<div class="data-row"><span>Visibility:</span> <b>{stats["vis"]} SM</b></div>'
                    card_html += f'<div class="data-row"><span>Sustained Wind:</span> <b>{stats["wind"]} KTS</b></div>'
                    card_html += f'<div class="data-row"><span>Cloud Ceiling:</span> <b>{stats["ceiling"]} FT</b></div>'
                    card_html += f'<p style="margin-top:10px;"><b>Risk Status:</b> {status_lbl}</p></div>'
                    st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.error("ICAO not found. Check codes.")

# --- FOOTER ---
st.markdown(f'<div class="footer-container"><img src="{LOGO_BOTTOM_CENTER}" width="160"><p style="color:#333; font-size:0.7em; margin-top:10px;">SYSTEM TIME: {datetime.utcnow().strftime("%H:%M")}Z</p></div>', unsafe_allow_html=True)
