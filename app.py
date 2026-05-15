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
    endpoint = "metar" if phase == "Live Ops (METAR)" else "taf"
    try:
        r_wx = requests.get(f"https://api.checkwx.com/{endpoint}/{icao}/decoded", headers={"X-API-Key": CK_KEY}, timeout=7).json()
        r_ap = requests.get(f"https://aerodatabox.p.rapidapi.com/airports/icao/{icao}", 
                            headers={"X-RapidAPI-Key": AD_KEY, "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"}, timeout=7).json()
        
        wx = r_wx["data"][0] if r_wx.get("results", 0) > 0 else None
        # Fail-safe para info de aeropuerto
        ap_name = r_ap.get("name", icao) if isinstance(r_ap, dict) else icao
        ap_city = r_ap.get("municipalityName", "Loc") if isinstance(r_ap, dict) else "Loc"
        ap = {"name": ap_name, "city": ap_city}
        return wx, ap
    except: return None, {"name": icao, "city": "N/A"}

# --- SIDEBAR ---
st.sidebar.header("✈️ Mission Briefing")
o_icao = st.sidebar.text_input("ORIGIN ICAO", "KTEB").upper()
d_icao = st.sidebar.text_input("DESTINATION ICAO", "KMIA").upper()
fase = st.sidebar.selectbox("Analysis Window", 
                            ["Live Ops (METAR)", "24h Pre-Flight (TAF)", "48h Outlook (Trends)"])

if st.button("GENERATE OPERATIONAL ASSESSMENT"):
    with st.spinner("Executing weather algorithms..."):
        w_o, a_o = get_ops_data(o_icao, fase)
        w_d, a_d = get_ops_data(d_icao, fase)

    if w_o and w_d:
        def advanced_eval(wx, phase):
            raw = wx.get("raw_text", "").upper()
            vis = wx.get("visibility", {}).get("miles_float", 10)
            wind = wx.get("wind", {}).get("speed_kts", 0)
            
            # Cálculo de Ceiling (Capa más baja de BKN o OVC)
            ceiling = 10000
            for layer in wx.get("clouds", []):
                if layer.get("code") in ["BKN", "OVC"]:
                    ceiling = min(ceiling, layer.get("base_feet_agl", 10000))
            
            if phase == "Live Ops (METAR)":
                is_crit = (vis < 3 or wind > 25 or ceiling < 1000 or any(x in raw for x in ["TS", "FG", "SN", "SQ"]))
                msg = "🔴 CRITICAL - IMMEDIATE ACTION" if is_crit else "🟢 NOMINAL - EXECUTE"
            elif phase == "24h Pre-Flight (TAF)":
                is_crit = (vis < 5 or wind > 20 or ceiling < 1500 or any(x in raw for x in ["PROB", "TEMPO", "TS"]))
                msg = "🟡 MONITORING - TAF REVISION" if is_crit else "🟢 STABLE - PLAN CONFIRMED"
            else: # 48h Outlook
                is_crit = any(x in raw for x in ["TS", "DZ", "RA", "SN", "VCTS"])
                msg = "🔵 ADVISORY - TREND ANALYSIS" if is_crit else "🟢 CLEAR - PROCEED"
            return msg, vis, wind, ceiling

        st_o, v_o, wd_o, c_o = advanced_eval(w_o, fase)
        st_d, v_d, wd_d, c_d = advanced_eval(w_d, fase)

        # --- REPORTE EJECUTIVO ---
        st.markdown(f"""<div class="vip-report">
            <h2 style="margin:0;">{a_o['name']} ➔ {a_d['name']}</h2>
            <p style="color:#005fcc; font-weight:bold;">{fase} | ID: {datetime.utcnow().strftime('%y%m%d-%H%M')}Z</p>
            <hr>
            <p style="font-size:1.1em;"><b>Departure:</b> {st_o}</p>
            <p style="font-size:1.1em;"><b>Arrival:</b> {st_d}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("### 🛠 Technical Specifications")
        c1, c2 = st.columns(2)
        
        for col, icao, status, wx, v, wd, ce, color in zip([c1, c2], [o_icao, d_icao], [st_o, st_d], [w_o, w_d], [v_o, v_d], [wd_o, wd_d], [c_o, c_d], ["#00d4ff", "#a855f7"]):
            with col:
                # Color del badge según estatus
                b_color = "#ff3333" if "CRITICAL" in status else "#ffcc00" if "MONITORING" in status else "#0080ff" if "ADVISORY" in status else "#00ff00"
                
                col.markdown(f"""<div class="status-card" style="border-top: 4px solid {color}">
                    <span class="window-badge" style="background:{b_color}; color:{'#000' if b_color=='#ffcc00' else '#fff'};">{status}</span>
                    <h4 style="margin:0; color:{color};">{icao} Assessment</h4>
                    <div class="raw">{wx['raw_text']}</div>
                    <div style="display:flex; gap:15px; margin-top:10px; font-size:0.9em;">
                        <span><b>VIS:</b> {v} SM</span>
                        <span><b>WIND:</b> {wd} KTS</span>
                        <span><b>CEIL:</b> {ce} FT</span>
                    </div>
                </div>""", unsafe
                
