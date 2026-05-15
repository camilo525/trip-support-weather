import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Ops Tool v4.0", layout="wide")

# --- ESTILOS COMPACTOS ---
st.markdown("""<style>
    .stApp { background-color: #000; color: #fff; }
    .status-card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #333; }
    .raw { font-family: monospace; color: #0f0; background: #111; padding: 5px; font-size: 0.75em; }
    .vip-report { background: #fff; padding: 20px; border-radius: 10px; color: #000; border-left: 10px solid #00d4ff; }
</style>""", unsafe_allow_html=True)

CK_KEY = "1b89b9a703e34d8596a1b932c0d30a82"
AD_KEY = "d6ae47d1-8477-42c4-9f26-dc4e7939a81b"

def get_data(icao, phase):
    try:
        s = "metar" if "Live" in phase else "taf"
        r_wx = requests.get(f"https://api.checkwx.com/{s}/{icao}/decoded", headers={"X-API-Key": CK_KEY}, timeout=5).json()
        r_ap = requests.get(f"https://aerodatabox.p.rapidapi.com/airports/icao/{icao}", 
                            headers={"X-RapidAPI-Key": AD_KEY, "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"}, timeout=5).json()
        return r_wx["data"][0], r_ap
    except: return None, None

# --- UI SIDEBAR ---
o_icao = st.sidebar.text_input("DEP", "KTEB").upper()
d_icao = st.sidebar.text_input("ARR", "KMIA").upper()
fase = st.sidebar.selectbox("Window", ["Live", "24h", "48h"])

if st.button("EXECUTE MISSION ASSESSMENT"):
    w_o, a_o = get_data(o_icao, fase)
    w_d, a_d = get_data(d_icao, fase)

    if w_o and w_d:
        # --- LÓGICA DE ICONOS Y STATUS ---
        def eval_ops(w):
            v = w.get("visibility", {}).get("miles_float", 10)
            wd = w.get("wind", {}).get("speed_kts", 0)
            c = 10000
            for l in w.get("clouds", []):
                if l.get("code") in ["BKN", "OVC"]: c = min(c, l.get("base_feet_agl", 10000))
            is_crit = (v < 3 or wd > 20 or c < 1000 or any(x in w["raw_text"].upper() for x in ["TS", "SN", "FG"]))
            return "🔴 CRITICAL" if is_crit else "🟢 NOMINAL", v, wd, c

        st_o, v_o, wd_o, c_o = eval_ops(w_o)
        st_d, v_d, wd_d, c_d = eval_ops(w_d)

        # --- EXECUTIVE VIEW ---
        st.markdown(f"""<div class="vip-report">
            <h2 style="margin:0;">{o_icao} ➔ {d_icao}</h2>
            <p><b>DEP Status:</b> {st_o} | <b>ARR Status:</b> {st_d}</p>
            <p style="font-size:0.9em; color:#444;">Mission assessment completed at {datetime.utcnow().strftime('%H:%MZ')}</p>
        </div>""", unsafe_allow_html=True)

        # --- TECHNICAL VIEW ---
        c1, c2 = st.columns(2)
        for col, icao, stt, w, v, wd, ce, color in zip([c1, c2], [o_icao, d_icao], [st_o, st_d], [w_o, w_d], [v_o, v_d], [wd_o, wd_d], [c_o, c_d], ["#00d4ff", "#a855f7"]):
            with col:
                st.markdown(f"""<div class="status-card" style="border-top: 5px solid {color}">
                    <h3 style="margin:0; color:{color};">{icao} Assessment</h3>
                    <div class="raw">{w["raw_text"]}</div>
                    <p style="margin:10px 0 0 0; font-size:0.85em;">
                        <b>VIS:</b> {v}SM | <b>WIND:</b> {wd}KT | <b>CEIL:</b> {ce}FT<br>
                        <b>OPS:</b> {stt}
                    </p>
                </div>""", unsafe_allow_html=True)
    else: st.error("Check ICAO / API Limits")
        
