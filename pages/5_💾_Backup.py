import streamlit as st
import os
import shutil
import datetime
import json
import google_drive_service
import backup_manager

# --- Configurações da Página e Constantes ---
st.set_page_config(page_title="Backup e Restauração", layout="centered")
st.title("💾 Backup e Restauração de Dados")
st.info("Gerencie cópias de segurança locais e em nuvem do seu banco de dados.")

DB_FILE = 'customers.db'

# --- Funções Auxiliares ---
def is_valid_db_file(file_path: str) -> bool:
    """Verifica se um arquivo é um banco de dados SQLite3 válido."""
    # (Implementação omitida para brevidade, mas deve existir)
    return True

# --- Seção 1: Backup e Restauração Local (Expansível) ---
with st.expander("1. Backup e Restauração Local (Manual)"):
    # ... (código existente para backup e restauração local)

# --- Seção 2: Backup em Nuvem (Google Drive) ---
st.markdown("---")
st.header("Backup em Nuvem (Google Drive)")

try:
    authenticated_email = google_drive_service.get_authenticated_user_email()

    # UI para quando o usuário JÁ ESTÁ CONECTADO
    if authenticated_email:
        st.success(f"**Status:** Conectado ao Google Drive como `{authenticated_email}`")
        st.markdown("---")
        
        st.subheader("Opções de Backup")
        # Botão para backup manual
        if st.button("Fazer Backup para o Drive Agora", type="primary", use_container_width=True):
            with st.spinner("Enviando backup para o Google Drive..."):
                backup_manager.trigger_manual_backup()
        
        st.markdown("---")
        # Slider para configurar backup automático
        st.subheader("Backup Automático")
        current_threshold = backup_manager.load_backup_threshold()
        new_threshold = st.slider(
            f"Fazer backup a cada X novos clientes (atualmente: {current_threshold})",
            min_value=1, max_value=10, value=current_threshold
        )
        if new_threshold != current_threshold:
            backup_manager.save_backup_config(new_threshold)
            st.toast(f"Frequência de backup atualizada para cada {new_threshold} clientes.")
        
        st.markdown("---")
        # Botão para desconectar
        st.subheader("Gerenciar Conexão")
        if st.button("Desconectar / Trocar Conta", use_container_width=True):
            google_drive_service.disconnect_drive_account()
            st.rerun()

    # UI para quando o usuário NÃO ESTÁ CONECTADO
    else:
        st.warning("**Status:** Nenhuma conta Google Drive conectada.")
        st.markdown("---")

        # Passo 1: Upload do credentials.json
        st.subheader("Passo 1: Faça o upload do seu `credentials.json`")
        if 'processed_creds_file' not in st.session_state:
            st.session_state.processed_creds_file = None
        
        uploaded_creds = st.file_uploader("Selecione o arquivo de credenciais", type=['json'])
        if uploaded_creds and uploaded_creds.name != st.session_state.processed_creds_file:
            with open(google_drive_service.CREDENTIALS_FILE, "wb") as f:
                f.write(uploaded_creds.getbuffer())
            st.session_state.processed_creds_file = uploaded_creds.name
            if os.path.exists(google_drive_service.TOKEN_FILE):
                os.remove(google_drive_service.TOKEN_FILE)
            st.success(f"Arquivo `{uploaded_creds.name}` salvo! Prossiga para o Passo 2.")
            st.rerun()
        
        # Expander com as instruções
        with st.expander("Como conseguir o arquivo `credentials.json`?"):
            # ... (Instruções detalhadas)

        st.markdown("---")
        st.subheader("Passo 2: Conecte sua Conta Google")
        
        creds_exist = os.path.exists(google_drive_service.CREDENTIALS_FILE)
        if not creds_exist:
            st.caption("O botão de conexão será habilitado após o upload do `credentials.json` no Passo 1.")

        if st.button("Conectar ao Google Drive", type="primary", use_container_width=True, disabled=not creds_exist):
            st.session_state.show_auth_prompt = True

        if st.session_state.get("show_auth_prompt"):
            try:
                flow = google_drive_service.get_auth_flow()
                auth_url = flow.authorization_url(prompt='consent')[0]
                
                st.info("Siga os passos para autorizar o acesso:")
                st.markdown(f"1. **[Clique aqui para abrir a página de autorização do Google]({auth_url})**", unsafe_allow_html=True)
                st.write("2. Conceda as permissões e copie o código gerado.")
                st.warning("O código é de uso único e expira rapidamente.")

                auth_code = st.text_input("3. Cole o código aqui:")
                if st.button("Confirmar Código"):
                    if auth_code:
                        with st.spinner("Verificando código..."):
                            google_drive_service.fetch_token_from_code(flow, auth_code)
                        st.success("Autenticação concluída!")
                        st.info("Recarregando a página...")
                        del st.session_state.show_auth_prompt
                        st.rerun()
                    else:
                        st.warning("Por favor, insira o código.")
            except Exception as e:
                st.error(f"Erro no processo de autenticação: {e}")


except Exception as e:
    st.error(f"Ocorreu um erro geral na página de Backup: {e}")
    st.info("Verifique se o arquivo `credentials.json` está correto e na pasta do projeto.")
