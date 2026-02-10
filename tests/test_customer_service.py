import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlmodel import Session, create_engine, SQLModel
from datetime import date
from services.customer_service import CustomerService
from models import Cliente, Contato, Endereco
from repositories.customer_repository import CustomerRepository


@pytest.fixture
def db_session():
    """Fixture que cria uma sessão de banco de dados em memória para testes."""
    engine = create_engine("sqlite:///:memory:")
    SQL Model.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def customer_service():
    """Fixture que cria uma instância do CustomerService."""
    return CustomerService()


class TestCustomerService:
    """Testes para CustomerService."""

    def test_sanitize_data(self, customer_service):
        """Testa a sanitização de dados."""
        raw_data = {
            "nome_completo": "  joão  da   silva  ",
            "cidade": " são paulo ",
            "estado": "sp",
            "cep": "01234-567"
        }
        
        sanitized = customer_service._sanitize_data(raw_data)
        
        assert sanitized["nome_completo"] == "João Da Silva"
        assert sanitized["cidade"] == "São Paulo"
        assert sanitized["estado"] == "SP"
        assert sanitized["cep"] == "01234567"

    def test_validate_cliente_data_cpf(self, customer_service):
        """Testa a validação de dados do cliente com CPF."""
        with patch('validators.is_valid_cpf') as mock_cpf:
            mock_cpf.return_value = True
            
            data = {
                "nome_completo": "João da Silva",
                "tipo_documento": "CPF",
                "cpf": "12345678900"
            }
            
            # Não deve lançar exceção
            customer_service._validate_cliente_data(data)
            mock_cpf.assert_called_once_with("12345678900")

    def test_validate_cliente_data_missing_name(self, customer_service):
        """Testa a validação com nome faltando."""
        from validators import ValidationError
        
        data = {
            "tipo_documento": "CPF",
            "cpf": "12345678900"
        }
        
        with pytest.raises(ValidationError):
            customer_service._validate_cliente_data(data)

    @patch('services.customer_service.CustomerRepository')
    @patch('integration_services.send_new_customer_email')
    @patch('backup_manager.increment_and_check_backup')
    def test_create_customer_success(self, mock_backup, mock_email, mock_repo_class, customer_service):
        """Testa a criação bem-sucedida de um cliente."""
        # Mock do repositório
        mock_repo = Mock()
        mock_repo.create_customer.return_value = Cliente(
            id=1,
            nome_completo="João Da Silva",
            tipo_documento="CPF",
            cpf="12345678900"
        )
        mock_repo_class.return_value = mock_repo
        
        # Mock da validação
        with patch.object(customer_service, '_validate_cliente_data'):
            data = {
                "nome_completo": "joão da silva",
                "tipo_documento": "CPF",
                "cpf": "123.456.789-00",
                "contato1": "João",
                "telefone1": "(11) 99999-9999",
                "endereco": "Rua Exemplo",
                "numero": "123",
                "cidade": "São Paulo",
                "estado": "SP"
            }
            
            result = customer_service.create_customer(data)
            
            assert result.id == 1
            assert result.nome_completo == "João Da Silva"
            mock_repo.create_customer.assert_called_once()
            mock_email.assert_called_once()
            mock_backup.assert_called_once()

    @patch('services.customer_service.CustomerRepository')
    def test_update_customer(self, mock_repo_class, customer_service):
        """Testa a atualização de um cliente."""
        mock_repo = Mock()
        mock_repo.update_customer.return_value = Cliente(
            id=1,
            nome_completo="João Silva Atualizado",
            tipo_documento="CPF",
            cpf="12345678900"
        )
        mock_repo_class.return_value = mock_repo
        
        data = {
            "nome_completo": "joão silva atualizado",
            "observacao": "Cliente VIP"
        }
        
        result = customer_service.update_customer(1, data)
        
        assert result.nome_completo == "João Silva Atualizado"
        mock_repo.update_customer.assert_called_once()

    @patch('services.customer_service.CustomerRepository')
    def test_delete_customer(self, mock_repo_class, customer_service):
        """Testa a exclusão de um cliente."""
        mock_repo = Mock()
        mock_repo.delete_customer.return_value = True
        mock_repo_class.return_value = mock_repo
        
        result = customer_service.delete_customer(1)
        
        assert result is True
        mock_repo.delete_customer.assert_called_once_with(1)

    @patch('services.customer_service.CustomerRepository')
    def test_get_customer_grid_data(self, mock_repo_class, customer_service):
        """Testa a obtenção de dados formatados para o grid."""
        mock_repo = Mock()
        mock_cliente = Cliente(
            id=1,
            nome_completo="João da Silva",
            tipo_documento="CPF",
            cpf="12345678900",
            data_cadastro=date.today()
        )
        mock_cliente.contatos = [
            Contato(
                nome_contato="João",
                telefone="11999999999",
                email_contato="joao@example.com",
                tipo_contato="Principal"
            )
        ]
        mock_cliente.enderecos = [
            Endereco(
                logradouro="Rua Exemplo",
                numero="123",
                cidade="São Paulo",
                estado="SP",
                tipo_endereco="Principal"
            )
        ]
        
        mock_repo.list_customers.return_value = [mock_cliente]
        mock_repo_class.return_value = mock_repo
        
        with patch('validators.format_cpf', return_value="123.456.789-00"):
            with patch('validators.format_whatsapp', return_value="(11) 99999-9999"):
                with patch('validators.get_whatsapp_url', return_value="https://wa.me/11999999999"):
                    result = customer_service.get_customer_grid_data(page=1, page_size=10)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["nome_completo"] == "João da Silva"
        assert result[0]["cidade"] == "São Paulo"

    @patch('services.customer_service.CustomerRepository')
    def test_count_customers(self, mock_repo_class, customer_service):
        """Testa a contagem de clientes."""
        mock_repo = Mock()
        mock_repo.count_customers.return_value = 42
        mock_repo_class.return_value = mock_repo
        
        result = customer_service.count_customers()
        
        assert result == 42
        mock_repo.count_customers.assert_called_once()

    @patch('services.customer_service.CustomerRepository')
    def test_get_unique_states(self, mock_repo_class, customer_service):
        """Testa a obtenção de estados únicos."""
        mock_repo = Mock()
        mock_repo.get_unique_states.return_value = ["SP", "RJ", "MG"]
        mock_repo_class.return_value = mock_repo
        
        result = customer_service.get_unique_states()
        
        assert len(result) == 3
        assert "SP" in result
        mock_repo.get_unique_states.assert_called_once()
