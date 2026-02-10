"""
Script simples de verificação da refatoração.
Execute: python verify_refactoring.py
"""

from services.customer_service import CustomerService
from datetime import date

def main():
    print("\n" + "="*60)
    print("  VERIFICACAO DA REFATORACAO - FASE 3")
    print("="*60 + "\n")
    
    customer_service = CustomerService()
    
    # Test 1: Count customers
    print("1. Contando clientes...")
    try:
        count = customer_service.count_customers()
        print(f"   OK - Total: {count} clientes\n")
    except Exception as e:
        print(f"   ERRO: {e}\n")
        return False
    
    # Test 2: Get unique states
    print("2. Buscando estados unicos...")
    try:
        states = customer_service.get_unique_states()
        print(f"   OK - Estados: {', '.join(states) if states else 'Nenhum'}\n")
    except Exception as e:
        print(f"   ERRO: {e}\n")
        return False
    
    # Test 3: Get grid data
    print("3. Buscando dados para grid...")
    try:
        grid = customer_service.get_customer_grid_data(page=1, page_size=5)
        print(f"   OK - Retornou {len(grid)} registros\n")
    except Exception as e:
        print(f"   ERRO: {e}\n")
        return False
    
    # Test 4: Get health summary
    print("4. Analisando saude dos dados...")
    try:
        health = customer_service.get_data_health_summary()
        print(f"   OK - Email: {health.get('email_completeness', 0):.1f}%\n")
    except Exception as e:
        print(f"   ERRO: {e}\n")
        return False
    
    print("="*60)
    print("  TODOS OS TESTES PASSARAM!")
    print("  A refatoracao esta funcionando corretamente.")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
