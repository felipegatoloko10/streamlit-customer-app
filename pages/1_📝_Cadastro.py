import streamlit as st
import datetime
import database
import validators
import time

# ... (funções de estado e callback mantidas como antes)
def initialize_session_state():
    if 'clear_trigger' not in st.session_state:
        st.session_state.clear_trigger = False

def clear_form():
    st.session_state.clear_trigger = True

def format_field_callback(field_name, formatter):
    if field_name in st.session_state and st.session_state[field_name]:
        st.session_state[field_name] = formatter(st.session_state[field_name])

# --- Inicialização ---
initialize_session_state()

if st.session_state.clear_trigger:
    st.session_state.clear_trigger = False
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith("input-")]
    for key in keys_to_clear:
        if key == "input-data_nascimento":
            st.session_state[key] = None
        else:
            st.session_state[key] = ""
    st.rerun()

# --- Configuração da Página ---
st.set_page_config(page_title="Cadastro de Clientes", page_icon="📝", layout="centered")
st.title('📝 Cadastro de Clientes')
st.markdown("Preencha os campos abaixo para registrar um novo cliente.")
st.markdown("---")


# --- Formulário com Layout Melhorado ---
with st.container(border=True):
    st.subheader("Dados Pessoais")
    col1, col2 = st.columns([2, 1])
    with col1:
        nome = st.text_input('Nome Completo *', key="input-nome_completo")
    with col2:
        cpf = st.text_input('CPF *', on_change=format_field_callback, args=('input-cpf', validators.format_cpf), key="input-cpf")

    col3, col4, col5 = st.columns(3)
    with col3:
        whatsapp = st.text_input('WhatsApp', on_change=format_field_callback, args=('input-whatsapp', validators.format_whatsapp), key="input-whatsapp")
    with col4:
        email = st.text_input('E-mail', key="input-email")
    with col5:
        data_nascimento = st.date_input('Data de Nascimento', value=None, min_value=datetime.date(1900, 1, 1), key="input-data_nascimento")
    
    st.subheader("Endereço")
    col6, col7 = st.columns([1, 3])
    with col6:
        cep = st.text_input('CEP', key="input-cep")
    with col7:
        endereco = st.text_input('Endereço', key="input-endereco")
    
    col8, col9, col10 = st.columns([1, 1, 2])
    with col8:
        numero = st.text_input('Número', key="input-numero")
    with col9:
        complemento = st.text_input('Complemento', key="input-complemento")
    with col10:
        bairro = st.text_input('Bairro', key="input-bairro")

    col11, col12 = st.columns([2, 1])
    with col11:
        cidade = st.text_input('Cidade', key="input-cidade")
    with col12:
        estado = st.text_input('UF', max_chars=2, key="input-estado")


st.markdown("---")
submit_button = st.button('Salvar Cliente', type="primary", use_container_width=True)
message_placeholder = st.empty()

# --- Lógica de Submissão ---
if submit_button:
    form_data = {
        'nome_completo': nome, 'cpf': cpf, 'whatsapp': whatsapp, 'email': email,
        'data_nascimento': data_nascimento, 'cep': cep, 'endereco': endereco, 'numero': numero,
        'complemento': complemento, 'bairro': bairro, 'cidade': cidade, 'estado': estado,
    }
    customer_data = {k: v for k, v in form_data.items() if v or k == 'complemento'}
    
    try:
        if not customer_data.get('nome_completo') or not customer_data.get('cpf'):
            raise validators.ValidationError("Os campos 'Nome Completo' e 'CPF' são obrigatórios.")
        validators.is_valid_cpf(customer_data['cpf'])
        if customer_data.get('whatsapp'):
            validators.is_valid_whatsapp(customer_data['whatsapp'])
        if customer_data.get('email'):
            validators.is_valid_email(customer_data['email'])

        if 'data_nascimento' in customer_data and customer_data['data_nascimento']:
            customer_data['data_nascimento'] = customer_data['data_nascimento'].strftime('%Y-%m-%d')
        
        database.insert_customer(customer_data)
        
        message_placeholder.success("Cliente salvo com sucesso! O formulário será limpo em instantes.")
        clear_form()
        time.sleep(2)
        st.rerun()

    except validators.ValidationError as e:
        message_placeholder.error(f"Erro de validação: {e}")
    except database.DatabaseError as e:
        message_placeholder.error(f"Erro no banco de dados: {e}")
    except Exception as e:
        message_placeholder.error("Ocorreu um erro inesperado.")
        st.exception(e)