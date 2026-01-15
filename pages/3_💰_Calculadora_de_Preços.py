import streamlit as st

st.set_page_config(
    page_title="Calculadora de Preços",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Calculadora de Preço para Impressão 3D")
st.markdown("Altere qualquer campo para recalcular o preço de venda em tempo real.")

# --- Dicionário para guardar todos os inputs ---
if 'calc_inputs' not in st.session_state:
    st.session_state.calc_inputs = {
        'design_hours': 0.0, 'design_rate': 100.0,
        'slice_hours': 0.0, 'slice_rate': 40.0,
        'assembly_hours': 0.0, 'assembly_rate': 30.0,
        'post_process_h': 0.0, 'labor_rate_h': 30.0,
        'print_time_h': 0.0,
        'material_weight_g': 0.0, 'filament_cost_kg': 120.0,
        'printer_consumption_w': 150.0, 'kwh_cost': 0.78,
        'printer_wear_rate_h': 1.50,
        'failure_rate_percent': 5.0,
        'complexity_factor': 1.0,
        'urgency_fee_percent': 0.0,
        'profit_margin_percent': 50.0
    }

inputs = st.session_state.calc_inputs

# --- Funções de Cálculo ---
def calculate_costs(inputs):
    """Calcula todos os custos e o preço final com base nos inputs."""
    
    # Custo de Mão de Obra e Tempo
    cost_design = inputs['design_hours'] * inputs['design_rate']
    cost_slice = inputs['slice_hours'] * inputs['slice_rate']
    cost_assembly = inputs['assembly_hours'] * inputs['assembly_rate']
    cost_post_process = inputs['post_process_h'] * inputs['labor_rate_h']
    total_labor_cost = cost_design + cost_slice + cost_assembly + cost_post_process

    # Custo de Material
    cost_per_gram = inputs['filament_cost_kg'] / 1000
    cost_material = inputs['material_weight_g'] * cost_per_gram
    
    # Custo de Impressão (Eletricidade + Desgaste)
    cost_electricity = (inputs['printer_consumption_w'] / 1000) * inputs['print_time_h'] * inputs['kwh_cost']
    cost_printer_wear = inputs['print_time_h'] * inputs['printer_wear_rate_h']
    total_printing_cost = cost_electricity + cost_printer_wear

    # Custo de Produção (Subtotal)
    subtotal = total_labor_cost + cost_material + total_printing_cost
    
    # Aplicar Fator de Complexidade
    cost_with_complexity = subtotal * inputs['complexity_factor']

    # Adicionar Taxa de Falha
    cost_with_failure = cost_with_complexity * (1 + (inputs['failure_rate_percent'] / 100))
    
    # Adicionar Taxa de Urgência
    cost_with_urgency = cost_with_failure * (1 + (inputs['urgency_fee_percent'] / 100))

    # Adicionar Margem de Lucro para o Preço Final
    final_price = cost_with_urgency * (1 + (inputs['profit_margin_percent'] / 100))
    
    return {
        "Custo de Mão de Obra Total": total_labor_cost,
        "Custo de Material": cost_material,
        "Custo Total de Impressão": total_printing_cost,
        "Custo de Produção": subtotal,
        "Custo com Complexidade": cost_with_complexity,
        "Custo com Taxa de Falha": cost_with_failure,
        "Custo com Taxa de Urgência": cost_with_urgency,
        "Preço de Venda Final": final_price
    }

# --- Exibição dos Resultados (no topo) ---
results = calculate_costs(inputs)
final_price = results["Preço de Venda Final"]

st.subheader("📊 Resultados da Precificação")
with st.container(border=True):
    st.success(f"**Preço de Venda Sugerido: R$ {final_price:.2f}**")
    
    with st.expander("Ver detalhamento completo dos custos"):
        # Detalhamento
        st.metric("Custo Total de Mão de Obra", f"R$ {results['Custo de Mão de Obra Total']:.2f}")
        st.metric("Custo de Material", f"R$ {results['Custo de Material']:.2f}")
        st.metric("Custo Total de Impressão (Eletricidade + Desgaste)", f"R$ {results['Custo Total de Impressão']:.2f}")
        st.divider()
        st.metric("Custo de Produção (Subtotal)", f"R$ {results['Custo de Produção']:.2f}")
        st.metric("Custo com Fator de Complexidade", f"R$ {results['Custo com Complexidade']:.2f}", help=f"Multiplicador de {inputs['complexity_factor']}x aplicado.")
        st.metric("Custo com Taxa de Falha", f"R$ {results['Custo com Taxa de Falha']:.2f}", help=f"{inputs['failure_rate_percent']}% adicionado ao custo.")
        st.metric("Custo com Taxa de Urgência", f"R$ {results['Custo com Taxa de Urgência']:.2f}", help=f"{inputs['urgency_fee_percent']}% adicionado ao custo.")
        st.divider()
        st.metric("Preço de Venda Final (com Lucro)", f"R$ {final_price:.2f}", help=f"{inputs['profit_margin_percent']}% de margem de lucro adicionada.")

st.markdown("---")
st.subheader("⚙️ Insira os Dados do Projeto")

# --- Interface de Inputs ---
with st.container(border=True):
    with st.expander("👨‍💻 Custos de Mão de Obra e Tempo", expanded=True):
        c1, c2 = st.columns(2)
        inputs['design_hours'] = c1.number_input("Horas de design (SolidWorks)", key='des_h', min_value=0.0, step=0.5)
        inputs['design_rate'] = c2.number_input("Valor da hora de design (R$)", key='des_r', min_value=0.0, step=5.0)
        inputs['slice_hours'] = c1.number_input("Horas de preparo/fatiamento", key='sli_h', min_value=0.0, step=0.25)
        inputs['slice_rate'] = c2.number_input("Valor da hora de preparo (R$)", key='sli_r', min_value=0.0, step=5.0)
        inputs['assembly_hours'] = c1.number_input("Horas de montagem", key='asm_h', min_value=0.0, step=0.25)
        inputs['assembly_rate'] = c2.number_input("Valor da hora de montagem (R$)", key='asm_r', min_value=0.0, step=5.0)
        inputs['post_process_h'] = c1.number_input("Horas de pós-processamento", key='pos_h', min_value=0.0, step=0.25)
        inputs['labor_rate_h'] = c2.number_input("Valor da hora de pós-processamento (R$)", key='pos_r', min_value=0.0, step=5.0)

    with st.expander("🖨️ Custos de Impressão e Material"):
        c1, c2 = st.columns(2)
        inputs['print_time_h'] = c1.number_input("Tempo de impressão (horas)", key='pri_h', min_value=0.0, step=0.25)
        inputs['material_weight_g'] = c1.number_input("Peso do material (gramas)", key='mat_w', min_value=0.0, step=1.0)
        inputs['filament_cost_kg'] = c2.number_input("Custo do filamento (R$ por kg)", key='mat_c', min_value=0.0, step=10.0)
        inputs['printer_consumption_w'] = c1.number_input("Consumo da impressora (Watts)", key='ele_w', min_value=0.0, step=10.0)
        inputs['kwh_cost'] = c2.number_input("Custo da eletricidade (R$ por kWh)", key='ele_c', min_value=0.0, step=0.01, format="%.2f")
        inputs['printer_wear_rate_h'] = c2.number_input("Desgaste da impressora (R$ por hora)", key='wea_r', min_value=0.0, step=0.50, format="%.2f")

    with st.expander("📈 Fatores de Negócio e Risco"):
        c1, c2 = st.columns(2)
        inputs['failure_rate_percent'] = c1.number_input("Taxa de falha (%)", key='fai_p', min_value=0.0, max_value=100.0, step=1.0)
        inputs['complexity_factor'] = c2.number_input("Fator de complexidade (multiplicador)", key='com_f', min_value=1.0, step=0.1, help="Use 1.0 para normal, 1.5 para complexo, etc.")
        inputs['urgency_fee_percent'] = c1.number_input("Taxa de urgência (%)", key='urg_p', min_value=0.0, max_value=200.0, step=5.0)
        inputs['profit_margin_percent'] = c2.number_input("Margem de lucro (%)", key='pro_p', min_value=0.0, step=5.0)
