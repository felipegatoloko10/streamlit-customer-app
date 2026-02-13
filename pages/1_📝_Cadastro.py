import streamlit as st
import datetime
import validators
import requests
import re
import base64
import os
import integration_services as services
from services.customer_service import CustomerService, DatabaseError

st.set_page_config(page_title="Cadastro de Clientes", page_icon="📝", layout="centered")

# Inicializa o serviço
customer_service = CustomerService()

# Exibe o status da nuvem na sidebar
services.show_cloud_status()

# --- Definições de Estado e Padrões ---
DEFAULT_VALUES = {
    "widget_cep_input": "", "widget_cnpj_search_input": "", "widget_tipo_documento_radio": "CPF",
    "widget_nome_completo_input": "", "widget_documento_input": "", "widget_email_input": "",
    "widget_telefone1_input": "", "widget_data_nascimento_input": None, "widget_contato1_input": "",
    "widget_cargo_input": "", "widget_contato2_input": "", "widget_telefone2_input": "",
    "widget_cep_address_input": "", "widget_endereco_input": "", "widget_numero_input": "",
    "widget_complemento_input": "", "widget_bairro_input": "", "widget_cidade_input": "",
    "widget_estado_input": "", "widget_observacao_input": "", "widget_use_client_name_checkbox": False,
    "widget_receber_atualizacoes_checkbox": True,
    "expand_contatos": False, "expand_cep": False, "expand_endereco": False, "expand_obs": False,
    "processing_submission": False, # Novo flag para evitar múltiplas submissões
    "clear_form_requested": False # Novo flag para controlar a limpeza do formulário
}

def initialize_state():
    """Inicializa as chaves do estado da sessão e processa pedidos de limpeza do formulário."""
    reset_requested = st.session_state.get("clear_form_requested", False)
    
    for key, value in DEFAULT_VALUES.items():
        if reset_requested or key not in st.session_state:
            if key not in ["processing_submission", "clear_form_requested"]:
                st.session_state[key] = value
                
    if reset_requested:
        st.session_state.clear_form_requested = False

# --- Gerenciamento Central de Estado e Callbacks ---
initialize_state()

if st.session_state.get("submission_success", False):
    st.session_state.submission_success = False
    st.session_state.clear_form_requested = True 
    st.rerun()

def expand_section(section_name):
    st.session_state[f"expand_{section_name}"] = True


def handle_use_client_name_change():
    if st.session_state.widget_use_client_name_checkbox:
        st.session_state.widget_contato1_input = st.session_state.widget_nome_completo_input
    else:
        st.session_state.widget_contato1_input = ""

def load_whatsapp_icon_b64():
    """Retorna o ícone do WhatsApp em base64 (placeholder ou arquivo)."""
    # Ícone verde simples em base64 para evitar dependência de arquivo externo
    return "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAKDSURBVEiJvZZNTxtNEMf/M7ve9e4msYmD7YAsiZSQSAsSAnEq9ZByiS9A6pEPoHeOfAn7An0B9ZByS6mUIpSInS9ZAsSJQ9YmNuS1vrt7eqhDInYToK0vOdK8zPOfX808M0IphXfS6vX19f86YDAY9I6Pj98vLy8v+b7vU0r9VquV9Hq9pFKpRLVaLcnzPF8p5fM8z1NK+Z7n+Z7n+Z7n+f8VvMv5X4Gnp6e9er2e9Pv97unpaW9tbe3FxsZGL0kSAnAAUAFQSglKKRpj6Onpqbe0tPRifX29Z4yhd3Z21mOM9VqtVvL2XfD+/n6vXq8nnU6ne3Z21mvDGGOMIdZaG2MsjTFgjAFjDIwxNMaAMQaMMYfGGDmMMX61Wk12d3d75XL5eS8MBIDxePzZ8zzf8zzfd113RSmV8DwfjuPA8zz4vg+Hw+F5XnieB8/z4DhO8p3v+3AcB0mSIPX99S7P83ynX84YQ6vVSt6+u1AIsUopvVJKv0spP0spH0opHymlfimlXymlPkopH0spHymlP0spH0opHymlP0spvX+FEGJ1PB5/fP+Lg8Ggd3x8/P78/Pzd8fHxe6XU7/V6Sa/XSyqVSlSr1ZI8z/OVUj7P8zyllO95nu95nud5nud5nv9fwX8L1uv1pNPpdE9PT3tLS0svNjc3e0mSEIAHBMC9UopSimKM0RhDT05OvZWVlRdra2s9Ywy9s7OzHmOs12q1krfvgv/8061bt36cnp7O93o9VqlUmE6nS7vdfpEkSfpvXNf97Xneh+M46Tf7vv9D8n7Z9/0fb968Sf4B3u0H6pY0oFcAAAAASUVORK5CYII="

WHATSAPP_ICON = load_whatsapp_icon_b64()

# --- Interface ---
st.title('📝 Cadastro de Clientes')
st.write("Preencha os dados abaixo. O formulário se expandirá conforme você avança.")

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
                    
                    # Enriquecimento: Adiciona informações extras nas observações se existirem
                    situacao = cnpj_data.get('situacao_cadastral')
                    cnae = cnpj_data.get('cnae_principal')
                    if situacao or cnae:
                        extra_info = f"\n--- Dados da Receita Federal ---\nSituação: {situacao}\nAtividade: {cnae}"
                        st.session_state.widget_observacao_input += extra_info
                        if situacao == "ATIVA":
                            st.success(f"Empresa com situação **{situacao}** na Receita Federal.")
                        else:
                            st.warning(f"Atenção: Esta empresa está com situação **{situacao}**.")
                            
                    expand_section("contatos"); expand_section("cep"); expand_section("endereco"); expand_section("obs")
                except (ValueError, services.CnpjNotFoundError, requests.exceptions.RequestException) as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Erro na busca: {e}")
    
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

with st.expander("Passo 2: Contatos", expanded=st.session_state.expand_contatos):
    st.date_input('Data de Nascimento / Fundação', min_value=datetime.date(1900, 1, 1), key="widget_data_nascimento_input", format="DD/MM/YYYY")
    st.checkbox("Usar nome do cliente como Contato 1", key="widget_use_client_name_checkbox", on_change=handle_use_client_name_change)
    st.text_input("Nome do Contato 1", key="widget_contato1_input", disabled=st.session_state.widget_use_client_name_checkbox)
    st.text_input("Cargo do Contato 1", key="widget_cargo_input")
    st.markdown("---")
    st.text_input("Nome do Contato 2", key="widget_contato2_input")
    st.text_input('Telefone 2', key="widget_telefone2_input", on_change=lambda: expand_section("cep"))
    if WHATSAPP_ICON and st.session_state.widget_telefone2_input:
        st.markdown(f'<div style="text-align: right;"><a href="{validators.get_whatsapp_url(st.session_state.widget_telefone2_input)}" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a></div>', unsafe_allow_html=True)

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

with st.expander("Passo 5: Observações", expanded=st.session_state.expand_obs):
    st.text_area("Observações", height=150, max_chars=1000, key="widget_observacao_input")
    st.checkbox("Receber atualizações e novidades por e-mail", key="widget_receber_atualizacoes_checkbox", value=True)

st.markdown("---")

# Botões de Ação
col_submit, col_clear = st.columns(2)
with col_submit:
    if st.button('Salvar Cliente', type="primary", use_container_width=True):
        if not st.session_state.get("processing_submission", False): # Acesso seguro
            st.session_state.processing_submission = True
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
                'receber_atualizacoes': st.session_state.widget_receber_atualizacoes_checkbox,
            }

            # Constrói o endereço completo para geocodificação
            full_address = f"{customer_data['endereco']}, {customer_data['numero']}, {customer_data['bairro']}, {customer_data['cidade']}, {customer_data['estado']}"
            latitude, longitude = services.get_coords_for_address(full_address, customer_data['cep'])

            customer_data['latitude'] = latitude
            customer_data['longitude'] = longitude
            
            if latitude is None or longitude is None:
                st.warning("⚠️ Não foi possível localizar as coordenadas geográficas deste endereço. O cliente será salvo, mas não aparecerá no mapa.")

            try:
                customer_service.create_customer(customer_data)
                st.session_state.user_message = {"type": "success", "text": "Cliente salvo com sucesso!"}
                st.session_state.submission_success = True
            except (validators.ValidationError, DatabaseError) as e:
                st.session_state.user_message = {"type": "error", "text": f"Erro ao salvar: {e}"}
            except Exception as e:
                st.session_state.user_message = {"type": "error", "text": f"Ocorreu um erro inesperado: {e}"}
            finally:
                st.session_state.processing_submission = False # Resetar o flag
            st.rerun()

with col_clear:
    if st.button('Limpar Formulário', use_container_width=True):
        st.session_state.clear_form_requested = True # Define a flag para limpar na próxima execução
        st.rerun()

# Exibição de mensagens de feedback no final da página
if "user_message" in st.session_state:
    message = st.session_state.pop("user_message")
    if message["type"] == "success":
        st.success(message["text"], icon="✅")
    elif message["type"] == "error":
        st.error(message["text"], icon="🚨")