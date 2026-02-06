import sqlite3
import shutil
import datetime
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def delete_all_customers_from_db():
    """
    Apaga todos os clientes do banco de dados 'customers.db'.
    Cria um backup antes de apagar.
    """
    db_path = 'customers.db'
    
    if not os.path.exists(db_path):
        logging.error(f"Banco de dados não encontrado em: {db_path}")
        return

    # 1. Criar backup do banco de dados
    backup_dir = './backups'
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = os.path.join(backup_dir, f'customers_all_deleted_backup_{timestamp}.db')
    shutil.copyfile(db_path, backup_path)
    logging.info(f"Backup do banco de dados criado em: {backup_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 2. Apagar todos os clientes
        cursor.execute("DELETE FROM clientes")
        deleted_count = cursor.rowcount
        conn.commit()
        logging.info(f"Todos os {deleted_count} clientes foram apagados do banco de dados.")

    except sqlite3.Error as e:
        conn.rollback()
        logging.error(f"Erro ao apagar clientes do banco de dados: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    delete_all_customers_from_db()
