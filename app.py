import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Ops Control Center v4.5", layout="wide")

# --- ESTILOS OCC AVANZADOS ---
st.markdown("""<style>
    .stApp { background-color: #000; color: #fff; }
    .status-card { padding: 20px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #222; background: #0a0a0a; }
    .raw { font-family: 'Courier New', monospace; color: #00ff00; background: #000; padding: 12px; font-size: 0.85em; border-left: 3px solid #00ff00; margin: 10px 0; }
    .vip-report { background: #ffffff; padding: 30px; border-radius: 15px; color: #000; border-left: 10px solid #005fcc; }
    .window-badge { padding: 4px 10px; border-radius: 5px; font-size: 0.7em; font-weight: bold; text-transform: uppercase; margin-bottom: 10px; display: inline-block; }
</style>""", unsafe_allow_html=True)

# --- CONFIGURACIÓN ---
CK_KEY = "1b89b9a703e34d8596a1b932c0d30a82"
AD_KEY = "d6ae47d1-8477-42c4-9f26-dc4e7939a81b"

def get_ops_data(icao, phase):
    icao = icao.strip().upper()
    # Cambiamos el endpoint según la necesidad real de la ventana
    endpoint = "metar" if phase == "Live Ops (METAR)" else "taf"
    try:
        r_wx = requests.get(f"https://api.checkwx.com/{endpoint}/{icao}/decoded", headers={"X-API-Key": CK_KEY}, timeout=7).json()
        r_ap = requests.get(f"https://aerodatabox.p.rapidapi.com/airports/icao/{icao}", 
                            headers={"X-RapidAPI-Key": AD_KEY, "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"}, timeout=7).json()
        
        wx = r_wx["data"][0] if r_wx.get("results", 0) > 0 else None
        ap = {"name": r_ap.get("name", icao), "city": r_ap.get("municipalityName", "Loc"), 
              "lat": r_ap.get("location", {}).get("lat", 0), "lon": r_ap.get("location", {}).get("lon", 0)}
        return wx, ap
    except: return None, {"name": icao, "city": "N/A", "lat": 0, "lon": 0}

# --- SIDEBAR ---
st.sidebar.header("✈️ Mission Briefing")
o_icao = st.sidebar.text_input("ORIGIN", "KTEB").upper()
d_icao = st.sidebar.text_input("DESTINATION", "KMIA").upper()
# Definición de Ventanas según tu requerimiento
fase = st.sidebar.selectbox("Analysis Window", 
                            ["Live Ops (METAR)", "24h Pre-Flight (TAF)", "48h Outlook (Trends)"])

if st.button("GENERATE OPERATIONAL ASSESSMENT"):
    w_o, a_o = get_ops_data(o_icao, fase)
    w_d, a_d = get_ops_data(d_icao, fase)

    if w_o and w_d:
        def advanced_eval(wx, phase):
            raw = wx.get("raw_text", "").upper()
            vis = wx.get("visibility", {}).get("miles_float", 10)
            wind = wx.get("wind", {}).get("speed_kts", 0)
            
            # Lógica por Ventana
            if phase == "Live Ops (METAR)":
                is_crit = (vis < 3 or wind > 25 or any(x in raw for x in ["TS", "FG", "SN", "SQ"]))
                msg = "🔴 CRITICAL - IMMEDIATE ACTION" if is_crit else "🟢 NOMINAL - EXECUTE"
            elif phase == "24h Pre-Flight (TAF)":
                is_crit = (vis < 5 or wind > 20 or any(x in raw for x in ["PROB", "TEMPO", "TS"]))
                msg = "🟡 MONITORING - TAF REVISION" if is_crit else "🟢 STABLE - PLAN CONFIRMED"
            else: # 48h Outlook
                is_crit = any(x in raw for x in ["TS", "DZ", "RA", "SN", "VCTS"])
                msg = "🔵 ADVISORY - TREND ANALYSIS" if is_crit else "🟢 CLEAR - PROCEED"
            return msg, vis, wind

        st_o, v_o, wd_o = advanced_eval(w_o, fase)
        st_d, v_d, wd_d = advanced_eval(w_d, fase)

        # --- REPORTE EJECUTIVO ---
        st.markdown(f"""<div class="vip-report">
            <h2 style="margin:0;">{a_o['name']} ➔ {a_d['name']}</h2>
            <p style="color:#005fcc; font-weight:bold;">{fase} | Assessment ID: {datetime.utcnow().strftime('%y%m%d-%H%M')}Z</p>
            <hr>
            <p><b>Departure Assessment:</b> {st_o}</p>
            <p><b>Arrival Assessment:</b> {st_d}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("### 🛠 Technical Specifications")
        c1, c2 = st.columns(2)
        
        for col, icao, status, wx, color in zip([c1, c2], [o_icao, d_icao], [st_o, st_d], [w_o, w_d], ["#00d4ff", "#a855f7"]):
            with col:
                badge_bg = "#ff3333" if "CRITICAL" in status or "MONITORING" in status else "#00ff00"
                col.markdown(f"""<div class="status-card" style="border-top: 4px solid {color}">
                    <span class="window-badge" style="background:{badge_bg}; color:#fff;">{status}</span>
                    <h4 style="margin:0; color:{color};">{icao} Report</h4>
                    <div class="raw">{wx['raw_text']}</div>
                    <p style="font-size:0.9em; margin-top:10px;">
                        <b>Ops Window:</b> {fase}<br>
                        <b>Internal Note:</b> Data synchronized with global aviation datalink.
                    </p>
                </div>""", unsafe_allow_html=True)
    else:
        st.error("Connection Error: Verify ICAO or API Key Status.")
