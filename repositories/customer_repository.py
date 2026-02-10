from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from sqlalchemy import text
from models import Cliente, Contato, Endereco, AuditLog
from repositories.base import BaseRepository
import json
import datetime
import pandas as pd

class CustomerRepository(BaseRepository[Cliente]):
    def __init__(self, session: Session):
        super().__init__(session, Cliente)
    
    def get(self, id: int) -> Optional[Cliente]:
        """Get customer by ID with eager loaded relationships."""
        statement = select(Cliente).options(
            selectinload(Cliente.contatos),
            selectinload(Cliente.enderecos)
        ).where(Cliente.id == id)
        return self.session.exec(statement).first()

    def create_customer(self, cliente: Cliente, contatos: List[Contato], enderecos: List[Endereco]) -> Cliente:
        """
        Cria um cliente com seus contatos e endereços em uma transação única.
        """
        try:
            self.session.add(cliente)
            self.session.flush() # Para gerar o ID do cliente

            for contato in contatos:
                contato.cliente_id = cliente.id
                self.session.add(contato)

            for endereco in enderecos:
                endereco.cliente_id = cliente.id
                self.session.add(endereco)

            self._log_audit('cliente', cliente.id, 'INSERT', depois=cliente.model_dump())
            
            self.session.commit()
            self.session.refresh(cliente)
            return cliente
        except Exception as e:
            self.session.rollback()
            raise e

    def update_customer(self, customer_id: int, data: dict, contatos_data: List[dict] = None, enderecos_data: List[dict] = None) -> Optional[Cliente]:
        try:
            cliente = self.get(customer_id)
            if not cliente:
                return None

            antes = cliente.model_dump()
            
            # Filtra apenas campos que pertencem ao modelo Cliente
            # para evitar ValueError quando campos de UI (como 'contato1') são passados
            cliente_fields = self.model.__fields__.keys()
            for key, value in data.items():
                if key in cliente_fields and key != 'id':
                    setattr(cliente, key, value)
            
            self.session.add(cliente)

            # Para simplificar e manter a compatibilidade com o database.py original,
            # vamos atualizar contatos e endereços se os dados estiverem presentes no dicionário 'data'
            # (mapeando os nomes de campos da UI para os modelos)
            
            # 1. Contatos
            for tipo in ['Principal', 'Secundário']:
                suffix = '1' if tipo == 'Principal' else '2'
                nome_key = f'contato{suffix}'
                tel_key = f'telefone{suffix}'
                
                # Campos específicos do contato principal
                email_key = 'email' if tipo == 'Principal' else None
                cargo_key = 'cargo' if tipo == 'Principal' else None

                if any(data.get(k) for k in [nome_key, tel_key, email_key, cargo_key] if k):
                    contato = next((c for c in cliente.contatos if c.tipo_contato == tipo), None)
                    if not contato:
                        contato = Contato(cliente_id=cliente.id, tipo_contato=tipo)
                    
                    if data.get(nome_key): contato.nome_contato = data.get(nome_key)
                    if data.get(tel_key): contato.telefone = data.get(tel_key)
                    if email_key and data.get(email_key): contato.email_contato = data.get(email_key)
                    if cargo_key and data.get(cargo_key): contato.cargo_contato = data.get(cargo_key)
                    self.session.add(contato)

            # 2. Endereço
            if any(data.get(k) for k in ['cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado']):
                endereco = next((e for e in cliente.enderecos if e.tipo_endereco == 'Principal'), None)
                if not endereco:
                    endereco = Endereco(cliente_id=cliente.id, tipo_endereco='Principal')
                
                if data.get('cep'): endereco.cep = data.get('cep')
                if data.get('endereco'): endereco.logradouro = data.get('endereco')
                if data.get('numero'): endereco.numero = data.get('numero')
                if data.get('complemento'): endereco.complemento = data.get('complemento')
                if data.get('bairro'): endereco.bairro = data.get('bairro')
                if data.get('cidade'): endereco.cidade = data.get('cidade')
                if data.get('estado'): endereco.estado = data.get('estado')
                if data.get('latitude'): endereco.latitude = data.get('latitude')
                if data.get('longitude'): endereco.longitude = data.get('longitude')
                self.session.add(endereco)

            self._log_audit('cliente', customer_id, 'UPDATE', antes=antes, depois=cliente.model_dump())
            self.session.commit()
            self.session.refresh(cliente)
            return cliente
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_customer(self, customer_id: int) -> bool:
        try:
            # Busca o cliente com relacionamentos para garantir que a cascata funcione
            cliente = self.get(customer_id)
            if not cliente:
                return False

            self._log_audit('cliente', customer_id, 'DELETE', antes=cliente.model_dump())
            self.session.delete(cliente)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e

    def _log_audit(self, entidade: str, entidade_id: int, acao: str, antes: dict = None, depois: dict = None, usuario: str = "Sistema"):
        log = AuditLog(
            entidade=entidade,
            entidade_id=entidade_id,
            acao=acao,
            dados_anteriores=json.dumps(antes, default=str) if antes else None,
            dados_novos=json.dumps(depois, default=str) if depois else None,
            usuario=usuario,
            timestamp=datetime.datetime.now()
        )
        self.session.add(log)
    def list_customers(self, search_query: str = None, state_filter: str = None, offset: int = 0, limit: int = 10) -> List[Cliente]:
        from sqlmodel import func
        
        # Eager load relationships to avoid N+1 queries
        statement = select(Cliente).options(
            selectinload(Cliente.contatos),
            selectinload(Cliente.enderecos)
        ).distinct()
        
        # Joins para filtros
        if state_filter and state_filter != "Todos":
             statement = statement.join(Endereco).where(Endereco.tipo_endereco == 'Principal', Endereco.estado == state_filter)
        
        if search_query:
            statement = statement.where(
                (Cliente.nome_completo.contains(search_query)) | 
                (Cliente.cpf.contains(search_query)) | 
                (Cliente.cnpj.contains(search_query))
            )
        
        statement = statement.offset(offset).limit(limit)
        results = self.session.exec(statement).all()
        return results

    def count_customers(self, search_query: str = None, state_filter: str = None) -> int:
        from sqlmodel import func, select
        
        # Simplified count statement
        statement = select(func.count(Cliente.id))

        if state_filter and state_filter != "Todos":
             statement = statement.join(Endereco).where(Endereco.tipo_endereco == 'Principal', Endereco.estado == state_filter)
        
        if search_query:
            statement = statement.where(
                (Cliente.nome_completo.contains(search_query)) | 
                (Cliente.cpf.contains(search_query)) | 
                (Cliente.cnpj.contains(search_query))
            )
            
        return self.session.exec(statement).one()

    def get_unique_states(self) -> List[str]:
        """Retorna lista de estados únicos dos endereços principais."""
        query = text("""
            SELECT DISTINCT estado 
            FROM enderecos 
            WHERE tipo_endereco = 'Principal' AND estado IS NOT NULL
            ORDER BY estado;
        """)
        return pd.read_sql_query(query, self.session.connection())['estado'].tolist()

    def get_new_customers_timeseries(self, start_date, end_date, period='M') -> pd.DataFrame:
        if period == 'D':
            date_format = '%Y-%m-%d'
        elif period == 'W':
            date_format = '%Y-%W'
        else:
            date_format = '%Y-%m'
            
        query = text(f"""
            SELECT 
                strftime('{date_format}', data_cadastro) as time_period,
                COUNT(id) as count
            FROM clientes
            WHERE data_cadastro BETWEEN :start_date AND :end_date
            GROUP BY time_period
            ORDER BY time_period;
        """)
        return pd.read_sql_query(query, self.session.connection(), params={"start_date": start_date, "end_date": end_date})

    def get_customer_locations(self) -> pd.DataFrame:
        query = text("""
            SELECT cl.id, en.latitude, en.longitude, cl.nome_completo, en.estado, en.cidade
            FROM clientes cl
            JOIN enderecos en ON cl.id = en.cliente_id
            WHERE en.latitude IS NOT NULL AND en.longitude IS NOT NULL;
        """)
        return pd.read_sql_query(query, self.session.connection())

    def get_data_health_summary(self) -> dict:
        query = text("""
            SELECT
                COUNT(DISTINCT cl.id) as total_customers,
                COUNT(CASE WHEN co.email_contato IS NOT NULL AND co.email_contato != '' THEN 1 END) as with_email,
                COUNT(CASE WHEN co.telefone IS NOT NULL AND co.telefone != '' THEN 1 END) as with_phone,
                COUNT(CASE WHEN en.cep IS NOT NULL AND en.cep != '' THEN 1 END) as with_cep
            FROM clientes cl
            LEFT JOIN contatos co ON cl.id = co.cliente_id AND co.tipo_contato = 'Principal'
            LEFT JOIN enderecos en ON cl.id = en.cliente_id AND en.tipo_endereco = 'Principal';
        """)
        df = pd.read_sql_query(query, self.session.connection())
        if df.empty or df['total_customers'][0] == 0:
            return {'email_completeness': 0, 'phone_completeness': 0, 'cep_completeness': 0}
        
        summary = {
            'email_completeness': (df['with_email'][0] / df['total_customers'][0]) * 100,
            'phone_completeness': (df['with_phone'][0] / df['total_customers'][0]) * 100,
            'cep_completeness': (df['with_cep'][0] / df['total_customers'][0]) * 100
        }
        return summary

    def get_incomplete_customers(self) -> pd.DataFrame:
        query = text("""
            SELECT cl.id, cl.nome_completo, 
                   CASE WHEN co.email_contato IS NULL OR co.email_contato = '' THEN 1 ELSE 0 END as missing_email,
                   CASE WHEN co.telefone IS NULL OR co.telefone = '' THEN 1 ELSE 0 END as missing_phone,
                   CASE WHEN en.cep IS NULL OR en.cep = '' THEN 1 ELSE 0 END as missing_cep
            FROM clientes cl
            LEFT JOIN contatos co ON cl.id = co.cliente_id AND co.tipo_contato = 'Principal'
            LEFT JOIN enderecos en ON cl.id = en.cliente_id AND en.tipo_endereco = 'Principal'
            WHERE missing_email = 1 OR missing_phone = 1 OR missing_cep = 1
            ORDER BY cl.id DESC;
        """)
        return pd.read_sql_query(query, self.session.connection())

