import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import streamlit as st

SCOPES = [
    'https://www.googleapis.com/auth/drive.file', 
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, 'token.pickle')
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')

class GoogleDriveServiceError(Exception):
    pass

def get_credentials():
    """Carrega credenciais existentes e as atualiza se necessário."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        except (EOFError, pickle.UnpicklingError):
            creds = None
            if os.path.exists(TOKEN_FILE): os.remove(TOKEN_FILE)
    
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        except Exception:
            if os.path.exists(TOKEN_FILE): os.remove(TOKEN_FILE)
            return None
            
    if creds and creds.valid:
        return creds
    return None

def initiate_authentication():
    """
    Inicia o fluxo de autenticação automático e interativo.
    Retorna True se a autenticação foi bem-sucedida, False caso contrário.
    """
    if not os.path.exists(CREDENTIALS_FILE):
        st.error(f"Arquivo '{CREDENTIALS_FILE}' não encontrado. Por favor, faça o upload no Passo 1.")
        return False

    try:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        with st.spinner("Aguardando autorização do Google... Abra a aba do navegador que apareceu para continuar."):
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        
        st.session_state.auth_success = True # Sinaliza sucesso para a próxima execução
        return True

    except Exception as e:
        st.error(f"Ocorreu um erro durante a autenticação: {e}")
        return False

def get_drive_service():
    """Retorna um objeto de serviço do Google Drive se autenticado, senão None."""
    creds = get_credentials()
    if not creds:
        return None
    try:
        return build('drive', 'v3', credentials=creds)
    except HttpError as error:
        raise GoogleDriveServiceError(f"Erro ao construir serviço do Drive: {error}")

def get_authenticated_user_email():
    """Retorna o e-mail do usuário autenticado, ou None."""
    creds = get_credentials()
    if not creds:
        return None
    try:
        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        return user_info.get('email')
    except Exception:
        if os.path.exists(TOKEN_FILE): os.remove(TOKEN_FILE)
        return None

def disconnect_drive_account():
    """Deleta o arquivo de token para forçar uma nova autenticação."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)

def upload_file_to_drive(local_file_path, drive_file_name):
    """Faz upload de um arquivo para o Google Drive, sobrescrevendo se já existir."""
    import logging
    service = get_drive_service()
    if not service:
        logging.error("Backup falhou: Usuário não autenticado no Google Drive.")
        raise GoogleDriveServiceError("Não autenticado com o Google Drive.")
    
    try:
        # Tenta encontrar o arquivo pelo nome exato para sobrescrever
        response = service.files().list(
            q=f"name='{drive_file_name}' and trashed=false", 
            spaces='drive', 
            fields='files(id)'
        ).execute()
        
        items = response.get('files', [])
        file_id = items[0]['id'] if items else None
        
        media_body = MediaFileUpload(local_file_path, mimetype='application/octet-stream', resumable=True)
        
        if file_id:
            logging.info(f"Atualizando arquivo existente no Drive (ID: {file_id})...")
            request = service.files().update(fileId=file_id, media_body=media_body)
        else:
            logging.info(f"Criando novo arquivo '{drive_file_name}' no Drive...")
            file_metadata = {'name': drive_file_name}
            request = service.files().create(body=file_metadata, media_body=media_body, fields='id')
        
        result = request.execute()
        logging.info(f"Upload para o Drive concluído com sucesso. ID: {result.get('id')}")
        return True
        
    except Exception as e:
        logging.error(f"Falha técnica no upload para o Drive: {e}")
        raise GoogleDriveServiceError(f"Erro no upload: {e}")
