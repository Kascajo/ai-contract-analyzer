import streamlit as st
import pdfplumber
import json
from dotenv import load_dotenv
from pydantic import BaseModel
from google import genai

# 1. Configuración de credenciales
load_dotenv()
cliente_ia = genai.Client()

# 2. El Molde de Datos
class AnalisisContrato(BaseModel):
    partes_involucradas: list[str]
    fecha_de_firma: str
    clausulas_de_riesgo_o_penalizacion: list[str]
    resumen_ejecutivo: str

# 3. Funciones base
def extraer_texto_pdf(archivo_pdf):
    texto_completo = ""
    # Streamlit nos entrega el archivo listo para que pdfplumber lo lea
    with pdfplumber.open(archivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto_extraido = pagina.extract_text()
            if texto_extraido:
                texto_completo += texto_extraido + "\n"
    return texto_completo

def analizar_contrato_con_ia(texto_del_contrato):
    instruccion = f"""
    Eres un abogado experto. Analiza el siguiente contrato y extrae la información solicitada.
    Si no encuentras una fecha, escribe 'No especificada'.
    Contrato:
    {texto_del_contrato}
    """
    respuesta = cliente_ia.models.generate_content(
        model='gemini-3.8-flash',
        contents=instruccion,
        config={
            'response_mime_type': 'application/json',
            'response_schema': AnalisisContrato,
            'temperature': 0.1
        }
    )
    return respuesta.text

# 4. EL DECORADOR: Interfaz de Usuario
st.title("⚖️ Analizador Inteligente de Contratos")
st.write("Sube un contrato en formato PDF para extraer automáticamente sus datos clave y riesgos.")

# Widget para subir el archivo
archivo_subido = st.file_uploader("Arrastra tu PDF aquí", type="pdf")

# Si hay un archivo cargado, mostramos el botón de análisis
if archivo_subido is not None:
    if st.button("Analizar Contrato"):
        
        # Rueda de carga mientras se ejecuta el proceso
        with st.spinner("Analizando con IA... esto puede tomar unos segundos."):
            
            # Paso A: Leer el documento
            texto_contrato = extraer_texto_pdf(archivo_subido)
            
            if texto_contrato.strip() == "":
                st.error("No se pudo extraer texto. Verifica que el PDF no sea una imagen escaneada.")
            else:
                # Paso B: Enviar texto a la IA
                resultado_json_str = analizar_contrato_con_ia(texto_contrato)
                
                # Paso C: Convertir la respuesta de texto a un diccionario de Python
                datos = json.loads(resultado_json_str)
                
                # Paso D: Mostrar los datos extraídos de forma elegante
                st.success("¡Análisis completado!")
                
                st.subheader("Resumen Ejecutivo")
                st.write(datos["resumen_ejecutivo"])
                
                st.subheader("📅 Fecha de Firma")
                st.write(datos["fecha_de_firma"])
                
                st.subheader("🤝 Partes Involucradas")
                for parte in datos["partes_involucradas"]:
                    st.markdown(f"- {parte}")
                    
                st.subheader("⚠️ Cláusulas de Riesgo o Penalización")
                for riesgo in datos["clausulas_de_riesgo_o_penalizacion"]:
                    st.markdown(f"- {riesgo}")