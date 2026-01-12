import streamlit as st
import datetime
import database
import validators

# --- Inicialização do Session State ---
if 'form_values' not in st.session_state:
    st.session_state['form_values'] = {
        'nome_completo': '', 'cpf': '', 'whatsapp': '', 'email': '', 
        'data_nascimento': None, 'cep': '', 'endereco': '', 'numero': '', 
        'complemento': '', 'bairro': '', 'cidade': '', 'estado': ''
    }

# --- Funções de Callback ---
def format_field_callback(field_name, formatter):
    if field_name in st.session_state:
        current_value = st.session_state[field_name]
        st.session_state.form_values[field_name] = formatter(current_value)

# --- Configuração da Página ---
st.set_page_config(page_title="Cadastro de Clientes", page_icon="📝")
st.title('Cadastro de Clientes')

# --- Inputs do Formulário ---
form = st.session_state.form_values
st.header("Dados Pessoais")
form['nome_completo'] = st.text_input('Nome Completo', value=form['nome_completo'], key='nome_completo')
form['cpf'] = st.text_input('CPF', value=form['cpf'], key='cpf', on_change=format_field_callback, args=('cpf', validators.format_cpf))
form['whatsapp'] = st.text_input('WhatsApp (com DDD)', value=form['whatsapp'], key='whatsapp', on_change=format_field_callback, args=('whatsapp', validators.format_whatsapp))
form['email'] = st.text_input('E-mail', value=form['email'], key='email')
form['data_nascimento'] = st.date_input('Data de Nascimento', min_value=datetime.date(1900, 1, 1), value=form['data_nascimento'], key='data_nascimento')

st.header("Endereço")
form['cep'] = st.text_input('CEP', value=form['cep'], key='cep')
form['endereco'] = st.text_input('Endereço', value=form['endereco'], key='endereco')
form['numero'] = st.text_input('Número', value=form['numero'], key='numero')
form['complemento'] = st.text_input('Complemento', value=form['complemento'], key='complemento')
form['bairro'] = st.text_input('Bairro', value=form['bairro'], key='bairro')
form['cidade'] = st.text_input('Cidade', value=form['cidade'], key='cidade')
form['estado'] = st.text_input('Estado (UF)', value=form['estado'], max_chars=2, key='estado')

st.markdown("---")

message_placeholder = st.empty()

# --- Lógica de Submissão ---
if st.button('Salvar Cliente', type="primary", use_container_width=True):
    final_form_values = st.session_state.form_values

    if not final_form_values['nome_completo'] or not final_form_values['cpf']:
        message_placeholder.error("Os campos 'Nome Completo' e 'CPF' são obrigatórios.")
    else:
        customer_data_to_insert = {k: v for k, v in final_form_values.items() if v or k == 'complemento'}
        if final_form_values['data_nascimento']:
            customer_data_to_insert['data_nascimento'] = final_form_values['data_nascimento'].strftime('%Y-%m-%d')
        
        success, error_message = database.insert_customer(customer_data_to_insert)
        
        if success:
            message_placeholder.success("Cliente salvo com sucesso!")
            # CORREÇÃO: Lógica de limpeza do formulário ajustada
            for key in st.session_state.form_values:
                if key == 'data_nascimento':
                    st.session_state.form_values[key] = None # Garante que o campo de data receba None
                else:
                    st.session_state.form_values[key] = '' # Outros campos recebem string vazia
            
            import time
            time.sleep(2)
            st.rerun()
        else:
            message_placeholder.error(f"Erro ao salvar: {error_message}")

# Este bloco pode ser removido ou mantido para casos de uso mais complexos,
# mas a lógica principal agora está acima.
if 'submission_status' in st.session_state:
    status = st.session_state.submission_status
    if status.get('success'):
        message_placeholder.success(status['message'])
    else:
        message_placeholder.error(status['message'])
    del st.session_state.submission_status