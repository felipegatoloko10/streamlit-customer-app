import importlib.util
import sys
import os
import pytest

# Adiciona o diretório raiz do projeto ao sys.path
# para permitir a importação de módulos de `pages`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Caminho para o arquivo da calculadora
file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pages', '3_💰_Calculadora_de_Preços.py'))

# Carrega o módulo a partir do caminho do arquivo
spec = importlib.util.spec_from_file_location("calculadora_module", file_path)
calculadora_module = importlib.util.module_from_spec(spec)
sys.modules["calculadora_module"] = calculadora_module
spec.loader.exec_module(calculadora_module)

calculate_costs = calculadora_module.calculate_costs

def test_calculate_costs_simple_case():
    """Testa um cenário de cálculo simples sem taxas extras."""
    inputs = {
        'design_hours': 1.0, 'design_rate': 100.0,      # Custo: 100.0
        'slice_hours': 0.5, 'slice_rate': 40.0,        # Custo: 20.0
        'assembly_hours': 0.0, 'assembly_rate': 30.0,     # Custo: 0.0
        'post_process_h': 1.0, 'labor_rate_h': 30.0,    # Custo: 30.0
        'print_time_h': 2.0,                           # Horas de impressão
        'material_weight_g': 50.0,                     # Gramas
        'filament_cost_kg': 120.0,                     # Custo por kg (R$0.12/g) -> Custo: 6.0
        'printer_consumption_w': 150.0,                # Watts
        'kwh_cost': 0.80,                              # Custo kWh
        'printer_wear_rate_h': 1.50,                   # Desgaste por hora -> Custo: 3.0
        'failure_rate_percent': 0.0,                   # Taxa de falha
        'complexity_factor': 1.0,                      # Fator de complexidade
        'urgency_fee_percent': 0.0,                    # Taxa de urgência
        'profit_margin_percent': 50.0                  # Margem de lucro
    }

    # --- Cálculos Manuais para Verificação ---
    # Custo Mão de Obra: 100 (design) + 20 (slice) + 30 (post) = 150.0
    # Custo Material: 50g * (120/1000) = 6.0
    # Custo Eletricidade: (150W / 1000) * 2h * R$0.80 = 0.24
    # Custo Desgaste: 2h * R$1.50 = 3.0
    # Custo Total de Impressão: 0.24 + 3.0 = 3.24
    # Subtotal (Custo de Produção): 150.0 + 6.0 + 3.24 = 159.24
    # Custo com Falha (0%): 159.24
    # Custo com Urgência (0%): 159.24
    # Preço Final (50% de lucro): 159.24 * 1.5 = 238.86

    results = calculate_costs(inputs)
    assert results["Preço de Venda Final"] == pytest.approx(238.86)

def test_calculate_costs_with_fees():
    """Testa um cenário com taxas de falha, complexidade e urgência."""
    inputs = {
        'design_hours': 2.0, 'design_rate': 100.0,      # Custo: 200.0
        'slice_hours': 1.0, 'slice_rate': 40.0,        # Custo: 40.0
        'assembly_hours': 0.0, 'assembly_rate': 30.0,
        'post_process_h': 0.0, 'labor_rate_h': 30.0,
        'print_time_h': 4.0,
        'material_weight_g': 100.0,
        'filament_cost_kg': 100.0,                     # Custo por kg (R$0.10/g) -> Custo: 10.0
        'printer_consumption_w': 200.0,                # Watts
        'kwh_cost': 1.00,                              # Custo kWh
        'printer_wear_rate_h': 2.00,                   # Desgaste por hora -> Custo: 8.0
        'failure_rate_percent': 10.0,                  # Taxa de falha
        'complexity_factor': 1.5,                      # Fator de complexidade
        'urgency_fee_percent': 25.0,                   # Taxa de urgência
        'profit_margin_percent': 100.0                 # Margem de lucro
    }

    # --- Cálculos Manuais ---
    # Custo Mão de Obra: 200 (design) + 40 (slice) = 240.0
    # Custo Material: 100g * (100/1000) = 10.0
    # Custo Eletricidade: (200W / 1000) * 4h * R$1.00 = 0.80
    # Custo Desgaste: 4h * R$2.00 = 8.0
    # Custo Total de Impressão: 0.80 + 8.0 = 8.80
    # Subtotal: 240.0 + 10.0 + 8.80 = 258.80
    # Custo com Complexidade (1.5x): 258.80 * 1.5 = 388.20
    # Custo com Falha (10%): 388.20 * 1.1 = 427.02
    # Custo com Urgência (25%): 427.02 * 1.25 = 533.775
    # Preço Final (100% de lucro): 533.775 * 2.0 = 1067.55

    results = calculate_costs(inputs)
    assert results["Preço de Venda Final"] == pytest.approx(1067.55)
