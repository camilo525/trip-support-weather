import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ops Control Center v5.0", layout="wide")

# --- ESTILOS OCC (Operations Control Center) ---
st.markdown("""<style>
    .stApp { background-color: #000; color: #fff; }
    .status-card { padding: 20px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #222; background: #0a0a0a; }
    .raw { font-family: 'Courier New', monospace; color: #00ff00; background: #000; padding: 12px; font-size: 0.85em; border-left: 3px solid #00ff00; margin: 10px 0; overflow-wrap: break-word; }
    .vip-report { background: #ffffff; padding: 30px; border-radius: 15px; color: #000; border-left: 10px solid #005fcc; margin-bottom: 25px; }
    .window-badge { padding: 4px 10px; border-radius: 5px; font-size: 0.75em; font-weight: bold; text-transform: uppercase; margin-bottom: 10px; display: inline-block; }
    .metric-inline { display: inline-block; margin-right: 20px; font-size: 0.95em; }
</style>""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE LLAVES ---
CK_KEY = "1b89b9a703e34d8596a1b932c0d30a82"
AD_KEY = "d6ae47d1-8477-42c4-9f26-dc4e7939a81b"

# --- FUNCIONES DE OBTENCIÓN DE DATOS ---
def get_weather(icao, phase):
    icao = icao.strip().upper()
    endpoint = "metar" if phase == "Live Ops (METAR)" else "taf"
    url = "https://api.checkwx.com/" + endpoint + "/" + icao + "/decoded"
    try:
        r = requests.get(url, headers={"X-API-Key": CK_KEY}, timeout=8)
        data = r.json()
        if data.get("results", 0) > 0:
            return data["data"][0]
        return None
    except:
        return None

def get_airport(icao):
    icao = icao.strip().upper()
    url = "https://aerodatabox.p.rapidapi.com/airports/icao/" + icao
    headers = {"X-RapidAPI-Key": AD_KEY, "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            d = r.json()
            return {"name": d.get("name", icao), "city": d.get("municipalityName", "Loc"), "lat": d.get("location", {}).get("lat", 0), "lon": d.get("location", {}).get("lon", 0)}
        return {"name": icao, "city": "N/A", "lat": 0, "lon": 0}
    except:
        return {"name": icao, "city": "N/A", "lat": 0, "lon": 0}

# --- SIDEBAR ---
st.sidebar.header("✈️ Mission Briefing")
origin_icao = st.sidebar.text_input("ORIGIN ICAO", "KTEB").upper()
destination_icao = st.sidebar.text_input("DESTINATION ICAO", "KMIA").upper()
fase = st.sidebar.selectbox("Analysis Window", ["Live Ops (METAR)", "24h Pre-Flight (TAF)", "48h Outlook (Trends)"])

# --- HEADER ---
st.markdown('<h1 style="color:#00d4ff; margin-bottom:0;">OCC Mission Assessment</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#555; margin-bottom:30px;">Flight Support Operations Center | Global Datalink</p>', unsafe_allow_html=True)

# --- EJECUCIÓN ---
if st.button("EXECUTE ANALYSIS"):
    with st.spinner("Analyzing weather patterns and airport data..."):
        # Obtener Clima
        w_o = get_weather(origin_icao, fase)
        w_d = get_weather(destination_icao, fase)
        # Obtener Aeropuertos
        a_o = get_airport(origin_icao)
        a_d = get_airport(destination_icao)

    if w_o and w_d:
        # Lógica de Evaluación por Ventana
        def evaluate(wx, phase):
            raw = wx.get("raw_text", "").upper()
            vis = wx.get("visibility", {}).get("miles_float", 10)
            wind = wx.get("wind", {}).get("speed_kts", 0)
            ceil = 10000
            for layer in wx.get("clouds", []):
                if layer.get("code") in ["BKN", "OVC"]:
                    ceil = min(ceil, layer.get("base_feet_agl", 10000))
            
            if phase == "Live Ops (METAR)":
                crit = (vis < 3 or wind > 25 or ceil < 1000 or any(x in raw for x in ["TS", "FG", "SN", "SQ"]))
                msg = "🔴 CRITICAL - IMMEDIATE ACTION" if crit else "🟢 NOMINAL - EXECUTE"
            elif phase == "24h Pre-Flight (TAF)":
                crit = (vis < 5 or wind > 20 or ceil < 1500 or any(x in raw for x in ["PROB", "TEMPO", "TS"]))
                msg = "🟡 MONITORING - TAF REVISION" if crit else "🟢 STABLE - PLAN CONFIRMED"
            else:
                crit = any(x in raw for x in ["TS", "RA", "SN", "VCTS"])
                msg = "🔵 ADVISORY - TREND ANALYSIS" if crit else "🟢 CLEAR - PROCEED"
            return msg, vis, wind, ceil

        st_o, v_o, wd_o, c_o = evaluate(w_o, fase)
        st_d, v_d, wd_d, c_d = evaluate(w_d, fase)

        # 1. REPORTE VIP
        report_title = a_o['name'] + " ➔ " + a_d['name']
        timestamp = datetime.utcnow().strftime('%y%m%d-%H%M') + "Z"
        
        st.markdown('<div class="vip-report">', unsafe_allow_html=True)
        st.markdown('<h2 style="margin:0; color:#005fcc;">' + report_title + '</h2>', unsafe_allow_html=True)
        st.markdown('<p style="color:#777; font-weight:bold; margin-bottom:20px;">' + fase + ' | ID: ' + timestamp + '</p>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:1.1em;"><b>Departure:</b> ' + st_o + '</p>', unsafe_allow_html=True)
        st.markdown('<p
