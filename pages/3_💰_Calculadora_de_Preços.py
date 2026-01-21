import streamlit as st
import json
import os
from streamlit_modal import Modal # Importar Modal

# Define os valores padrão para a calculadora
DEFAULT_CALC_INPUTS = {
    'design_hours': 0.0, 'design_rate': 100.0, 'slice_hours': 0.0, 'slice_rate': 40.0,
    'assembly_hours': 0.0, 'assembly_rate': 30.0, 'post_process_h': 0.0, 'labor_rate_h': 30.0,
    'print_time_h': 0.0, 'material_weight_g': 0.0, 'filament_cost_kg': 120.0,
    'printer_consumption_w': 150.0, 'kwh_cost': 0.78, 'printer_wear_rate_h': 1.50,
    'failure_rate_percent': 5.0, 'complexity_factor': 1.0, 'urgency_fee_percent': 0.0,
    'profit_margin_percent': 50.0
}
DEFAULT_PRESETS = {}

# --- Funções de Lógica de Estado ---

def initialize_calculator_state():
    """Garante que todas as chaves do estado da calculadora existam."""
    for key, value in DEFAULT_CALC_INPUTS.items():
        if key not in st.session_state:
            st.session_state[key] = value

def clear_calculator_state():
    """Reseta o estado da calculadora para os valores padrão."""
    for key, value in DEFAULT_CALC_INPUTS.items():
        st.session_state[key] = value
    if 'calc_results' in st.session_state:
        del st.session_state.calc_results

def load_preset_into_state(preset_values):
    """Carrega os valores de uma predefinição no estado da sessão."""
    for key, value in preset_values.items():
        if key in st.session_state:
            st.session_state[key] = value
    if 'calc_results' in st.session_state:
        del st.session_state.calc_results

# --- Inicialização e Ações de Estado ---

initialize_calculator_state()

if st.session_state.get("clear_calc_form", False):
    clear_calculator_state()
    st.session_state.clear_calc_form = False # Limpa a flag

# --- Gerenciamento de Predefinições ---
PRESETS_FILE = "presets.json"

# (As funções load_presets e save_presets permanecem as mesmas)
def load_presets():
    """Carrega as predefinições do arquivo JSON ou retorna as padrão."""
    if os.path.exists(PRESETS_FILE):
        try:
            with open(PRESETS_FILE, 'r') as f:
                saved_presets = json.load(f)
                if saved_presets:
                    return saved_presets
        except json.JSONDecodeError:
            st.error(f"Erro ao ler o arquivo de predefinições '{PRESETS_FILE}'. O arquivo pode estar corrompido. Considere deletá-lo ou corrigi-lo.")
            return DEFAULT_PRESETS
    return DEFAULT_PRESETS

def save_presets(presets):
    """Salva as predefinições no arquivo JSON."""
    os.makedirs(os.path.dirname(PRESETS_FILE), exist_ok=True)
    with open(PRESETS_FILE, 'w') as f:
        json.dump(presets, f, indent=4)

# --- Funções de Cálculo (permanece a mesma) ---
def calculate_costs(inputs):
    """Calcula todos os custos e o preço final com base nos inputs."""
    cost_design = inputs['design_hours'] * inputs['design_rate']
    cost_slice = inputs['slice_hours'] * inputs['slice_rate']
    cost_assembly = inputs['assembly_hours'] * inputs['assembly_rate']
    cost_post_process = inputs['post_process_h'] * inputs['labor_rate_h']
    total_labor_cost = cost_design + cost_slice + cost_assembly + cost_post_process
    cost_per_gram = inputs['filament_cost_kg'] / 1000 if inputs['filament_cost_kg'] > 0 else 0
    cost_material = inputs['material_weight_g'] * cost_per_gram
    cost_electricity = (inputs['printer_consumption_w'] / 1000) * inputs['print_time_h'] * inputs['kwh_cost']
    cost_printer_wear = inputs['print_time_h'] * inputs['printer_wear_rate_h']
    total_printing_cost = cost_electricity + cost_printer_wear
    subtotal = total_labor_cost + cost_material + total_printing_cost
    cost_with_complexity = subtotal * inputs['complexity_factor']
    cost_with_failure = cost_with_complexity * (1 + (inputs['failure_rate_percent'] / 100))
    cost_with_urgency = cost_with_failure * (1 + (inputs['urgency_fee_percent'] / 100))
    final_price = cost_with_urgency * (1 + (inputs['profit_margin_percent'] / 100))
    return {
        "Custo de Mão de Obra Total": total_labor_cost, "Custo de Material": cost_material,
        "Custo Total de Impressão": total_printing_cost, "Custo de Produção": subtotal,
        "Custo com Complexidade": cost_with_complexity, "Custo com Taxa de Falha": cost_with_failure,
        "Custo com Taxa de Urgência": cost_with_urgency, "Preço de Venda Final": final_price
    }

# --- Interface ---
st.title("💰 Calculadora de Preço para Impressão 3D")
st.markdown("Preencha os campos abaixo e clique em 'Calcular' para gerar o preço de venda.")

with st.expander("💾 Gerenciar Predefinições", expanded=True):
    presets = load_presets()
    col_select, col_load, col_delete = st.columns([0.7, 0.15, 0.15])
    
    with col_select:
        preset_options = [""] + list(presets.keys())
        selected_preset = st.selectbox("Selecione uma predefinição:", options=preset_options, label_visibility="collapsed")
    with col_load:
        if st.button("Carregar", width='stretch', disabled=not selected_preset):
            load_preset_into_state(presets[selected_preset])
            st.success(f"Predefinição '{selected_preset}' carregada!")
            st.rerun()
    with col_delete:
        delete_modal = Modal(title=f"Confirmar Exclusão: {selected_preset}", key="delete_preset_modal")
        if st.button("🗑️", width='stretch', disabled=not selected_preset, help="Excluir predefinição selecionada"):
            if selected_preset in presets: delete_modal.open()
            else: st.error("Predefinição não encontrada para exclusão.")
        if delete_modal.is_open():
            with delete_modal.container():
                st.write(f"Tem certeza que deseja excluir a predefinição '{selected_preset}'?")
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    if st.button("Confirmar", type="primary"):
                        del presets[selected_preset]
                        save_presets(presets)
                        st.success(f"Predefinição '{selected_preset}' excluída!")
                        delete_modal.close()
                        st.rerun()
                with col_cancel:
                    st.button("Cancelar", on_click=delete_modal.close)
            
    st.markdown("---")
    save_modal = Modal("Salvar Predefinição", key="save_preset_modal")
    if st.button("💾 Salvar Configuração Atual", width='stretch'):
        save_modal.open()
    if save_modal.is_open():
        with save_modal.container():
            new_preset_name = st.text_input("Nome da nova predefinição:", placeholder="Ex: Peça Pequena PLA")
            if st.button("Salvar", type="primary"):
                if new_preset_name:
                    current_inputs_for_preset = {key: st.session_state[key] for key in DEFAULT_CALC_INPUTS}
                    presets[new_preset_name] = current_inputs_for_preset
                    save_presets(presets)
                    st.success(f"Predefinição '{new_preset_name}' salva!")
                    save_modal.close()
                    st.rerun()
                else:
                    st.warning("Por favor, dê um nome para a predefinição.")

st.markdown("---")
st.subheader("⚙️ Insira os Dados do Projeto")

with st.form("price_calculator_form"):
    with st.container(border=True):
        with st.expander("👨‍💻 Custos de Mão de Obra e Tempo", expanded=True):
            c1, c2 = st.columns(2)
            c1.number_input("Horas de design (SolidWorks)", min_value=0.0, step=0.5, key='design_hours')
            c2.number_input("Valor da hora de design (R$)", min_value=0.0, step=5.0, key='design_rate')
            c1.number_input("Horas de preparo/fatiamento", min_value=0.0, step=0.25, key='slice_hours')
            c2.number_input("Valor da hora de preparo (R$)", min_value=0.0, step=5.0, key='slice_rate')
            c1.number_input("Horas de montagem", min_value=0.0, step=0.25, key='assembly_hours')
            c2.number_input("Valor da hora de montagem (R$)", min_value=0.0, step=5.0, key='assembly_rate')
            c1.number_input("Horas de pós-processamento", min_value=0.0, step=0.25, key='post_process_h')
            c2.number_input("Valor da hora de pós-processamento (R$)", min_value=0.0, step=5.0, key='labor_rate_h')

        with st.expander("🖨️ Custos de Impressão e Material"):
            c1, c2 = st.columns(2)
            c1.number_input("Tempo de impressão (horas)", min_value=0.0, step=0.25, key='print_time_h')
            c1.number_input("Peso do material (gramas)", min_value=0.0, step=1.0, key='material_weight_g')
            c2.number_input("Custo do filamento (R$ por kg)", min_value=0.0, step=10.0, key='filament_cost_kg')
            c2.number_input("Consumo da impressora (Watts)", min_value=0.0, step=10.0, key='printer_consumption_w')
            c1.number_input("Custo da eletricidade (R$ por kWh)", min_value=0.0, step=0.01, format="%.2f", key='kwh_cost')
            c2.number_input("Desgaste da impressora (R$ por hora)", min_value=0.0, step=0.50, format="%.2f", key='printer_wear_rate_h')

        with st.expander("📈 Fatores de Negócio e Risco"):
            c1, c2 = st.columns(2)
            c1.number_input("Taxa de falha (%)", min_value=0.0, max_value=100.0, step=1.0, key='failure_rate_percent')
            c2.number_input("Fator de complexidade (multiplicador)", min_value=1.0, step=0.1, help="Use 1.0 para normal, 1.5 para complexo, etc.", key='complexity_factor')
            c1.number_input("Taxa de urgência (%)", min_value=0.0, max_value=200.0, step=5.0, key='urgency_fee_percent')
            c2.number_input("Margem de lucro (%)", min_value=0.0, step=5.0, key='profit_margin_percent')
    
    submitted = st.form_submit_button("Calcular Preço", type="primary", width='stretch')

if st.button("🧹 Limpar Formulário", width='stretch'):
    st.session_state.clear_calc_form = True
    st.rerun()

if submitted:
    current_inputs = {key: st.session_state[key] for key in DEFAULT_CALC_INPUTS}
    st.session_state.calc_results = calculate_costs(current_inputs)

if 'calc_results' in st.session_state:
    results = st.session_state.calc_results
    final_price = results["Preço de Venda Final"]

    st.markdown("---")
    st.subheader("📊 Resultados da Precificação")
    with st.container(border=True):
        st.success(f"**Preço de Venda Sugerido: R$ {final_price:.2f}**")
        
        with st.expander("Ver detalhamento completo dos custos"):
            st.metric("Custo Total de Mão de Obra", f"R$ {results['Custo de Mão de Obra Total']:.2f}")
            st.metric("Custo de Material", f"R$ {results['Custo de Material']:.2f}")
            st.metric("Custo Total de Impressão (Eletricidade + Desgaste)", f"R$ {results['Custo Total de Impressão']:.2f}")
            st.divider()
            st.metric("Custo de Produção (Subtotal)", f"R$ {results['Custo de Produção']:.2f}")
            st.metric("Custo com Fator de Complexidade", f"R$ {results['Custo com Complexidade']:.2f}", help=f"Multiplicador de {st.session_state.complexity_factor}x aplicado.")
            st.metric("Custo com Taxa de Falha", f"R$ {results['Custo com Taxa de Falha']:.2f}", help=f"{st.session_state.failure_rate_percent}% adicionado ao custo.")
            st.metric("Custo com Taxa de Urgência", f"R$ {results['Custo com Taxa de Urgência']:.2f}", help=f"{st.session_state.urgency_fee_percent}% adicionado ao custo.")
            st.divider()
            st.metric("Preço de Venda Final (com Lucro)", f"R$ {final_price:.2f}", help=f"{st.session_state.profit_margin_percent}% de margem de lucro adicionada.")
