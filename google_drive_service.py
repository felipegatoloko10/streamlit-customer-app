import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'

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

def get_auth_flow():
    """Cria e retorna um objeto de fluxo de autenticação."""
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(f"Arquivo '{CREDENTIALS_FILE}' não encontrado.")
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    return flow

def fetch_token_from_code(flow, auth_code):
    """Busca o token de acesso usando o código de autorização e o salva."""
    flow.fetch_token(code=auth_code)
    creds = flow.credentials
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(creds, token)
    return creds

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
    service = get_drive_service()
    if not service:
        raise GoogleDriveServiceError("Não autenticado com o Google Drive.")
    
    response = service.files().list(q=f"name='{drive_file_name}' and trashed=false", spaces='drive', fields='files(id)').execute()
    items = response.get('files', [])
    file_id = items[0]['id'] if items else None
    
    media_body = MediaFileUpload(local_file_path, mimetype='application/octet-stream', resumable=True)
    
    if file_id:
        request = service.files().update(fileId=file_id, media_body=media_body)
    else:
        file_metadata = {'name': drive_file_name}
        request = service.files().create(body=file_metadata, media_body=media_body, fields='id')
    
    request.execute()
