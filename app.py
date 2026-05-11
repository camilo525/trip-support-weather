import streamlit as st
import requests

# Configuración visual
st.set_page_config(page_title="Trip Support Weather AI", page_icon="✈️")

st.title("✈️ Trip Support Weather Concierge")
st.markdown("Genera reportes ejecutivos para clientes en segundos.")

# --- TU LLAVE API ---
API_KEY = "1b89b9a703e34d8596a1b932c0d30a82"

# Entradas del usuario
icao = st.text_input("Ingrese el código ICAO (ej. KTEB, LEIB):", value="KTEB").upper()
tipo = st.selectbox("Tipo de reporte:", ["taf", "metar"])

if st.button("Generar Reporte para Cliente"):
    url = f"https://api.checkwx.com/{tipo}/{icao}/decoded"
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data["results"] > 0:
            info = data["data"][0]
            raw = info["raw_text"]
            
            # Lógica de traducción simple
            vis = info.get("visibility", {}).get("miles_float", 10)
            viento = info.get("wind", {}).get("speed_kts", 0)
            
            # Crear el resumen
            resumen = f"**FLIGHT WEATHER ASSESSMENT - {icao}**\n\n"
            resumen += f"**[RAW DATA]**\n`{raw}`\n\n"
            resumen += "**[EXECUTIVE SUMMARY]**\n"
            
            if vis >= 6:
                resumen += "• **Visibility:** Excellent skies for flight operations.\n"
            else:
                resumen += "• **Visibility:** Limited visibility; monitoring closely.\n"
                
            if viento < 15:
                resumen += "• **Winds:** Light and favorable winds.\n"
            else:
                resumen += f"• **Winds:** Gusty winds ({viento}kts). Expect minor turbulence.\n"
            
            resumen += "\n**OPERATIONAL IMPACT:** No major weather delays anticipated."

            # Mostrar resultado
            st.info("Reporte listo para copiar:")
            st.code(resumen, language="markdown")
            
        else:
            st.error("No se encontró información para ese aeropuerto.")
    except:
        st.error("Error de conexión.")

st.caption("Trip Support AI Tool v1.0")
