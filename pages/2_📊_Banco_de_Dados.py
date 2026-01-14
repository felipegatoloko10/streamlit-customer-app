import streamlit as st
import pandas as pd
import database
from streamlit_modal import Modal
import math

# --- Constantes ---
EXPORT_LIMIT = 20000 # Limite para exportação completa de dados

st.set_page_config(
    page_title="Banco de Dados de Clientes",
    page_icon="📊",
    layout="wide" 
)

st.title("Banco de Dados de Clientes")

# ... (código do Modal, Status e process_changes mantido como antes)
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

def clear_full_export_state():
    """Limpa o estado da exportação completa quando os filtros mudam."""
    if 'full_export_data' in st.session_state:
        del st.session_state.full_export_data

# --- Barra Lateral (Filtros, Paginação e Ações) ---
st.sidebar.header("Filtros e Ações")
search_query = st.sidebar.text_input("Buscar por Nome ou CPF", on_change=clear_full_export_state)
conn = database.get_db_connection()
try:
    all_states = pd.read_sql_query("SELECT DISTINCT estado FROM customers WHERE estado IS NOT NULL AND estado != '' ORDER BY estado", conn)
    state_options = ["Todos"] + all_states['estado'].tolist()
    state_filter = st.sidebar.selectbox("Filtrar por Estado", options=state_options, on_change=clear_full_export_state)
except Exception as e:
    st.sidebar.error("Filtros indisponíveis.")
    st.stop()

# Paginação
page_size = st.sidebar.selectbox("Itens por página", options=[10, 25, 50, 100], index=0)
total_records = database.count_total_records(search_query, state_filter)
total_pages = math.ceil(total_records / page_size) if total_records > 0 else 1
page_number = st.sidebar.number_input('Página', min_value=1, max_value=total_pages, value=1, step=1)

st.sidebar.markdown("---")

# --- Lógica Principal e de Exportação ---
df_page = database.fetch_data(search_query=search_query, state_filter=state_filter, page=page_number, page_size=page_size)

if not df_page.empty:
    st.sidebar.download_button(
        label="Exportar página atual para CSV",
        data=database.df_to_csv(df_page),
        file_name=f'clientes_pagina_{page_number}.csv',
        mime='text/csv'
    )
    
    # Botão para exportar todos os resultados da busca
    if total_records > page_size:
        can_export_full = total_records <= EXPORT_LIMIT
        export_button_label = "Preparar Exportação Completa"
        
        if not can_export_full:
            st.sidebar.warning(f"A exportação completa é limitada a {EXPORT_LIMIT} registros. Por favor, refine seus filtros.")
            
        if st.sidebar.button(export_button_label, disabled=not can_export_full):
            with st.spinner(f"Buscando todos os {total_records} registros..."):
                df_full = database.fetch_data(search_query=search_query, state_filter=state_filter, page_size=total_records)
                st.session_state.full_export_data = database.df_to_csv(df_full)

        if 'full_export_data' in st.session_state:
             st.sidebar.download_button(
                label=f"Baixar {total_records} registros como CSV",
                data=st.session_state.full_export_data,
                file_name='clientes_completo.csv',
                mime='text/csv',
                on_click=lambda: st.session_state.pop('full_export_data') # Limpa o estado após o clique
            )
    else:
        st.sidebar.info("Não há dados para exportar.")
# ... (resto do código da Interface de Edição mantido como antes)
if not df_page.empty:
    df_for_editing = df_page.copy()
    df_for_editing.insert(0, 'Deletar', False)

    st.info("Marque 'Deletar' para remover um registro ou edite os campos. As alterações são salvas com o botão abaixo.")
    
    column_config = {
        "id": st.column_config.NumberColumn("ID", disabled=True),
        "Deletar": st.column_config.CheckboxColumn("Deletar?", default=False),
        "nome_completo": "Nome Completo",
        "tipo_documento": "Tipo",
        "cpf": st.column_config.TextColumn("CPF", disabled=True),
        "cnpj": st.column_config.TextColumn("CNPJ", disabled=True),
        "contato1": "Contato 1",
        "telefone1": "Telefone 1",
        "contato2": "Contato 2",
        "telefone2": "Telefone 2",
        "cargo": "Cargo",
        "email": "E-mail",
        "data_nascimento": st.column_config.DateColumn("Nascimento/Fundação", format="DD/MM/YYYY"),
        "observacao": st.column_config.TextColumn("Observação", width="large"),
        "data_cadastro": st.column_config.DateColumn("Data de Cadastro", format="DD/MM/YYYY", disabled=True),
    }
    
    # Define a ordem desejada das colunas
    column_order = [
        'Deletar', 'id', 'nome_completo', 'tipo_documento', 'cpf', 'cnpj',
        'contato1', 'telefone1', 'contato2', 'telefone2', 'cargo', 'email', 
        'data_nascimento', 'cidade', 'estado', 'observacao'
    ]

    edited_df = st.data_editor(
        df_for_editing,
        key="data_editor",
        width='stretch',
        hide_index=True,
        column_order=column_order,
        column_config=column_config
    )
    
    st.markdown(f"Mostrando **{len(df_page)}** de **{total_records}** registros. Página **{page_number}** de **{total_pages}**.")

    if st.button("Salvar Alterações", width='stretch', disabled=df_page.empty):
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