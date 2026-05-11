import streamlit as st
import requests

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Flight Support Team Weather Tool", page_icon="✈️", layout="wide")

# Diseño Corporativo
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { background-color: #002e5d; color: white; font-weight: bold; width: 100%; border-radius: 8px; height: 3em; }
    .client-box { padding: 25px; border-radius: 12px; background-color: #ffffff; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); color: #1a1a1a; }
    .tech-box { padding: 20px; border-radius: 10px; background-color: #263238; color: #eceff1; font-family: monospace; }
    .alert-card { padding: 10px; border-radius: 5px; background-color: #ffcdd2; color: #b71c1c; font-weight: bold; margin-bottom: 5px; border-left: 5px solid #b71c1c; }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# 2. SIDEBAR - TRIP INFO
st.sidebar.title("FST Trip Manager")
origin = st.sidebar.text_input("ORIGIN ICAO", value="KTEB").upper()
destination = st.sidebar.text_input("DESTINATION ICAO", value="KMIA").upper()
fase = st.sidebar.selectbox("TIMELINE PHASE", ["48h Outlook", "24h Before", "Flight Day"])
tipo_reporte = st.sidebar.radio("REPORT TYPE", ["Executive (Client)", "Technical (Internal)"])

st.title("✈️ Flight Support Team: Route Assessment")
st.markdown(f"### Route: {origin} ➔ {destination}")

def get_wx(icao, phase):
    search_type = "taf" if "Before" in phase or "Outlook" in phase else "metar"
    url = f"https://api.checkwx.com/{search_type}/{icao}/decoded"
    headers = {"X-API-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers)
        d = r.json()
        return d["data"][0] if d.get("results", 0) > 0 else None
    except:
        return None

if st.button("RUN COMPLETE ROUTE ASSESSMENT"):
    with st.spinner('Analyzing Departure and Arrival conditions...'):
        wx_org = get_wx(origin, fase)
        wx_dst = get_wx(destination, fase)

        if wx_org and wx_dst:
            # --- ANALISIS ORIGEN ---
            org_raw = wx_org.get("raw_text", "")
            org_vis = wx_org.get("visibility", {}).get("miles_float", 10)
            org_wind = wx_org.get("wind", {}).get("speed_kts", 0)
            
            # --- ANALISIS DESTINO ---
            dst_raw = wx_dst.get("raw_text", "")
            dst_vis = wx_dst.get("visibility", {}).get("miles_float", 10)
            dst_wind = wx_dst.get("wind", {}).get("speed_kts", 0)

            # --- ALERTAS ---
            all_alerts = []
            for raw, name in [(org_raw, origin), (dst_raw, destination)]:
                if "TS" in raw or "CB" in raw: all_alerts.append(f"⚠️ {name}: Thunderstorms detected.")
                if "SN" in raw or "FZ" in raw: all_alerts.append(f"⚠️ {name}: Icing/Snow risk.")
                if "FG" in raw or "BR" in raw: all_alerts.append(f"⚠️ {name}: Fog/Mist (Low visibility).")

            if all_alerts:
                for a in all_alerts:
                    st.markdown(f'<div class="alert-card">{a}</div>', unsafe_allow_html=True)

            if tipo_reporte == "Executive (Client)":
                report = f"""
### 📋 TRIP WEATHER SUMMARY
**Route:** {origin} to {destination} | **Phase:** {fase}
**Status:** {"🟢 Favorable" if not all_alerts else "🟡 Under Monitoring"}

**DEPARTURE: {origin}**
• **Conditions:** {"Clear skies and good visibility." if org_vis >= 6 else "Partial cloudiness/haze, normal operations."}
• **Wind:** {"Light winds." if org_wind < 15 else "Breezy conditions, minor turbulence possible."}

**ARRIVAL: {destination}**
• **Conditions:** {"Optimal conditions for arrival." if dst_vis >= 6 else "Visibility monitored; standard procedures in place."}
• **Wind:** {"Calm winds." if dst_wind < 15 else "Gusty winds expected; expect a firm landing."}

**FLIGHT SUPPORT NOTE:** Our team is continuously monitoring this route. No major delays are anticipated for your ETD.
                """
                st.markdown(f'<div class="client-box">{report}</div>', unsafe_allow_html=True)
            
            else:
                # REPORTE TÉCNICO
                st.markdown("### 🛠 INTERNAL TECHNICAL BRIEF")
                col_org, col_dst = st.columns(2)
                with col_org:
                    st.subheader(f"Origin: {origin}")
                    st.code(f"RAW: {org_raw}\n\nVis: {org_vis}SM\nWind: {org_wind}KT")
                with col_dst:
                    st.subheader(f"Destination: {destination}")
                    st.code(f"RAW: {dst_raw}\n\nVis: {dst_vis}SM\nWind: {dst_wind}KT")
        else:
            st.error("Error: Could not retrieve data for one or both airports. Please verify ICAO codes.")

st.markdown("---")
st.caption("Flight Support Team Weather Tool | Phase-Based Route Analysis")
