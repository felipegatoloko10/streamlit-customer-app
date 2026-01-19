import streamlit as st
import datetime
import database
import validators
import requests
import re

st.set_page_config(page_title="Cadastro de Clientes", page_icon="📝", layout="centered")

# --- Funções ---

import services

def clear_form_inputs():
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith("form_") or k == "cep_input"]
    for key in keys_to_clear:
        if "data_nascimento" in key:
            st.session_state[key] = None
        elif "tipo_documento" in key:
            st.session_state[key] = "CPF"
        elif "use_client_name" in key:
            st.session_state[key] = False
        else:
            st.session_state[key] = ""

# --- Lógica para o botão 'Usar nome do cliente' ---
if st.session_state.get("use_client_name_for_contact", False):
    st.session_state.form_contato1 = st.session_state.get("form_nome", "")
    st.session_state.use_client_name_for_contact = False

# --- Carrega o ícone do WhatsApp ---
WHATSAPP_ICON = services.load_whatsapp_icon_b64()

# --- Lógica para atualizar o CEP vindo da busca de CNPJ ---
if "cep_from_cnpj" in st.session_state:
    st.session_state.cep_input = st.session_state.pop("cep_from_cnpj")

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
            services.fetch_address_data(cep_input)
            st.rerun()

st.markdown("---")

# Use a container to group the selector and the form
with st.container(border=True):
    # This radio button is now OUTSIDE the form. Its change will trigger a rerun.
    st.subheader("Dados Principais")
    _, col2 = st.columns([2, 1])
    with col2:
        tipo_documento = st.radio(
            "Tipo de Documento", 
            ["CPF", "CNPJ"], 
            horizontal=True, 
            key="form_tipo_documento",
            label_visibility="collapsed" # The subheader acts as the label
        )

    # We read the value from session state to determine the label
    tipo_selecionado = st.session_state.get("form_tipo_documento", "CPF")
    
    # --- Lógica de Busca de CNPJ (fora do formulário principal) ---
    if tipo_selecionado == "CNPJ":
        with st.container():
            col_cnpj_input, col_cnpj_btn = st.columns([0.7, 0.3])
            with col_cnpj_input:
                # Usamos uma chave diferente para o input de CNPJ na busca para não conflitar com o do formulário
                cnpj_to_search = st.text_input("CNPJ para busca", key="cnpj_search_input", label_visibility="collapsed", placeholder="Digite o CNPJ para buscar dados")
            with col_cnpj_btn:
                if st.button("🔎 Buscar CNPJ", use_container_width=True):
                    # O valor do input do CNPJ do formulário é atualizado com o valor da busca
                    st.session_state.form_documento = cnpj_to_search
                    services.fetch_cnpj_data(cnpj_to_search)
                    st.rerun()
        st.markdown("---")


    with st.form(key="new_customer_form", clear_on_submit=False):
        nome = st.text_input('Nome Completo / Razão Social *', key="form_nome")

        label_documento = "CPF *" if tipo_selecionado == "CPF" else "CNPJ *"
        documento = st.text_input(label_documento, key="form_documento")

        col_email, col_data = st.columns(2)
        with col_email:
            email = st.text_input('E-mail', key="form_email")
        with col_data:
            data_nascimento = st.date_input('Data de Nascimento / Fundação', value=None, min_value=datetime.date(1900, 1, 1), key="form_data_nascimento")

        with st.expander("Contatos"):
            use_client_name = st.checkbox("Usar nome do cliente como Contato 1", key="form_use_client_name")
            
            if use_client_name:
                # Mostra o nome do cliente em um campo desabilitado
                st.text_input("Nome do Contato 1", value=nome, disabled=True)
                # Salva o nome do cliente no estado do contato para consistência
                contato1 = nome
            else:
                # Mostra o campo de input normal
                contato1 = st.text_input("Nome do Contato 1", key="form_contato1")

            col_tel1, col_icon1, col_cargo = st.columns([0.45, 0.1, 0.45])
            with col_tel1:
                telefone1 = st.text_input('Telefone 1', key="form_telefone1")
            with col_icon1:
                if WHATSAPP_ICON:
                    st.markdown("##") # Espaçador para alinhar
                    st.markdown(f'<a href="#" id="whatsapp-link-1" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a>', unsafe_allow_html=True)
            with col_cargo:
                cargo = st.text_input("Cargo do Contato 1", key="form_cargo")

            st.markdown("---")

            col6, col_icon2, col7 = st.columns([0.8, 0.1, 0.1])
            with col6:
                contato2 = st.text_input("Nome do Contato 2", key="form_contato2")
            with col_icon2:
                 if WHATSAPP_ICON:
                    st.markdown("##") # Espaçador
                    st.markdown(f'<a href="#" id="whatsapp-link-2" target="_blank"><img src="data:image/png;base64,{WHATSAPP_ICON}" width="25"></a>', unsafe_allow_html=True)
            with col7:
                telefone2 = st.text_input('Telefone 2', key="form_telefone2")

        # --- Injeção de JavaScript para links dinâmicos ---
        # Este script é uma solução alternativa e pode quebrar em futuras versões do Streamlit
        js_code = """
        <script>
        function setupWhatsAppLink(inputAriaLabel, linkId) {
            const phoneInput = document.querySelector(`input[aria-label='${inputAriaLabel}']`);
            const whatsappLink = document.getElementById(linkId);

            if (phoneInput && whatsappLink) {
                const updateLink = () => {
                    let phoneValue = phoneInput.value.replace(/[^0-9]/g, '');
                    if (phoneValue.length >= 10) {
                        whatsappLink.href = `https://wa.me/55${phoneValue}`;
                    } else {
                        whatsappLink.href = '#';
                    }
                };
                
                phoneInput.addEventListener('keyup', updateLink);
                // Atualiza o link na carga inicial também
                updateLink();
            }
        }

        // Garante que o script rode após a renderização dos elementos
        setTimeout(() => {
            setupWhatsAppLink('Telefone 1', 'whatsapp-link-1');
            setupWhatsAppLink('Telefone 2', 'whatsapp-link-2');
        }, 500);
        </script>
        """
        st.components.v1.html(js_code, height=0)

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
        submit_button = st.form_submit_button('Salvar Cliente', type="primary", width='stretch')

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