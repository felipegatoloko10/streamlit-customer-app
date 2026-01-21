import streamlit as st
import datetime
import database
import validators
import requests
import re
import base64
import os

st.set_page_config(page_title="Cadastro de Clientes", page_icon="📝", layout="centered")

# --- Default Form Data ---
DEFAULT_FORM_DATA = {
    "nome_completo": "", "tipo_documento": "CPF", "documento": "",
    "email": "", "data_nascimento": None, "contato1": "", "telefone1": "",
    "cargo": "", "contato2": "", "telefone2": "", "cep": "",
    "endereco": "", "numero": "", "complemento": "", "bairro": "",
    "cidade": "", "estado": "", "observacao": "", "use_client_name": False
}

# --- Funções Utilitárias Locais ---
@st.cache_data
def load_whatsapp_icon_b64():
    """Lê a imagem do ícone do WhatsApp e a converte para base64, com cache."""
    image_path = os.path.join(os.path.dirname(__file__), '..', 'whatsapp.png')
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        st.warning("Arquivo 'whatsapp.png' não encontrado. O ícone do WhatsApp não será exibido.")
        return None

import services

def clear_form_inputs():
    """Reseta o estado do formulário para os valores padrão."""
    st.session_state.form_data = DEFAULT_FORM_DATA.copy()
    # Limpa CEP input separado
    st.session_state.cep_input = ""
    # Clear any pending messages
    if 'cep_notification' in st.session_state:
        del st.session_state.cep_notification

def update_contato1_from_nome():
    """Callback para o checkbox 'Usar nome do cliente como Contato 1'."""
    if st.session_state.form_data['use_client_name']:
        st.session_state.form_data['contato1'] = st.session_state.form_data['nome_completo']
    else:
        st.session_state.form_data['contato1'] = ""

# --- Carrega o ícone do WhatsApp ---
WHATSAPP_ICON = load_whatsapp_icon_b64()

# --- Initialize Form Data in Session State ---
if 'form_data' not in st.session_state:
    st.session_state.form_data = DEFAULT_FORM_DATA.copy()
if 'cep_input' not in st.session_state:
    st.session_state.cep_input = ""

# --- Lógica para atualizar o CEP vindo da busca de CNPJ ---
# Esta parte agora deve atualizar diretamente st.session_state.form_data['cep']
if "cep_from_cnpj" in st.session_state:
    st.session_state.form_data['cep'] = st.session_state.pop("cep_from_cnpj")

# --- Lógica de Estado (apenas notificações de CEP) ---
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

# --- Interface ---
st.title('📝 Cadastro de Clientes')

with st.container(border=True):
    st.subheader("Busca de Endereço por CEP")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.session_state.cep_input = st.text_input("CEP", max_chars=9, key="cep_input_widget", value=st.session_state.cep_input)
    with col2:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("Buscar Endereço"):
            # Update form_data with services result
            services.fetch_address_data(st.session_state.cep_input, st.session_state.form_data)
            st.rerun()


st.markdown("---")

with st.container(border=True):
    st.subheader("Dados Principais")
    col_tipo_doc, col_radio = st.columns([0.7, 0.3])
    with col_radio:
        st.session_state.form_data['tipo_documento'] = st.radio(
            "Tipo de Documento", 
            ["CPF", "CNPJ"], 
            horizontal=True, 
            key="tipo_documento",
            label_visibility="collapsed",
            index=["CPF", "CNPJ"].index(st.session_state.form_data['tipo_documento'])
        )

    st.session_state.form_data['nome_completo'] = st.text_input(
        'Nome Completo / Razão Social *', 
        key="nome_completo", 
        value=st.session_state.form_data['nome_completo']
    )

    label_documento = "CPF *" if st.session_state.form_data['tipo_documento'] == "CPF" else "CNPJ *"
    st.session_state.form_data['documento'] = st.text_input(
        label_documento, 
        key="documento", 
        value=st.session_state.form_data['documento']
    )

    if st.session_state.form_data['tipo_documento'] == "CNPJ":
        with st.container():
            col_cnpj_input, col_cnpj_btn = st.columns([0.7, 0.3])
            with col_cnpj_input:
                cnpj_to_search = st.text_input(
                    "CNPJ para busca", 
                    key="cnpj_search_input", 
                    label_visibility="collapsed", 
                    placeholder="Digite o CNPJ para buscar dados", 
                    value=st.session_state.form_data['documento']
                )
            with col_cnpj_btn:
                if st.button("🔎 Buscar CNPJ", use_container_width=True):
                    st.session_state.form_data['documento'] = cnpj_to_search
                    services.fetch_cnpj_data(cnpj_to_search, st.session_state.form_data)
                    st.rerun()
        st.markdown("---")

    with st.form(key="new_customer_form", clear_on_submit=False):
        col_email, col_data = st.columns(2)
        with col_email:
            st.session_state.form_data['email'] = st.text_input(
                'E-mail', 
                key="email", 
                value=st.session_state.form_data['email']
            )
        with col_data:
            st.session_state.form_data['data_nascimento'] = st.date_input(
                'Data de Nascimento / Fundação', 
                value=st.session_state.form_data['data_nascimento'], 
                min_value=datetime.date(1900, 1, 1), 
                key="data_nascimento"
            )

        with st.expander("Contatos"):
            st.session_state.form_data['use_client_name'] = st.checkbox(
                "Usar nome do cliente como Contato 1", 
                key="use_client_name", 
                value=st.session_state.form_data['use_client_name'],
                on_change=update_contato1_from_nome
            )
            
            st.session_state.form_data['contato1'] = st.text_input(
                "Nome do Contato 1", 
                value=st.session_state.form_data['contato1'], 
                key="contato1",
                disabled=st.session_state.form_data['use_client_name']
            )

            col_tel1, col_icon1, col_cargo = st.columns([0.45, 0.1, 0.45])
            with col_tel1:
                st.session_state.form_data['telefone1'] = st.text_input(
                    'Telefone 1', 
                    key="telefone1", 
                    value=st.session_state.form_data['telefone1']
                )
            with col_icon1:
                if WHATSAPP_ICON:
                    whatsapp_link_1 = validators.get_whatsapp_url(validators.unformat_whatsapp(st.session_state.form_data['telefone1']))
                    st.markdown(f'<div style="padding-top: 28px;"><a href="{whatsapp_link_1}" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a></div>', unsafe_allow_html=True)
            with col_cargo:
                st.session_state.form_data['cargo'] = st.text_input(
                    "Cargo do Contato 1", 
                    key="cargo", 
                    value=st.session_state.form_data['cargo']
                )

            st.markdown("---")
            st.session_state.form_data['contato2'] = st.text_input(
                "Nome do Contato 2", 
                key="contato2", 
                value=st.session_state.form_data['contato2']
            )
            
            col_tel2, col_icon2 = st.columns([0.9, 0.1])
            with col_tel2:
                st.session_state.form_data['telefone2'] = st.text_input(
                    'Telefone 2', 
                    key="telefone2", 
                    value=st.session_state.form_data['telefone2']
                )
            with col_icon2:
                 if WHATSAPP_ICON:
                    whatsapp_link_2 = validators.get_whatsapp_url(validators.unformat_whatsapp(st.session_state.form_data['telefone2']))
                    st.markdown(f'<div style="padding-top: 28px;"><a href="{whatsapp_link_2}" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a></div>', unsafe_allow_html=True)

        # Removed JavaScript Injection, as we are now using pythonic way for links

        with st.expander("Endereço"):
            st.session_state.form_data['cep'] = st.text_input(
                'CEP', 
                key="cep", 
                value=st.session_state.form_data['cep']
            )
            col_end, col_num = st.columns([3, 1])
            with col_end:
                st.session_state.form_data['endereco'] = st.text_input(
                    'Endereço', 
                    key="endereco", 
                    value=st.session_state.form_data['endereco']
                )
            with col_num:
                st.session_state.form_data['numero'] = st.text_input(
                    'Número', 
                    key="numero", 
                    value=st.session_state.form_data['numero']
                )

            col_bairro, col_comp = st.columns(2)
            with col_bairro:
                st.session_state.form_data['bairro'] = st.text_input(
                    'Bairro', 
                    key="bairro", 
                    value=st.session_state.form_data['bairro']
                )
            with col_comp:
                st.session_state.form_data['complemento'] = st.text_input(
                    'Complemento', 
                    key="complemento", 
                    value=st.session_state.form_data['complemento']
                )

            col_cidade, col_estado = st.columns([3, 1])
            with col_cidade:
                st.session_state.form_data['cidade'] = st.text_input(
                    'Cidade', 
                    key="cidade", 
                    value=st.session_state.form_data['cidade']
                )
            with col_estado:
                st.session_state.form_data['estado'] = st.text_input(
                    'UF', 
                    max_chars=2, 
                    key="estado", 
                    value=st.session_state.form_data['estado']
                )
        
        with st.expander("Observações"):
            st.session_state.form_data['observacao'] = st.text_area(
                "Observações", "", 
                height=150, 
                max_chars=1000, 
                key="observacao", 
                value=st.session_state.form_data['observacao']
            )

        st.markdown("---")
        submit_button = st.form_submit_button('Salvar Cliente', type="primary", use_container_width=True)

if submit_button:
    # Prepare customer_data from st.session_state.form_data
    form_data = st.session_state.form_data
    tipo_selecionado = form_data['tipo_documento']

    cpf_valor, cnpj_valor = (validators.unformat_cpf(form_data['documento']), None) if tipo_selecionado == "CPF" else (None, validators.unformat_cnpj(form_data['documento']))
    
    customer_data = {
        'nome_completo': form_data['nome_completo'], 
        'tipo_documento': tipo_selecionado, 
        'cpf': cpf_valor, 
        'cnpj': cnpj_valor,
        'contato1': form_data['contato1'], 
        'telefone1': validators.unformat_whatsapp(form_data['telefone1']), 
        'contato2': form_data['contato2'], 
        'telefone2': validators.unformat_whatsapp(form_data['telefone2']), 
        'cargo': form_data['cargo'],
        'email': form_data['email'], 
        'data_nascimento': form_data['data_nascimento'], 
        'cep': form_data['cep'], 
        'endereco': form_data['endereco'], 
        'numero': form_data['numero'],
        'complemento': form_data['complemento'], 
        'bairro': form_data['bairro'], 
        'cidade': form_data['cidade'], 
        'estado': form_data['estado'], 
        'observacao': form_data['observacao'],
    }
    
    try:
        database.insert_customer(customer_data)
        st.balloons()
        st.success("Cliente salvo com sucesso!")
        clear_form_inputs()
        st.rerun() # Rerun to clear form and show empty fields
    except (validators.ValidationError, database.DatabaseError, database.DuplicateEntryError) as e:
        st.error(f"Erro ao salvar: {e}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")