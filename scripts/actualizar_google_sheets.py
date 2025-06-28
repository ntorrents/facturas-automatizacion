import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# Guarda el contenido del secret como un archivo en tiempo de ejecución
credentials_path = "credentials.json"
with open(credentials_path, "w") as f:
    f.write(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON", ""))

SERVICE_ACCOUNT_FILE = credentials_path
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
RANGE_NAME = os.getenv('RANGE_NAME', 'Facturas!A1')

def leer_google_sheet():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE,
                                                  scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])
    if not values:
        return pd.DataFrame()
    else:
        df = pd.DataFrame(values[1:], columns=values[0])
        return df

def escribir_google_sheet(df):
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE,
                                                  scopes=['https://www.googleapis.com/auth/spreadsheets'])
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    values = [df.columns.to_list()] + df.values.tolist()
    body = {'values': values}
    result = sheet.values().update(spreadsheetId=SPREADSHEET_ID,
                                  range=RANGE_NAME,
                                  valueInputOption='RAW',
                                  body=body).execute()
    print(f"{result.get('updatedCells')} celdas actualizadas.")

def actualizar_facturas():
    df_nuevo = pd.read_excel('facturas_extraidas_todas.xlsx')
    df_actual = leer_google_sheet()
    if df_actual.empty:
        print("Google Sheet vacío, se añade todo el nuevo dataset.")
        df_final = df_nuevo
    else:
        df_final = pd.concat([df_actual, df_nuevo[~df_nuevo['archivo'].isin(df_actual['archivo'])]], ignore_index=True)
    df_final = df_final.sort_values(by='archivo').reset_index(drop=True)
    escribir_google_sheet(df_final)

if __name__ == '__main__':
    actualizar_facturas()
