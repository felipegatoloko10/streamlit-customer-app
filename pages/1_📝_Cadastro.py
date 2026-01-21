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

def clear_form_inputs():
    """Reseta o estado do formulário para os valores padrão e limpa chaves de notificação."""
    st.session_state.form_data = DEFAULT_FORM_DATA.copy()
    
    # Explicitly clear input widget values by setting their session_state keys
    # This ensures a clean state for widgets not managed by st.form
    st.session_state.cep_input_widget = ""
    st.session_state.cnpj_search_input = ""
    st.session_state.nome_completo_input_widget = ""
    st.session_state.documento_input_widget = ""
    st.session_state.email_input_widget = ""
    st.session_state.telefone1_input_widget = ""
    st.session_state.cep_address_input_widget = ""
    st.session_state.endereco_input_widget = ""
    st.session_state.numero_input_widget = ""
    st.session_state.complemento_input_widget = ""
    st.session_state.bairro_input_widget = ""
    st.session_state.cidade_input_widget = ""
    st.session_state.estado_input_widget = ""

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

# Initialize widget keys outside the form for direct binding.
# Streamlit will manage these keys. We only need to provide initial values here.
# The value parameter of the widget will link to st.session_state.form_data.
if 'cep_input_widget' not in st.session_state: st.session_state.cep_input_widget = ""
if 'cnpj_search_input' not in st.session_state: st.session_state.cnpj_search_input = ""


# --- Lógica para atualizar o CEP vindo da busca de CNPJ ---
if "cep_from_cnpj" in st.session_state:
    st.session_state.form_data['cep'] = st.session_state.pop("cep_from_cnpj")
    # Update widget value directly as it's outside the form
    st.session_state.cep_address_input_widget = st.session_state.form_data['cep']


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

# --- Seção de Busca de CEP (fora do formulário) ---
with st.container(border=True):
    st.subheader("Busca de Endereço por CEP")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.text_input("CEP", max_chars=9, key="cep_input_widget", value=st.session_state.cep_input_widget)
    with col2:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("Buscar Endereço"):
            services.fetch_address_data(st.session_state.cep_input_widget, st.session_state.form_data)
            # Update individual widget states from form_data to reflect changes
            st.session_state.cep_address_input_widget = st.session_state.form_data['cep']
            st.session_state.endereco_input_widget = st.session_state.form_data['endereco']
            st.session_state.bairro_input_widget = st.session_state.form_data['bairro']
            st.session_state.cidade_input_widget = st.session_state.form_data['cidade']
            st.session_state.estado_input_widget = st.session_state.form_data['estado']
            st.rerun() # Rerun to reflect changes immediately


st.markdown("---")

# --- Seção de Dados Principais e CNPJ Search (fora do formulário) ---
with st.container(border=True):
    st.subheader("Dados Principais")
    
    col_tipo_doc, col_radio = st.columns([0.7, 0.3])
    with col_radio:
        st.session_state.form_data['tipo_documento'] = st.radio(
            "Tipo de Documento", 
            ["CPF", "CNPJ"], 
            horizontal=True, 
            key="tipo_documento_radio", # Unique key for radio
            label_visibility="collapsed",
            index=["CPF", "CNPJ"].index(st.session_state.form_data['tipo_documento'])
        )
        # Update form_data from radio widget's session_state value
        st.session_state.form_data['tipo_documento'] = st.session_state.tipo_documento_radio


    # CNPJ Search input (moved above nome_completo as requested)
    if st.session_state.form_data['tipo_documento'] == "CNPJ":
        with st.container():
            col_cnpj_input, col_cnpj_btn = st.columns([0.7, 0.3])
            with col_cnpj_input:
                st.text_input(
                    "CNPJ para busca", 
                    key="cnpj_search_input", 
                    label_visibility="collapsed", 
                    placeholder="Digite o CNPJ para buscar dados", 
                    value=st.session_state.cnpj_search_input
                )
            with col_cnpj_btn:
                if st.button("🔎 Buscar CNPJ", use_container_width=True):
                    # Ensure the main document field gets the searched CNPJ
                    st.session_state.form_data['documento'] = st.session_state.cnpj_search_input 
                    services.fetch_cnpj_data(st.session_state.cnpj_search_input, st.session_state.form_data)
                    # Update widgets directly from form_data to reflect changes
                    st.session_state.nome_completo_input_widget = st.session_state.form_data['nome_completo']
                    st.session_state.documento_input_widget = st.session_state.form_data['documento'] # Explicitly update documento_input_widget
                    st.session_state.email_input_widget = st.session_state.form_data['email']
                    st.session_state.telefone1_input_widget = st.session_state.form_data['telefone1']
                    st.session_state.cep_address_input_widget = st.session_state.form_data['cep']
                    st.session_state.endereco_input_widget = st.session_state.form_data['endereco']
                    st.session_state.numero_input_widget = st.session_state.form_data['numero']
                    st.session_state.complemento_input_widget = st.session_state.form_data['complemento']
                    st.session_state.bairro_input_widget = st.session_state.form_data['bairro']
                    st.session_state.cidade_input_widget = st.session_state.form_data['cidade']
                    st.session_state.estado_input_widget = st.session_state.form_data['estado']
                    st.rerun() # Rerun to reflect changes immediately
        st.markdown("---")
    
    # Nome Completo / Razão Social
    st.text_input(
        'Nome Completo / Razão Social *', 
        key="nome_completo_input_widget", 
        value=st.session_state.nome_completo_input_widget 
    )
    # Update form_data immediately on change for this field
    st.session_state.form_data['nome_completo'] = st.session_state.nome_completo_input_widget


    # CPF / CNPJ Input (this field is filled by search or manual input)
    label_documento = "CPF *" if st.session_state.form_data['tipo_documento'] == "CPF" else "CNPJ *"
    st.text_input(
        label_documento, 
        key="documento_input_widget", 
        value=st.session_state.documento_input_widget 
    )
    # Update form_data immediately on change for this field
    st.session_state.form_data['documento'] = st.session_state.documento_input_widget
    
    # Email and Telefone1 (also directly updated by CNPJ search)
    col_email, col_tel1_main = st.columns(2)
    with col_email:
        st.text_input(
            'E-mail', 
            key="email_input_widget", 
            value=st.session_state.email_input_widget
        )
        st.session_state.form_data['email'] = st.session_state.email_input_widget
    with col_tel1_main: 
        st.text_input(
            'Telefone 1', 
            key="telefone1_input_widget", 
            value=st.session_state.telefone1_input_widget
        )
        st.session_state.form_data['telefone1'] = st.session_state.telefone1_input_widget
        if WHATSAPP_ICON and st.session_state.form_data['telefone1']:
            whatsapp_link_1 = validators.get_whatsapp_url(validators.unformat_whatsapp(st.session_state.form_data['telefone1']))
            st.markdown(f'<div style="text-align: right;"><a href="{whatsapp_link_1}" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a></div>', unsafe_allow_html=True)

# --- Endereço ---
st.markdown("---")
with st.container(border=True):
    st.subheader("Endereço")
    st.text_input(
        'CEP', 
        key="cep_address_input_widget", 
        value=st.session_state.cep_address_input_widget
    )
    st.session_state.form_data['cep'] = st.session_state.cep_address_input_widget

    col_end, col_num = st.columns([3, 1])
    with col_end:
        st.text_input(
            'Endereço', 
            key="endereco_input_widget", 
            value=st.session_state.endereco_input_widget
        )
        st.session_state.form_data['endereco'] = st.session_state.endereco_input_widget
    with col_num:
        st.text_input(
            'Número', 
            key="numero_input_widget", 
            value=st.session_state.numero_input_widget
        )
        st.session_state.form_data['numero'] = st.session_state.numero_input_widget

    col_bairro, col_comp = st.columns(2)
    with col_bairro:
        st.text_input(
            'Bairro', 
            key="bairro_input_widget", 
            value=st.session_state.bairro_input_widget
        )
        st.session_state.form_data['bairro'] = st.session_state.bairro_input_widget
    with col_comp:
        st.text_input(
            'Complemento', 
            key="complemento_input_widget", 
            value=st.session_state.complemento_input_widget
        )
        st.session_state.form_data['complemento'] = st.session_state.complemento_input_widget

    col_cidade, col_estado = st.columns([3, 1])
    with col_cidade:
        st.text_input(
            'Cidade', 
            key="cidade_input_widget", 
            value=st.session_state.cidade_input_widget
        )
        st.session_state.form_data['cidade'] = st.session_state.cidade_input_widget
    with col_estado:
        st.text_input(
            'UF', 
            max_chars=2, 
            key="estado_input_widget", 
            value=st.session_state.estado_input_widget
        )
        st.session_state.form_data['estado'] = st.session_state.estado_input_widget


st.markdown("---")

# --- Restante do Formulário (dentro de st.form) ---
with st.form(key="new_customer_form", clear_on_submit=False):
    # Data de Nascimento (less likely to be pre-filled)
    data_nascimento_form_widget = st.date_input(
        'Data de Nascimento / Fundação', 
        value=st.session_state.form_data['data_nascimento'], 
        min_value=datetime.date(1900, 1, 1), 
        key="data_nascimento_form_widget" 
    )

    with st.expander("Outros Contatos"):
        use_client_name_form_widget = st.checkbox(
            "Usar nome do cliente como Contato 1", 
            key="use_client_name_form_widget", 
            value=st.session_state.form_data['use_client_name']
        )
        
        # Logic for contato1 (now tied to form_data)
        if st.session_state.form_data['use_client_name']:
            st.session_state.form_data['contato1'] = st.session_state.form_data['nome_completo']
            contato1_value = st.session_state.form_data['contato1']
            contato1_disabled = True
        else:
            contato1_value = st.session_state.form_data['contato1']
            contato1_disabled = False

        contato1_form_widget = st.text_input(
            "Nome do Contato 1", 
            value=contato1_value, 
            key="contato1_form_widget", 
            disabled=contato1_disabled
        )

        cargo_form_widget = st.text_input(
            "Cargo do Contato 1", 
            key="cargo_form_widget", 
            value=st.session_state.form_data['cargo']
        )
        st.markdown("---")
        
        contato2_form_widget = st.text_input(
            "Nome do Contato 2", 
            key="contato2_form_widget", 
            value=st.session_state.form_data['contato2']
        )
        telefone2_form_widget = st.text_input(
            'Telefone 2', 
            key="telefone2_form_widget", 
            value=st.session_state.form_data['telefone2']
        )
        if WHATSAPP_ICON and st.session_state.form_data['telefone2']:
            whatsapp_link_2 = validators.get_whatsapp_url(validators.unformat_whatsapp(st.session_state.form_data['telefone2']))
            st.markdown(f'<div style="text-align: right;"><a href="{whatsapp_link_2}" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a></div>', unsafe_allow_html=True)


    with st.expander("Observações"):
        observacao_form_widget = st.text_area(
            "Observações", 
            value=st.session_state.form_data['observacao'], 
            height=150, 
            max_chars=1000, 
            key="observacao_form_widget" 
        )

    st.markdown("---")
    submit_button = st.form_submit_button('Salvar Cliente', type="primary", use_container_width=True)


# --- Handle Form Submission ---
if submit_button:
    # Update form_data with values from widgets inside the st.form
    st.session_state.form_data['data_nascimento'] = data_nascimento_form_widget
    st.session_state.form_data['use_client_name'] = use_client_name_form_widget
    st.session_state.form_data['contato1'] = contato1_form_widget
    st.session_state.form_data['cargo'] = cargo_form_widget
    st.session_state.form_data['contato2'] = contato2_form_widget
    st.session_state.form_data['telefone2'] = telefone2_form_widget
    st.session_state.form_data['observacao'] = observacao_form_widget


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

# --- Handle checkbox logic for 'use_client_name' (outside the form) ---
# This logic is applied on every rerun, ensuring form_data is consistent
# Note: This logic now needs to update st.session_state.form_data directly
# and potentially trigger a rerun if the change isn't picked up automatically by widgets outside form.

if st.session_state.form_data['use_client_name'] and st.session_state.form_data['contato1'] != st.session_state.form_data['nome_completo']:
    st.session_state.form_data['contato1'] = st.session_state.form_data['nome_completo']
    # st.rerun() # Removed to avoid infinite loop
elif not st.session_state.form_data['use_client_name'] and st.session_state.form_data['contato1'] == st.session_state.form_data['nome_completo']:
    st.session_state.form_data['contato1'] = "" # Clear if unchecked and it was previously set by this logic
    # st.rerun() # Removed to avoid infinite loop
