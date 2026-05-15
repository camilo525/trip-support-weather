import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ops Control Center v6.1", layout="wide")

# --- ESTILOS VISUALES ---
st.markdown("""<style>
    .stApp { background-color: #000; color: #fff; }
    .status-card { padding: 20px; border-radius: 12px; border: 1px solid #222; background: #0a0a0a; margin-bottom: 15px; }
    .raw { font-family: 'Courier New', monospace; color: #00ff00; background: #000; padding: 12px; font-size: 0.85em; border-left: 3px solid #00ff00; overflow-x: auto; }
    .vip-report { background: #fff; padding: 30px; border-radius: 15px; color: #000; border-left: 10px solid #005fcc; margin-bottom: 25px; }
    .metric-inline { display: inline-block; margin-right: 20px; font-size: 1em; font-weight: bold; color: #00d4ff; }
</style>""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE API ---
CK_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

def get_mission_data(icao, phase):
    icao = icao.strip().upper()
    # Selección de endpoint: METAR para tiempo real, TAF para planificación
    endpoint = "metar" if "Live" in phase else "taf"
    url = f"https://api.checkwx.com/{endpoint}/{icao}/decoded"
    
    try:
        r = requests.get(url, headers={"X-API-Key": CK_KEY}, timeout=10)
        data = r.json()
        if data.get("results", 0) > 0:
            wx = data["data"][0]
            station = wx.get("station", {})
            coords = station.get("geometry", {}).get("coordinates", [0,0])
            return {
                "wx": wx,
                "name": station.get("name", icao),
                "city": station.get("city", "N/A"),
                "lat": coords[1],
                "lon": coords[0]
            }
    except:
        return None
    return None

# --- SIDEBAR ---
st.sidebar.header("✈️ Mission Briefing")
dep_icao = st.sidebar.text_input("DEPARTURE ICAO", "KTEB").upper()
arr_icao = st.sidebar.text_input("ARRIVAL ICAO", "KMIA").upper()
fase = st.sidebar.selectbox("Analysis Window", 
                            ["Live Ops (METAR)", "24h Pre-Flight (TAF)", "48h Outlook (Trends)"])

# --- HEADER ---
st.markdown('<h1 style="color:#00d4ff; margin-bottom:0;">OCC Mission Assessment</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#555; margin-bottom:30px;">Flight Support Operations | Global Weather Datalink</p>', unsafe_allow_html=True)

# --- EJECUCIÓN ---
if st.button("GENERATE OPERATIONAL ASSESSMENT"):
    with st.spinner("Processing flight parameters..."):
        d_dep = get_mission_data(dep_icao, fase)
        d_arr = get_mission_data(arr_icao, fase)

    if d_dep and d_arr:
        # LÓGICA DE EVALUACIÓN SEGÚN VENTANA
        def evaluate_risk(wx, phase):
            raw = wx.get("raw_text", "").upper()
            vis = wx.get("visibility", {}).get("miles_float", 10)
            wind = wx.get("wind", {}).get("speed_kts", 0)
            
            # Cálculo de Ceiling (Techo de nubes)
            ceil = 10000
            for layer in wx.get("clouds", []):
                if layer.get("code") in ["BKN", "OVC"]:
                    ceil = min(ceil, layer.get("base_feet_agl", 10000))
            
            if "Live" in phase:
                crit = (vis < 3 or wind > 25 or ceil < 1000 or any(x in raw for x in ["TS", "FG", "SN", "SQ"]))
                msg = "🔴 CRITICAL - EXECUTION ALERT" if crit else "🟢 NOMINAL - PROCEED"
            elif "24h" in phase:
                crit = (vis < 5 or wind > 20 or ceil < 1500 or any(x in raw for x in ["PROB", "TEMPO", "TS"]))
                msg = "🟡 MONITORING - TAF REVISION" if crit else "🟢 STABLE - PLAN CONFIRMED"
            else:
                crit = any(x in raw for x in ["TS", "RA", "SN", "DZ", "VCTS"])
                msg = "🔵 ADVISORY - TREND ANALYSIS" if crit else "🟢 CLEAR - NO TRENDS"
            return msg, vis, wind, ceil

        st_dep, v_dep, w_dep, c_dep = evaluate_risk(d_dep["wx"], fase)
        st_arr, v_arr, w_arr, c_arr = evaluate_risk(d_arr["wx"], fase)

        # 1. REPORTE EJECUTIVO (VIP)
        st.markdown(f"""<div class="vip-report">
            <h2 style="margin:0; color:#005fcc;">{d_dep['name']} ➔ {d_arr['name']}</h2>
            <p style="color:#777; font-weight:bold; margin-bottom:20px;">{fase} | ID: {datetime.utcnow().strftime('%y%m%d-%H%M')}Z</p>
            <p style="font-size:1.15em;"><b>Departure Assessment:</b> {st_dep}</p>
            <p style="font-size:1.15em;"><b>Arrival Assessment:</b> {st_arr}</p>
        </div>""", unsafe_allow_html=True)

        # 2. MAPA DE RUTA
        fig = go.Figure(go.Scattergeo(
            lat=[d_dep['lat'], d_arr['lat']],
            lon=[d_dep['lon'], d_arr['lon']],
            mode='lines+markers',
            line=dict(width=2, color='#00d4ff'),
            marker=dict(size=10, color=['#00d4ff', '#a855f7'], symbol='diamond')
        ))
        fig.update_layout(geo=dict(showland=True, landcolor="#111", bgcolor="rgba(0,0,0,0)"), 
                          height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

        # 3. ESPECIFICACIONES TÉCNICAS
        st.markdown("### 🛠 Technical Specifications")
        col1, col2 = st.columns(2)
        
        for col, icao, info, status, v, w, c, color in zip(
            [col1, col2], [dep_icao, arr_icao], [d_dep, d_arr], [st_dep, st_arr], 
            [v_dep, v_arr], [w_dep, w_arr], [c_dep, c_arr], ["#00d4ff", "#a855f7"]
        ):
            with col:
                st.markdown(f"""<div class="status-card" style="border-top: 4px solid {color}">
                    <h4 style="margin:0; color:{color};">{info['name']} Technical Briefing</h4>
                    <p style="font-size:0.85em; color:#aaa; margin-bottom:10px;">Location: {info['city']}</p>
                    <div class="raw">{info['wx']['raw_text']}</div>
                    <div style="margin-top:15px;">
                        <span class="metric-inline">VIS: {v} SM</span>
                        <span class="metric-inline">WIND: {w} KT</span>
                        <span class="metric-inline">CEIL: {c} FT</span>
                    </div>
                    <p style="margin-top:15px; font-weight:bold;">Status: {status}</p>
                </div>""", unsafe_allow_html=True)
    else:
        st.error("❌ Data Synchronization Error: Verify ICAO codes or API limits.")
