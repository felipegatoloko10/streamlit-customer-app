import streamlit as st
import os
import shutil
import datetime

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
    
    **Esta ação não pode ser desfeita.**
    """)
    
    if st.button("Confirmar e Restaurar Backup", type="primary"):
        try:
            # Salva o arquivo enviado temporariamente para um caminho seguro
            temp_restore_path = f"temp_restore_{uploaded_file.name}"
            with open(temp_restore_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Substitui o banco de dados atual pelo arquivo de backup
            shutil.move(temp_restore_path, DB_FILE)
            
            st.success("Banco de dados restaurado com sucesso! O aplicativo será reiniciado para aplicar as alterações.")
            
            # Limpa o cache de recursos do Streamlit para forçar a releitura da conexão com o banco de dados
            st.cache_resource.clear()
            
            # Força um rerun para refletir o estado pós-restauração
            st.rerun()

        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao restaurar o backup: {e}")
            # Se o arquivo temporário ainda existir em caso de erro, remove
            if os.path.exists(temp_restore_path):
                os.remove(temp_restore_path)