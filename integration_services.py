import logging
import streamlit as st
import requests
import re
import os
import json
import time

class CnpjNotFoundError(Exception):
    """Exceção para CNPJ não encontrado na API."""
    pass

def fetch_address_data(cep: str) -> dict | None:
    """Busca dados de um CEP no ViaCEP."""
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

@st.cache_data(ttl=3600)
def fetch_cnpj_data(cnpj: str) -> dict:
    """Busca dados de um CNPJ na BrasilAPI com lógica de re-tentativa (Retry)."""
    cnpj_cleaned = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj_cleaned) != 14:
        raise ValueError("CNPJ inválido. Deve conter 14 dígitos.")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_cleaned}", timeout=10)
            
            if response.status_code == 429: # Too Many Requests
                if attempt < max_retries - 1:
                    time.sleep(3 * (attempt + 1)) # Aumentado de 2s para 3s
                    continue
                else:
                    raise Exception("A API de CNPJ está sobrecarregada. Por favor, aguarde alguns segundos e tente novamente.")

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
                'cnpj': cnpj_cleaned,
                'situacao_cadastral': data.get("situacao_cadastral_texto", "N/A"),
                'cnae_principal': data.get("cnae_fiscal_descricao", "N/A")
            }
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)
    return {}

def get_coords_for_address(full_address: str, cep: str = None) -> tuple[float | None, float | None]:
    """Obtém coordenadas usando Nominatim com fallback para CEP."""
    if not full_address or not full_address.strip():
        return None, None

    # Tenta com endereço completo primeiro
    search_query = f"{full_address}, Brasil"
    params = {"q": search_query, "format": "json", "limit": 1}
    headers = {"User-Agent": "StreamlitCustomerApp/1.0 (https://github.com/felipegatoloko10)"}

    try:
        response = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data:
            return float(data[0].get("lat")), float(data[0].get("lon"))
        
        # Fallback: Tenta apenas pelo CEP se o endereço falhar
        if cep:
            logging.info(f"Endereço não encontrado, tentando fallback por CEP: {cep}")
            params["q"] = f"{cep}, Brasil"
            response = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers, timeout=10)
            data = response.json()
            if data:
                return float(data[0].get("lat")), float(data[0].get("lon"))

        logging.warning(f"Nominatim não encontrou coordenadas para: '{search_query}'")
        return None, None
    except Exception as e:
        logging.error(f"Erro ao buscar coordenadas: {e}")
        return None, None


def show_cloud_status():
    """Exibe o status da conexão com o Google Drive na sidebar."""
    import google_drive_service
    import os
    
    with st.sidebar:
        st.markdown("---")
        if os.path.exists(google_drive_service.TOKEN_FILE):
            st.markdown("🟢 **Nuvem:** Online")
            # Tenta mostrar o e-mail em um texto menor
            email = google_drive_service.get_authenticated_user_email()
            if email:
                st.caption(f"Conectado como {email}")
        else:
            st.markdown("🔴 **Nuvem:** Offline")
            st.caption("Conecte no menu Backup")
        st.markdown("---")

def send_new_customer_email(customer_data: dict, customer_id: int):
    """Envia um e-mail de notificação para o admin sobre um novo cliente cadastrado."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    email_config = {}
    config_file = 'email_config.json'

    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            email_config = json.load(f)
    
    if not email_config:
        if all(k in st.secrets for k in ["name", "key", "smtp_server", "smtp_port"]):
            email_config['sender_email'] = st.secrets["name"]
            email_config['password'] = st.secrets["key"]
            email_config['smtp_server'] = st.secrets["smtp_server"]
            email_config['smtp_port'] = st.secrets["smtp_port"]
    
    app_base_url = email_config.get("app_base_url") or st.secrets.get("app_base_url", "http://localhost:8501")

    required_keys = ['sender_email', 'password', 'smtp_server', 'smtp_port']
    if not all(key in email_config for key in required_keys):
        st.warning("Configurações de e-mail incompletas. Notificação não enviada.")
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = f"Novo Cliente: {customer_data.get('nome_completo')}"
    message["From"] = email_config['sender_email']
    message["To"] = email_config['sender_email']

    app_url = f"{app_base_url}/Banco_de_Dados?id={customer_id}"

    text_body = f"Novo cliente cadastrado: {customer_data.get('nome_completo')}. Link: {app_url}"
    html_body = f"<html><body><p>Novo cliente: <b>{customer_data.get('nome_completo')}</b></p><p><a href='{app_url}'>Ver Perfil</a></p></body></html>"

    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(email_config['smtp_server'], int(email_config['smtp_port'])) as server:
            server.starttls()
            server.login(email_config['sender_email'], email_config['password'])
            server.sendmail(email_config['sender_email'], email_config['sender_email'], message.as_string())
        st.toast("📧 Notificação enviada!")
    except Exception as e:
        st.warning(f"Erro ao enviar e-mail: {e}")