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
             # Se o arquivo de token estiver corrompido, trata como se não existisse
            creds = None
    
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        except Exception:
            # Se a atualização falhar, remove o token inválido
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            return None
            
    if creds and creds.valid:
        return creds
    return None

def initiate_authentication():
    """
    Inicia o fluxo de autenticação interativo para o usuário.
    Esta função deve ser chamada por um botão na UI.
    """
    if not os.path.exists(CREDENTIALS_FILE):
        st.error(f"Arquivo '{CREDENTIALS_FILE}' não encontrado. Siga as instruções para criá-lo e faça o upload.")
        st.stop()

    try:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE, SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        st.info("Para autorizar o acesso ao Google Drive, siga os passos abaixo:")
        st.markdown(f"1. **[Clique aqui para abrir a página de autorização do Google]({auth_url})**", unsafe_allow_html=True)
        st.write("2. Faça login, conceda as permissões e copie o código de autorização gerado.")
        
        auth_code = st.text_input("3. Cole o código de autorização aqui e pressione Enter para confirmar:")
        
        if auth_code:
            with st.spinner("Verificando código..."):
                flow.fetch_token(code=auth_code)
                creds = flow.credentials
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
        service = googleapiclient.discovery.build('drive', 'v3', credentials=creds)
        return service
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
        return None

def disconnect_drive_account():
    """Deleta o arquivo de token, forçando uma re-autenticação na próxima vez."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
    st.success("Conta Google Drive desconectada com sucesso!")
    st.rerun()

def upload_file_to_drive(local_file_path, drive_file_name):
    """
    Faz upload de um arquivo para o Google Drive.
    Se o arquivo já existir, ele será sobrescrito.
    """
    service = get_drive_service()
    if not service:
        raise GoogleDriveServiceError("Não autenticado com o Google Drive. Por favor, conecte uma conta na página de Backup.")

    # Busca o arquivo pelo nome para ver se ele já existe
    response = service.files().list(
        q=f"name='{drive_file_name}' and trashed=false",
        spaces='drive',
        fields='nextPageToken, files(id, name)').execute()
    
    items = response.get('files', [])
    file_id = items[0]['id'] if items else None

    media_body = googleapiclient.http.MediaFileUpload(local_file_path, mimetype='application/octet-stream', resumable=True)

    if file_id:
        # Atualiza o arquivo existente
        updated_file = service.files().update(fileId=file_id, media_body=media_body).execute()
        return updated_file.get('id')
    else:
        # Cria um novo arquivo
        file_metadata = {'name': drive_file_name}
        uploaded_file = service.files().create(body=file_metadata, media_body=media_body, fields='id').execute()
        return uploaded_file.get('id')