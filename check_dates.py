import sqlite3
import pandas as pd
import os
import sys

# Adiciona o diretório pai ao PATH para que o módulo 'database' possa ser encontrado
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import database

db_path = 'customers.db'

if not os.path.exists(db_path):
    print(f"Error: Database file not found at {db_path}")
else:
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT id, nome_completo, data_cadastro FROM clientes ORDER BY data_cadastro DESC LIMIT 10;"
        cursor.execute(query)
        rows = cursor.fetchall()

        if rows:
            print("Últimos 10 clientes e suas datas de cadastro:")
            for row in rows:
                print(f"ID: {row[0]}, Nome: {row[1]}, Data Cadastro: {row[2]}")
        else:
            print("Nenhum cliente encontrado na tabela 'clientes'.")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()
