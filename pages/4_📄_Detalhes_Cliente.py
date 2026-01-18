import streamlit as st
import database
import datetime
from streamlit_modal import Modal

st.set_page_config(page_title="Detalhes do Cliente", page_icon="📄", layout="centered")

# Helper function to display a field and a copy-able code block
def display_field_with_copy(label, value, is_date=False, is_text_area=False):
    """Exibe um campo (desabilitado) e um bloco de código para cópia."""
    
    # Converte data para string no formato brasileiro, se aplicável
    if is_date and isinstance(value, (datetime.date, datetime.datetime)):
        display_value = value.strftime("%d/%m/%Y")
    elif value is None:
        display_value = ""
    else:
        display_value = str(value)

    if is_text_area:
        st.text_area(label, value=display_value, disabled=True, height=150)
    else:
        st.text_input(label, value=display_value, disabled=True)
    
    if display_value:
        st.code(display_value, language=None)
    
    st.markdown("---")


# --- Lógica Principal ---

# 1. Obter o ID do cliente do estado da sessão
if "selected_customer_id" not in st.session_state:
    st.error("Nenhum cliente foi selecionado.")
    st.warning("Por favor, selecione um cliente na página do Banco de Dados.")
    if st.button("Voltar ao Banco de Dados"):
        st.switch_page("pages/2_📊_Banco_de_Dados.py")
    st.stop()

customer_id = st.session_state["selected_customer_id"]
try:
    customer_id = int(customer_id)
except (ValueError, TypeError):
    st.error("ID de cliente inválido na sessão.")
    if st.button("Voltar ao Banco de Dados"):
        st.switch_page("pages/2_📊_Banco_de_Dados.py")
    st.stop()

# 2. Buscar os dados do cliente
try:
    customer = database.get_customer_by_id(customer_id)
except database.DatabaseError as e:
    st.error(f"Erro ao buscar dados do cliente: {e}")
    st.stop()

if not customer:
    st.error(f"Cliente com ID {customer_id} não encontrado.")
    if st.button("Voltar ao Banco de Dados"):
        st.switch_page("pages/2_📊_Banco_de_Dados.py")
    st.stop()


# 3. Exibir os dados
st.title(f"📄 Detalhes de: {customer.get('nome_completo')}")
if st.button("⬅️ Voltar para a lista", use_container_width=True):
    st.switch_page("pages/2_📊_Banco_de_Dados.py")

# --- Exibição de Mensagens de Status ---
if 'db_status' in st.session_state:
    status = st.session_state.pop('db_status') 
    if status.get('success'):
        st.success(status['message'])
    else:
        st.error(status['message'])

st.markdown("---")


# Usando a estrutura da página de cadastro como referência
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

with st.expander("Contatos"):
    display_field_with_copy("Nome do Contato 1", customer.get('contato1'))
    
    col_tel1, col_cargo = st.columns(2)
    with col_tel1:
        display_field_with_copy('Telefone 1', customer.get('telefone1'))
    with col_cargo:
        display_field_with_copy("Cargo do Contato 1", customer.get('cargo'))
    
    st.markdown("---")

    col6, col7 = st.columns([2, 1])
    with col6:
        display_field_with_copy("Nome do Contato 2", customer.get('contato2'))
    with col7:
        display_field_with_copy('Telefone 2', customer.get('telefone2'))

with st.expander("Endereço"):
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

with st.expander("Observações"):
    display_field_with_copy("Observações", customer.get('observacao'), is_text_area=True)

with st.container(border=True):
    st.subheader("Informações do Sistema")
    display_field_with_copy("Data de Cadastro", customer.get("data_cadastro"), is_date=True)
    display_field_with_copy("ID do Cliente", customer.get("id"))

st.markdown("---")
with st.container(border=True):
    st.subheader("Excluir Cliente")
    st.warning("Esta ação é irreversível e removerá permanentemente o cliente do banco de dados.")

    delete_modal = Modal("Confirmar Exclusão", key="delete_customer_modal")
    
    if st.button("🗑️ Excluir Cliente", type="primary", use_container_width=True):
        delete_modal.open()

    if delete_modal.is_open():
        with delete_modal.container():
            st.warning(f"Tem certeza que deseja excluir o cliente '{customer.get('nome_completo')}' (ID: {customer_id})?")
            col1, col2 = st.columns(2)
            if col1.button("Confirmar Exclusão", type="primary"):
                try:
                    database.delete_customer_by_id(customer_id)
                    st.session_state.db_status = {"success": True, "message": f"Cliente '{customer.get('nome_completo')}' (ID: {customer_id}) excluído com sucesso!"}
                    delete_modal.close()
                    # Clear session state and go back to the database page
                    if "selected_customer_id" in st.session_state:
                        del st.session_state["selected_customer_id"]
                    st.switch_page("pages/2_📊_Banco_de_Dados.py")
                except database.DatabaseError as e:
                    st.session_state.db_status = {"success": False, "message": str(e)}
                    delete_modal.close()
                    st.rerun() # Rerun to show error message
            if col2.button("Cancelar"):
                delete_modal.close()
