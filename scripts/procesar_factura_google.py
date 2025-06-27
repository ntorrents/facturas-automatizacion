from google.cloud import documentai_v1 as documentai
import os
import pandas as pd
import glob
from dateutil import parser

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "documentai-key.json"

client_options = {"api_endpoint": "eu-documentai.googleapis.com"}
client = documentai.DocumentProcessorServiceClient(client_options=client_options)

PROJECT_ID = "179194022162"
LOCATION = "eu"
PROCESSOR_ID = "c68749698500d498"

PDF_FOLDER = "data"
OUTPUT_XLSX = "facturas_extraidas_todas.xlsx"

def extraer_campo(entities, tipo_campo):
    for entity in entities:
        if entity.type_ == tipo_campo:
            return entity.mention_text
    return ""

def normalizar_fecha(fecha_str):
    if not fecha_str:
        return ""
    try:
        # Parser inteligente para fechas en varios formatos (ej: "15 de enero de 2025")
        fecha = parser.parse(fecha_str, dayfirst=True, fuzzy=True)
        return fecha.strftime("%d/%m/%Y")
    except Exception:
        return fecha_str  # Devuelve la original si no puede parsear

def procesar_pdf(ruta_pdf):
    name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"
    with open(ruta_pdf, "rb") as f:
        contenido = f.read()

    documento_raw = documentai.RawDocument(content=contenido, mime_type="application/pdf")
    request = documentai.ProcessRequest(name=name, raw_document=documento_raw)
    resultado = client.process_document(request=request)
    documento = resultado.document

    empresa = extraer_campo(documento.entities, "supplier_name")
    fecha_raw = extraer_campo(documento.entities, "invoice_date")
    fecha = normalizar_fecha(fecha_raw)
    importe = extraer_campo(documento.entities, "total_amount")

    return {
        "archivo": os.path.basename(ruta_pdf),
        "empresa": empresa,
        "fecha": fecha,
        "importe": importe
    }

def main():
    archivos_pdf = glob.glob(os.path.join(PDF_FOLDER, "*.pdf"))
    print(f"Procesando {len(archivos_pdf)} PDFs...")

    resultados = []
    for ruta in archivos_pdf:
        print(f"Procesando {ruta}...")
        datos = procesar_pdf(ruta)
        resultados.append(datos)

    df = pd.DataFrame(resultados)
    df.to_excel(OUTPUT_XLSX, index=False)
    print(f"Excel generado: {OUTPUT_XLSX}")

if __name__ == "__main__":
    main()
