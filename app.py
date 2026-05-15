import streamlit as st
import requests

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="VIP Milestone Console", layout="centered")

# --- API CONFIGURATION ---
# Tu API Key de AeroDataBox (RapidAPI)
API_KEY = "d6ae47d1-8477-42c4-9f26-dc4e7939a81b"

# --- UI DESIGN (CONSOLE INTERFACE) ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #ffffff; }
    .main-title {
        font-size: 32px; font-weight: bold;
        background: -webkit-linear-gradient(#cb2d42, #8e1e2d);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 30px; letter-spacing: 2px;
    }
    div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"], div[data-baseweb="checkbox"], div[data-baseweb="radio"] { 
        background-color: #111 !important; border: 1px solid #333 !important; 
    }
    input, textarea, select { color: #cb2d42 !important; }
    label { color: #aaa !important; font-size: 14px !important; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">VIP MILESTONE CONSOLE</div>', unsafe_allow_html=True)

# --- BACKUP AIRPORT DATABASE ---
AIRPORT_DB = {
    "KTEB": ["Teterboro", "Teterboro", "NJ", "US/Eastern"],
    "KOPF": ["Opa-Locka Exec", "Miami", "FL", "US/Eastern"],
    "KASE": ["Aspen/Pitkin Co", "Aspen", "CO", "US/Mountain"],
    "KVNY": ["Van Nuys", "Los Angeles", "CA", "US/Pacific"]
}

WEATHER_ICONS = {"Sunny": "☼", "Partly Cloudy": "☁", "Cloudy": "☁", "Rainy": "☂", "Thunderstorm": "⚡", "Snowy": "❄", "Foggy": "░"}

# --- DATA FETCHING LOGIC ---
def get_airport_details(icao):
    if not icao or len(icao) < 3:
        return [icao, "City", "ST", "UTC"]
    
    url = f"https://aerodatabox.p.rapidapi.com/airports/icao/{icao}"
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=3)
        if response.status_code == 200:
            data = response.json()
            name = data.get('shortName') or data.get('name') or icao
            city = data.get('municipalityName', 'Unknown City')
            country = data.get('countryCode', 'US')
            tz_raw = data.get('timeZone', 'UTC')
            
            # Simplificación de zona horaria para el reporte VIP
            tz = "UTC"
            if "New_York" in tz_raw or "Miami" in tz_raw: tz = "EST"
            elif "Chicago" in tz_raw or "Dallas" in tz_raw: tz = "CST"
            elif "Denver" in tz_raw or "Phoenix" in tz_raw: tz = "MST"
            elif "Los_Angeles" in tz_raw: tz = "PST"
            else: tz = tz_raw.split('/')[-1].replace('_', ' ')
                
            return [name, city, country, tz]
    except:
        pass
    
    # Si la API falla, busca en el diccionario local
    return AIRPORT_DB.get(icao, [icao, "Unknown City", "Unknown", "UTC"])

# --- 1. ITINERARY INPUTS ---
st.subheader("📍 Flight Itinerary")
col1, col2 = st.columns(2)

with col1:
    origin_icao = st.text_input("Departure ICAO", value="KTEB").upper()
    dep_name, dep_city, dep_state, dep_tz = get_airport_details(origin_icao)
    st.caption(f"✨ {dep_name} | {dep_city}, {dep_state}")
    dep_fbo = st.text_input("Departure FBO", value="Signature Flight Support")
    dep_time = st.text_input("Departure Time", value="10:00 AM")
    ramp_dep = st.radio("Dep. Ramp Access", ["Authorized", "Not Authorized"], horizontal=True, key="r_dep")

with col2:
    dest_icao = st.text_input("Arrival ICAO", value="KOPF").upper()
    arr_name, arr_city, arr_state, arr_tz = get_airport_details(dest_icao)
    st.caption(f"✨ {arr_name} | {arr_city}, {arr_state}")
    arr_fbo = st.text_input("Arrival FBO", value="Jet Aviation")
    arr_time = st.text_input("Arrival Time", value="01:30 PM")
    ramp_arr = st.radio("Arr. Ramp Access", ["Authorized", "Not Authorized"], horizontal=True, key="r_arr")

milestone = st.selectbox("Current Milestone", [
    "Trip Coordination", 
    "Repositioning Update", 
    "FBO Arrival & Boarding Coordination", 
    "Departure & Enroute Monitoring"
])

# --- 2. WEATHER & 3. SERVICES (Manteniendo tu estructura) ---
st.subheader("🌫️ Weather & ⚙️ Services")
cw1, cw2 = st.columns(2)
with cw1:
    d_icon_k = st.selectbox("Dep WX", list(WEATHER_ICONS.keys()))
    dep_wx_msg = st.text_input("Dep Brief", value="Visual conditions")
with cw2:
    a_icon_k = st.selectbox("Arr WX", list(WEATHER_ICONS.keys()))
    arr_wx_msg = st.text_input("Arr Brief", value="Standard arrival")

s_pets = st.checkbox("Pets")
s_catering = st.checkbox("Catering")
s_ground = st.checkbox("Ground Transportation")

# --- 4. GENERATOR FUNCTION (ESTRUCTURA SEGURA) ---
def generate_newsletter_html():
    BRAND_COLOR = "#cb2d42"
    DARK_BAR = "#282522"
    
    # Mapeo de mensajes según Milestone
    msg_map = {
        "Trip Coordination": "Please find attached the updated trip sheet reflecting the confirmed revisions.",
        "Repositioning Update": "The aircraft is currently in its repositioning phase, operations are on track.",
        "FBO Arrival & Boarding Coordination": f"Aircraft is ready at {dep_fbo}. Crew is standing by for boarding.",
        "Departure & Enroute Monitoring": "The aircraft is preparing for departure. Monitoring flight progress."
    }

    # Estilos para Ramp Access
    def r_tag(status):
        c = BRAND_COLOR if status == "Authorized" else "#999"
        return f'<div style="font-size:8px; color:{c}; font-weight:800; margin-top:5px;">• PLANE-SIDE: <b>{status.upper()}</b></div>'

    html = f"""
    <div style="font-family:Arial; max-width:550px; border:1px solid {DARK_BAR}; margin:auto; background:#fff;">
        <div style="background:{DARK_BAR}; padding:35px 20px; text-align:center;">
            <h2 style="color:#fff; margin:0; font-size:15px; letter-spacing:3px;">{milestone.upper()}</h2>
        </div>
        <div style="padding:35px; color:#333;">
            <div style="text-align:center; margin-bottom:30px; background:#f9f9f9; padding:25px; border-radius:12px;">
                <span style="font-size:32px; font-weight:800;">{origin_icao}</span> 
                <span style="color:{BRAND_COLOR}; font-size:20px; margin:0 15px;">➤</span> 
                <span style="font-size:32px; font-weight:800;">{dest_icao}</span>
                <div style="font-size:12px; color:#666; margin-top:8px; font-weight:600;">{dep_city.upper()} TO {arr_city.upper()}</div>
            </div>
            <p style="font-size:15px; line-height:1.5; color:#444; text-align:center;">{msg_map[milestone]}</p>
            
            <table width="100%" style="margin-top:30px; border-top:1px solid #eee; padding-top:20px;">
                <tr>
                    <td style="width:50%; vertical-align:top; border-right:1px solid #eee; padding-right:15px;">
                        <b style="color:{BRAND_COLOR}; font-size:10px;">DEPARTURE</b><br>
                        <b style="font-size:16px;">{dep_time} <span style="font-size:11px; color:#666; font-weight:400;">({dep_tz})</span></b><br>
                        <div style="font-size:12px;">FBO: {dep_fbo}</div>
                        {r_tag(ramp_dep)}
                    </td>
                    <td style="width:50%; vertical-align:top; padding-left:15px; text-align:right;">
                        <b style="color:{BRAND_COLOR}; font-size:10px;">ARRIVAL</b><br>
                        <b style="font-size:16px;">{arr_time} <span style="font-size:11px; color:#666; font-weight:400;">({arr_tz})</span></b><br>
                        <div style="font-size:12px;">FBO: {arr_fbo}</div>
                        {r_tag(ramp_arr)}
                    </td>
                </tr>
            </table>
        </div>
        <div style="background:{DARK_BAR}; padding:15px; text-align:center; font-size:10px; color:#fff;">VIP OPERATIONAL UPDATE | PRIVATE AVIATION</div>
    </div>
    """
    return html

# --- 5. ACTION ---
st.markdown("---")
if st.button("Generate Executive Report"):
    report_html = generate_newsletter_html()
    st.components.v1.html(report_html, height=800)
