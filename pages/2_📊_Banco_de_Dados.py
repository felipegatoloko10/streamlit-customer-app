import streamlit as st
import pandas as pd
import database
from streamlit_modal import Modal
import math

st.set_page_config(
    page_title="Banco de Dados de Clientes",
    page_icon="📊",
    layout="wide" 
)

st.title("Banco de Dados de Clientes")

# --- Modal de Confirmação ---
delete_modal = Modal("Confirmar Exclusão", key="delete_modal")

# --- Exibição de Mensagens de Status ---
if 'db_status' in st.session_state:
    status = st.session_state.pop('db_status') 
    if status.get('success'):
        st.success(status['message'])
    else:
        st.error(status['message'])

# --- Funções de Lógica ---
def process_changes(df_edited, df_original):
    """Processa e comita as alterações no banco de dados."""
    try:
        results = database.commit_changes(df_edited, df_original)
        updated = results.get("updated", 0)
        deleted = results.get("deleted", 0)
        
        message_parts = []
        if updated > 0:
            message_parts.append(f"{updated} registro(s) atualizado(s)")
        if deleted > 0:
            message_parts.append(f"{deleted} registro(s) deletado(s)")
        
        if message_parts:
            message = " e ".join(message_parts) + " com sucesso!"
            st.session_state.db_status = {"success": True, "message": message}
        else:
            st.session_state.db_status = {"success": True, "message": "Nenhuma alteração foi detectada."}

    except database.DatabaseError as e:
        st.session_state.db_status = {"success": False, "message": str(e)}
    except Exception as e:
        st.session_state.db_status = {"success": False, "message": f"Ocorreu um erro inesperado: {e}"}

# --- Barra Lateral (Filtros e Paginação) ---
st.sidebar.header("Filtros e Ações")
search_query = st.sidebar.text_input("Buscar por Nome ou CPF")
conn = database.get_db_connection()
try:
    all_states = pd.read_sql_query("SELECT DISTINCT estado FROM customers WHERE estado IS NOT NULL AND estado != '' ORDER BY estado", conn)
    state_options = ["Todos"] + all_states['estado'].tolist()
    state_filter = st.sidebar.selectbox("Filtrar por Estado", options=state_options)
except Exception as e:
    st.sidebar.error("Filtros indisponíveis.")
    st.stop()

# Controles de Paginação
st.sidebar.markdown("---")
st.sidebar.header("Paginação")
page_size = st.sidebar.selectbox("Itens por página", options=[10, 25, 50, 100], index=0)

try:
    total_records = database.count_total_records(search_query, state_filter)
    total_pages = math.ceil(total_records / page_size) if total_records > 0 else 1
except database.DatabaseError as e:
    st.error(f"Não foi possível carregar os dados: {e}")
    st.stop()

page_number = st.sidebar.number_input('Página', min_value=1, max_value=total_pages, value=1, step=1)

# --- Lógica Principal ---
df_page = database.fetch_data(search_query=search_query, state_filter=state_filter, page=page_number, page_size=page_size)

if not df_page.empty:
    csv = database.df_to_csv(df_page)
    st.sidebar.download_button(label="Exportar página para CSV", data=csv, file_name='clientes_pagina.csv', mime='text/csv')
else:
    st.sidebar.info("Não há dados para exportar.")

# --- Interface de Edição ---
if not df_page.empty:
    df_for_editing = df_page.copy()
    df_for_editing.insert(0, 'Deletar', False)

    st.info("Marque 'Deletar' para remover um registro ou edite os campos. As alterações são salvas com o botão abaixo.")
    
    edited_df = st.data_editor(df_for_editing, key="data_editor", use_container_width=True, hide_index=True, column_config={
        "id": st.column_config.NumberColumn("ID", disabled=True),
        # ... (outras configurações de coluna)
    })
    
    st.markdown(f"Mostrando **{len(df_page)}** de **{total_records}** registros. Página **{page_number}** de **{total_pages}**.")

    if st.button("Salvar Alterações", use_container_width=True, disabled=df_page.empty):
        deletes = edited_df[edited_df['Deletar'] == True]
        if not deletes.empty:
            delete_modal.open()
        else:
            process_changes(edited_df, df_page.copy())
            st.rerun()
            
    if delete_modal.is_open():
        with delete_modal.container():
            st.warning(f"Confirmar a exclusão de {len(edited_df[edited_df['Deletar'] == True])} registro(s)?")
            col1, col2 = st.columns(2)
            if col1.button("Confirmar", type="primary"):
                process_changes(edited_df, df_page.copy())
                delete_modal.close()
                st.rerun()
            if col2.button("Cancelar"):
                delete_modal.close()
else:
    st.info("Nenhum cliente cadastrado corresponde aos filtros aplicados.")