from sqlmodel import SQLModel, create_engine, Session
import os

# Configuração do Supabase Postgres
# IMPORTANTE: Usar porta 6543 (Transaction Mode / PgBouncer) para suportar
# mais conexões simultâneas. O Session Mode (5432) tem limite baixo de clientes.
# O Transaction Mode (6543) é escalável e ideal para aplicações com polling frequente.
DATABASE_URL = "postgresql+psycopg2://postgres.nayxxppiufxpdghtlgki:Tomati%402412@aws-0-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"

# Pool limitado para não esgotar conexões no plano gratuito do Supabase.
# pool_size=3: máximo 3 conexões persistentes
# max_overflow=2: até 2 conexões extras temporárias
# pool_pre_ping=True: testa conexão antes de usar (evita "dead connections")
# pool_recycle=300: descarta conexões ociosas após 5 minutos
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=3,
    max_overflow=2,
    pool_pre_ping=True,
    pool_recycle=300,
)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
