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

# --- Callbacks para sincronização de estado ---
def on_change_callback(form_key, widget_key):
    """Sincroniza o valor do widget com o form_data."""
    st.session_state.form_data[form_key] = st.session_state[widget_key]
    # Handle specific logic for 'use_client_name'
    if form_key == 'use_client_name':
        if st.session_state.form_data['use_client_name']:
            st.session_state.form_data['contato1'] = st.session_state.form_data['nome_completo']
            st.session_state.widget_contato1_input = st.session_state.form_data['nome_completo']
        else:
            st.session_state.form_data['contato1'] = ""
            st.session_state.widget_contato1_input = ""
        st.rerun() # Force rerun to update disabled state and value of contato1


def clear_form_inputs():
    """Reseta o estado do formulário para os valores padrão e limpa chaves de notificação."""
    st.session_state.form_data = DEFAULT_FORM_DATA.copy()
    
    # Reset widget state explicitly
    st.session_state.widget_cep_input = ""
    st.session_state.widget_cnpj_search_input = ""
    st.session_state.widget_tipo_documento_radio = "CPF"

    st.session_state.widget_nome_completo_input = ""
    st.session_state.widget_documento_input = ""
    st.session_state.widget_email_input = ""
    st.session_state.widget_telefone1_input = ""
    st.session_state.widget_data_nascimento_input = None
    st.session_state.widget_contato1_input = ""
    st.session_state.widget_cargo_input = ""
    st.session_state.widget_contato2_input = ""
    st.session_state.widget_telefone2_input = ""
    st.session_state.widget_cep_address_input = ""
    st.session_state.widget_endereco_input = ""
    st.session_state.widget_numero_input = ""
    st.session_state.widget_complemento_input = ""
    st.session_state.widget_bairro_input = ""
    st.session_state.widget_cidade_input = ""
    st.session_state.widget_estado_input = ""
    st.session_state.widget_observacao_input = ""
    st.session_state.widget_use_client_name_checkbox = False # Reset checkbox

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


# --- Initialize Widget Keys in Session State ---
# This ensures every widget has an initialized value in st.session_state
if 'widget_cep_input' not in st.session_state: st.session_state.widget_cep_input = ""
if 'widget_cnpj_search_input' not in st.session_state: st.session_state.widget_cnpj_search_input = ""
if 'widget_tipo_documento_radio' not in st.session_state: st.session_state.widget_tipo_documento_radio = "CPF"

if 'widget_nome_completo_input' not in st.session_state: st.session_state.widget_nome_completo_input = ""
if 'widget_documento_input' not in st.session_state: st.session_state.widget_documento_input = ""
if 'widget_email_input' not in st.session_state: st.session_state.widget_email_input = ""
if 'widget_telefone1_input' not in st.session_state: st.session_state.widget_telefone1_input = ""
if 'widget_data_nascimento_input' not in st.session_state: st.session_state.widget_data_nascimento_input = None
if 'widget_contato1_input' not in st.session_state: st.session_state.widget_contato1_input = ""
if 'widget_cargo_input' not in st.session_state: st.session_state.widget_cargo_input = ""
if 'widget_contato2_input' not in st.session_state: st.session_state.widget_contato2_input = ""
if 'widget_telefone2_input' not in st.session_state: st.session_state.widget_telefone2_input = ""
if 'widget_cep_address_input' not in st.session_state: st.session_state.widget_cep_address_input = ""
if 'widget_endereco_input' not in st.session_state: st.session_state.widget_endereco_input = ""
if 'widget_numero_input' not in st.session_state: st.session_state.widget_numero_input = ""
if 'widget_complemento_input' not in st.session_state: st.session_state.widget_complemento_input = ""
if 'widget_bairro_input' not in st.session_state: st.session_state.widget_bairro_input = ""
if 'widget_cidade_input' not in st.session_state: st.session_state.widget_cidade_input = ""
if 'widget_estado_input' not in st.session_state: st.session_state.widget_estado_input = ""
if 'widget_observacao_input' not in st.session_state: st.session_state.widget_observacao_input = ""
if 'widget_use_client_name_checkbox' not in st.session_state: st.session_state.widget_use_client_name_checkbox = False


# --- Lógica para atualizar o CEP vindo da busca de CNPJ ---
# This updates form_data, which then needs to be propagated to widget state
if "cep_from_cnpj" in st.session_state:
    st.session_state.form_data['cep'] = st.session_state.pop("cep_from_cnpj")
    st.session_state.widget_cep_address_input = st.session_state.form_data['cep'] # Propagate to widget state


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
        st.text_input("CEP", max_chars=9, key="widget_cep_input", value=st.session_state.widget_cep_input)
    with col2:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("Buscar Endereço"):
            services.fetch_address_data(st.session_state.widget_cep_input, st.session_state.form_data)
            # Propagate updated form_data to widget states
            st.session_state.widget_cep_address_input = st.session_state.form_data['cep']
            st.session_state.widget_endereco_input = st.session_state.form_data['endereco']
            st.session_state.widget_bairro_input = st.session_state.form_data['bairro']
            st.session_state.widget_cidade_input = st.session_state.form_data['cidade']
            st.session_state.widget_estado_input = st.session_state.form_data['estado']
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
            key="widget_tipo_documento_radio", 
            label_visibility="collapsed",
            index=["CPF", "CNPJ"].index(st.session_state.widget_tipo_documento_radio),
            on_change=lambda: on_change_callback("tipo_documento", "widget_tipo_documento_radio")
        )

    # CNPJ Search input
    if st.session_state.form_data['tipo_documento'] == "CNPJ":
        with st.container():
            col_cnpj_input, col_cnpj_btn = st.columns([0.7, 0.3])
            with col_cnpj_input:
                st.text_input(
                    "CNPJ para busca", 
                    key="widget_cnpj_search_input", 
                    label_visibility="collapsed", 
                    placeholder="Digite o CNPJ para buscar dados", 
                    value=st.session_state.widget_cnpj_search_input
                )
            with col_cnpj_btn:
                if st.button("🔎 Buscar CNPJ", use_container_width=True):
                    services.fetch_cnpj_data(st.session_state.widget_cnpj_search_input, st.session_state.form_data)
                    # Propagate updated form_data to widget states
                    st.session_state.widget_nome_completo_input = st.session_state.form_data['nome_completo']
                    st.session_state.widget_documento_input = st.session_state.form_data['documento']
                    st.session_state.widget_email_input = st.session_state.form_data['email']
                    st.session_state.widget_telefone1_input = st.session_state.form_data['telefone1']
                    st.session_state.widget_cep_address_input = st.session_state.form_data['cep']
                    st.session_state.widget_endereco_input = st.session_state.form_data['endereco']
                    st.session_state.widget_numero_input = st.session_state.form_data['numero']
                    st.session_state.widget_complemento_input = st.session_state.form_data['complemento']
                    st.session_state.widget_bairro_input = st.session_state.form_data['bairro']
                    st.session_state.widget_cidade_input = st.session_state.form_data['cidade']
                    st.session_state.widget_estado_input = st.session_state.form_data['estado']
                    st.rerun() # Rerun to reflect changes immediately
        st.markdown("---")
    
    st.text_input(
        'Nome Completo / Razão Social *', 
        key="widget_nome_completo_input", 
        value=st.session_state.widget_nome_completo_input,
        on_change=lambda: on_change_callback("nome_completo", "widget_nome_completo_input")
    )

    label_documento = "CPF *" if st.session_state.form_data['tipo_documento'] == "CPF" else "CNPJ *"
    st.text_input(
        label_documento, 
        key="widget_documento_input", 
        value=st.session_state.widget_documento_input,
        on_change=lambda: on_change_callback("documento", "widget_documento_input")
    )
    
    col_email, col_tel1_main = st.columns(2)
    with col_email:
        st.text_input(
            'E-mail', 
            key="widget_email_input", 
            value=st.session_state.widget_email_input,
            on_change=lambda: on_change_callback("email", "widget_email_input")
        )
    with col_tel1_main: 
        st.text_input(
            'Telefone 1', 
            key="widget_telefone1_input", 
            value=st.session_state.widget_telefone1_input,
            on_change=lambda: on_change_callback("telefone1", "widget_telefone1_input")
        )
        if WHATSAPP_ICON and st.session_state.widget_telefone1_input: # Use widget state for display
            whatsapp_link_1 = validators.get_whatsapp_url(validators.unformat_whatsapp(st.session_state.widget_telefone1_input))
            st.markdown(f'<div style="text-align: right;"><a href="{whatsapp_link_1}" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a></div>', unsafe_allow_html=True)


st.markdown("---")

# --- Seção de Contatos ---
with st.container(border=True):
    st.subheader("Contatos")
    
    st.date_input(
        'Data de Nascimento / Fundação', 
        value=st.session_state.form_data['data_nascimento'], # Reads from form_data
        min_value=datetime.date(1900, 1, 1), 
        key="widget_data_nascimento_input",
        on_change=lambda: on_change_callback("data_nascimento", "widget_data_nascimento_input")
    )

    st.checkbox(
        "Usar nome do cliente como Contato 1", 
        key="widget_use_client_name_checkbox", 
        value=st.session_state.form_data['use_client_name'], # Reads from form_data
        on_change=lambda: on_change_callback("use_client_name", "widget_use_client_name_checkbox") # on_change will also trigger sync
    )
    
    # Logic for contato1 (reads from form_data, updated via checkbox callback)
    contato1_value = st.session_state.form_data['contato1']
    contato1_disabled = st.session_state.form_data['use_client_name']

    st.text_input(
        "Nome do Contato 1", 
        value=contato1_value, 
        key="widget_contato1_input", 
        disabled=contato1_disabled,
        on_change=lambda: on_change_callback("contato1", "widget_contato1_input")
    )


    st.text_input(
        "Cargo do Contato 1", 
        key="widget_cargo_input", 
        value=st.session_state.form_data['cargo'],
        on_change=lambda: on_change_callback("cargo", "widget_cargo_input")
    )
    st.markdown("---")
    
    st.text_input(
        "Nome do Contato 2", 
        key="widget_contato2_input", 
        value=st.session_state.form_data['contato2'],
        on_change=lambda: on_change_callback("contato2", "widget_contato2_input")
    )
    st.text_input(
        'Telefone 2', 
        key="widget_telefone2_input", 
        value=st.session_state.form_data['telefone2'],
        on_change=lambda: on_change_callback("telefone2", "widget_telefone2_input")
    )
    if WHATSAPP_ICON and st.session_state.widget_telefone2_input:
        whatsapp_link_2 = validators.get_whatsapp_url(validators.unformat_whatsapp(st.session_state.widget_telefone2_input))
        st.markdown(f'<div style="text-align: right;"><a href="{whatsapp_link_2}" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a></div>', unsafe_allow_html=True)


st.markdown("---")

# --- Endereço ---
with st.container(border=True):
    st.subheader("Endereço")
    st.text_input(
        'CEP', 
        key="widget_cep_address_input", 
        value=st.session_state.form_data['cep'],
        on_change=lambda: on_change_callback("cep", "widget_cep_address_input")
    )

    col_end, col_num = st.columns([3, 1])
    with col_end:
        st.text_input(
            'Endereço', 
            key="widget_endereco_input", 
            value=st.session_state.form_data['endereco'],
            on_change=lambda: on_change_callback("endereco", "widget_endereco_input")
        )
    with col_num:
        st.text_input(
            'Número', 
            key="widget_numero_input", 
            value=st.session_state.form_data['numero'],
            on_change=lambda: on_change_callback("numero", "widget_numero_input")
        )

    col_bairro, col_comp = st.columns(2)
    with col_bairro:
        st.text_input(
            'Bairro', 
            key="widget_bairro_input", 
            value=st.session_state.form_data['bairro'],
            on_change=lambda: on_change_callback("bairro", "widget_bairro_input")
        )
    with col_comp:
        st.text_input(
            'Complemento', 
            key="widget_complemento_input", 
            value=st.session_state.form_data['complemento'],
            on_change=lambda: on_change_callback("complemento", "widget_complemento_input")
        )

    col_cidade, col_estado = st.columns([3, 1])
    with col_cidade:
        st.text_input(
            'Cidade', 
            key="widget_cidade_input", 
            value=st.session_state.form_data['cidade'],
            on_change=lambda: on_change_callback("cidade", "widget_cidade_input")
        )
    with col_estado:
        st.text_input(
            'UF', 
            max_chars=2, 
            key="widget_estado_input", 
            value=st.session_state.form_data['estado'],
            on_change=lambda: on_change_callback("estado", "widget_estado_input")
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
        key="widget_observacao_input",
        on_change=lambda: on_change_callback("observacao", "widget_observacao_input") 
    )

st.markdown("---")

# --- Submit Button ---
submit_button = st.button('Salvar Cliente', type="primary", use_container_width=True)


# --- Handle Form Submission ---
if submit_button:
    # After submission, st.session_state.form_data should be fully synchronized
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
