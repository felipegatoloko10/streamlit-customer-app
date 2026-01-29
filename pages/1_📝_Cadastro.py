import streamlit as st
import datetime
import database
import validators
import requests
import re
import base64
import os
import services

st.set_page_config(page_title="Cadastro de Clientes", page_icon="📝", layout="centered")

# --- Definições de Estado e Padrões ---
DEFAULT_VALUES = {
    "widget_cep_input": "", "widget_cnpj_search_input": "", "widget_tipo_documento_radio": "CPF",
    "widget_nome_completo_input": "", "widget_documento_input": "", "widget_email_input": "",
    "widget_telefone1_input": "", "widget_data_nascimento_input": None, "widget_contato1_input": "",
    "widget_cargo_input": "", "widget_contato2_input": "", "widget_telefone2_input": "",
    "widget_cep_address_input": "", "widget_endereco_input": "", "widget_numero_input": "",
    "widget_complemento_input": "", "widget_bairro_input": "", "widget_cidade_input": "",
    "widget_estado_input": "", "widget_observacao_input": "", "widget_use_client_name_checkbox": False,
    # Estados de expansão
    "expand_contatos": False, "expand_cep": False, "expand_endereco": False, "expand_obs": False
}

def initialize_state():
    """Inicializa todas as chaves de widget e de estado no estado da sessão se não existirem."""
    for key, value in DEFAULT_VALUES.items():
        if key not in st.session_state:
            st.session_state[key] = value

def clear_form():
    """Reseta todas as chaves de widget e de estado para seus valores padrão."""
    for key, value in DEFAULT_VALUES.items():
        st.session_state[key] = value

@st.cache_data
def load_whatsapp_icon_b64():
    image_path = os.path.join(os.path.dirname(__file__), '..', 'whatsapp.png')
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        st.warning("Arquivo 'whatsapp.png' não encontrado.")
        return None

# --- Gerenciamento Central de Estado e Callbacks ---
initialize_state()

if st.session_state.get("submission_success", False):
    clear_form()
    st.session_state.submission_success = False

def expand_section(section_name):
    st.session_state[f"expand_{section_name}"] = True

def handle_use_client_name_change():
    if st.session_state.widget_use_client_name_checkbox:
        st.session_state.widget_contato1_input = st.session_state.widget_nome_completo_input
    else:
        st.session_state.widget_contato1_input = ""

WHATSAPP_ICON = load_whatsapp_icon_b64()

# --- Interface ---
st.title('📝 Cadastro de Clientes')
st.write("Preencha os dados abaixo. O formulário se expandirá conforme você avança.")

# Passo 1: Dados Principais
with st.expander("Passo 1: Dados Principais", expanded=True):
    st.radio("Tipo de Documento", ["CPF", "CNPJ"], horizontal=True, key="widget_tipo_documento_radio")
    if st.session_state.widget_tipo_documento_radio == "CNPJ":
        col_cnpj_input, col_cnpj_btn = st.columns([0.7, 0.3])
        with col_cnpj_input:
            st.text_input("CNPJ para busca", key="widget_cnpj_search_input", placeholder="Digite um CNPJ para preencher os dados")
        with col_cnpj_btn:
            if st.button("🔎 Buscar CNPJ", use_container_width=True):
                try:
                    with st.spinner("Buscando dados..."):
                        cnpj_data = services.fetch_cnpj_data(st.session_state.widget_cnpj_search_input)
                    st.toast("Dados do CNPJ preenchidos!", icon="✅")
                    st.session_state.widget_nome_completo_input = cnpj_data.get('nome_completo', '')
                    st.session_state.widget_documento_input = cnpj_data.get('cnpj', '')
                    st.session_state.widget_email_input = cnpj_data.get('email', '')
                    st.session_state.widget_telefone1_input = cnpj_data.get('telefone1', '')
                    st.session_state.widget_cep_input = cnpj_data.get('cep', '')
                    st.session_state.widget_cep_address_input = cnpj_data.get('cep', '')
                    st.session_state.widget_endereco_input = cnpj_data.get('endereco', '')
                    st.session_state.widget_numero_input = cnpj_data.get('numero', '')
                    st.session_state.widget_complemento_input = cnpj_data.get('complemento', '')
                    st.session_state.widget_bairro_input = cnpj_data.get('bairro', '')
                    st.session_state.widget_cidade_input = cnpj_data.get('cidade', '')
                    st.session_state.widget_estado_input = cnpj_data.get('estado', '')
                    expand_section("contatos"); expand_section("cep"); expand_section("endereco"); expand_section("obs")
                except (ValueError, services.CnpjNotFoundError, requests.exceptions.RequestException) as e:
                    st.error(str(e))
    
    st.text_input('Nome Completo / Razão Social *', key="widget_nome_completo_input", on_change=lambda: expand_section("contatos"))
    label_documento = "CPF *" if st.session_state.widget_tipo_documento_radio == "CPF" else "CNPJ *"
    st.text_input(label_documento, key="widget_documento_input")
    col_email, col_tel1 = st.columns(2)
    with col_email:
        st.text_input('E-mail', key="widget_email_input")
    with col_tel1: 
        st.text_input('Telefone 1', key="widget_telefone1_input")
        if WHATSAPP_ICON and st.session_state.widget_telefone1_input:
            st.markdown(f'<div style="text-align: right;"><a href="{validators.get_whatsapp_url(st.session_state.widget_telefone1_input)}" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a></div>', unsafe_allow_html=True)

# Passo 2: Contatos
with st.expander("Passo 2: Contatos", expanded=st.session_state.expand_contatos):
    st.date_input('Data de Nascimento / Fundação', min_value=datetime.date(1900, 1, 1), key="widget_data_nascimento_input")
    st.checkbox("Usar nome do cliente como Contato 1", key="widget_use_client_name_checkbox", on_change=handle_use_client_name_change)
    st.text_input("Nome do Contato 1", key="widget_contato1_input", disabled=st.session_state.widget_use_client_name_checkbox)
    st.text_input("Cargo do Contato 1", key="widget_cargo_input")
    st.markdown("---")
    st.text_input("Nome do Contato 2", key="widget_contato2_input")
    st.text_input('Telefone 2', key="widget_telefone2_input", on_change=lambda: expand_section("cep"))
    if WHATSAPP_ICON and st.session_state.widget_telefone2_input:
        st.markdown(f'<div style="text-align: right;"><a href="{validators.get_whatsapp_url(st.session_state.widget_telefone2_input)}" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a></div>', unsafe_allow_html=True)

# Passo 3: Busca de CEP
with st.expander("Passo 3: Busca de Endereço por CEP", expanded=st.session_state.expand_cep):
    col1, col2 = st.columns([1, 2])
    with col1:
        st.text_input("CEP para busca de endereço", max_chars=9, key="widget_cep_input")
    with col2:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("Buscar Endereço"):
            try:
                with st.spinner("Buscando CEP..."):
                    address_data = services.fetch_address_data(st.session_state.widget_cep_input)
                if address_data:
                    st.toast("Endereço encontrado!", icon="✅")
                    st.session_state.widget_cep_address_input = st.session_state.widget_cep_input
                    st.session_state.widget_endereco_input = address_data.get('endereco', '')
                    st.session_state.widget_bairro_input = address_data.get('bairro', '')
                    st.session_state.widget_cidade_input = address_data.get('cidade', '')
                    st.session_state.widget_estado_input = address_data.get('estado', '')
                    expand_section("endereco")
                else:
                    st.warning("CEP não encontrado.")
            except (ValueError, requests.exceptions.RequestException) as e:
                st.error(str(e))

# Passo 4: Endereço
with st.expander("Passo 4: Endereço", expanded=st.session_state.expand_endereco):
    st.text_input('CEP', key="widget_cep_address_input")
    col_end, col_num = st.columns([3, 1])
    with col_end:
        st.text_input('Endereço', key="widget_endereco_input")
    with col_num:
        st.text_input('Número', key="widget_numero_input", on_change=lambda: expand_section("obs"))
    col_bairro, col_comp = st.columns(2)
    with col_bairro:
        st.text_input('Bairro', key="widget_bairro_input")
    with col_comp:
        st.text_input('Complemento', key="widget_complemento_input")
    col_cidade, col_estado = st.columns([3, 1])
    with col_cidade:
        st.text_input('Cidade', key="widget_cidade_input")
    with col_estado:
        st.text_input('UF', max_chars=2, key="widget_estado_input")

# Passo 5: Observações
with st.expander("Passo 5: Observações", expanded=st.session_state.expand_obs):
    st.text_area("Observações", height=150, max_chars=1000, key="widget_observacao_input")

st.markdown("---")

# Botões de Ação
col_submit, col_clear = st.columns(2)
with col_submit:
    if st.button('Salvar Cliente', type="primary", use_container_width=True):
        customer_data = {
            'nome_completo': st.session_state.widget_nome_completo_input,
            'tipo_documento': st.session_state.widget_tipo_documento_radio,
            'cpf': st.session_state.widget_documento_input if st.session_state.widget_tipo_documento_radio == "CPF" else None,
            'cnpj': st.session_state.widget_documento_input if st.session_state.widget_tipo_documento_radio == "CNPJ" else None,
            'contato1': st.session_state.widget_contato1_input, 'telefone1': st.session_state.widget_telefone1_input,
            'contato2': st.session_state.widget_contato2_input, 'telefone2': st.session_state.widget_telefone2_input,
            'cargo': st.session_state.widget_cargo_input, 'email': st.session_state.widget_email_input,
            'data_nascimento': st.session_state.widget_data_nascimento_input, 'cep': st.session_state.widget_cep_address_input,
            'endereco': st.session_state.widget_endereco_input, 'numero': st.session_state.widget_numero_input,
            'complemento': st.session_state.widget_complemento_input, 'bairro': st.session_state.widget_bairro_input,
            'cidade': st.session_state.widget_cidade_input, 'estado': st.session_state.widget_estado_input,
            'observacao': st.session_state.widget_observacao_input,
        }
        try:
            database.insert_customer(customer_data)
            st.balloons()
            st.success("Cliente salvo com sucesso! O formulário será limpo.")
            st.session_state.submission_success = True
            st.rerun()
        except (validators.ValidationError, database.DatabaseError) as e:
            st.error(f"Erro ao salvar: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")

with col_clear:
    if st.button('Limpar Formulário', use_container_width=True):
        clear_form()
        st.rerun()