import re
from validate_docbr import CPF

def format_cpf(cpf: str) -> str:
    """Formata uma string de CPF para o formato XXX.XXX.XXX-XX."""
    cpf_cleaned = re.sub(r'[^0-9]', '', cpf)
    if len(cpf_cleaned) == 11:
        return f'{cpf_cleaned[:3]}.{cpf_cleaned[3:6]}.{cpf_cleaned[6:9]}-{cpf_cleaned[9:]}'
    return cpf

def is_valid_cpf(cpf: str) -> bool:
    """Verifica se um CPF é válido usando a biblioteca validate_docbr."""
    cpf_validator = CPF()
    return cpf_validator.validate(cpf)

def format_whatsapp(whatsapp: str) -> str:
    """Formata um número de WhatsApp para (XX) XXXXX-XXXX."""
    whatsapp_cleaned = re.sub(r'[^0-9]', '', whatsapp)
    if len(whatsapp_cleaned) == 11:
        return f'({whatsapp_cleaned[:2]}) {whatsapp_cleaned[2:7]}-{whatsapp_cleaned[7:]}'
    if len(whatsapp_cleaned) == 10:
        return f'({whatsapp_cleaned[:2]}) {whatsapp_cleaned[2:6]}-{whatsapp_cleaned[6:]}'
    return whatsapp

def is_valid_whatsapp(whatsapp: str) -> bool:
    """Verifica se o número de WhatsApp contém 10 ou 11 dígitos numéricos."""
    whatsapp_cleaned = re.sub(r'[^0-9]', '', whatsapp)
    return 10 <= len(whatsapp_cleaned) <= 11

def is_valid_email(email: str) -> bool:
    """Verifica se o formato do e-mail é válido."""
    # Regex simples para validação de e-mail
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None
