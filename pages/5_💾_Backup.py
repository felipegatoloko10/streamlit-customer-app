import streamlit as st
import os
import shutil
import datetime
from streamlit_modal import Modal

st.set_page_config(
    page_title="Backup e Restauração",
    page_icon="💾"
)

st.title("💾 Backup e Restauração de Dados")

st.info("Esta seção permite que você salve (backup) e recupere (restaure) o banco de dados de clientes.")

DB_FILE = 'customers.db'

# --- Seção de Backup ---
st.header("1. Criar e Baixar um Backup")
st.write(f"Clique no botão abaixo para baixar uma cópia de segurança do seu banco de dados atual (`{DB_FILE}`).")

try:
    with open(DB_FILE, "rb") as fp:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"backup_{DB_FILE}_{timestamp}.db"
        
        st.download_button(
            label="Clique para Baixar o Backup",
            data=fp,
            file_name=backup_filename,
            mime="application/octet-stream",
            width='stretch'
        )
except FileNotFoundError:
    st.error(f"O arquivo do banco de dados (`{DB_FILE}`) não foi encontrado. Cadastre pelo menos um cliente para criar o banco de dados e poder fazer o backup.")
except Exception as e:
    st.error(f"Ocorreu um erro inesperado ao preparar o backup para download: {e}")


st.markdown("---")

# --- Seção de Restauração ---
st.header("2. Restaurar a partir de um Backup")
st.write(f"Selecione um arquivo de backup (.db) para restaurar a base de dados. **Atenção: esta ação substituirá todos os dados atuais!**")

uploaded_file = st.file_uploader("Escolha um arquivo de backup (.db)", type=['db'])

if uploaded_file is not None:
    st.warning(f"""
    **Você está prestes a substituir o banco de dados atual pelos dados do arquivo '{uploaded_file.name}'.**
    
    Todos os clientes cadastrados desde a criação deste backup serão perdidos. 
    
    Esta ação criará um backup de segurança do estado atual antes de restaurar, mas prossiga com cautela.
    """)

    restore_modal = Modal(
        "Confirmar Restauração",
        key="restore_modal",
        padding=20,
        max_width=500
    )

    if st.button("Iniciar Processo de Restauração", type="primary"):
        restore_modal.open()

    if restore_modal.is_open():
        with restore_modal.container():
            st.write("### Confirmação Final")
            st.write(f"Tem certeza de que deseja substituir o banco de dados atual pelo arquivo **{uploaded_file.name}**?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Sim, Restaurar Agora", type="primary"):
                    try:
                        # 1. Criar um backup de segurança do banco de dados atual, se ele existir
                        if os.path.exists(DB_FILE):
                            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                            pre_restore_backup_filename = f"pre-restore-backup_{timestamp}.db"
                            shutil.copy(DB_FILE, pre_restore_backup_filename)
                            st.info(f"Backup de segurança criado: `{pre_restore_backup_filename}`")

                        # 2. Salvar o arquivo enviado temporariamente
                        temp_restore_path = f"temp_restore_{uploaded_file.name}"
                        with open(temp_restore_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # 3. Substituir o banco de dados atual pelo arquivo de backup
                        shutil.move(temp_restore_path, DB_FILE)
                        
                        st.success("Banco de dados restaurado com sucesso! O aplicativo será reiniciado.")
                        
                        # 4. Limpar caches para forçar a releitura do novo BD
                        st.cache_resource.clear()
                        st.cache_data.clear()
                        
                        restore_modal.close()
                        st.rerun()

                    except Exception as e:
                        st.error(f"Ocorreu um erro inesperado durante a restauração: {e}")
                        if 'temp_restore_path' in locals() and os.path.exists(temp_restore_path):
                            os.remove(temp_restore_path)
                        restore_modal.close()

            with col2:
                if st.button("Cancelar"):
                    restore_modal.close()