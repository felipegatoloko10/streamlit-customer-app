import pytest
from unittest.mock import patch
import validators

def test_format_cpf():
    assert validators.format_cpf("12345678901") == "123.456.789-01"
    assert validators.format_cpf("123.456.789-01") == "123.456.789-01"

@patch('validators.CPF.validate')
def test_is_valid_cpf(mock_validate):
    mock_validate.return_value = True
    assert validators.is_valid_cpf("123.456.789-00") is True

@patch('validators.CPF.validate')
def test_is_valid_cpf_invalid(mock_validate):
    mock_validate.return_value = False
    with pytest.raises(validators.CPFValueError):
        validators.is_valid_cpf("111.111.111-11")

def test_format_whatsapp():
    assert validators.format_whatsapp("11987654321") == "(11) 98765-4321"
    assert validators.format_whatsapp("1187654321") == "(11) 8765-4321"

def test_is_valid_whatsapp():
    assert validators.is_valid_whatsapp("11987654321") is True
    assert validators.is_valid_whatsapp("1187654321") is True

def test_is_valid_whatsapp_invalid_ddd():
    with pytest.raises(validators.WhatsAppValueError):
        validators.is_valid_whatsapp("01987654321")

def test_is_valid_whatsapp_invalid_length():
    with pytest.raises(validators.WhatsAppValueError):
        validators.is_valid_whatsapp("119876543") # 9 digits
    with pytest.raises(validators.WhatsAppValueError):
        validators.is_valid_whatsapp("119876543210") # 12 digits

def test_is_valid_email():
    assert validators.is_valid_email("test@example.com") is True

def test_is_valid_email_invalid():
    with pytest.raises(validators.EmailValueError):
        validators.is_valid_email("not-an-email")
    with pytest.raises(validators.EmailValueError):
        validators.is_valid_email("")
