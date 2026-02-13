import logging
import time
from database_config import engine, create_db_and_tables, get_session
from models import Cliente
from sqlmodel import select, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_connection():
    print("--- Verificando Conexão e Tabelas ---")
    try:
        # 1. Create Tables
        print("Criando tabelas (se não existirem)...")
        create_db_and_tables()
        print("Tabelas verificadas/criadas.")

        # 2. Test Connection
        print("Testando conexão simples...")
        with next(get_session()) as session:
            result = session.exec(text("SELECT 1")).one()
            print(f"Conexão OK! Resultado: {result}")

        # 3. Check for existing data
        print("Verificando dados existentes...")
        with next(get_session()) as session:
            statement = select(Cliente)
            results = session.exec(statement).all()
            print(f"Número de clientes encontrados: {len(results)}")
            
            if len(results) == 0:
                print("Banco vazio. Pronto para receber dados.")
            else:
                print(f"Último cliente: {results[-1].nome_completo}")

    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        raise e

if __name__ == "__main__":
    verify_connection()
