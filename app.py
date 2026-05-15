import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Ops Control Center v5.1", layout="wide")

# --- CSS SIN BLOQUES LARGOS ---
st.markdown("<style>.stApp { background-color: #000; color: #fff; } .status-card { padding: 20px; border-radius: 12px; border: 1px solid #222; background: #0a0a0a; margin-bottom: 15px; } .raw { font-family: monospace; color: #00ff00; background: #000; padding: 10px; font-size: 0.85em; border-left: 3px solid #00ff00; } .vip-report { background: #fff; padding: 25px; border-radius: 15px; color: #000; border-left: 10px solid #005fcc; margin-bottom: 20px; } .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.7em; font-weight: bold; }</style>", unsafe_allow_html=True)

# --- CONFIG ---
CK_KEY = "1b89b9a703e34d8596a1b932c0d30a82"
AD_KEY = "d6ae47d1-8477-42c4-9f26-dc4e7939a81b"

def get_wx(icao, phase):
    icao = icao.strip().upper()
    ep = "metar" if "Live" in phase else "taf"
    try:
        r = requests.get("https://api.checkwx.com/" + ep + "/" + icao + "/decoded", headers={"X-API-Key": CK_KEY}, timeout=7)
        d = r.json()
        return d["data"][0] if d.get("results", 0) > 0 else None
    except: return None

def get_ap(icao):
    icao = icao.strip().upper()
    try:
        h = {"X-RapidAPI-Key": AD_KEY, "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"}
        r = requests.get("https://aerodatabox.p.rapidapi.com/airports/icao/" + icao, headers=h, timeout=7)
        if r.status_code == 200:
            d = r.json()
            return {"n": d.get("name", icao), "lat": d.get("location", {}).get("lat", 0), "lon": d.get("location", {}).get("lon", 0)}
    except: pass
    return {"n": icao, "lat": 0, "lon": 0}

# --- UI ---
st.sidebar.header("Mission Briefing")
orig = st.sidebar.text_input("ORIGIN ICAO", "KTEB").upper()
dest = st.sidebar.text_input("DEST ICAO", "KMIA").upper()
fase = st.sidebar.selectbox("Window", ["Live Ops (METAR)", "24h Pre-Flight (TAF)", "48h Outlook (Trends)"])

st.markdown("<h1 style='color:#00d4ff;'>OCC Assessment</h1>", unsafe_allow_html=True)

if st.button("EXECUTE ANALYSIS"):
    with st.spinner("Analyzing..."):
        w_o = get_wx(orig, fase)
        w_d = get_wx(dest, fase)
        a_o = get_ap(orig)
        a_d = get_ap(dest)

    if w_o and w_d:
        def eval_wx(wx, ph):
            raw = wx.get("raw_text", "").upper()
            vis = wx.get("visibility", {}).get("miles_float", 10)
            wind = wx.get("wind", {}).get("speed_kts", 0)
            ceil = 10000
            for l in wx.get("clouds", []):
                if l.get("code") in ["BKN", "OVC"]: ceil = min(ceil, l.get("base_feet_agl", 10000))
            
            if "Live" in ph:
                crit = (vis < 3 or wind > 25 or ceil < 1000 or any(x in raw for x in ["TS", "FG", "SN"]))
                m = "🔴 CRITICAL" if crit else "🟢 NOMINAL"
            elif "24h" in ph:
                crit = (vis < 5 or wind > 20 or any(x in raw for x in ["PROB", "TEMPO", "TS"]))
                m = "🟡 MONITORING" if crit else "🟢 STABLE"
            else:
                crit = any(x in raw for x in ["TS", "RA", "SN"])
                m = "🔵 ADVISORY" if crit else "🟢 CLEAR"
            return m, vis, wind, ceil

        st_o, v_o, wd_o, c_o = eval_wx(w_o, fase)
        st_d, v_d, wd_d, c_d = eval_wx(w_d, fase)

        # REPORTE VIP (Cadenas cortas concatenadas)
        st.markdown("<div class='vip-report'>", unsafe_allow_html=True)
        st.markdown("<h2>" + a_o['n'] + " ➔ " + a_d['n'] + "</h2>", unsafe_allow_html=True)
        st.markdown("<p><b>Status:</b> Departure " + st_o + " | Arrival " + st_d + "</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # TECHNICAL
        c1, c2 = st.columns(2)
        for col, icao, stat, wx, v, wd, ce, color in zip([c1, c2], [orig, dest], [st_o, st_d], [w_o, w_d], [v_o, v_d], [wd_o, wd_d], [c_o, c_d], ["#00d4ff", "#a855f7"]):
            with col:
                st.markdown("<div class='status-card' style='border-top:4px solid " + color + "'>", unsafe_allow_html=True)
                st.markdown("<h4>" + icao + " Assessment</h4>", unsafe_allow_html=True)
                st.markdown("<div class='raw'>" + wx['raw_text'] + "</div>", unsafe_allow_html=True)
                st.markdown("<p style='margin-top:10px;'>VIS: " + str(v) + " | WIND: " + str(wd) + " | CEIL: " + str(ce) + "</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.error("Data Sync Error. Check ICAO codes or API Keys.")
