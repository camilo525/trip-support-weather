import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ops Assessment Tool", page_icon="✈️", layout="wide")

# --- DISEÑO PRO / CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #050505 !important; color: #FFFFFF !important; }
    .header-style {
        font-size: 26px; font-weight: bold;
        background: -webkit-linear-gradient(#00d4ff, #005fcc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 20px; letter-spacing: 1px;
    }
    .tech-card-origin { padding: 20px; border-radius: 15px; border: 1px solid #00d4ff; background-color: rgba(0, 212, 255, 0.03); margin-bottom: 20px; }
    .tech-card-dest { padding: 20px; border-radius: 15px; border: 1px solid #a855f7; background-color: rgba(168, 85, 247, 0.03); margin-bottom: 20px; }
    .raw-code { font-family: 'Courier New', monospace; color: #00ff00; background: #000; padding: 10px; border-radius: 5px; font-size: 0.9em; line-height: 1.4; border: 1px solid #222; }
    
    .stButton>button {
        background: linear-gradient(45deg, #005fcc, #00d4ff); color: white !important;
        font-weight: bold; border: none; border-radius: 8px; height: 3em; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 15px rgba(0, 212, 255, 0.4); }

    .tool-container { display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap; }
    .tool-btn {
        flex: 1; min-width: 180px; padding: 12px; border-radius: 8px;
        text-align: center; text-decoration: none; font-weight: bold; font-size: 0.8em;
        transition: 0.2s; border: 1px solid rgba(255,255,255,0.1);
    }
    .btn-sat { background: rgba(0, 212, 255, 0.1); color: #00d4ff !important; border-color: #00d4ff; }
    .btn-map { background: rgba(168, 85, 247, 0.1); color: #a855f7 !important; border-color: #a855f7; }
    .btn-notam { background: rgba(255, 204, 0, 0.1); color: #ffcc00 !important; border-color: #ffcc00; }

    .executive-card { 
        background: #ffffff; padding: 40px; border-radius: 15px; 
        border-left: 8px solid #00d4ff; color: #111; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .status-stable { color: #00ff00; font-weight: bold; }
    .status-alert { color: #ff3333; font-weight: bold; }
    
    input { background-color: #111 !important; border: 1px solid #333 !important; color: #00d4ff !important; }
    .footer-container { display: flex; flex-direction: column; align-items: center; padding: 40px 0; margin-top: 30px; border-top: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

# --- ASSETS & API ---
LOGO_UP_LEFT = "https://images.teamtailor-cdn.com/images/s3/teamtailor-na-maroon/logotype-v3/image_uploads/d1ea3807-ceaf-486c-aefb-af34155789ba/original.png" 
LOGO_BOTTOM_CENTER = "
