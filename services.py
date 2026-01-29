import streamlit as st
import requests
import re
import os
import json

class CnpjNotFoundError(Exception):
    """Exceção para CNPJ não encontrado na API."""
    pass

def fetch_address_data(cep: str) -> dict | None:
    """Busca dados de um CEP no ViaCEP.

    Args:
        cep: O CEP a ser buscado (pode conter máscara).

    Returns:
        Um dicionário com os dados do endereço em caso de sucesso,
        None se o CEP não for encontrado.
    
    Raises:
        ValueError: Se o formato do CEP for inválido.
        requests.exceptions.RequestException: Em caso de erro de rede.
    """
    cep_cleaned = re.sub(r'[^0-9]', '', cep)
    if len(cep_cleaned) != 8:
        raise ValueError("CEP inválido. Deve conter 8 dígitos.")
    
    response = requests.get(f"https://viacep.com.br/ws/{cep_cleaned}/json/", timeout=5)
    response.raise_for_status()
    data = response.json()

    if data.get("erro"):
        return None
    
    return {
        'endereco': data.get("logradouro", ""),
        'bairro': data.get("bairro", ""),
        'cidade': data.get("localidade", ""),
        'estado': data.get("uf", "")
    }

def fetch_cnpj_data(cnpj: str) -> dict:
    """Busca dados de um CNPJ na BrasilAPI.

    Args:
        cnpj: O CNPJ a ser buscado (pode conter máscara).

    Returns:
        Um dicionário com os dados da empresa.
    
    Raises:
        ValueError: Se o formato do CNPJ for inválido.
        CnpjNotFoundError: Se o CNPJ não for encontrado na BrasilAPI (erro 404).
        requests.exceptions.RequestException: Em caso de outros erros de rede.
    """
    cnpj_cleaned = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj_cleaned) != 14:
        raise ValueError("CNPJ inválido. Deve conter 14 dígitos.")

    try:
        response = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_cleaned}", timeout=10)
        
        if response.status_code == 404:
            raise CnpjNotFoundError(f"CNPJ não encontrado ou inválido: {cnpj_cleaned}")
        
        response.raise_for_status()
        data = response.json()

        return {
            'nome_completo': data.get("razao_social", ""),
            'email': data.get("email", ""),
            'telefone1': data.get("ddd_telefone_1", ""),
            'cep': data.get("cep", ""),
            'endereco': data.get("logradouro", ""),
            'numero': data.get("numero", ""),
            'complemento': data.get("complemento", ""),
            'bairro': data.get("bairro", ""),
            'cidade': data.get("municipio", ""),
            'estado': data.get("uf", ""),
            # Corrigido: a função original tinha um bug e não retornava o documento.
            'cnpj': cnpj_cleaned
        }
    except requests.exceptions.RequestException:
        # Re-levanta a exceção para ser tratada pela camada de UI
        raise

def send_new_customer_email(customer_data: dict, customer_id: int):
    """Envia um e-mail de notificação para o admin sobre um novo cliente cadastrado."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    email_config = {}
    config_file = 'email_config.json'

    # 1. Tenta carregar a configuração do arquivo JSON
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            email_config = json.load(f)
    
    # 2. Se não encontrou no JSON, tenta carregar dos segredos do Streamlit
    if not email_config:
        if all(k in st.secrets for k in ["name", "key", "smtp_server", "smtp_port"]):
            email_config['sender_email'] = st.secrets["name"]
            email_config['password'] = st.secrets["key"]
            email_config['smtp_server'] = st.secrets["smtp_server"]
            email_config['smtp_port'] = st.secrets["smtp_port"]
    
    # Pega a URL base de qualquer uma das fontes
    app_base_url = email_config.get("app_base_url") or st.secrets.get("app_base_url", "http://localhost:8501") # Fallback para localhost

    # 3. Verifica se tem as credenciais necessárias
    required_keys = ['sender_email', 'password', 'smtp_server', 'smtp_port']
    if not all(key in email_config for key in required_keys):
        st.warning("As configurações de e-mail (remetente, senha, servidor, porta) não foram configuradas. A notificação não será enviada.")
        return

    # --- Monta o corpo do e-mail ---
    message = MIMEMultipart("alternative")
    message["Subject"] = f"Novo Cliente Cadastrado: {customer_data.get('nome_completo')}"
    message["From"] = email_config['sender_email']
    message["To"] = email_config['sender_email'] # Envia para si mesmo

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
        with smtplib.SMTP(email_config['smtp_server'], int(email_config['smtp_port'])) as server:
            server.starttls()
            server.login(email_config['sender_email'], email_config['password'])
            server.sendmail(email_config['sender_email'], email_config['sender_email'], message.as_string())
        st.toast("📧 E-mail de notificação enviado com sucesso!")
    except Exception as e:
        # Não trava a aplicação se o e-mail falhar, apenas avisa.
        st.warning(f"Ocorreu um erro ao enviar o e-mail de notificação: {e}")


