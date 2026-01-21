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
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        st.warning("Arquivo 'whatsapp.png' não encontrado. O ícone do WhatsApp não será exibido.")
        return None

import services

# Helper to sync widget state to form_data
def sync_form_data(key):
    """Callback para sincronizar o valor do widget com st.session_state.form_data."""
    if key in st.session_state:
        st.session_state.form_data[key] = st.session_state[key]
    # Special handling for 'use_client_name'
    if key == 'use_client_name':
        if st.session_state.form_data['use_client_name']:
            st.session_state.form_data['contato1'] = st.session_state.form_data['nome_completo']
        else:
            st.session_state.form_data['contato1'] = ""
        # Rerun is needed to reflect changes in disabled state or value of 'contato1'
        # Only rerun if it's not already in a rerun cycle (e.g. from an API call button)
        if not st.runtime.state.session_state._is_in_rerun: # Use _is_in_rerun to prevent infinite loop
             st.rerun()

def clear_form_inputs():
    """Reseta o estado do formulário para os valores padrão e limpa chaves de notificação."""
    st.session_state.form_data = DEFAULT_FORM_DATA.copy()
    
    # Reset specific widget keys in session state for elements not directly mapped to form_data
    if 'cnpj_search_input_widget' in st.session_state: st.session_state.cnpj_search_input_widget = ""
    if 'cep_input_widget' in st.session_state: st.session_state.cep_input_widget = ""
    if 'tipo_documento' in st.session_state: st.session_state.tipo_documento = "CPF" # Reset radio button
    
    # Ensure form_data fields are correctly set in session_state for widgets to pick up
    for key, value in DEFAULT_FORM_DATA.items():
        if key in st.session_state: # If a widget has this key
            st.session_state[key] = value

    if 'cep_notification' in st.session_state:
        del st.session_state.cep_notification
    if 'form_error' in st.session_state:
        del st.session_state.form_error
    
    st.rerun() # Rerun to reflect changes immediately


# --- Carrega o ícone do WhatsApp ---
WHATSAPP_ICON = load_whatsapp_icon_b64()

# --- Initialize Form Data in Session State ---
if 'form_data' not in st.session_state:
    st.session_state.form_data = DEFAULT_FORM_DATA.copy()


# Initialize widget keys in session_state that are used for 'value' in widgets
# These are the direct binding keys.
if 'cep_input_widget' not in st.session_state: st.session_state.cep_input_widget = ""
if 'cnpj_search_input_widget' not in st.session_state: st.session_state.cnpj_search_input_widget = ""
# If 'tipo_documento' is used as key for st.radio, initialize it here
if 'tipo_documento' not in st.session_state: st.session_state.tipo_documento = "CPF"


# --- Lógica para atualizar o CEP vindo da busca de CNPJ ---
if "cep_from_cnpj" in st.session_state:
    st.session_state.form_data['cep'] = st.session_state.pop("cep_from_cnpj")


# --- Lógica de Estado para Notificações ---
if 'cep_notification' in st.session_state:
    notification = st.session_state.pop('cep_notification')
    msg_type = notification['type']
    message = notification['message']
    if msg_type == "success":
        st.toast(message, icon="✅")
    elif msg_type == "warning":
        st.warning(message)
    elif msg_type == "error":
        st.error(message)

if st.session_state.get("form_error"):
    st.error(st.session_state.pop("form_error"))


# --- Interface ---
st.title('📝 Cadastro de Clientes')

# --- Seção de Busca de CEP ---
with st.container(border=True):
    st.subheader("Busca de Endereço por CEP")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.text_input("CEP", max_chars=9, key="cep_input_widget", value=st.session_state.cep_input_widget)
    with col2:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("Buscar Endereço"):
            services.fetch_address_data(st.session_state.cep_input_widget, st.session_state.form_data)
            st.rerun() # Rerun to reflect changes immediately


st.markdown("---")

# --- Seção de Dados Principais e CNPJ Search ---
with st.container(border=True):
    st.subheader("Dados Principais")
    
    col_tipo_doc, col_radio = st.columns([0.7, 0.3])
    with col_radio:
        st.radio(
            "Tipo de Documento", 
            ["CPF", "CNPJ"], 
            horizontal=True, 
            key="tipo_documento", # Streamlit will manage this key
            label_visibility="collapsed",
            index=["CPF", "CNPJ"].index(st.session_state.form_data['tipo_documento']),
            on_change=lambda: sync_form_data("tipo_documento")
        )

    # CNPJ Search input
    if st.session_state.form_data['tipo_documento'] == "CNPJ":
        with st.container():
            col_cnpj_input, col_cnpj_btn = st.columns([0.7, 0.3])
            with col_cnpj_input:
                st.text_input(
                    "CNPJ para busca", 
                    key="cnpj_search_input_widget", 
                    label_visibility="collapsed", 
                    placeholder="Digite o CNPJ para buscar dados", 
                    value=st.session_state.cnpj_search_input_widget
                )
            with col_cnpj_btn:
                if st.button("🔎 Buscar CNPJ", use_container_width=True):
                    services.fetch_cnpj_data(st.session_state.cnpj_search_input_widget, st.session_state.form_data)
                    st.rerun() # Rerun to reflect changes immediately
        st.markdown("---")
    
    st.text_input(
        'Nome Completo / Razão Social *', 
        key="nome_completo", 
        value=st.session_state.form_data['nome_completo'],
        on_change=lambda: sync_form_data("nome_completo")
    )

    label_documento = "CPF *" if st.session_state.form_data['tipo_documento'] == "CPF" else "CNPJ *"
    st.text_input(
        label_documento, 
        key="documento", 
        value=st.session_state.form_data['documento'],
        on_change=lambda: sync_form_data("documento")
    )
    
    col_email, col_tel1_main = st.columns(2)
    with col_email:
        st.text_input(
            'E-mail', 
            key="email", 
            value=st.session_state.form_data['email'],
            on_change=lambda: sync_form_data("email")
        )
    with col_tel1_main: 
        st.text_input(
            'Telefone 1', 
            key="telefone1", 
            value=st.session_state.form_data['telefone1'],
            on_change=lambda: sync_form_data("telefone1")
        )
        if WHATSAPP_ICON and st.session_state.form_data['telefone1']:
            whatsapp_link_1 = validators.get_whatsapp_url(validators.unformat_whatsapp(st.session_state.form_data['telefone1']))
            st.markdown(f'<div style="text-align: right;"><a href="{whatsapp_link_1}" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a></div>', unsafe_allow_html=True)


st.markdown("---")

# --- Seção de Contatos ---
with st.container(border=True):
    st.subheader("Contatos")
    
    st.date_input(
        'Data de Nascimento / Fundação', 
        value=st.session_state.form_data['data_nascimento'], 
        min_value=datetime.date(1900, 1, 1), 
        key="data_nascimento",
        on_change=lambda: sync_form_data("data_nascimento")
    )

    st.checkbox(
        "Usar nome do cliente como Contato 1", 
        key="use_client_name", 
        value=st.session_state.form_data['use_client_name'],
        on_change=lambda: sync_form_data("use_client_name") # on_change will also trigger sync
    )
    
    # Logic for contato1
    contato1_value = st.session_state.form_data['contato1']
    contato1_disabled = st.session_state.form_data['use_client_name']

    st.text_input(
        "Nome do Contato 1", 
        value=contato1_value, 
        key="contato1", 
        disabled=contato1_disabled,
        on_change=lambda: sync_form_data("contato1")
    )


    st.text_input(
        "Cargo do Contato 1", 
        key="cargo", 
        value=st.session_state.form_data['cargo'],
        on_change=lambda: sync_form_data("cargo")
    )
    st.markdown("---")
    
    st.text_input(
        "Nome do Contato 2", 
        key="contato2", 
        value=st.session_state.form_data['contato2'],
        on_change=lambda: sync_form_data("contato2")
    )
    st.text_input(
        'Telefone 2', 
        key="telefone2", 
        value=st.session_state.form_data['telefone2'],
        on_change=lambda: sync_form_data("telefone2")
    )
    if WHATSAPP_ICON and st.session_state.form_data['telefone2']:
        whatsapp_link_2 = validators.get_whatsapp_url(validators.unformat_whatsapp(st.session_state.form_data['telefone2']))
        st.markdown(f'<div style="text-align: right;"><a href="{whatsapp_link_2}" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a></div>', unsafe_allow_html=True)


st.markdown("---")

# --- Endereço ---
with st.container(border=True):
    st.subheader("Endereço")
    st.text_input(
        'CEP', 
        key="cep", 
        value=st.session_state.form_data['cep'],
        on_change=lambda: sync_form_data("cep")
    )

    col_end, col_num = st.columns([3, 1])
    with col_end:
        st.text_input(
            'Endereço', 
            key="endereco", 
            value=st.session_state.form_data['endereco'],
            on_change=lambda: sync_form_data("endereco")
        )
    with col_num:
        st.text_input(
            'Número', 
            key="numero", 
            value=st.session_state.form_data['numero'],
            on_change=lambda: sync_form_data("numero")
        )

    col_bairro, col_comp = st.columns(2)
    with col_bairro:
        st.text_input(
            'Bairro', 
            key="bairro", 
            value=st.session_state.form_data['bairro'],
            on_change=lambda: sync_form_data("bairro")
        )
    with col_comp:
        st.text_input(
            'Complemento', 
            key="complemento", 
            value=st.session_state.form_data['complemento'],
            on_change=lambda: sync_form_data("complemento")
        )

    col_cidade, col_estado = st.columns([3, 1])
    with col_cidade:
        st.text_input(
            'Cidade', 
            key="cidade", 
            value=st.session_state.form_data['cidade'],
            on_change=lambda: sync_form_data("cidade")
        )
    with col_estado:
        st.text_input(
            'UF', 
            max_chars=2, 
            key="estado", 
            value=st.session_state.form_data['estado'],
            on_change=lambda: sync_form_data("estado")
        )


st.markdown("---")

# --- Observações ---
with st.container(border=True):
    st.subheader("Observações")
    st.text_area(
        "Observações", 
        value=st.session_state.form_data['observacao'], 
        height=150, 
        max_chars=1000, 
        key="observacao",
        on_change=lambda: sync_form_data("observacao") 
    )

st.markdown("---")

# --- Submit Button ---
submit_button = st.button('Salvar Cliente', type="primary", use_container_width=True)


# --- Handle Form Submission ---
if submit_button:
    form_data = st.session_state.form_data
    tipo_selecionado = form_data['tipo_documento']

    cpf_valor = validators.unformat_cpf(form_data['documento']) if tipo_selecionado == "CPF" else None
    cnpj_valor = validators.unformat_cnpj(form_data['documento']) if tipo_selecionado == "CNPJ" else None
    
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
    except (validators.ValidationError, database.DatabaseError, database.DuplicateEntryError) as e:
        st.error(f"Erro ao salvar: {e}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")