if st.button("RUN FULL MISSION ANALYSIS"):
    with st.spinner("Accessing High-Resolution Datalink..."):
        d_dep = get_ops_data(dep_icao, fase)
        d_arr = get_ops_data(arr_icao, fase)

    if d_dep and d_arr:
        def analyze_technical(wx, phase):
            raw = wx.get("raw_text", "").upper()
            vis = wx.get("visibility", {}).get("miles_float", 10)
            wind_dir = wx.get("wind", {}).get("degrees", 0)
            wind_spd = wx.get("wind", {}).get("speed_kts", 0)
            temp = wx.get("temperature", {}).get("celsius", 0)
            altim = wx.get("barometer", {}).get("hg", 0)
            
            ceil = 10000
            cloud_desc = "Clear Skies"
            
            if wx.get("clouds"):
                layers = wx["clouds"]
                cloud_desc = ", ".join([f"{l['code']} at {l.get('base_feet_agl', 0)}ft" for l in layers])
                for l in layers:
                    if l.get("code") in ["BKN", "OVC"]:
                        ceil = min(ceil, l.get("base_feet_agl", 10000))
            
            if "Live" in phase:
                crit = (vis < 3 or wind_spd > 25 or ceil < 1000 or any(x in raw for x in ["TS", "FG", "SN", "SQ"]))
                status = "🔴 CRITICAL" if crit else "🟢 NOMINAL"
                client_msg = "Current conditions are stable for departure." if not crit else "Operations are currently under weather delay/monitoring."
            elif "24h" in phase:
                crit = (vis < 5 or wind_spd > 20 or any(x in raw for x in ["PROB", "TEMPO", "TS"]))
                status = "🟡 MONITORING" if crit else "🟢 STABLE"
                client_msg = "Forecast indicates favorable windows for the scheduled time." if not crit else "Potential weather fluctuations detected. Monitoring closely."
            else:
                status = "🔵 ADVISORY"
                client_msg = "Long-range outlook remains consistent with operational standards."
            
            return {
                "status": status, "vis": vis, "wind": f"{wind_dir}°/{wind_spd}KT", 
                "ceil": ceil, "cloud_desc": cloud_desc, "temp": temp, "alt": altim,
                "client_msg": client_msg, "raw": raw
            }

        res_dep = analyze_technical(d_dep["wx"], fase)
        res_arr = analyze_technical(d_arr["wx"], fase)

        # 1. CLIENT EXECUTIVE REPORT
        st.markdown(f"""<div class="executive-report">
            <h2 style="margin:0; color:#005fcc;">Executive Summary: {d_dep['name']} to {d_arr['name']}</h2>
            <p style="color:#666;">Date: {datetime.utcnow().strftime('%B %d, %Y')} | Assessment: {fase}</p>
            <hr style="border:0.5px solid #eee; margin:20px 0;">
            <p><b>Departure ({dep_icao}):</b> {res_dep['status']} — {res_dep['client_msg']}</p>
            <p><b>Arrival ({arr_icao}):</b> {res_arr['status']} — {res_arr['client_msg']}</p>
        </div>""", unsafe_allow_html=True)

        # 2. TECHNICAL ANALYSIS
        st.markdown("### 🛠 Internal Flight Support Analysis")
        col1, col2 = st.columns(2)
        
        for col, icao, res, info, color in zip([col1, col2], [dep_icao, arr_icao], [res_dep, res_arr], [d_dep, d_arr], ["#00d4ff", "#a855f7"]):
            with col:
                st.markdown(f"""<div class="status-card" style="border-top: 6px solid {color}">
                    <h3 style="margin:0; color:{color};">{info['name']} ({icao})</h3>
                    <p style="font-size:0.8em;
                    
