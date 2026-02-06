import sqlite3
import shutil
import datetime
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def truncate_customers_db(keep_n_customers: int = 10):
    """
    Reduz o banco de dados 'customers.db' para um número específico de clientes,
    mantendo os clientes com os IDs mais baixos. Cria um backup antes de truncar.
    """
    db_path = 'customers.db'
    
    if not os.path.exists(db_path):
        logging.error(f"Banco de dados não encontrado em: {db_path}")
        return

    # 1. Criar backup do banco de dados
    backup_dir = './backups'
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = os.path.join(backup_dir, f'customers_backup_{timestamp}.db')
    shutil.copyfile(db_path, backup_path)
    logging.info(f"Backup do banco de dados criado em: {backup_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 2. Obter os IDs dos clientes a serem mantidos (os N primeiros)
        cursor.execute(f"SELECT id FROM clientes ORDER BY id ASC LIMIT {keep_n_customers}")
        customer_ids_to_keep = [row[0] for row in cursor.fetchall()]

        if not customer_ids_to_keep:
            logging.info("Nenhum cliente encontrado para manter. O banco de dados permanecerá vazio.")
            return

        logging.info(f"Mantendo {len(customer_ids_to_keep)} clientes com IDs: {customer_ids_to_keep}")

        # 3. Excluir todos os clientes que NÃO estão na lista de IDs a serem mantidos
        # Isso também excluirá contatos e endereços devido ao ON DELETE CASCADE
        placeholders = ','.join('?' * len(customer_ids_to_keep))
        cursor.execute(f"DELETE FROM clientes WHERE id NOT IN ({placeholders})", customer_ids_to_keep)
        deleted_count = cursor.rowcount
        conn.commit()
        logging.info(f"Excluídos {deleted_count} clientes. Total de clientes restantes: {len(customer_ids_to_keep)}.")

    except sqlite3.Error as e:
        conn.rollback()
        logging.error(f"Erro ao truncar o banco de dados: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    truncate_customers_db(keep_n_customers=10)
