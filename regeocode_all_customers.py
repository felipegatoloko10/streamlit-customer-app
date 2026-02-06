import database
import services
import logging
import pandas as pd
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def regeocode_all_customers():
    """
    Itera sobre todos os clientes no banco de dados, re-geocodifica seus endereços
    usando a função services.get_coords_for_address e atualiza suas coordenadas.
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()

    # Selecionar todos os IDs de clientes
    cursor.execute("SELECT id FROM clientes")
    customer_ids = [row[0] for row in cursor.fetchall()]

    logging.info(f"Iniciando re-geocodificação para {len(customer_ids)} clientes.")

    regeocoded_count = 0
    failed_count = 0

    for customer_id in customer_ids:
        try:
            # Obter os dados completos do cliente, incluindo endereço
            customer_data = database.get_customer_by_id(customer_id)
            if not customer_data:
                logging.warning(f"Cliente com ID {customer_id} não encontrado. Pulando.")
                continue

            # Construir o endereço completo
            full_address_parts = [
                customer_data.get('endereco'),
                customer_data.get('numero'),
                customer_data.get('bairro'),
                customer_data.get('cidade'),
                customer_data.get('estado'),
                customer_data.get('cep')
            ]
            full_address = ", ".join(filter(None, full_address_parts))

            if not full_address.strip():
                logging.warning(f"Cliente {customer_id} ({customer_data.get('nome_completo')}) não possui endereço completo. Pulando.")
                failed_count += 1
                continue
            
            # Geocodificar o endereço
            latitude, longitude = services.get_coords_for_address(full_address)

            if latitude is not None and longitude is not None:
                # Atualizar o cliente no banco de dados com as novas coordenadas
                database.update_customer(customer_id, {'latitude': latitude, 'longitude': longitude})
                logging.info(f"Cliente {customer_id} ({customer_data.get('nome_completo')}): Coordenadas atualizadas para ({latitude}, {longitude}).")
                regeocoded_count += 1
            else:
                logging.warning(f"Cliente {customer_id} ({customer_data.get('nome_completo')}): Não foi possível obter coordenadas para o endereço '{full_address}'.")
                failed_count += 1
            
            # Pequeno delay para evitar sobrecarregar a API do Nominatim
            time.sleep(1) # Pode ser ajustado ou removido se necessário, respeitando os limites da API

        except Exception as e:
            logging.error(f"Erro ao processar cliente {customer_id} ({customer_data.get('nome_completo')}): {e}")
            failed_count += 1
            # Continua para o próximo cliente mesmo em caso de erro

    logging.info(f"Processo de re-geocodificação concluído.")
    logging.info(f"Clientes re-geocodificados com sucesso: {regeocoded_count}")
    logging.info(f"Falhas na geocodificação: {failed_count}")

if __name__ == "__main__":
    regeocode_all_customers()
