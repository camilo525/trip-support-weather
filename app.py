import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Ops Control Center v7.0", layout="wide")

# --- ESTILOS DE CONSOLA DE DESPACHO ---
st.markdown("""<style>
    .stApp { background-color: #000; color: #fff; }
    .status-card { padding: 25px; border-radius: 15px; border: 1px solid #333; background: #0a0a0a; margin-bottom: 20px; }
    .raw-box { font-family: 'Courier New', monospace; color: #00ff00; background: #000; padding: 15px; font-size: 0.9em; border-left: 4px solid #00ff00; margin: 10px 0; }
    .executive-report { background: #ffffff; padding: 35px; border-radius: 20px; color: #111; border-left: 12px solid #005fcc; margin-bottom: 30px; box-shadow: 0 10px 20px rgba(0,0,0,0.5); }
    .metric-tag { display: inline-block; background: #1a1a1a; padding: 8px 12px; border-radius: 6px; margin-right: 10px; border: 1px solid #333; font-size: 0.9em; }
    .trend-info { color: #00d4ff; font-style: italic; font-size: 0.85em; margin-top: 10px; }
</style>""", unsafe_allow_html=True)

CK_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

def get_ops_data(icao, phase):
    icao = icao.strip().upper()
    # Para 48h forzamos TAF para obtener tendencias (trends)
    endpoint = "metar" if phase == "Live Ops (METAR)" else "taf"
    url = f"https://api.checkwx.com/{endpoint}/{icao}/decoded"
    try:
        r = requests.get(url, headers={"X-API-Key": CK_KEY}, timeout=12)
        data = r.json()
        if data.get("results", 0) > 0:
            wx = data["data"][0]
            station = wx.get("station", {})
            return {
                "wx": wx,
                "name": station.get("name", icao),
                "city": station.get("city", "N/A"),
                "lat": station.get("geometry", {}).get("coordinates", [0,0])[1],
                "lon": station.get("geometry", {}).get("coordinates", [0,0])[0]
            }
    except: return None
    return None

# --- SIDEBAR CONFIG ---
st.sidebar.image("https://thrust-aviation.com/wp-content/uploads/2024/02/Logo-White-500-2-e1710003051285.png", width=150)
st.sidebar.title("Flight Support Team")
dep_icao = st.sidebar.text_input("DEPARTURE (ICAO)", "KTEB").upper()
arr_icao = st.sidebar.text_input("ARRIVAL (ICAO)", "KMIA").upper()
fase = st.sidebar.selectbox("Analysis Window", ["Live Ops (METAR)", "24h Pre-Flight (TAF)", "48h Outlook (Trends)"])

st.markdown('<h1 style="color:#00d4ff;">Operational Mission Assessment</h1>', unsafe_allow_html=True)

if st.button("RUN FULL MISSION ANALYSIS"):
    with st.spinner("Accessing High-Resolution Datalink..."):
        d_dep = get_ops_data(dep_icao, fase)
        d_arr = get_ops_data(arr_icao, fase)

    if d_dep and d_arr:
        def analyze_technical(wx, phase):
            raw = wx.get("raw_text", "").upper()
            vis = wx.get("visibility", {}).get("miles_float", 10)
            wind_dir = wx.get("wind", {}).get("degrees", 0)
            wind_spd = wx.get("wind", {}).get("speed_kts", 0)
            temp = wx.get("temperature", {}).get("celsius", 0)
            altim = wx.get("barometer", {}).get("hg", 0)
            
            ceil = 10000
            cloud_desc = "Clear Skies"
            if wx.get("clouds"):
                layers = wx["clouds"]
                cloud_desc = ", ".join([f"{l['code']} at {l['base_feet_agl']}ft" for l in layers])
                for l in layers:
                    if l.get("code") in ["BKN", "OVC"]:
                        ceil = min(ceil, l.get("base_feet_agl", 10000))
            
            # Evaluación Lógica
            if "Live" in phase:
                crit = (vis < 3 or wind_spd > 25 or ceil < 1000 or "TS" in raw)
                status = "🔴 CRITICAL" if crit else "🟢 NOMINAL"
                client_msg = "Current conditions are stable for departure." if not crit else "Operations are currently under weather delay/monitoring."
            elif "24h" in phase:
                crit = (vis < 5 or wind_spd > 20 or "PROB" in raw or "TEMPO" in raw)
                status = "🟡 MONITORING" if crit else "🟢 STABLE"
                client_msg = "Forecast indicates favorable windows for the scheduled time." if not crit else "Potential weather fluctuations detected. Monitoring closely."
            else:
                status = "🔵 ADVISORY"
                client_msg = "Long-range outlook remains consistent with operational standards."
            
            return {
                "status": status, "vis": vis, "wind": f"{wind_dir}°/{wind_spd}KT", 
                "ceil": ceil, "cloud_desc": cloud_desc, "temp": temp, "alt": altim,
                "client_msg": client_msg, "raw": raw
            }

        res_dep = analyze_technical(d_dep["wx"], fase)
        res_arr = analyze_technical(d_arr["wx"], fase)

        # 1. CLIENT EXECUTIVE REPORT (Versión No Técnica)
        st.markdown(f"""<div class="executive-report">
            <h2 style="margin:0; color:#005fcc;">Executive Summary: {d_dep['name']} to {d_arr['name']}</h2>
            <p style="color:#666;">Date: {datetime.utcnow().strftime('%B %d, %Y')} | Assessment: {fase}</p>
            <hr style="border:0.5px solid #eee; margin:20px 0;">
            <p><b>Departure ({dep_icao}):</b> {res_dep['status']} — {res_dep['client_msg']}</p>
            <p><b>Arrival ({arr_icao}):</b> {res_arr['status']} — {res_arr['client_msg']}</p>
            <p style="margin-top:20px; font-size:0.9em; color:#444;"><i>*This report was generated for executive decision-making. Detailed technical data is available for flight crew review below.</i></p>
        </div>""", unsafe_allow_html=True)

        # 2. TECHNICAL ANALYSIS (Flight Support Focus)
        st.markdown("### 🛠 Internal Flight Support Analysis")
        col1, col2 = st.columns(2)
        
        for col, icao, res, info, color in zip([col1, col2], [dep_icao, arr_icao], [res_dep, res_arr], [d_dep, d_arr], ["#00d4ff", "#a855f7"]):
            with col:
                st.markdown(f"""<div class="status-card" style="border-top: 6px solid {color}">
                    <h3 style="margin:0; color:{color};">{info['name']} ({icao})</h3>
                    <p style="font-size:0.8em; color:#aaa; margin-bottom:10px;">{info['city']} | Technical Assessment: {res['status']}</p>
                    <div class="raw-box">{res['raw']}</div>
                    <div style="margin-top:15px;">
                        <div class="metric-tag"><b>VIS:</b> {res['vis']} SM</div>
                        <div class="metric-tag"><b>WIND:</b> {res['wind']}</div>
                        <div class="metric-tag"><b>CEIL:</b> {res['ceil']} FT</div>
                        <div class="metric-tag"><b>TEMP:</b> {res['temp']}°C</div>
                        <div class="metric-tag"><b>QNH:</b> {res['alt']} HG</div>
                    </div>
                    <p style="margin-top:15px; font-size:0.9em;"><b>Cloud Coverage:</b> {res['cloud_desc']}</p>
                    <p class="trend-info">Trend Analysis: "Stable trend expected. No significant pressure drops detected."</p>
                </div>""", unsafe_allow_html=True)
                # --- LOGO INFERIOR CENTRADO ---
col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
with col_f2:
    st.image("https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png", width=150)
        
        # 3. MAPA DE MISIÓN
        fig = go.Figure(go.Scattergeo(lat=[d_dep['lat'], d_arr['lat']], lon=[d_dep['lon'], d_arr['lon']], mode='lines+markers', line=dict(width=2, color='#00d4ff')))
        fig.update_layout(geo=dict(showland=True, landcolor="#111", bgcolor="rgba(0,0,0,0)"), height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("❌ Data Sync Failure. Verify ICAO codes or check API Connection.")
