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

    .tool-container {
        display: flex; gap: 15px; margin-top: 25px; margin-bottom: 25px; flex-wrap: wrap;
    }
    .tool-btn {
        flex: 1; min-width: 200px; padding: 15px; border-radius: 12px;
        text-align: center; text-decoration: none; font-weight: bold; font-size: 0.9em;
        transition: 0.3s; border: 1px solid rgba(255,255,255,0.1);
    }
    .btn-sat { background: rgba(0, 212, 255, 0.1); color: #00d4ff !important; border-color: #00d4ff; }
    .btn-map { background: rgba(168, 85, 247, 0.1); color: #a855f7 !important; border-color: #a855f7; }
    .btn-notam { background: rgba(255, 204, 0, 0.1); color: #ffcc00 !important; border-color: #ffcc00; }
    
    .tool-btn:hover { transform: translateY(-3px); background: rgba(255,255,255,0.1); box-shadow: 0 4px 15px rgba(0,0,0,0.5); }

    .executive-card { background: rgba(255,255,255,0.03); padding: 35px; border-radius: 20px; border-left: 6px solid #00d4ff; }
    .status-stable { color: #00ff00; font-weight: bold; }
    .status-alert { color: #ff0000; font-weight: bold; text-decoration: underline; }
    input { background-color: #0a0a0a !important; border: 1px solid #333333 !important; color: #00d4ff !important; }
    .footer-container { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; padding: 40px 0px; margin-top: 30px; border-top: 1px solid #222222; }
    </style>
    """, unsafe_allow_html=True)

LOGO
