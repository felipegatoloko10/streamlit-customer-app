import os
import pickle
import google.oauth2.credentials
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request
import googleapiclient.discovery
import googleapiclient.errors
import streamlit as st

# Escopos e nomes de arquivo
SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'

class GoogleDriveServiceError(Exception):
    """Exceção base para erros do serviço Google Drive."""
    pass

def _get_credentials():
    """
    Função interna para carregar credenciais existentes do token.pickle.
    Tenta atualizar se estiverem expiradas. Retorna None se não forem válidas.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        except (EOFError, pickle.UnpicklingError):
            creds = None
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
    
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        except Exception:
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            return None
            
    if creds and creds.valid:
        return creds
    return None

def initiate_authentication():
    """
    Inicia o fluxo de autenticação automático e interativo, abrindo uma aba
    no navegador e rodando um servidor local temporário para receber a resposta.
    """
    if not os.path.exists(CREDENTIALS_FILE):
        st.error(f"Arquivo '{CREDENTIALS_FILE}' não encontrado. Por favor, faça o upload dele na seção de configuração da página de Backup.")
        return

    try:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE, SCOPES)
        
        # O run_local_server abre o navegador e captura a resposta automaticamente.
        with st.spinner("Aguardando autorização do Google... Abra a aba do navegador que apareceu para continuar."):
            creds = flow.run_local_server(port=0)
        
        # Salva as credenciais para a próxima execução
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        
        st.success("Autenticação com Google Drive concluída com sucesso!")
        st.info("A página será recarregada para aplicar a nova conexão.")
        st.rerun()

    except Exception as e:
        st.error(f"Ocorreu um erro durante a autenticação: {e}")

def get_drive_service():
    """
    Retorna um objeto de serviço Google Drive API v3 se autenticado, senão None.
    Não inicia o fluxo de autenticação interativo.
    """
    creds = _get_credentials()
    if not creds:
        return None
    try:
        return googleapiclient.discovery.build('drive', 'v3', credentials=creds)
    except Exception as e:
        raise GoogleDriveServiceError(f"Erro ao construir o serviço Google Drive: {e}")

def get_authenticated_user_email():
    """Retorna o email do usuário autenticado no Google Drive, ou None."""
    creds = _get_credentials()
    if not creds:
        return None
    try:
        service = googleapiclient.discovery.build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        return user_info.get('email')
    except Exception:
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        return None

def disconnect_drive_account():
    """Deleta o arquivo de token, forçando uma re-autenticação na próxima vez."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
    st.success("Conta Google Drive desconectada com sucesso!")
    st.rerun()

def upload_file_to_drive(local_file_path, drive_file_name):
    """
    Faz upload de um arquivo para o Google Drive, sobrescrevendo se já existir.
    """
    service = get_drive_service()
    if not service:
        raise GoogleDriveServiceError("Não autenticado com o Google Drive. Conecte uma conta na página de Backup.")

    response = service.files().list(q=f"name='{drive_file_name}' and trashed=false", spaces='drive', fields='files(id, name)').execute()
    items = response.get('files', [])
    file_id = items[0]['id'] if items else None
    
    media_body = googleapiclient.http.MediaFileUpload(local_file_path, mimetype='application/octet-stream', resumable=True)

    if file_id:
        request = service.files().update(fileId=file_id, media_body=media_body, fields='id')
    else:
        file_metadata = {'name': drive_file_name}
        request = service.files().create(body=file_metadata, media_body=media_body, fields='id')
    
    st.toast(f"Enviando backup '{drive_file_name}' para o Google Drive...")
    response = request.execute()
    return response.get('id') if response else file_id
