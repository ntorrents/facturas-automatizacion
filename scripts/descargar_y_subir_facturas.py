import os
from imap_tools import MailBox, AND
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Cargar variables del archivo .env
load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
CARPETA_DESCARGA = "data"
NOMBRE_CARPETA_DRIVE = "10 Facturas"
SCOPES = ['https://www.googleapis.com/auth/drive.file']

os.makedirs(CARPETA_DESCARGA, exist_ok=True)

def autenticar_google_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def obtener_o_crear_carpeta(service, nombre_carpeta):
    resultados = service.files().list(
        q=f"name='{nombre_carpeta}' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields="files(id, name)").execute()
    archivos = resultados.get('files', [])

    if archivos:
        return archivos[0]['id']
    else:
        archivo_metadata = {
            'name': nombre_carpeta,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        carpeta = service.files().create(body=archivo_metadata, fields='id').execute()
        return carpeta.get('id')

def subir_archivo(service, folder_id, ruta_archivo, nombre_archivo):
    file_metadata = {
        'name': nombre_archivo,
        'parents': [folder_id]
    }
    media = MediaFileUpload(ruta_archivo, mimetype='application/pdf')
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    print(f'✅ Subido: {nombre_archivo} (ID: {file.get("id")})')

def descargar_y_subir_facturas():
    servicio = autenticar_google_drive()
    carpeta_id = obtener_o_crear_carpeta(servicio, NOMBRE_CARPETA_DRIVE)

    with MailBox(IMAP_SERVER).login(EMAIL, PASSWORD, initial_folder='INBOX') as mailbox:
        print("Buscando correos con facturas no leídas...")
        for msg in mailbox.fetch(AND(subject='factura', seen=False)):
            print(f"📧 Asunto: {msg.subject}")
            for att in msg.attachments:
                if att.filename.endswith('.pdf'):
                    ruta_archivo = os.path.join(CARPETA_DESCARGA, att.filename)
                    with open(ruta_archivo, 'wb') as f:
                        f.write(att.payload)
                    print(f"📥 PDF guardado localmente: {att.filename}")

                    subir_archivo(servicio, carpeta_id, ruta_archivo, att.filename)

            # Opcional: marcar el correo como leído para no volver a procesarlo
            mailbox.flag(msg.uid, '\\Seen', True)

if __name__ == "__main__":
    descargar_y_subir_facturas()
