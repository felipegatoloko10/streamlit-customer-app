import os
import pickle
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import streamlit as st
import time

# Se os escopos forem modificados, o token.json deve ser deletado.
SCOPES = ['https://www.googleapis.com/auth/drive.file'] # Permissão para gerenciar arquivos criados/abertos por este app
TOKEN_FILE = 'token.pickle' # Onde as credenciais são salvas após o primeiro login
CREDENTIALS_FILE = 'credentials.json' # Baixado do Google Cloud Console

class GoogleDriveServiceError(Exception):
    """Exceção base para erros do serviço Google Drive."""
    pass

def get_drive_service():
    """Autentica o usuário e retorna um objeto de serviço Google Drive API v3."""
    creds = None
    
    # O arquivo token.pickle armazena os tokens de acesso e refresh do usuário,
    # e é criado automaticamente quando o fluxo de autorização é concluído pela primeira vez.
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            st.warning(f"Erro ao carregar token.pickle: {e}. Re-autenticando.")
            creds = None

    # Se não há credenciais válidas (ou expiraram/não existem), o usuário precisa fazer login.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(google.auth.Request())
            except Exception as e:
                st.warning(f"Erro ao refrescar token: {e}. Re-autenticando.")
                creds = None
        
        if not creds: # Se ainda não temos credenciais, ou o refresh falhou
            if os.path.exists(CREDENTIALS_FILE):
                try:
                    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                        CREDENTIALS_FILE, SCOPES)
                    
                    # Usa um servidor local para o fluxo de autenticação
                    # Permite que o Streamlit interaja com o navegador
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    
                    st.info("Para autorizar o acesso ao Google Drive, por favor, abra o link abaixo no seu navegador, faça login e copie o código de autorização de volta para o campo abaixo.")
                    st.markdown(f"**[Clique aqui para autorizar o Google Drive]({auth_url})**")
                    
                    auth_code = st.text_input("Cole o código de autorização aqui:", key="gdrive_auth_code")
                    
                    if auth_code:
                        try:
                            flow.fetch_token(code=auth_code)
                            creds = flow.credentials
                            # Salva as credenciais para a próxima execução
                            with open(TOKEN_FILE, 'wb') as token:
                                pickle.dump(creds, token)
                            st.success("Autenticação com Google Drive bem-sucedida! Por favor, reinicie a página.")
                            st.rerun() # Reruns to apply new credentials
                        except Exception as e:
                            st.error(f"Erro ao obter token de acesso: {e}. Verifique o código.")
                            st.session_state.gdrive_auth_code = "" # Limpa o campo para nova tentativa
                    else:
                        st.stop() # Páre a execução até que o código seja inserido
                except FileNotFoundError:
                    raise GoogleDriveServiceError(f"Arquivo '{CREDENTIALS_FILE}' não encontrado. Siga as instruções para criá-lo no Google Cloud Console.")
                except Exception as e:
                    raise GoogleDriveServiceError(f"Erro durante o fluxo de autenticação: {e}")
            else:
                raise GoogleDriveServiceError(f"Arquivo '{CREDENTIALS_FILE}' não encontrado. Siga as instruções para criá-lo no Google Cloud Console.")

    try:
        service = googleapiclient.discovery.build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        raise GoogleDriveServiceError(f"Erro ao construir o serviço Google Drive: {e}")

def get_authenticated_user_email():
    """Retorna o email do usuário autenticado no Google Drive."""
    try:
        creds = None
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        if creds and creds.valid:
            service = googleapiclient.discovery.build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            return user_info.get('email')
        return None
    except Exception:
        return None

def disconnect_drive_account():
    """Deleta o arquivo de token, forçando uma re-autenticação na próxima vez."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
    st.success("Conta Google Drive desconectada. Você será solicitado a fazer login novamente na próxima vez que o backup automático for acionado.")
    st.rerun()

def upload_file_to_drive(local_file_path, drive_file_name):
    """
    Faz upload de um arquivo para o Google Drive.
    Se o arquivo já existir, ele será sobrescrito.
    """
    service = get_drive_service() # Isso também autenticará se necessário

    # Busca o arquivo pelo nome para ver se ele já existe
    response = service.files().list(
        q=f"name='{drive_file_name}' and trashed=false",
        spaces='drive',
        fields='nextPageToken, files(id, name)').execute()
    
    items = response.get('files', [])
    file_id = None
    if items:
        file_id = items[0]['id'] # Pega o ID do primeiro arquivo encontrado

    media_body = googleapiclient.http.MediaFileUpload(
        local_file_path,
        mimetype='application/octet-stream', # Ou um mimetype mais específico se souber
        resumable=True
    )

    if file_id:
        # Atualiza o arquivo existente
        updated_file = service.files().update(
            fileId=file_id,
            media_body=media_body
        ).execute()
        st.success(f"Arquivo '{updated_file.get('name')}' atualizado no Google Drive.")
        return updated_file.get('id')
    else:
        # Cria um novo arquivo
        file_metadata = {'name': drive_file_name}
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media_body,
            fields='id, name'
        ).execute()
        st.success(f"Arquivo '{uploaded_file.get('name')}' enviado para o Google Drive.")
        return uploaded_file.get('id')
