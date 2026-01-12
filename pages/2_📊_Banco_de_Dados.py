import streamlit as st
import pandas as pd
import database

st.set_page_config(
    page_title="Banco de Dados de Clientes",
    page_icon="📊",
)

st.title("Banco de Dados de Clientes")

# --- Exibição de Mensagens de Status ---
# Exibe a mensagem de sucesso/erro da última operação, se houver.
if 'db_status' in st.session_state:
    status = st.session_state.db_status
    if status.get('success'):
        st.success(status['message'])
    else:
        st.error(status['message'])
    # Limpa o status para não exibir novamente.
    del st.session_state.db_status

# --- Conexão e Lógica Principal ---
conn = database.get_db_connection()

# --- Barra Lateral com Filtros e Ações ---
st.sidebar.header("Filtros e Ações")
search_query = st.sidebar.text_input("Buscar por Nome ou CPF")
all_states = pd.read_sql_query("SELECT DISTINCT estado FROM customers WHERE estado IS NOT NULL AND estado != '' ORDER BY estado", conn)
state_options = ["Todos"] + all_states['estado'].tolist()
state_filter = st.sidebar.selectbox("Filtrar por Estado", options=state_options)

original_df = database.fetch_data(conn, search_query=search_query, state_filter=state_filter)

if not original_df.empty:
    csv = database.df_to_csv(original_df)
    st.sidebar.download_button(
        label="Exportar para CSV",
        data=csv,
        file_name='clientes.csv',
        mime='text/csv',
    )
else:
    st.sidebar.info("Não há dados para exportar.")

# --- Exibição e Edição dos Dados ---
if not original_df.empty:
    df_for_editing = original_df.copy()
    df_for_editing.insert(0, 'Deletar', False)

    st.info("Marque a caixa 'Deletar' para remover um registro ou edite os campos diretamente. Clique em 'Salvar Alterações' para aplicar.")

    column_config = {
        "id": st.column_config.NumberColumn("ID", disabled=True),
        "Deletar": st.column_config.CheckboxColumn("Deletar?", default=False),
        "nome_completo": "Nome Completo",
        "cpf": st.column_config.TextColumn("CPF", disabled=True),
        "whatsapp": "WhatsApp",
        "email": "E-mail",
        "data_nascimento": st.column_config.DateColumn("Data de Nascimento", format="DD/MM/YYYY"),
        "cep": "CEP",
        "endereco": "Endereço",
        "numero": "Número",
        "complemento": "Complemento",
        "bairro": "Bairro",
        "cidade": "Cidade",
        "estado": "UF"
    }
    column_order = ['Deletar', 'id', 'nome_completo', 'cpf', 'whatsapp', 'email', 'data_nascimento', 'cep', 'endereco', 'numero', 'bairro', 'cidade', 'estado', 'complemento']

    edited_df = st.data_editor(
        df_for_editing,
        key="data_editor",
        num_rows="dynamic",
        hide_index=True,
        column_order=column_order,
        column_config=column_config
    )

    if st.button("Salvar Alterações"):
        results, error = database.commit_changes(edited_df, original_df, conn)
        
        if error:
            st.session_state.db_status = {"success": False, "message": error}
        else:
            updated = results.get("updated", 0)
            deleted = results.get("deleted", 0)
            if updated > 0 or deleted > 0:
                parts = []
                if updated > 0:
                    parts.append(f"{updated} registro(s) atualizado(s)")
                if deleted > 0:
                    parts.append(f"{deleted} registro(s) deletado(s)")
                message = " e ".join(parts) + " com sucesso!"
                st.session_state.db_status = {"success": True, "message": message}
            else:
                st.session_state.db_status = {"success": True, "message": "Nenhuma alteração foi detectada."}
        
        st.rerun()

else:
    st.info("Nenhum cliente cadastrado corresponde aos filtros aplicados.")

conn.close()