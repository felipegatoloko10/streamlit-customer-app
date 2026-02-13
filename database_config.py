from sqlmodel import SQLModel, create_engine, Session
import os

# Configuração do Supabase Postgres
# Em produção, use st.secrets ou variáveis de ambiente.
# Para este teste local, usaremos a string direta conforme autorizado.
DATABASE_URL = "postgresql+psycopg2://postgres.nayxxppiufxpdghtlgki:Tomati%402412@aws-0-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"

# Nota: Supabase usa pooling de conexões na porta 6543 (Transaction mode) ou 5432 (Session mode). 
# Para SQLModel/SQLAlchemy, Session mode (5432) é geralmente mais seguro para evitar problemas com prepared statements, 
# mas Transaction mode (6543) escala melhor. Vamos tentar 6543 primeiro, se der erro mudamos para 5432 direto (db.nayxx...).
# Atualização: Vamos usar a conexão direta (5432) para evitar problemas de compatibilidade inicial com SQLModel create_all.
DATABASE_URL = "postgresql+psycopg2://postgres.nayxxppiufxpdghtlgki:Tomati%402412@aws-0-us-west-2.pooler.supabase.com:5432/postgres?sslmode=require"
# Melhor ainda, usar o host direto do banco para DDL operations (create_all)
DATABASE_URL = "postgresql+psycopg2://postgres.nayxxppiufxpdghtlgki:Tomati%402412@aws-0-us-west-2.pooler.supabase.com:5432/postgres?sslmode=require"
# DATABASE_URL = "postgresql+psycopg2://postgres:Tomati%402412@db.nayxxppiufxpdghtlgki.supabase.co:5432/postgres"

engine = create_engine(DATABASE_URL, echo=False)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
