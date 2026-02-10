from typing import Optional, List
from datetime import date, datetime
from sqlmodel import Field, Relationship, SQLModel

class ClienteBase(SQLModel):
    nome_completo: str
    tipo_documento: str
    cpf: Optional[str] = Field(default=None, unique=True)
    cnpj: Optional[str] = Field(default=None, unique=True)
    data_nascimento: Optional[date] = None
    observacao: Optional[str] = None
    data_cadastro: Optional[date] = Field(default_factory=date.today)

class Cliente(ClienteBase, table=True):
    __tablename__ = "clientes"
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    
    contatos: List["Contato"] = Relationship(back_populates="cliente")
    enderecos: List["Endereco"] = Relationship(back_populates="cliente")

class ContatoBase(SQLModel):
    nome_contato: Optional[str] = None
    telefone: Optional[str] = None
    email_contato: Optional[str] = None
    cargo_contato: Optional[str] = None
    tipo_contato: Optional[str] = None  # 'Principal', 'Secundário'

class Contato(ContatoBase, table=True):
    __tablename__ = "contatos"
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="clientes.id")
    
    cliente: Cliente = Relationship(back_populates="contatos")

class EnderecoBase(SQLModel):
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tipo_endereco: Optional[str] = None # 'Principal'

class Endereco(EnderecoBase, table=True):
    __tablename__ = "enderecos"
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="clientes.id")
    
    cliente: Cliente = Relationship(back_populates="enderecos")

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    entidade: str
    entidade_id: int
    acao: str # 'INSERT', 'UPDATE', 'DELETE'
    dados_anteriores: Optional[str] = None # JSON string
    dados_novos: Optional[str] = None # JSON string
    usuario: str = Field(default="Sistema")
    timestamp: datetime = Field(default_factory=datetime.now)
    entidade: str
    entidade_id: int
    acao: str # 'INSERT', 'UPDATE', 'DELETE'
    dados_anteriores: Optional[str] = None # JSON string
    dados_novos: Optional[str] = None # JSON string
    usuario: str = Field(default="Sistema")
