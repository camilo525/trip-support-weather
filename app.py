import streamlit as st
import requests

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Flight Support Team Weather Tool", page_icon="✈️", layout="wide")

# Estilo Corporativo Azul Aeronáutico
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { background-color: #002e5d; color: white; font-weight: bold; width: 100%; border-radius: 8px; height: 3em; }
    .client-box { padding: 20px; border-radius: 10px; background-color: #e3f2fd; border-left: 5px solid #1976d2; color: #0d47a1; }
    .tech-box { padding: 20px; border-radius: 10px; background-color: #fff3e0; border-left: 5px solid #ef6c00; color: #e65100; }
    .alert-box { padding: 15px; border-radius: 8px; background-color: #ffebee; border: 1px solid #c62828; color: #c62828; font-weight: bold; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# 2. SIDEBAR - CONTROL DE MANDOS
st.sidebar.image("https://thrust-aviation.com/wp-content/uploads/2024/02/Logo-White-500-2-e1710003051285.png", width=100)
st.sidebar.title("FST Weather Tool")
icao = st.sidebar.text_input("ICAO AIRPORT CODE", value="KTEB").upper()
fase = st.sidebar.selectbox("TIMELINE PHASE", ["48h Outlook (Trends)", "24h Before (TAF)", "Flight Day (METAR)"])
tipo_reporte = st.sidebar.radio("REPORT TYPE", ["Executive (Client)", "Technical (Internal Team)"])

st.title("✈️ Flight Support Team Weather Tool")
st.markdown("---")

if st.button("RUN ASSESSMENT"):
    # Selección de fuente de datos
    search_type = "taf" if "Before" in fase or "Outlook" in fase else "metar"
    url = f"https://api.checkwx.com/{search_type}/{icao}/decoded"
    headers = {"X-API-Key": API_KEY}
    
    with st.spinner('Accessing Official Aviation Sources...'):
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data.get("results", 0) > 0:
            info = data["data"][0]
            raw = info.get("raw_text", "")
            vis = info.get("visibility", {}).get("miles_float", 10)
            wind = info.get("wind", {}).get("speed_kts", 0)
            
            # --- DETECCIÓN DE ALERTAS CRÍTICAS ---
            alerts = []
            if "TS" in raw or "CB" in raw: alerts.append("⚠️ THUNDERSTORMS DETECTED")
            if "SN" in raw or "FZ" in raw: alerts.append("⚠️ ICING / SNOW RISK")
            if wind > 25: alerts.append("⚠️ HIGH WIND ALERT")
            if vis < 3: alerts.append("⚠️ LOW VISIBILITY / IFR CONDITIONS")

            if alerts:
                for a in alerts:
                    st.markdown(f'<div class="alert-box">{a}</div>', unsafe_allow_html=True)

            # --- LÓGICA DE REPORTES ---
            if tipo_reporte == "Executive (Client)":
                st.subheader("Client-Ready Summary")
                # Traducción amigable
                status = "🟢 GO" if not alerts else "🟡 MONITORING" if len(alerts) < 2 else "🔴 ADVISORY"
                
                exec_report = f"""
**FLIGHT WEATHER ASSESSMENT: {icao}**
**Current Status:** {status}

**[Summary]**
Conditions are being monitored by our Flight Support Team. {"The outlook is favorable for on-time operations." if status == "🟢 GO" else "We are observing some weather patterns that may require minor adjustments."}

**[Key Details]**
• **Visibility:** {"Excellent visibility at the airport." if vis >= 6 else "Some local haze/mist, no operational impact expected."}
• **Comfort:** {"Expect a smooth flight." if wind < 15 else "Slightly gusty conditions; possible minor turbulence on departure."}
• **Operational Outlook:** No major delays anticipated at this moment.

*Thank you for trusting our Flight Support Team.*
                """
                st.markdown(f'<div class="client-box">{exec_report}</div>', unsafe_allow_html=True)
                st.button("Copy Executive Report", on_click=lambda: st.write(f"Copied: {exec_report}")) # Simulación

            else:
                st.subheader("Internal Technical Brief")
                tech_report = f"""
**INTERNAL FST BRIEFING - {icao}**
**Phase:** {fase}

**RAW DATA:** `{raw}`

**METRICS:**
- **Visibility:** {vis} SM
- **Surface Winds:** {wind} KTS
- **Alert Flags:** {", ".join(alerts) if alerts else "NONE"}

**DISPATCH NOTES:**
Check fuel alternates if status is Yellow/Red. Monitor NOTAMs for de-icing or runway condition codes (RCC).
                """
                st.markdown(f'<div class="tech-box">{tech_report}</div>', unsafe_allow_html=True)
        else:
            st.error("Invalid ICAO code or no data available.")

st.sidebar.markdown("---")
st.sidebar.caption("v2.1 | Aviation Data: CheckWX")
