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
def clear_form_state():
    """Reseta o form_data e todos os 'widget_*' para os valores padrão."""
    st.session_state.form_data = DEFAULT_FORM_DATA.copy()
    for key, value in DEFAULT_FORM_DATA.items():
        widget_key = f"widget_{key}_input"
        if widget_key in st.session_state:
            st.session_state[widget_key] = value
    # Reset widgets that don't map directly
    st.session_state.widget_cep_input = ""
    st.session_state.widget_cnpj_search_input = ""
    st.session_state.widget_tipo_documento_radio = "CPF"
    st.session_state.widget_cep_address_input = ""
    st.session_state.widget_use_client_name_checkbox = False

@st.cache_data
def load_whatsapp_icon_b64():
    image_path = os.path.join(os.path.dirname(__file__), '..', 'whatsapp.png')
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        st.warning("Arquivo 'whatsapp.png' não encontrado.")
        return None

import services

# --- Inicialização e Gerenciamento de Estado ---

# Executa a limpeza do formulário no início da execução do script, se a flag estiver ativa
if st.session_state.get("submission_success", False):
    clear_form_state()
    st.session_state.submission_success = False # Reseta a flag

# Inicializa o estado na primeira execução
if 'form_data' not in st.session_state:
    clear_form_state()

def on_change_callback(form_key, widget_key):
    """Sincroniza o valor do widget com o dicionário de dados do formulário."""
    st.session_state.form_data[form_key] = st.session_state[widget_key]
    if form_key == 'use_client_name':
        if st.session_state.form_data['use_client_name']:
            st.session_state.widget_contato1_input = st.session_state.form_data['nome_completo']
            st.session_state.form_data['contato1'] = st.session_state.form_data['nome_completo']
        else:
            st.session_state.widget_contato1_input = ""
            st.session_state.form_data['contato1'] = ""

WHATSAPP_ICON = load_whatsapp_icon_b64()

# --- Interface ---
st.title('📝 Cadastro de Clientes')

# Seção de Busca de CEP
with st.container(border=True):
    st.subheader("Busca de Endereço por CEP")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.text_input("CEP", max_chars=9, key="widget_cep_input")
    with col2:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("Buscar Endereço"):
            try:
                with st.spinner("Buscando CEP..."):
                    address_data = services.fetch_address_data(st.session_state.widget_cep_input)
                if address_data:
                    st.toast("Endereço encontrado!", icon="✅")
                    st.session_state.form_data.update(address_data)
                    st.session_state.form_data['cep'] = st.session_state.widget_cep_input
                    # Propaga para os widgets
                    st.session_state.widget_cep_address_input = st.session_state.form_data['cep']
                    st.session_state.widget_endereco_input = st.session_state.form_data['endereco']
                    st.session_state.widget_bairro_input = st.session_state.form_data['bairro']
                    st.session_state.widget_cidade_input = st.session_state.form_data['cidade']
                    st.session_state.widget_estado_input = st.session_state.form_data['estado']
                else:
                    st.warning("CEP não encontrado.")
            except (ValueError, requests.exceptions.RequestException) as e:
                st.error(str(e))
            st.rerun()

st.markdown("---")

# Seção de Dados Principais e Busca de CNPJ
with st.container(border=True):
    st.subheader("Dados Principais")
    st.radio("Tipo de Documento", ["CPF", "CNPJ"], horizontal=True, key="widget_tipo_documento_radio", on_change=lambda: on_change_callback("tipo_documento", "widget_tipo_documento_radio"))
    if st.session_state.widget_tipo_documento_radio == "CNPJ":
        col_cnpj_input, col_cnpj_btn = st.columns([0.7, 0.3])
        with col_cnpj_input:
            st.text_input("CNPJ para busca", key="widget_cnpj_search_input", placeholder="Digite um CNPJ para buscar")
        with col_cnpj_btn:
            if st.button("🔎 Buscar CNPJ", use_container_width=True):
                try:
                    with st.spinner("Buscando dados do CNPJ..."):
                        cnpj_data = services.fetch_cnpj_data(st.session_state.widget_cnpj_search_input)
                    st.toast("Dados do CNPJ preenchidos!", icon="✅")
                    st.session_state.form_data.update(cnpj_data)
                    st.session_state.form_data['documento'] = cnpj_data.get('cnpj', '')
                    # Propaga para todos os widgets
                    for key, value in st.session_state.form_data.items():
                        if f"widget_{key}_input" in st.session_state:
                            st.session_state[f"widget_{key}_input"] = value
                    st.session_state.widget_cep_address_input = st.session_state.form_data['cep']

                except (ValueError, services.CnpjNotFoundError, requests.exceptions.RequestException) as e:
                    st.error(str(e))
                st.rerun()
        st.markdown("---")
    
    st.text_input('Nome Completo / Razão Social *', key="widget_nome_completo_input", on_change=lambda: on_change_callback("nome_completo", "widget_nome_completo_input"))
    label_documento = "CPF *" if st.session_state.widget_tipo_documento_radio == "CPF" else "CNPJ *"
    st.text_input(label_documento, key="widget_documento_input", on_change=lambda: on_change_callback("documento", "widget_documento_input"))
    
    col_email, col_tel1_main = st.columns(2)
    with col_email:
        st.text_input('E-mail', key="widget_email_input", on_change=lambda: on_change_callback("email", "widget_email_input"))
    with col_tel1_main: 
        st.text_input('Telefone 1', key="widget_telefone1_input", on_change=lambda: on_change_callback("telefone1", "widget_telefone1_input"))
        if WHATSAPP_ICON and st.session_state.widget_telefone1_input:
            whatsapp_link_1 = validators.get_whatsapp_url(validators.unformat_whatsapp(st.session_state.widget_telefone1_input))
            st.markdown(f'<div style="text-align: right;"><a href="{whatsapp_link_1}" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a></div>', unsafe_allow_html=True)

st.markdown("---")

# Seção de Contatos
with st.container(border=True):
    st.subheader("Contatos")
    st.date_input('Data de Nascimento / Fundação', min_value=datetime.date(1900, 1, 1), key="widget_data_nascimento_input", on_change=lambda: on_change_callback("data_nascimento", "widget_data_nascimento_input"))
    st.checkbox("Usar nome do cliente como Contato 1", key="widget_use_client_name_checkbox", on_change=lambda: on_change_callback("use_client_name", "widget_use_client_name_checkbox"))
    st.text_input("Nome do Contato 1", key="widget_contato1_input", disabled=st.session_state.form_data.get('use_client_name', False), on_change=lambda: on_change_callback("contato1", "widget_contato1_input"))
    st.text_input("Cargo do Contato 1", key="widget_cargo_input", on_change=lambda: on_change_callback("cargo", "widget_cargo_input"))
    st.markdown("---")
    st.text_input("Nome do Contato 2", key="widget_contato2_input", on_change=lambda: on_change_callback("contato2", "widget_contato2_input"))
    st.text_input('Telefone 2', key="widget_telefone2_input", on_change=lambda: on_change_callback("telefone2", "widget_telefone2_input"))
    if WHATSAPP_ICON and st.session_state.widget_telefone2_input:
        whatsapp_link_2 = validators.get_whatsapp_url(validators.unformat_whatsapp(st.session_state.widget_telefone2_input))
        st.markdown(f'<div style="text-align: right;"><a href="{whatsapp_link_2}" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a></div>', unsafe_allow_html=True)

st.markdown("---")

# Endereço
with st.container(border=True):
    st.subheader("Endereço")
    st.text_input('CEP', key="widget_cep_address_input", on_change=lambda: on_change_callback("cep", "widget_cep_address_input"))
    col_end, col_num = st.columns([3, 1])
    with col_end:
        st.text_input('Endereço', key="widget_endereco_input", on_change=lambda: on_change_callback("endereco", "widget_endereco_input"))
    with col_num:
        st.text_input('Número', key="widget_numero_input", on_change=lambda: on_change_callback("numero", "widget_numero_input"))
    col_bairro, col_comp = st.columns(2)
    with col_bairro:
        st.text_input('Bairro', key="widget_bairro_input", on_change=lambda: on_change_callback("bairro", "widget_bairro_input"))
    with col_comp:
        st.text_input('Complemento', key="widget_complemento_input", on_change=lambda: on_change_callback("complemento", "widget_complemento_input"))
    col_cidade, col_estado = st.columns([3, 1])
    with col_cidade:
        st.text_input('Cidade', key="widget_cidade_input", on_change=lambda: on_change_callback("cidade", "widget_cidade_input"))
    with col_estado:
        st.text_input('UF', max_chars=2, key="widget_estado_input", on_change=lambda: on_change_callback("estado", "widget_estado_input"))

st.markdown("---")

# Observações
with st.container(border=True):
    st.subheader("Observações")
    st.text_area("Observações", height=150, max_chars=1000, key="widget_observacao_input", on_change=lambda: on_change_callback("observacao", "widget_observacao_input"))

st.markdown("---")

# Botões de Ação
col_submit, col_clear = st.columns(2)
with col_submit:
    if st.button('Salvar Cliente', type="primary", use_container_width=True):
        form_data = st.session_state.form_data
        customer_data = {
            'nome_completo': form_data.get('nome_completo'), 
            'tipo_documento': form_data.get('tipo_documento'), 
            'cpf': validators.unformat_cpf(form_data['documento']) if form_data.get('tipo_documento') == "CPF" else None,
            'cnpj': validators.unformat_cnpj(form_data['documento']) if form_data.get('tipo_documento') == "CNPJ" else None,
            'contato1': form_data.get('contato1'), 
            'telefone1': validators.unformat_whatsapp(form_data['telefone1']), 
            'contato2': form_data.get('contato2'), 
            'telefone2': validators.unformat_whatsapp(form_data['telefone2']), 
            'cargo': form_data.get('cargo'),
            'email': form_data.get('email'), 
            'data_nascimento': form_data.get('data_nascimento'), 
            'cep': form_data.get('cep'), 
            'endereco': form_data.get('endereco'), 
            'numero': form_data.get('numero'),
            'complemento': form_data.get('complemento'), 
            'bairro': form_data.get('bairro'), 
            'cidade': form_data.get('cidade'), 
            'estado': form_data.get('estado'), 
            'observacao': form_data.get('observacao'),
        }
        try:
            database.insert_customer(customer_data)
            st.balloons()
            st.success("Cliente salvo com sucesso!")
            st.session_state.submission_success = True
            st.rerun()
        except (validators.ValidationError, database.DatabaseError) as e:
            st.error(f"Erro ao salvar: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")

with col_clear:
    if st.button('Limpar Formulário', use_container_width=True):
        st.session_state.submission_success = True
        st.rerun()
