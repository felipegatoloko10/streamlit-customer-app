from typing import Optional, List
from sqlmodel import Session, select
from models import Cliente, Contato, Endereco
from repositories.customer_repository import CustomerRepository
from database_config import engine
import validators
import integration_services as services
import logging
import backup_manager
import datetime

class DatabaseError(Exception):
    """Exceção base para erros de banco de dados."""
    pass

class DuplicateEntryError(DatabaseError):
    """Exceção para entradas duplicadas (CPF/CNPJ)."""
    pass


class CustomerService:
    def __init__(self):
        self.engine = engine

    def get_session(self):
        return Session(self.engine)

    def create_customer(self, data: dict) -> Cliente:
        # Sanitização e Validação
        data = self._sanitize_data(data)
        self._validate_cliente_data(data)

        # Preparação dos dados para os modelos
        # Cliente
        cliente_data = {
            'nome_completo': data.get('nome_completo'),
            'tipo_documento': data.get('tipo_documento'),
            'data_nascimento': data.get('data_nascimento'),
            'observacao': data.get('observacao'),
            'data_cadastro': data.get('data_cadastro') or datetime.date.today(),
            'cpf': validators.unformat_cpf(data.get('cpf')),
            'cnpj': validators.unformat_cnpj(data.get('cnpj'))
        }
        cliente = Cliente(**cliente_data)

        # Contatos
        contatos = []
        # Contato 1
        if any(data.get(f) for f in ['contato1', 'telefone1', 'email', 'cargo']):
            contatos.append(Contato(
                nome_contato=data.get('contato1'),
                telefone=validators.unformat_whatsapp(data.get('telefone1')),
                email_contato=data.get('email'),
                cargo_contato=data.get('cargo'),
                tipo_contato='Principal'
            ))
        # Contato 2
        if any(data.get(f) for f in ['contato2', 'telefone2']):
            contatos.append(Contato(
                nome_contato=data.get('contato2'),
                telefone=validators.unformat_whatsapp(data.get('telefone2')),
                tipo_contato='Secundário'
            ))

        # Endereço
        enderecos = []
        if any(data.get(f) for f in ['cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado']):
            enderecos.append(Endereco(
                cep=data.get('cep'),
                logradouro=data.get('endereco'),
                numero=data.get('numero'),
                complemento=data.get('complemento'),
                bairro=data.get('bairro'),
                cidade=data.get('cidade'),
                estado=data.get('estado'),
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                tipo_endereco='Principal'
            ))

        try:
            with self.get_session() as session:
                repo = CustomerRepository(session)
                created_customer = repo.create_customer(cliente, contatos, enderecos)
                
                # Tarefas Pós-Criação (Async/Side-effects)
                try:
                    # Reconstrói o dicionário 'data' enriquecido com IDs se necessário
                    # Mas o services.send... usa 'data' bruto, então passamos o original sanitizado
                    services.send_new_customer_email(data, created_customer.id)
                except Exception as e:
                    logging.error(f"Falha ao enviar e-mail de notificação: {e}")
                
                try:
                    backup_manager.increment_and_check_backup()
                except Exception as e:
                    logging.error(f"Erro ao tentar backup automático: {e}")

                return created_customer
        except Exception as e:
            # Importa aqui para evitar dependência circular se houver
            from database import DatabaseError, DuplicateEntryError
            if "UNIQUE constraint failed" in str(e) or "psycopg2.errors.UniqueViolation" in str(e):
                 raise DuplicateEntryError("O CPF ou CNPJ informado já existe.") from e
            raise DatabaseError(f"Erro ao salvar cliente: {e}") from e

    def update_customer(self, customer_id: int, data: dict) -> Optional[Cliente]:
        data = self._sanitize_data(data)
        # Validação pode ser adicionada aqui se necessário
        
        # Unformat data for updates
        if data.get('cpf'):
            data['cpf'] = validators.unformat_cpf(data['cpf'])
        if data.get('cnpj'):
            data['cnpj'] = validators.unformat_cnpj(data['cnpj'])
        if data.get('telefone1'):
            data['telefone1'] = validators.unformat_whatsapp(data['telefone1'])
        if data.get('telefone2'):
            data['telefone2'] = validators.unformat_whatsapp(data['telefone2'])

        with self.get_session() as session:
            repo = CustomerRepository(session)
            # A lógica de update no repositório ainda precisa ser refinada para lidar com contatos/endereços
            # Mas vamos chamar o método existente.
            # O repositório espera 'cliente_data', 'contatos_data' (lista), 'enderecos_data' (lista)
            # Precisamos adaptar a chamada se quisermos suportar update completo.
            # Por enquanto, o update_customer do repo aceita cliente_data generalizado,
            # mas o ideal é separar.
            # Vamos simplificar e passar o data flat para o repo lidar ou (melhor)
            # preparar os dados como no create.
            
            # Para manter simples, vamos assumir que o repo.update_customer faz o trabalho 
            # ou refatorar o repo para aceitar objetos também? 
            # O repo.update_customer atual aceita dicts.
            
            return repo.update_customer(customer_id, data) 

    def delete_customer(self, customer_id: int) -> bool:
        with self.get_session() as session:
            repo = CustomerRepository(session)
            return repo.delete_customer(customer_id)

    def _sanitize_data(self, data: dict) -> dict:
        """Padroniza textos (Title Case) e remove espaços extras."""
        clean = data.copy()
        text_fields = ['nome_completo', 'contato1', 'contato2', 'cargo', 'logradouro', 'endereco', 'bairro', 'cidade']
        for field in text_fields:
            if clean.get(field) and isinstance(clean[field], str):
                clean[field] = " ".join(clean[field].split()).title()
        
        if clean.get('estado') and isinstance(clean['estado'], str):
            clean['estado'] = clean['estado'].strip().upper()[:2]
            
        if clean.get('cep') and isinstance(clean['cep'], str):
            clean['cep'] = "".join(filter(str.isdigit, clean['cep']))
            
        return clean

    def _validate_cliente_data(self, data: dict):
        if not data.get('nome_completo') or not data.get('tipo_documento'):
            raise validators.ValidationError("Os campos 'Nome Completo' e 'Tipo de Documento' são obrigatórios.")

        doc_type = data.get('tipo_documento')
        if doc_type == 'CPF':
            if not data.get('cpf'):
                raise validators.ValidationError("O campo 'CPF' é obrigatório.")
            validators.is_valid_cpf(data['cpf'])
        elif doc_type == 'CNPJ':
            if not data.get('cnpj'):
                raise validators.ValidationError("O campo 'CNPJ' é obrigatório.")
            validators.is_valid_cnpj(data['cnpj'])

    def get_customer_grid_data(self, search_query: str = None, state_filter: str = None, page: int = 1, page_size: int = 10) -> List[dict]:
        offset = (page - 1) * page_size
        with self.get_session() as session:
            repo = CustomerRepository(session)
            customers = repo.list_customers(search_query, state_filter, offset, page_size)
            
            grid_data = []
            for customer in customers:
                # Extrai dados principais
                data = {
                    "id": customer.id,
                    "nome_completo": customer.nome_completo,
                    "cpf": validators.format_cpf(customer.cpf) if customer.cpf else None,
                    "cnpj": validators.format_cnpj(customer.cnpj) if customer.cnpj else None,
                    "data_nascimento": customer.data_nascimento,
                    "data_cadastro": customer.data_cadastro,
                    "observacao": customer.observacao
                }
                
                # Extrai Contatos (Prioriza Principal)
                contato1 = next((c for c in customer.contatos if c.tipo_contato == 'Principal'), None)
                contato2 = next((c for c in customer.contatos if c.tipo_contato == 'Secundário'), None)
                
                if contato1:
                    data.update({
                        "contato1": contato1.nome_contato,
                        "telefone1": validators.format_whatsapp(contato1.telefone),
                        "email": contato1.email_contato,
                        "cargo": contato1.cargo_contato,
                        "link_wpp_1": validators.get_whatsapp_url(contato1.telefone)
                    })
                else:
                    # Se não tiver contato principal, tenta pegar o primeiro da lista
                    first_contact = customer.contatos[0] if customer.contatos else None
                    if first_contact:
                         data.update({
                            "telefone1": validators.format_whatsapp(first_contact.telefone),
                             "link_wpp_1": validators.get_whatsapp_url(first_contact.telefone)
                         })

                # Extrai Endereço (Prioriza Principal)
                endereco = next((e for e in customer.enderecos if e.tipo_endereco == 'Principal'), None)
                if not endereco and customer.enderecos:
                    endereco = customer.enderecos[0]
                
                if endereco:
                    data.update({
                        "endereco": endereco.logradouro,
                        "numero": endereco.numero,
                        "complemento": endereco.complemento,
                        "bairro": endereco.bairro,
                        "cidade": endereco.cidade,
                        "estado": endereco.estado,
                        "cep": endereco.cep
                    })
                
                grid_data.append(data)
            
            return grid_data

    def count_customers(self, search_query: str = None, state_filter: str = None) -> int:
        with self.get_session() as session:
            repo = CustomerRepository(session)
            return repo.count_customers(search_query, state_filter)

    def get_unique_states(self) -> List[str]:
        with self.get_session() as session:
            repo = CustomerRepository(session)
            return repo.get_unique_states()

    def get_customer_details(self, customer_id: int) -> Optional[dict]:
        with self.get_session() as session:
            repo = CustomerRepository(session)
            customer = repo.get(customer_id)
            if not customer:
                return None
            
            # Flatten data for UI compatibility
            data = customer.model_dump()
            
            # Formatação
            if data.get('cpf'): data['cpf'] = validators.format_cpf(data['cpf'])
            if data.get('cnpj'): data['cnpj'] = validators.format_cnpj(data['cnpj'])
            
            # Contatos
            contato1 = next((c for c in customer.contatos if c.tipo_contato == 'Principal'), None)
            if contato1:
                data.update({
                    "contato1": contato1.nome_contato,
                    "telefone1": validators.format_whatsapp(contato1.telefone),
                    "email": contato1.email_contato,
                    "cargo": contato1.cargo_contato
                })
            
            contato2 = next((c for c in customer.contatos if c.tipo_contato == 'Secundário'), None)
            if contato2:
                data.update({
                    "contato2": contato2.nome_contato,
                    "telefone2": validators.format_whatsapp(contato2.telefone)
                })

            # Endereço
            endereco = next((e for e in customer.enderecos if e.tipo_endereco == 'Principal'), None)
            if endereco:
                data.update(endereco.model_dump(exclude={'id', 'cliente_id'}))
                # Renomeia logradouro para endereco para compatibilidade
                data['endereco'] = data.get('logradouro')
                
            return data

    # Analytical methods for Dashboard
    def get_new_customers_timeseries(self, start_date, end_date, period='M'):
        import pandas as pd
        with self.get_session() as session:
            repo = CustomerRepository(session)
            return repo.get_new_customers_timeseries(start_date, end_date, period)

    def get_customer_locations(self):
        import pandas as pd
        with self.get_session() as session:
            repo = CustomerRepository(session)
            return repo.get_customer_locations()

    def get_data_health_summary(self) -> dict:
        with self.get_session() as session:
            repo = CustomerRepository(session)
            return repo.get_data_health_summary()

    def get_incomplete_customers(self):
        import pandas as pd
        with self.get_session() as session:
            repo = CustomerRepository(session)
            return repo.get_incomplete_customers()
