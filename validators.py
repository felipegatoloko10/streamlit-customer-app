import re
from validate_docbr import CPF, CNPJ
from email_validator import validate_email, EmailNotValidError

cpf_validator = CPF()
cnpj_validator = CNPJ()

class ValidationError(Exception):
    """Exceção base para erros de validação."""
    pass

class CPFValueError(ValidationError):
    """Exceção para CPF inválido."""
    pass

class CNPJValueError(ValidationError):
    """Exceção para CNPJ inválido."""
    pass

class WhatsAppValueError(ValidationError):
    """Exceção para WhatsApp inválido."""
    pass

class EmailValueError(ValidationError):
    """Exceção para E-mail inválido."""
    pass


def format_cpf(cpf: str) -> str:
    """Formata uma string de CPF para o formato XXX.XXX.XXX-XX."""
    if not cpf:
        return ""
    cpf_cleaned = re.sub(r'[^0-9]', '', cpf)
    if len(cpf_cleaned) == 11:
        return f'{cpf_cleaned[:3]}.{cpf_cleaned[3:6]}.{cpf_cleaned[6:9]}-{cpf_cleaned[9:]}'
    return cpf_cleaned # Retorna a string limpa se não for possível formatar

def is_valid_cpf(cpf: str) -> bool:
    """Verifica se um CPF é válido. Lança CPFValueError se inválido."""
    if not cpf_validator.validate(cpf):
        raise CPFValueError("O CPF informado é inválido.")
    return True

def format_cnpj(cnpj: str) -> str:
    """Formata uma string de CNPJ para o formato XX.XXX.XXX/XXXX-XX."""
    if not cnpj:
        return ""
    cnpj_cleaned = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj_cleaned) == 14:
        return f'{cnpj_cleaned[:2]}.{cnpj_cleaned[2:5]}.{cnpj_cleaned[5:8]}/{cnpj_cleaned[8:12]}-{cnpj_cleaned[12:]}'
    return cnpj_cleaned # Retorna a string limpa se não for possível formatar

def is_valid_cnpj(cnpj: str) -> bool:
    """Verifica se um CNPJ é válido. Lança CNPJValueError se inválido."""
    if not cnpj_validator.validate(cnpj):
        raise CNPJValueError("O CNPJ informado é inválido.")
    return True

def format_whatsapp(whatsapp: str) -> str:
    """Formata um número de WhatsApp para (XX) XXXXX-XXXX."""
    if not whatsapp:
        return ""
    whatsapp_cleaned = re.sub(r'[^0-9]', '', whatsapp)
    if len(whatsapp_cleaned) == 11:
        return f'({whatsapp_cleaned[:2]}) {whatsapp_cleaned[2:7]}-{whatsapp_cleaned[7:]}'
    if len(whatsapp_cleaned) == 10:
        return f'({whatsapp_cleaned[:2]}) {whatsapp_cleaned[2:6]}-{whatsapp_cleaned[6:]}'
    return whatsapp_cleaned # Retorna a string limpa se não for possível formatar

def is_valid_whatsapp(whatsapp: str) -> bool:
    # ... (função mantida como antes)
    whatsapp_cleaned = re.sub(r'[^0-9]', '', whatsapp)
    
    if not 10 <= len(whatsapp_cleaned) <= 11:
        raise WhatsAppValueError("O número de WhatsApp deve conter 10 ou 11 dígitos.")

    # Removida validação estática de DDD para permitir novos códigos de área da ANATEL.
        
    return True

def is_valid_email(email: str) -> bool:
    if not email:
        return True
    
    # Lista básica de domínios temporários para evitar "trash data"
    disposable_domains = [
        "mailinator.com", "yopmail.com", "tempmail.com", "10minutemail.com", 
        "guerrillamail.com", "sharklasers.com", "getnada.com"
    ]
    
    domain = email.split('@')[-1].lower() if '@' in email else ""
    if domain in disposable_domains:
        raise EmailValueError(f"O domínio '{domain}' é de uso temporário e não é permitido.")

    try:
        # Desativa a verificação de DNS para agilizar, mas valida o formato rigorosamente
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError as e:
        raise EmailValueError(f"O formato do e-mail é inválido: {e}")

def get_whatsapp_url(whatsapp: str) -> str:
    """Gera uma URL de WhatsApp (wa.me) a partir de um número de telefone."""
    if not whatsapp:
        return ""
    # Remove todos os caracteres não numéricos e adiciona o código do país (Brasil)
    whatsapp_cleaned = re.sub(r'[^0-9]', '', whatsapp)
    if len(whatsapp_cleaned) >= 10:
        return f"https://wa.me/55{whatsapp_cleaned}"
    return "" # Retorna vazio se o número for inválido

def unformat_cpf(cpf: str) -> str:
    """Remove a formatação de uma string de CPF."""
    if not cpf:
        return ""
    return re.sub(r'[^0-9]', '', cpf)

def unformat_cnpj(cnpj: str) -> str:
    """Remove a formatação de uma string de CNPJ."""
    if not cnpj:
        return ""
    return re.sub(r'[^0-9]', '', cnpj)

def unformat_whatsapp(whatsapp: str) -> str:
    """Remove a formatação de uma string de WhatsApp."""
    if not whatsapp:
        return ""
    return re.sub(r'[^0-9]', '', whatsapp)

