import integration_services as services
from services.customer_service import CustomerService
import logging
import pandas as pd
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

customer_service = CustomerService()

def regeocode_all_customers():
    """
    Itera sobre todos os clientes no banco de dados, re-geocodifica seus endereços
    usando a função services.get_coords_for_address e atualiza suas coordenadas.
    """
    # Obter lista de todos os clientes com endereços
    logging.info("Buscando todos os clientes...")
    
    # Paginação para evitar carregar todos os clientes de uma vez
    page = 1
    page_size = 50
    total_processed = 0
    regeocoded_count = 0
    failed_count = 0
    
    while True:
        customers_data = customer_service.get_customer_grid_data(
            search_query=None, 
            state_filter=None, 
            page=page, 
            page_size=page_size
        )
        
        if not customers_data:
            break
            
        logging.info(f"Processando página {page} ({len(customers_data)} clientes)...")
        
        for customer_data in customers_data:
            customer_id = customer_data.get('id')
            total_processed += 1
            
            try:
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
                    customer_service.update_customer(customer_id, {'latitude': latitude, 'longitude': longitude})
                    logging.info(f"Cliente {customer_id} ({customer_data.get('nome_completo')}): Coordenadas atualizadas para ({latitude}, {longitude}).")
                    regeocoded_count += 1
                else:
                    logging.warning(f"Cliente {customer_id} ({customer_data.get('nome_completo')}): Não foi possível obter coordenadas para o endereço '{full_address}'.")
                    failed_count += 1
                
                # Pequeno delay para evitar sobrecarregar a API do Nominatim
                time.sleep(1)

            except Exception as e:
                logging.error(f"Erro ao processar cliente {customer_id} ({customer_data.get('nome_completo', 'Unknown')}): {e}")
                failed_count += 1
        
        page += 1

    logging.info(f"Processo de re-geocodificação concluído.")
    logging.info(f"Total de clientes processados: {total_processed}")
    logging.info(f"Clientes re-geocodificados com sucesso: {regeocoded_count}")
    logging.info(f"Falhas na geocodificação: {failed_count}")

if __name__ == "__main__":
    regeocode_all_customers()

