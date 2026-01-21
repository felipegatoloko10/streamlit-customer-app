import streamlit as st
import requests
import re

def fetch_address_data(cep, form_data):
    cep_cleaned = re.sub(r'[^0-9]', '', cep)
    if len(cep_cleaned) != 8:
        st.session_state.cep_notification = {"type": "error", "message": "CEP inválido. Deve conter 8 dígitos."}
        return
    try:
        with st.spinner("Buscando CEP..."):
            response = requests.get(f"https://viacep.com.br/ws/{cep_cleaned}/json/", timeout=5)
            response.raise_for_status()
            data = response.json()
        if data.get("erro"):
            st.session_state.cep_notification = {"type": "warning", "message": "CEP não encontrado. Por favor, preencha o endereço manualmente."}
        else:
            st.session_state.cep_notification = {"type": "success", "message": "Endereço encontrado!"}
            form_data['endereco'] = data.get("logradouro", "")
            form_data['bairro'] = data.get("bairro", "")
            form_data['cidade'] = data.get("localidade", "")
            form_data['estado'] = data.get("uf", "")
    except requests.exceptions.RequestException as e:
        st.session_state.cep_notification = {"type": "error", "message": f"Erro de rede ao buscar o CEP: {e}"}

def fetch_cnpj_data(cnpj, form_data):
    """Busca dados de um CNPJ na BrasilAPI e atualiza o estado do formulário."""
    cnpj_cleaned = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj_cleaned) != 14:
        st.session_state.form_error = "CNPJ inválido. Deve conter 14 dígitos."
        return

    try:
        with st.spinner("Buscando dados do CNPJ..."):
            response = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_cleaned}", timeout=10)
            # A BrasilAPI retorna 404 para CNPJ não encontrado, o que causa um HTTPError
            if response.status_code == 404:
                st.session_state.form_error = f"CNPJ não encontrado ou inválido: {cnpj}"
                return
            response.raise_for_status()
            data = response.json()

        # Atualiza os campos do formulário no form_data
        form_data['nome_completo'] = data.get("razao_social", "")
        form_data['email'] = data.get("email", "")
        form_data['telefone1'] = data.get("ddd_telefone_1", "")
        
        # Preenche o endereço
        form_data['cep'] = data.get("cep", "")
        form_data['endereco'] = data.get("logradouro", "")
        form_data['numero'] = data.get("numero", "")
        form_data['complemento'] = data.get("complemento", "")
        form_data['bairro'] = data.get("bairro", "")
        form_data['cidade'] = data.get("municipio", "")
        form_data['estado'] = data.get("uf", "")

        st.toast("Dados do CNPJ preenchidos com sucesso!", icon="✅")

    except requests.exceptions.RequestException as e:
        st.session_state.form_error = f"Erro de rede ao buscar o CNPJ: {e}"
    except Exception as e:
        st.session_state.form_error = f"Ocorreu um erro inesperado ao processar os dados do CNPJ: {e}"

def send_new_customer_email(customer_data: dict, customer_id: int):
    """Envia um e-mail de notificação para o admin sobre um novo cliente cadastrado."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    # --- Verifica se os segredos para o e-mail estão configurados ---
    required_secrets = ["name", "key", "app_base_url"]
    if not all(k in st.secrets for k in required_secrets):
        st.warning("As credenciais de e-mail ('name', 'key') e a URL base do app ('app_base_url') não foram configuradas nos Segredos do Streamlit. A notificação não será enviada.")
        return

    sender_email = st.secrets["name"]
    password = st.secrets["key"]
    app_base_url = st.secrets["app_base_url"]
    receiver_email = sender_email # Envia o e-mail para si mesmo

    # --- Monta o corpo do e-mail ---
    message = MIMEMultipart("alternative")
    message["Subject"] = f"Novo Cliente Cadastrado: {customer_data.get('nome_completo')}"
    message["From"] = sender_email
    message["To"] = receiver_email

    # Constrói a URL do App com a base vinda dos secrets
    app_url = f"{app_base_url}/Banco_de_Dados?id={customer_id}"

    text_body = f"""
    Um novo cliente foi cadastrado no sistema.

    Nome: {customer_data.get('nome_completo')}
    Documento: {customer_data.get('cpf') or customer_data.get('cnpj')}
    Telefone: {customer_data.get('telefone1')}
    E-mail: {customer_data.get('email')}
    Cidade: {customer_data.get('cidade')} - {customer_data.get('estado')}

    Acesse o perfil do cliente diretamente pelo link: {app_url}
    """

    html_body = f"""
    <html>
    <body>
        <p>Um novo cliente foi cadastrado no sistema.</p>
        <h3>Dados do Cliente:</h3>
        <ul>
            <li><strong>Nome:</strong> {customer_data.get('nome_completo')}</li>
            <li><strong>Documento:</strong> {customer_data.get('cpf') or customer_data.get('cnpj')}</li>
            <li><strong>Telefone:</strong> {customer_data.get('telefone1')}</li>
            <li><strong>E-mail:</strong> {customer_data.get('email')}</li>
            <li><strong>Local:</strong> {customer_data.get('cidade')} - {customer_data.get('estado')}</li>
        </ul>
        <p>
            <a href="{app_url}" style="background-color: #0068c9; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                Ver Perfil do Cliente no App
            </a>
        </p>
    </body>
    </html>
    """

    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    # --- Envia o e-mail ---
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        st.toast("📧 E-mail de notificação enviado com sucesso!")
    except Exception as e:
        # Não trava a aplicação se o e-mail falhar, apenas avisa.
        st.warning(f"Ocorreu um erro ao enviar o e-mail de notificação: {e}")


