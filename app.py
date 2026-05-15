import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ops Control Center v7.2", layout="wide")

# --- ESTILOS CSS ---
st.markdown("<style>.stApp { background-color: #000; color: #fff; } .status-card { padding: 25px; border-radius: 15px; border: 1px solid #333; background: #0a0a0a; margin-bottom: 20px; } .raw-box { font-family: 'Courier New', monospace; color: #00ff00; background: #000; padding: 15px; font-size: 0.9em; border-left: 4px solid #00ff00; margin: 10px 0; } .executive-report { background: #ffffff; padding: 35px; border-radius: 20px; color: #111; border-left: 12px solid #005fcc; margin-bottom: 30px; } .metric-tag { display: inline-block; background: #1a1a1a; padding: 8px 12px; border-radius: 6px; margin-right: 10px; border: 1px solid #333; font-size: 0.9em; }</style>", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE LLAVE ---
CK_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

def get_ops_data(icao, phase):
    icao = icao.strip().upper()
    endpoint = "metar" if "Live" in phase else "taf"
    url = f"https://api.checkwx.com/{endpoint}/{icao}/decoded"
    try:
        r = requests.get(url, headers={"X-API-Key": CK_KEY}, timeout=12)
        data = r.json()
        if data.get("results", 0) > 0:
            wx = data["data"][0]
            stn = wx.get("station", {})
            return {
                "wx": wx, "name": stn.get("name", icao), "city": stn.get("city", "N/A"),
                "lat": stn.get("geometry", {}).get("coordinates", [0,0])[1],
                "lon": stn.get("geometry", {}).get("coordinates", [0,0])[0]
            }
    except: return None
    return None

# --- SIDEBAR ---
st.sidebar.image("https://static.wixstatic.com/media/5f5db0_453d7f17105a415a995e86d080031853~mv2.png/v1/fill/w_316,h_152,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/Logotipo%20Thrust%20Aviation_edited.png", width=220)
st.sidebar.title("Flight Support Desk")
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
            wind_spd = wx.get("wind", {}).get("speed_kts", 0)
            wind_dir = wx.get("wind", {}).get("degrees", 0)
            ceil = 10000
            if wx.get("clouds"):
                for l in wx["clouds"]:
                    if l.get("code") in ["BKN", "OVC"]:
                        ceil = min(ceil, l.get("base_feet_agl", 10000))
            
            if "Live" in phase:
                crit = (vis < 3 or wind_spd > 25 or ceil < 1000 or any(x in raw for x in ["TS", "FG", "SN"]))
                status, msg = ("🔴 CRITICAL", "Weather monitoring in effect.") if crit else ("🟢 NOMINAL", "Conditions stable.")
            elif "24h" in phase:
                crit = (vis < 5 or wind_spd > 20 or any(x in raw for x in ["PROB", "TEMPO", "TS"]))
                status, msg = ("🟡 MONITORING", "Fluctuations possible.") if crit else ("🟢 STABLE", "Favorable windows detected.")
            else:
                status, msg = "🔵 ADVISORY", "Outlook consistent with standards."
            
            return {"status": status, "vis": vis, "wind": f"{wind_dir}/{wind_spd}KT", "ceil": ceil, "msg": msg, "raw": raw}

        res_dep = analyze_technical(d_dep["wx"], fase)
        res_arr = analyze_technical(d_arr["wx"], fase)

        # 1. EXECUTIVE REPORT (Sin saltos de línea manuales en el string)
        exec_html = f"<div class='executive-report'><h2 style='margin:0; color:#005fcc;'>Executive Summary: {d_dep['name']} to {d_arr['name']}</h2><hr><p><b>Departure:</b> {res_dep['status']} — {res_dep['msg']}</p><p><b>Arrival:</b> {res_arr['status']} — {res_arr['msg']}</p></div>"
        st.markdown(exec_html, unsafe_allow_html=True)

        # 2. TECHNICAL
        c1, c2 = st.columns(2)
        for col, icao, res, info, color in zip([c1, c2], [dep_icao, arr_icao], [res_dep, res_arr], [d_dep, d_arr], ["#00d4ff", "#a855f7"]):
            with col:
                st.markdown(f"<div class='status-card' style='border-top: 6px solid {color}'><h3 style='margin:0; color:{color};'>{info['name']}</h3><div class='raw-box'>{res['raw']}</div><div style='margin-top:15px;'><span class='metric-tag'>VIS: {res['vis']} SM</span><span class='metric-tag'>WIND: {res['wind']}</span><span class='metric-tag'>CEIL: {res['ceil']} FT</span></div></div>", unsafe_allow_html=True)
        
        # 3. MAPA
        fig = go.Figure(go.Scattergeo(lat=[d_dep['lat'], d_arr['lat']], lon=[d_dep['lon'], d_arr['lon']], mode='lines+markers', line=dict(width=2, color='#00d4ff')))
        fig.update_layout(geo=dict(showland=True, landcolor="#111", bgcolor="rgba(0,0,0,0)"), height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

        # 4. LOGO FBO AUDIT
        f1, f2, f3 = st.columns([1, 1, 1])
        with f2: st.image("https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png", width=150)
    else:
        st.error("❌ Data Sync Failure. Verify ICAO codes.")
