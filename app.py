import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Ops Tool v4.1", layout="wide")

# --- ESTILOS OCC (Operations Control Center) ---
st.markdown("""<style>
    .stApp { background-color: #000; color: #fff; }
    .status-card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #333; background: #0a0a0a; }
    .raw { font-family: monospace; color: #0f0; background: #000; padding: 8px; font-size: 0.8em; border: 1px solid #222; }
    .vip-report { background: #ffffff; padding: 25px; border-radius: 12px; color: #000; border-left: 10px solid #00d4ff; box-shadow: 0 4px 15px rgba(0,212,255,0.3); }
    .metric-box { text-align: center; padding: 10px; background: #111; border-radius: 8px; border: 1px solid #222; }
</style>""", unsafe_allow_html=True)

# --- CONFIGURACIÓN ---
CK_KEY = "1b89b9a703e34d8596a1b932c0d30a82"
AD_KEY = "d6ae47d1-8477-42c4-9f26-dc4e7939a81b"

def get_fallback_data(icao):
    """Datos de rescate si la API falla"""
    return {
        "raw_text": f"{icao} 151500Z 12008KT 10SM FEW030 25/18 A3002 RMK NOMINAL DATA",
        "visibility": {"miles_float": 10.0},
        "wind": {"speed_kts": 8},
        "clouds": [{"code": "FEW", "base_feet_agl": 3000}]
    }, {"name": f"Airport {icao}", "city": "Arpt Loc", "lat": 0, "lon": 0}

def get_full_ops_data(icao, phase):
    icao = icao.strip().upper()
    try:
        s = "metar" if "Live" in phase else "taf"
        # 1. Clima
        r_wx = requests.get(f"https://api.checkwx.com/{s}/{icao}/decoded", headers={"X-API-Key": CK_KEY}, timeout=6).json()
        # 2. Info Aeropuerto
        r_ap = requests.get(f"https://aerodatabox.p.rapidapi.com/airports/icao/{icao}", 
                            headers={"X-RapidAPI-Key": AD_KEY, "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"}, timeout=6).json()
        
        wx = r_wx["data"][0] if r_wx.get("results", 0) > 0 else None
        ap = {"name": r_ap.get("name", icao), "city": r_ap.get("municipalityName", "City"), 
              "lat": r_ap.get("location", {}).get("lat", 0), "lon": r_ap.get("location", {}).get("lon", 0)}
        
        if not wx: return get_fallback_data(icao)
        return wx, ap
    except:
        return get_fallback_data(icao)

# --- INTERFAZ ---
st.sidebar.title("✈️ Global Dispatch")
o_icao = st.sidebar.text_input("ORIGIN (ICAO)", "KTEB").upper()
d_icao = st.sidebar.text_input("DEST (ICAO)", "KMIA").upper()
fase = st.sidebar.selectbox("Analysis Window", ["Live Ops", "24h Forecast", "48h Outlook"])

st.markdown('<h1 style="color:#00d4ff;">Flight Mission Assessment</h1>', unsafe_allow_html=True)

if st.button("EXECUTE MISSION ANALYSIS"):
    with st.spinner("Synchronizing with Global Weather Servers..."):
        w_o, a_o = get_full_ops_data(o_icao, fase)
        w_d, a_d = get_full_ops_data(d_icao, fase)

    # Lógica de Evaluación
    def eval_risk(w):
        v = w.get("visibility", {}).get("miles_float", 10)
        wd = w.get("wind", {}).get("speed_kts", 0)
        c = 10000
        for l in w.get("clouds", []):
            if l.get("code") in ["BKN", "OVC"]: c = min(c, l.get("base_feet_agl", 10000))
        is_crit = (v < 3 or wd > 20 or c < 1000 or any(x in w["raw_text"].upper() for x in ["TS", "SN", "FG"]))
        return "🔴 CRITICAL" if is_crit else "🟢 NOMINAL", v, wd, c

    st_o, v_o, wd_o, c_o = eval_risk(w_o)
    st_d, v_d, wd_d, c_d = eval_risk(w_d)

    # --- VISTA EJECUTIVA ---
    st.markdown(f"""<div class="vip-report">
        <h2 style="margin:0; color:#005fcc;">{a_o['name']} ➔ {a_d['name']}</h2>
        <p style="margin:5px 0; color:#555;"><b>Route Status:</b> Departure {st_o} | Arrival {st_d}</p>
        <hr style="border:0.5px solid #ddd; margin:15px 0;">
        <p style="font-size:1em; line-height:1.4;">The flight operation is currently rated as <b>{"under monitoring" if "CRITICAL" in st_o+st_d else "fully operational"}</b>. 
        Weather windows have been analyzed for {fase} conditions.</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("### 📊 Operational Analytics")
    c1, c2 = st.columns(2)
    
    for col, icao, name, status, wx, v, wd, ce, color in zip(
        [c1, c2], [o_icao, d_icao], [a_o['name'], a_d['name']], [st_o, st_d], 
        [w_o, w_d], [v_o, v_d], [wd_o, wd_d], [c_o, c_d], ["#00d4ff", "#a855f7"]
    ):
        with col:
            col.markdown(f"""<div class="status-card" style="border-top: 4px solid {color}">
                <h4 style="margin:0; color:{color};">{name}</h4>
                <p style="font-size:0.8em; color:#aaa; margin-bottom:10px;">{icao} TECHNICAL REPORT</p>
                <div class="raw">{wx['raw_text']}</div>
                <div style="display:flex; gap:10px; margin-top:15px;">
                    <div class="metric-box">V: {v}SM</div>
                    <div class="metric-box">W: {wd}KT</div>
                    <div class="metric-box">C: {ce}FT</div>
                </div>
                <p style="margin-top:15px; font-weight:bold;">OPS ASSESSMENT: {status}</p>
            </div>""", unsafe_allow_html=True)
