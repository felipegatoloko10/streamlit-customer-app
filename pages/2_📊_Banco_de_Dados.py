import streamlit as st
import pandas as pd
import database
import datetime # Adicionado para formatação de data
from streamlit_modal import Modal
import math
import logging # Adicionar esta linha

# --- Constantes ---
EXPORT_LIMIT = 20000 # Limite para exportação completa de dados

st.set_page_config(
    page_title="Banco de Dados de Clientes",
    page_icon="📊"
)

st.title("📊 Banco de Dados de Clientes")

# --- Exibição de Mensagens de Status (transferida da página de detalhes) ---
if 'db_status' in st.session_state:
    status = st.session_state.pop('db_status') 
    if status.get('success'):
        st.success(status['message'])
    else:
        st.error(status['message'])

# Helper function to display a field and a copy-able code block (transferida da página de detalhes)
def display_field_with_copy(label, value, is_date=False, is_text_area=False):
    """Exibe o label e um bloco de código para copiar a informação."""
    
    # Converte data para string no formato brasileiro, se aplicável
    if is_date and isinstance(value, (datetime.date, datetime.datetime)):
        display_value = value.strftime("%d/%m/%Y")
    elif value is None:
        display_value = ""
    else:
        display_value = str(value)

    st.text(label) # Display the label explicitly
    
    if display_value:
        st.code(display_value, language=None)
    
    # st.markdown("---") # Removido para reduzir espaçamento

def clear_full_export_state():
    """Limpa o estado da exportação completa quando os filtros mudam."""
    if 'full_export_data' in st.session_state:
        del st.session_state.full_full_export_data

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

# Verifica se um cliente foi selecionado para exibir os detalhes
if "selected_customer_id" in st.session_state and st.session_state.selected_customer_id:
    customer_id = st.session_state.selected_customer_id
    try:
        customer = database.get_customer_by_id(customer_id)
    except database.DatabaseError as e:
        st.error(f"Erro ao buscar dados do cliente: {e}")
        customer = None # Garante que não tentaremos exibir dados de um cliente que falhou

    if customer:
        st.subheader(f"Detalhes de: {customer.get('nome_completo')}")
        if st.button("⬅️ Fechar Detalhes", use_container_width=True):
            del st.session_state.selected_customer_id
            st.rerun()
        st.markdown("---")

        # Layout dos detalhes (replicando o da página de cadastro)
        with st.container(border=True):
            st.subheader("Dados Principais")
            
            tipo_doc = customer.get('tipo_documento')
            label_doc = "CPF" if tipo_doc == "CPF" else "CNPJ"
            valor_doc = customer.get('cpf') or customer.get('cnpj')

            display_field_with_copy('Nome Completo / Razão Social', customer.get('nome_completo'))
            display_field_with_copy(label_doc, valor_doc)

            col_email, col_data = st.columns(2)
            with col_email:
                display_field_with_copy('E-mail', customer.get('email'))
            with col_data:
                display_field_with_copy('Data de Nascimento / Fundação', customer.get('data_nascimento'), is_date=True)

        with st.expander("Contatos", expanded=True): # Alterado para expanded=True
            display_field_with_copy("Nome do Contato 1", customer.get('contato1'))
            
            col_tel1, col_cargo = st.columns(2)
            with col_tel1:
                display_field_with_copy('Telefone 1', customer.get('telefone1'))
            with col_cargo:
                display_field_with_copy("Cargo do Contato 1", customer.get('cargo'))
            
            # st.markdown("---") # Removido para reduzir espaçamento

            col6, col7 = st.columns([2, 1])
            with col6:
                display_field_with_copy("Nome do Contato 2", customer.get('contato2'))
            with col7:
                display_field_with_copy('Telefone 2', customer.get('telefone2'))

        with st.expander("Endereço", expanded=True): # Alterado para expanded=True
            display_field_with_copy("CEP", customer.get("cep"))
            
            col_end, col_num = st.columns([3, 1])
            with col_end:
                display_field_with_copy('Endereço', customer.get('endereco'))
            with col_num:
                display_field_with_copy('Número', customer.get('numero'))

            col_bairro, col_comp = st.columns(2)
            with col_bairro:
                display_field_with_copy('Bairro', customer.get('bairro'))
            with col_comp:
                display_field_with_copy('Complemento', customer.get('complemento'))

            col_cidade, col_estado = st.columns([3, 1])
            with col_cidade:
                display_field_with_copy('Cidade', customer.get('cidade'))
            with col_estado:
                display_field_with_copy('UF', customer.get('estado'))

        with st.expander("Observações", expanded=True): # Alterado para expanded=True
            display_field_with_copy("Observações", customer.get('observacao'), is_text_area=True)

        with st.container(border=True):
            st.subheader("Informações do Sistema")
            display_field_with_copy("Data de Cadastro", customer.get("data_cadastro"), is_date=True)
            display_field_with_copy("ID do Cliente", customer.get("id"))
        

    else: # Cliente não encontrado
        st.error(f"Cliente com ID {customer_id} não encontrado.")
        if st.button("⬅️ Fechar Detalhes e Voltar", use_container_width=True):
            del st.session_state.selected_customer_id
            st.rerun()

else: # Nenhum cliente selecionado, exibe a tabela
    if not df_page.empty:
        st.info("Selecione um cliente na tabela para ver seus detalhes completos.")

        # Configuração das colunas para a nova visualização
        column_config = {
            "id": st.column_config.NumberColumn("ID"),
            "nome_completo": "Nome Completo",
            "tipo_documento": "Tipo",
            "cpf": "CPF",
            "cnpj": "CNPJ",
            "telefone1": "Telefone 1",
            "link_wpp_1": st.column_config.LinkColumn("WhatsApp 1", display_text="🔗 Abrir"),
            "cidade": "Cidade",
            "estado": "Estado",
        }
        
        # Define a ordem e quais colunas serão visíveis na grade principal
        visible_columns = [
            'id', 'nome_completo', 'tipo_documento', 'cpf', 'cnpj', 
            'telefone1', 'link_wpp_1', 'cidade', 'estado'
        ]

        # Garante que apenas colunas existentes no dataframe são usadas
        columns_to_display = [col for col in visible_columns if col in df_page.columns]

        st.dataframe(
            df_page[columns_to_display],
            key="customer_grid",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
            column_order=columns_to_display,
            column_config=column_config,
            use_container_width=True
        )
        
        st.markdown(f"Mostrando **{len(df_page)}** de **{total_records}** registros. Página **{page_number}** de **{total_pages}**.")

        # Lógica de seleção
        grid_state = st.session_state.get("customer_grid")
        if grid_state and grid_state['selection']['rows']:
            selected_row_index = grid_state['selection']['rows'][0]
            selected_customer_id = int(df_page.iloc[selected_row_index]['id'])
            
            # Salva o ID no estado da sessão e muda de página
            st.session_state.selected_customer_id = selected_customer_id
            grid_state['selection']['rows'] = [] # Limpa a seleção
            st.rerun() # Rerun para exibir os detalhes na mesma página

    else:
        st.info("Nenhum cliente cadastrado corresponde aos filtros aplicados.")
        if st.button("➕ Cadastrar Novo Cliente"):
            st.switch_page("pages/1_📝_Cadastro.py")