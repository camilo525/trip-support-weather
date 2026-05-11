import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Flight Support Team Weather Tool", page_icon="✈️", layout="wide")

# --- PRO DESIGN ---
st.markdown("""
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
        font-weight: bold; border: none; border-radius: 10px; height: 3.5em; width: 100%;
        transition: 0.3s;
    }

    /* TOOLKIT BUTTONS DESIGN */
    .tool-container {
        display: flex; gap: 12px; margin-top: 10px; margin-bottom: 25px; flex-wrap: wrap;
    }
    .tool-btn {
        flex: 1; min-width: 170px; padding: 12px; border-radius: 10px;
        text-align: center; text-decoration: none; font-weight: bold; font-size: 0.8em;
        transition: 0.3s; border: 1px solid rgba(255,255,255,0.1);
    }
    .btn-sat { background: rgba(0, 212, 255, 0.1); color: #00d4ff !important; border-color: #00d4ff; }
    .btn-map { background: rgba(168, 85, 247, 0.1); color: #a855f7 !important; border-color: #a855f7; }
    .btn-nas { background: rgba(0, 255, 127, 0.1); color: #00ff7f !important; border-color: #00ff7f; }
    .btn-notam { background: rgba(255, 204, 0, 0.1); color: #ffcc00 !important; border-color: #ffcc00; }
    
    .tool-btn:hover { transform: translateY(-3px); background: rgba(255,255,255,0.1); }

    .executive-card { background: rgba(255,255,255,0.03); padding: 35px; border-radius: 20px; border-left: 6px solid #00d4ff; }
    .status-stable { color: #00ff00; font-weight: bold; }
    .status-alert { color: #ff0000; font-weight: bold; text-decoration: underline; }
    input { background-color: #0a0a0a !important; border: 1px solid #333333 !important; color: #00d4ff !important; }
    .footer-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; padding: 40px 0px; margin-top: 30px; border-top: 1px solid #222222; }
    </style>
    """, unsafe_allow_html=True)

LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png" 
LOGO_BOTTOM_CENTER = "https://static.wixstatic.com/media/5f5db0_d7471efb590b4734a38048043fb3b2c1~mv2.png/v1/fill/w_300,h_300,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/FBO%20Audit%20Logo%20Silver.png"
API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

col_logo, col_title = st.columns([1, 8])
with col_logo: st.image(LOGO_UP_LEFT, width=300)
with col_title: st.markdown('<div class="header-style">Flight Support Team | Trip Assessment</div>', unsafe_allow_html=True)

# 3. SIDEBAR
st.sidebar.title("Trip Details")
origin = st.sidebar.text_input("DEPARTURE ICAO", value="KTEB").upper()
etd = st.sidebar.text_input("ETD (UTC Internal)", value="1200")
destination = st.sidebar.text_input("ARRIVAL ICAO", value="KMIA").upper()
eta = st.sidebar.text_input("ETA (UTC Internal)", value="1600")
fase = st.sidebar.selectbox("Assessment Window", ["Flight Day (Live)", "24h Pre-Flight", "48h Outlook"])
tipo_reporte = st.sidebar.radio("REPORT MODE", ["Executive (Client)", "Technical (Internal)"])

def get_wx(icao, phase):
    stype = "metar" if phase == "Flight Day (Live)" else "taf"
    url = f"https://api.checkwx.com/{stype}/{icao}/decoded"
    headers = {"X-API-Key": API_KEY}
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        if data.get("results", 0) > 0: return data["data"][0]
        return None
    except: return None

def generate_client_text(wx, icao, type="dep"):
    raw = wx.get("raw_text", "").upper()
    vis = wx.get("visibility", {}).get("miles_float", 10)
    is_critical = any(x in raw for x in ["TS", "SN", "FG", "DZ", "RA", "SQ"]) or vis < 3
    if type == "dep":
        if is_critical:
            return f"The Operations Team is currently analyzing weather conditions for your departure from {icao} and we are reporting if there are any issues. We are evaluating the most efficient window for your day of travel."
        else:
            return f"Meteorological analysis for your departure from {icao} indicates ideal conditions. The Operations Team is monitoring conditions and confirms a seamless process."
    else:
        if is_critical:
            return f"The Operations Team is currently analyzing weather conditions for your arrival at {icao} and we are reporting if there are any issues due to forecasted meteorological activity."
        else:
            return f"The terminal forecast for your arrival at {icao} remains favorable. The Operations Team is monitoring conditions and we are reporting a comfortable arrival."

def get_coords(wx):
    try: return wx['station']['geometry']['coordinates'][1], wx['station']['geometry']['coordinates'][0]
    except:
        try: return wx['geometry']['coordinates'][1], wx['geometry']['coordinates'][0]
        except: return None, None

if st.button("Run Mission Assessment"):
