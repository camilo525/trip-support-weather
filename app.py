import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Flight Support Team Weather Tool", page_icon="✈️", layout="wide")

API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"
LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png"
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"

# --- CSS ---
STYLE = """
<style>
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    .header-style {
        font-size: 24px; font-weight: bold;
        background: -webkit-linear-gradient(#00d4ff, #005fcc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .tech-card-origin { padding: 20px; border-radius: 15px; border: 2px solid #00d4ff; background-color: rgba(0, 212, 255, 0.05); margin-bottom: 20px; }
    .tech-card-dest { padding: 20px; border-radius: 15px; border: 2px solid #a855f7; background-color: rgba(168, 85, 247, 0.05); margin-bottom: 20px; }
    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: transparent; font-size: 1.1em; line-height: 1.5; }
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important;
        font-weight: bold; border: none; border-radius: 10px; height: 3.5em; width: 100%; transition: 0.3s;
    }
    .tool-container { display: flex; gap: 15px; margin: 25px 0; flex-wrap: wrap; }
    .tool-btn {
        flex: 1; min-width: 200px; padding: 15px; border-radius: 12px;
        text-align: center; text-decoration: none; font-weight: bold; font-size: 0.9em;
        transition: 0.3s; border: 1px solid rgba(255,255,255,0.1);
    }
    .btn-sat { background: rgba(0, 212, 255, 0.1); color: #00d4ff !important; border-color: #00d4ff; }
    .btn-map { background: rgba(168, 85, 247, 0.1); color: #a855f7 !important; border-color: #a855f7; }
    .btn-notam { background: rgba(255, 204, 0, 0.1); color: #ffcc00 !important; border-color: #ffcc00; }
    .executive-card { background: rgba(255,255,255,0.03); padding: 35px; border-radius: 20px; border-left: 6px solid #00d4ff; }
    .status-stable { color: #00ff00; font-weight: bold; }
    .status-alert { color: #ff0000; font-weight: bold; text-decoration: underline; }
    input { background-color: #0a0a0a !important; border: 1px solid #333333 !important; color: #00d4ff !important; }
    .footer-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; padding: 40px 0; margin-top: 30px; border-top: 1px solid #222222; }
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)

# --- FUNCTIONS ---
def get_wx(icao, phase):
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    try:
        r = requests.get(url, headers={"X-API-Key": API_KEY}, timeout=10)
        data = r.json()
        return data["data"][0] if data.get("results", 0) > 0 else None
    except Exception:
        return None

def generate_client_text(wx, icao, is_departure=True):
    raw = wx.get("raw_text", "").upper()
    vis = wx.get("visibility", {}).get("miles_float", 10)
    is_critical = any(x in raw for x in ["TS", "SN", "FG", "DZ", "RA", "SQ"]) or vis < 3
    role = "departure from" if is_departure else "arrival at"
    if is_critical:
        return f"The Operations Team is currently analyzing weather conditions for your {role} {icao} and we are reporting if there are any issues."
    return f"Meteorological analysis for your {role} {icao} indicates ideal conditions."

def get_coords(wx):
    try:
        if 'station' in wx:
            return wx['station']['geometry']['coordinates'][1], wx['station']['geometry']['coordinates'][0]
        return wx['geometry']['coordinates'][1], wx['geometry']['coordinates'][0]
    except:
        return None, None

# --- HEADER ---
col_l, col_r = st.columns([1, 8])
with col_l: 
    st.image(LOGO_UP_LEFT, width=300)
with col_r: 
    st.markdown('<div class="header-style">Flight Support Team | Trip Assessment</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("Trip Details")
    origin = st.text_input("DEPARTURE ICAO", value="KTEB").upper()
    etd = st.text_input("ETD (UTC Internal)", value="1200")
    destination = st.text_input("ARRIVAL ICAO", value="KMIA").upper()
    eta = st.text_input("ETA (UTC Internal)", value="1600")
    fase = st.selectbox("Assessment Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
    tipo_reporte = st.radio("REPORT MODE", ["Executive (Client)", "Technical (Internal)"])

# --- MAIN ---
if st.button("Run Mission Assessment"):
    wx_org, wx_dst = get_wx(origin, fase), get_wx(destination, fase)

    if wx_org and wx_dst:
        o_lat, o_lon = get_coords(wx_org)
        d_lat, d_lon = get_coords(wx_dst)
        
        if o_lat and d_lat:
            fig = go.Figure(go.Scattergeo(
                lon=[o_lon, d_lon], lat=[o_lat, d_lat],
                mode='lines+markers+text', text=[origin, destination],
                textposition="top center", line=dict(width=3, color='#00d4ff'),
                marker=dict(size=12, color=['#00d4ff', '#a855f7'], symbol='diamond')
            ))
            fig.update_layout(
                showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=450, paper_bgcolor="rgba(0,0,0,0)",
                geo=dict(showland=True, landcolor="#0a0a0a", showocean=True, oceancolor="#000000",
                         showlakes=True, lakecolor="#002b4d", showcountries=True, countrycolor="#888888",
                         showsubunits=True, subunitcolor="#005fcc", resolution=50, projection_type='equirectangular')
            )
            st.plotly_chart(fig, use_container_width=True)

        if tipo_reporte == "Executive (Client)":
            st.markdown(f"""
            <div class="executive-card">
                <h2 style="color:#00d4ff;">Flight Briefing: {origin} ➔ {destination}</h2>
                <p><b>Departure:</b> {generate_client_text(wx_org, origin, True)}</p>
                <p><b>Arrival:</b> {generate_client_text(wx_dst, destination, False)}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### 🛠 Dispatcher Toolkit")
            st.markdown(f"""
            <div class="tool-container">
                <a href="
