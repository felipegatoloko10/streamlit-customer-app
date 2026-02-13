import streamlit as st
import os
import shutil
import datetime
import json
import sqlite3
import google_drive_service
import backup_manager

import integration_services as services

# --- Configurações da Página e Constantes ---
st.set_page_config(page_title="Backup e Restauração", layout="centered")

# Exibe o status da nuvem na sidebar
services.show_cloud_status()

st.title("💾 Backup e Restauração de Dados")

# Exibe mensagem de sucesso se veio de uma autenticação
if st.session_state.get("auth_success"):
    st.success("✅ Conexão com Google Drive estabelecida com sucesso!")
    del st.session_state.auth_success

st.info("Gerencie cópias de segurança locais e em nuvem do seu banco de dados.")

DB_FILE = 'customers.db'

# --- Funções Auxiliares ---
def is_valid_db_file(file_path: str) -> bool:
    """Verifica se um arquivo é um banco de dados SQLite3 válido."""
    if not os.path.exists(file_path):
        return False
    try:
        conn = sqlite3.connect(f'file:{file_path}?mode=ro', uri=True)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        conn.close()
        return result and result[0] == 'ok'
    except sqlite3.Error:
        return False

def save_backup_config(threshold):
    """Salva a configuração de frequência do backup automático."""
    config_data = {"threshold": threshold}
    try:
        with open(backup_manager.BACKUP_CONFIG_FILE, 'w') as f:
            json.dump(config_data, f)
    except IOError as e:
        st.error(f"Erro ao salvar configurações de backup: {e}")

# --- Seção 1: Backup e Restauração Local ---
with st.expander("1. Backup e Restauração Local (Manual)", expanded=False):

    st.subheader("Criar e Baixar um Backup Local (Exportação)")
    
    col_fmt, col_btn = st.columns([1, 2])
    with col_fmt:
        export_format = st.radio("Formato:", ["JSON", "CSV"], horizontal=True)
    
    with col_btn:
        st.write("") # Spacer
        st.write("") # Spacer
        if st.button("Gerar Arquivo de Exportação"):
            with st.spinner(f"Gerando arquivo {export_format} com todos os dados..."):
                try:
                    # Gera o arquivo usando o manager
                    backup_file = backup_manager.generate_local_export(format=export_format)
                    
                    mime_type = "application/json" if export_format == "JSON" else "text/csv"
                    
                    with open(backup_file, "rb") as fp:
                        st.download_button(
                            label=f"⬇️ Baixar Exportação ({export_format})",
                            data=fp,
                            file_name=backup_file,
                            mime=mime_type,
                            use_container_width=True
                        )
                    
                except Exception as e:
                    st.error(f"Erro ao gerar exportação: {e}")
                
    st.info("O backup gera um arquivo contendo todos os dados dos clientes, compatível com o novo banco de dados Supabase.")
    
    st.markdown("---")
    
    st.subheader("Restaurar a partir de um Backup Local")
    uploaded_file = st.file_uploader("Selecione um arquivo de backup (.json ou .csv):", type=['json', 'csv'], key="backup_uploader")

    if uploaded_file:
        st.warning("⚠️ Atenção: A restauração irá adicionar os clientes do arquivo ao banco de dados. Clientes com CPF/CNPJ já existentes serão ignorados.")
        if st.button("Iniciar Restauração", type="primary"):
            with st.spinner("Processando restauração... isso pode levar alguns instantes..."):
                # Salva arquivo temporário para processamento
                try:
                    file_ext = uploaded_file.name.split('.')[-1].lower()
                    temp_filename = f"temp_restore.{file_ext}"
                    with open(temp_filename, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Chama o manager
                    result = backup_manager.restore_data(temp_filename, file_ext)
                    
                    # Remove temp
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
                    
                    if result["success"]:
                        st.success(f"Restauração concluída! {result['imported']} registros importados com sucesso.")
                        if result["errors"] > 0:
                            st.warning(f"{result['errors']} registros foram ignorados (provavelmente duplicados ou erros).")
                            with st.expander("Ver detalhes dos erros/ignorados"):
                                for err in result["details"]:
                                    st.write(err)
                    else:
                        st.error(result["message"])
                        
                except Exception as e:
                    st.error(f"Erro crítico na restauração: {e}")


# --- Seção 2: Backup em Nuvem (Google Drive) ---
st.markdown("---")
st.header("Backup em Nuvem (Google Drive)")

try:
    authenticated_email = google_drive_service.get_authenticated_user_email()

    if authenticated_email:
        st.success(f"**Status:** Conectado ao Google Drive como `{authenticated_email}`")
        st.markdown("---")
        
        st.subheader("Opções de Backup na Nuvem")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Fazer Backup para o Drive Agora", type="primary", use_container_width=True):
                backup_manager.trigger_manual_backup()
        with col2:
            if st.button("Desconectar / Trocar Conta", use_container_width=True):
                google_drive_service.disconnect_drive_account()
                st.rerun()
        
        st.markdown("---")
        st.subheader("Backup Automático")
        current_threshold = backup_manager.load_backup_threshold()
        new_threshold = st.slider(
            f"Fazer backup a cada X novos clientes:",
            min_value=1, max_value=10, value=current_threshold
        )
        if new_threshold != current_threshold:
            save_backup_config(new_threshold)
            st.toast(f"Frequência de backup atualizada para cada {new_threshold} clientes.")

    else: # UI para quando o usuário NÃO ESTÁ CONECTADO
        st.warning("**Status:** Nenhuma conta Google Drive conectada.")
        st.markdown("---")
        
        with st.expander("Como configurar o backup no Google Drive?", expanded=True):
            st.subheader("Passo 1: Faça o upload do seu `credentials.json`")
            st.info("Para usar o backup em nuvem, você precisa de um arquivo de credenciais do Google.")
            
            uploaded_creds = st.file_uploader("Selecione o arquivo de credenciais", type=['json'], key="gdrive_creds_uploader")
            
            if uploaded_creds:
                # Verifica se o arquivo já existe e se o conteúdo é o mesmo para evitar loop
                creds_content = uploaded_creds.getbuffer()
                should_save = True
                if os.path.exists(google_drive_service.CREDENTIALS_FILE):
                    with open(google_drive_service.CREDENTIALS_FILE, "rb") as f:
                        if f.read() == creds_content:
                            should_save = False
                
                if should_save:
                    with open(google_drive_service.CREDENTIALS_FILE, "wb") as f:
                        f.write(creds_content)
                    st.success(f"Arquivo `{uploaded_creds.name}` salvo! Prossiga para o Passo 2.")
                    # Limpa o token antigo para forçar nova autenticação se as credenciais mudaram
                    if os.path.exists(google_drive_service.TOKEN_FILE):
                        os.remove(google_drive_service.TOKEN_FILE)
                    st.rerun()

            st.markdown("---")
            
            st.subheader("Passo 2: Conecte sua Conta Google")
            creds_exist = os.path.exists(google_drive_service.CREDENTIALS_FILE)
            
            if not creds_exist:
                st.caption("O botão de conexão será habilitado após o upload do `credentials.json` no Passo 1.")
            
            if creds_exist:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 Conectar Automaticamente", type="primary", use_container_width=True):
                        try:
                            with st.spinner("Abrindo navegador..."):
                                success = google_drive_service.initiate_authentication()
                            if success:
                                st.success("Conectado!")
                                st.rerun()
                        except Exception as e:
                            st.error("Não foi possível abrir o navegador automaticamente no servidor. Use a 'Conexão Manual' abaixo.")
                
                with col2:
                    show_manual = st.toggle("Mostrar Conexão Manual", help="Use esta opção se estiver no Streamlit Cloud/Internet")

                if show_manual:
                    st.markdown("---")
                    auth_url = google_drive_service.get_auth_url()
                    st.markdown(f"1. [Clique aqui para autorizar o acesso]({auth_url})")
                    auth_code = st.text_input("Cole o código aqui:", key="gdrive_auth_code")
                    if st.button("Confirmar Código", use_container_width=True):
                        if google_drive_service.finalize_manual_auth(auth_code):
                            st.rerun()
            
            st.markdown("---")
            with st.expander("Instruções detalhadas para gerar o `credentials.json`"):
                st.markdown("""
                1.  **Acesse o Google Cloud Console:** [console.cloud.google.com](https://console.cloud.google.com/)
                2.  **Crie um Novo Projeto:** No topo da página, clique em "Selecionar um projeto" > "NOVO PROJETO". Dê um nome (ex: `App Backup`) e clique em "CRIAR".
                3.  **Ative a API do Google Drive:** Na barra de busca, procure por **"Google Drive API"** e clique em **"ATIVAR"**.
                4.  **Configure a Tela de Consentimento:**
                    *   No menu lateral, vá para "APIs e Serviços" > "Tela de consentimento OAuth".
                    *   Escolha **"Externo"** e clique em "CRIAR".
                    *   Preencha o "Nome do app" (ex: `App de Backup`) e seu "E-mail de suporte do usuário".
                    *   Role até o fim e clique em "SALVAR E CONTINUAR" nas seções seguintes, não precisa adicionar mais nada.
                5.  **Adicione seu E-mail como Testador:**
                    *   Ainda na "Tela de consentimento OAuth", vá para a aba **"Usuários de teste"**.
                    *   Clique em **"+ ADICIONAR USUÁRIOS"**, digite seu próprio e-mail do Google e clique em "SALVAR".
                6.  **Crie as Credenciais:**
                    *   No menu lateral, vá para **"Credenciais"**.
                    *   Clique em **"+ CRIAR CREDENCIAIS"** > **"ID do cliente OAuth"**.
                    *   Em "Tipo de aplicativo", selecione **"App para computador"**.
                    *   Clique em **"CRIAR"**.
                7.  **Baixe o Arquivo:**
                    *   Uma janela aparecerá. Clique no botão **"FAZER O DOWNLOAD DO JSON"**.
                    *   **Renomeie** o arquivo baixado para `credentials.json`.
                    *   Use o botão de upload no **Passo 1** acima para enviar este arquivo.
                """)

except Exception as e:
    st.error(f"Ocorreu um erro fatal na página de Backup: {e}")
    st.exception(e)

# --- Seção 3: Configuração de Notificações por E-mail ---
st.markdown("---")
st.header("📧 Configuração de Notificações por E-mail")

email_config_file = 'email_config.json'
current_config = {}

if os.path.exists(email_config_file):
    try:
        with open(email_config_file, 'r') as f:
            current_config = json.load(f)
    except:
        pass

with st.form("email_config_form"):
    st.info("Configure o envio de e-mails para receber notificações quando um novo cliente for cadastrado.")
    
    # Verifica se existem secrets configurados
    using_secrets = False
    secrets_source = ""
    
    if "email_config" in st.secrets:
        using_secrets = True
        secrets_source = "st.secrets['email_config']"
        secrets_data = st.secrets["email_config"]
    elif all(k in st.secrets for k in ["email_sender", "email_password"]):
        using_secrets = True
        secrets_source = "st.secrets (raiz)"
        secrets_data = {
            "sender_email": st.secrets.get("email_sender"),
            "password": st.secrets.get("email_password"),
            "smtp_server": st.secrets.get("smtp_server", "smtp.gmail.com"),
            "smtp_port": st.secrets.get("smtp_port", "587"),
            "app_base_url": st.secrets.get("app_base_url")
        }
    
    if using_secrets:
        st.success(f"🔒 Configurações carregadas via Secrets ({secrets_source}). O arquivo local `email_config.json` será ignorado se existir.")
        
        # Exibe valores como desabilitados para informar o usuário
        st.text_input("E-mail do Remetente", value=secrets_data.get('sender_email', ''), disabled=True)
        st.text_input("Senha de App", type="password", value="********", disabled=True)
        st.text_input("Servidor SMTP", value=secrets_data.get('smtp_server', ''), disabled=True)
        st.text_input("Porta SMTP", value=secrets_data.get('smtp_port', ''), disabled=True)
        st.text_input("URL Base", value=secrets_data.get('app_base_url', ''), disabled=True)
        
        st.caption("Para alterar essas configurações, edite o arquivo `.streamlit/secrets.toml` ou as configurações do Streamlit Cloud.")
        submitted = st.form_submit_button("Salvar Configurações Locais (Não Recomendado)", disabled=True)
        
    else:
        # Modo Edição Manual (JSON)
        sender_email = st.text_input("E-mail do Remetente (Gmail)", value=current_config.get('sender_email', ''))
        app_password = st.text_input("Senha de App do Google", type="password", value=current_config.get('password', ''), help="Não é a sua senha normal. É uma senha de 16 caracteres gerada no Google.")
        
        smtp_server = st.text_input("Servidor SMTP", value=current_config.get('smtp_server', 'smtp.gmail.com'))
        smtp_port = st.text_input("Porta SMTP", value=current_config.get('smtp_port', '587'))
        
        app_base_url = st.text_input("URL Base do App (para links)", value=current_config.get('app_base_url', 'http://localhost:8501'))

        submitted = st.form_submit_button("Salvar Configurações")
        
        if submitted:
            new_config = {
                'sender_email': sender_email,
                'password': app_password,
                'smtp_server': smtp_server,
                'smtp_port': smtp_port,
                'app_base_url': app_base_url
            }
            try:
                with open(email_config_file, 'w') as f:
                    json.dump(new_config, f)
                st.success("Configurações de e-mail salvas com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar configurações: {e}")

with st.expander("Como obter sua Senha de App do Google"):
    st.markdown("""
    1. Acesse sua Conta Google: [myaccount.google.com](https://myaccount.google.com/)
    2. No menu lateral, clique em **Segurança**.
    3. Em "Como você faz login no Google", ative a **Verificação em duas etapas** (se ainda não estiver ativa).
    4. Após ativar, procure por **Senhas de app** (você pode usar a barra de busca no topo da página).
    5. Em "Selecionar app", escolha **Outro (nome personalizado)** e digite um nome como "App de Clientes".
    6. Clique em **Gerar**.
    7. O Google mostrará uma senha de 16 letras. Copie essa senha (sem os espaços) e cole no campo "Senha de App do Google" acima.
    """)
