import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Ops Tool v3.4", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #fff; }
    .header-style { font-size: 24px; font-weight: bold; color: #00d4ff; margin-bottom: 20px; }
    .tech-card-origin { padding: 15px; border-radius: 10px; border: 1px solid #00d4ff; background: rgba(0,212,255,0.05); margin-bottom: 10px; }
    .tech-card-dest { padding: 15px; border-radius: 10px; border: 1px solid #a855f7; background: rgba(168,85,247,0.05); margin-bottom: 10px; }
    .raw-code { font-family: monospace; color: #0f0; background: #000; padding: 8px; font-size: 0.8em; border: 1px solid #333; }
    .executive-card { background: #fff; padding: 25px; border-radius: 15px; border-left: 5px solid #00d4ff; color: #000; }
    </style>
    """, unsafe_allow_html=True)

CK_KEY = "1b89b9a703e34d8596a1b932c0d30a82"
AD_KEY = "d6ae47d1-8477-42c4-9f26-dc4e7939a81b"

def get_wx(icao, phase):
    s = "metar" if phase == "Flight Day (Live)" else "taf"
    try:
        r = requests.get(f"https://api.checkwx.com/{s}/{icao.strip()}/decoded", headers={"X-API-Key": CK_KEY}, timeout=7)
        d = r.json()
        return d["data"][0] if d.get("results", 0) > 0 else None
    except: return None

def get_ap(icao):
    try:
        r = requests.get(f"https://aerodatabox.p.rapidapi.com/airports/icao/{icao.strip()}", 
                         headers={"X-RapidAPI-Key": AD_KEY, "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"}, timeout=7)
        if r.status_code == 200:
            d = r.json()
            return {"n": d.get("name", icao), "lat": d.get("location", {}).get("lat", 0), "lon": d.get("location", {}).get("lon", 0)}
    except: pass
    return {"n": icao, "lat": 0, "lon": 0}

st.sidebar.title("Settings")
origin = st.sidebar.text_input("Origin", "KTEB").upper()
dest = st.sidebar.text_input("Destination", "KMIA").upper()
fase = st.sidebar.selectbox("Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo = st.sidebar.radio("Mode", ["Executive", "Technical"])

st.markdown('<div class="header-style">Flight Support | Mission Assessment</div>', unsafe_allow_html=True)

if st.button("RUN ASSESSMENT"):
    with st.spinner("Loading..."):
        info_o, info_d = get_ap(origin), get_ap(dest)
        wx_o = get_wx(origin, fase) or {"raw_text": "No METAR", "visibility": {"miles_float": 10}, "wind": {"speed_kts": 0}}
        wx_d = get_wx(dest, fase) or {"raw_text": "No METAR", "visibility": {"miles_float": 10}, "wind": {"speed_kts": 0}}

    fig = go.Figure(go.Scattergeo(lat=[info_o["lat"], info_d["lat"]], lon=[info_o["lon"], info_d["lon"]], mode='lines+markers'))
    fig.update_layout(geo=dict(showland=True, landcolor="#111", bgcolor="rgba(0,0,0,0)"), height=250, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

    def eval_r(w):
        v = w.get("visibility", {}).get("miles_float", 10)
        wd = w.get("wind", {}).get("speed_kts", 0)
        raw = w.get("raw_text", "").upper()
        crit = (v < 3 or wd > 20 or any(x in raw for x in ["TS", "SN", "FG"]))
        return crit, v, wd

    r_o, v_o, w_o = eval_r(wx_o)
    r_d, v_d, w_d = eval_r(wx_d)

    if tipo == "Executive":
        st.markdown(f'<div class="executive-card"><h3>{info_o["n"]} to {info_d["n"]}</h3><p>Departure: {"Alert" if r_o else "Stable"}</p><p>Arrival: {"Alert" if r_d else "Stable"}</p></div>', unsafe_allow_html=True)
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="tech-card-origin"><b>{info_o["n"]}</b><div class="raw-code">{wx_o["raw_text"]}</div><p>Vis: {v_o}SM | Wind: {w_o}KT</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="tech-card-dest"><b>{info_d["n"]}</b><div class="raw-code">{wx_d["raw_text"]}</div><p>Vis: {v_d}SM | Wind: {w_d}KT</p></div>', unsafe_allow_html=True)
