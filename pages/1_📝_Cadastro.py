import streamlit as st
import datetime
import database
import validators
import requests
import re

st.set_page_config(page_title="Cadastro de Clientes", page_icon="📝", layout="centered")

# --- Funções ---

def fetch_address_data(cep):
    cep_cleaned = re.sub(r'[^0-9]', '', cep)
    if len(cep_cleaned) != 8:
        st.session_state.cep_notification = {"type": "error", "message": "CEP inválido. Deve conter 8 dígitos."}
        return
    try:
        with st.spinner("Buscando CEP..."):
            response = requests.get(f"https://viacep.com.br/ws/{cep_cleaned}/json/", timeout=5)
            response.raise_for_status()
            data = response.json()
        if data.get("erro"):
            st.session_state.cep_notification = {"type": "warning", "message": "CEP não encontrado. Por favor, preencha o endereço manualmente."}
        else:
            st.session_state.cep_notification = {"type": "success", "message": "Endereço encontrado!"}
            st.session_state.form_endereco = data.get("logradouro", "")
            st.session_state.form_bairro = data.get("bairro", "")
            st.session_state.form_cidade = data.get("localidade", "")
            st.session_state.form_estado = data.get("uf", "")
            # BUG: This JavaScript injection is brittle and relies on Streamlit's internal HTML structure (aria-label).
            # It might break in future Streamlit updates if the DOM structure changes.
            st.components.v1.html("<script>document.querySelector(\"input[aria-label='Número']\").focus();</script>", height=0)
    except requests.exceptions.RequestException as e:
        st.session_state.cep_notification = {"type": "error", "message": f"Erro de rede ao buscar o CEP: {e}"}

def clear_form_inputs():
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith("form_") or k == "cep_input"]
    for key in keys_to_clear:
        if "data_nascimento" in key:
            st.session_state[key] = None
        elif "tipo_documento" in key:
            st.session_state[key] = "CPF"
        else:
            st.session_state[key] = ""

# --- Lógica de Estado ---
# Exibe notificações da busca de CEP
if 'cep_notification' in st.session_state:
    notification = st.session_state.pop('cep_notification')
    msg_type = notification['type']
    message = notification['message']
    if msg_type == "success":
        st.success(message)
    elif msg_type == "warning":
        st.warning(message)
    elif msg_type == "error":
        st.error(message)

# Exibe erros do formulário principal
if st.session_state.get("form_error"):
    st.error(st.session_state.pop("form_error"))

# Exibe sucesso do formulário principal e limpa
if st.session_state.get("form_submitted_successfully", False):
    st.session_state.form_submitted_successfully = False
    clear_form_inputs()
    st.balloons()
    st.success("Cliente salvo com sucesso!")

# --- Interface ---
st.title('📝 Cadastro de Clientes')

with st.container(border=True):
    st.subheader("Busca de Endereço por CEP")
    col1, col2 = st.columns([1, 2])
    with col1:
        cep_input = st.text_input("CEP", max_chars=9, key="cep_input")
    with col2:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("Buscar Endereço"):
            fetch_address_data(cep_input)
            st.rerun()

st.markdown("---")

with st.form(key="new_customer_form", clear_on_submit=False):
    with st.expander("Dados Principais", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            nome = st.text_input('Nome Completo / Razão Social *', key="form_nome")
        with col2:
            tipo_documento = st.radio("Tipo de Documento", ["CPF", "CNPJ"], horizontal=True, key="form_tipo_documento")

        label_documento = "CPF *" if tipo_documento == "CPF" else "CNPJ *"
        documento = st.text_input(label_documento, key="form_documento")

        col_email, col_data = st.columns(2)
        with col_email:
            email = st.text_input('E-mail', key="form_email")
        with col_data:
            data_nascimento = st.date_input('Data de Nascimento / Fundação', value=None, min_value=datetime.date(1900, 1, 1), key="form_data_nascimento")

    with st.expander("Contatos"):
        col3, col4, col5 = st.columns(3)
        with col3:
            contato1 = st.text_input("Nome do Contato 1", key="form_contato1")
        with col4:
            telefone1 = st.text_input('Telefone 1', key="form_telefone1")
        with col5:
            cargo = st.text_input("Cargo do Contato 1", key="form_cargo")
        
        st.markdown("---")

        col6, col7 = st.columns([2, 1])
        with col6:
            contato2 = st.text_input("Nome do Contato 2", key="form_contato2")
        with col7:
            telefone2 = st.text_input('Telefone 2', key="form_telefone2")

    with st.expander("Endereço"):
        col_end, col_num = st.columns([3, 1])
        with col_end:
            endereco = st.text_input('Endereço', key="form_endereco")
        with col_num:
            numero = st.text_input('Número', key="form_numero")

        col_bairro, col_comp = st.columns(2)
        with col_bairro:
            bairro = st.text_input('Bairro', key="form_bairro")
        with col_comp:
            complemento = st.text_input('Complemento', key="form_complemento")

        col_cidade, col_estado = st.columns([3, 1])
        with col_cidade:
            cidade = st.text_input('Cidade', key="form_cidade")
        with col_estado:
            estado = st.text_input('UF', max_chars=2, key="form_estado")
    
    with st.expander("Observações"):
        observacao = st.text_area("Observações", "", height=150, max_chars=1000, key="form_observacao")

    st.markdown("---")
    submit_button = st.form_submit_button('Salvar Cliente', type="primary", use_container_width=True)

if submit_button:
    cpf_valor, cnpj_valor = (validators.format_cpf(documento), None) if tipo_documento == "CPF" else (None, validators.format_cnpj(documento))
    
    customer_data = {
        'nome_completo': nome, 'tipo_documento': tipo_documento, 'cpf': cpf_valor, 'cnpj': cnpj_valor,
        'contato1': contato1, 'telefone1': validators.format_whatsapp(telefone1), 
        'contato2': contato2, 'telefone2': validators.format_whatsapp(telefone2), 'cargo': cargo,
        'email': email, 'data_nascimento': data_nascimento, 
        'cep': cep_input, 'endereco': endereco, 'numero': numero,
        'complemento': complemento, 'bairro': bairro, 'cidade': cidade, 'estado': estado, 
        'observacao': observacao,
    }
    
    try:
        database.insert_customer(customer_data)
        st.session_state.form_submitted_successfully = True
        st.rerun()
    except (validators.ValidationError, database.DatabaseError, database.DuplicateEntryError) as e:
        st.session_state.form_error = f"Erro ao salvar: {e}"
        st.rerun()
    except Exception as e:
        st.session_state.form_error = f"Ocorreu um erro inesperado: {e}"
        st.rerun()