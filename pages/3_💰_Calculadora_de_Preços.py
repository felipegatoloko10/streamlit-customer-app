import streamlit as st
import json
import os
from streamlit_modal import Modal # Importar Modal

st.set_page_config(
    page_title="Calculadora de Preços",
    page_icon="💰",
    layout="centered"
)

# --- Lógica para limpar o formulário ---
if st.session_state.get("clear_calc_form", False):
    # Reseta o dicionário de inputs para os valores padrão
    st.session_state.calc_inputs = {
        'design_hours': 0.0, 'design_rate': 100.0, 'slice_hours': 0.0, 'slice_rate': 40.0,
        'assembly_hours': 0.0, 'assembly_rate': 30.0, 'post_process_h': 0.0, 'labor_rate_h': 30.0,
        'print_time_h': 0.0, 'material_weight_g': 0.0, 'filament_cost_kg': 120.0,
        'printer_consumption_w': 150.0, 'kwh_cost': 0.78, 'printer_wear_rate_h': 1.50,
        'failure_rate_percent': 5.0, 'complexity_factor': 1.0, 'urgency_fee_percent': 0.0,
        'profit_margin_percent': 50.0
    }
    # Remove os resultados calculados
    if 'calc_results' in st.session_state:
        del st.session_state.calc_results
    st.session_state.clear_calc_form = False # Limpa a flag

# --- Gerenciamento de Predefinições ---
PRESETS_FILE = "data/presets.json"

# Definições de predefinições padrão
DEFAULT_PRESETS = {
    "Pequena Peça Simples": {
        'design_hours': 0.5, 'design_rate': 100.0,
        'slice_hours': 0.25, 'slice_rate': 40.0,
        'assembly_hours': 0.0, 'assembly_rate': 30.0,
        'post_process_h': 0.25, 'labor_rate_h': 30.0,
        'print_time_h': 1.0,
        'material_weight_g': 20.0, 'filament_cost_kg': 120.0,
        'printer_consumption_w': 150.0, 'kwh_cost': 0.78,
        'printer_wear_rate_h': 1.50,
        'failure_rate_percent': 5.0,
        'complexity_factor': 1.0,
        'urgency_fee_percent': 0.0,
        'profit_margin_percent': 50.0
    },
    "Médio Complexo": {
        'design_hours': 2.0, 'design_rate': 100.0,
        'slice_hours': 1.0, 'slice_rate': 40.0,
        'assembly_hours': 0.5, 'assembly_rate': 30.0,
        'post_process_h': 1.0, 'labor_rate_h': 30.0,
        'print_time_h': 5.0,
        'material_weight_g': 100.0, 'filament_cost_kg': 120.0,
        'printer_consumption_w': 150.0, 'kwh_cost': 0.78,
        'printer_wear_rate_h': 1.50,
        'failure_rate_percent': 10.0,
        'complexity_factor': 1.2,
        'urgency_fee_percent': 0.0,
        'profit_margin_percent': 60.0
    },
    "Grande Peça Detalhada": {
        'design_hours': 5.0, 'design_rate': 100.0,
        'slice_hours': 2.0, 'slice_rate': 40.0,
        'assembly_hours': 1.0, 'assembly_rate': 30.0,
        'post_process_h': 2.0, 'labor_rate_h': 30.0,
        'print_time_h': 12.0,
        'material_weight_g': 300.0, 'filament_cost_kg': 120.0,
        'printer_consumption_w': 150.0, 'kwh_cost': 0.78,
        'printer_wear_rate_h': 1.50,
        'failure_rate_percent': 15.0,
        'complexity_factor': 1.5,
        'urgency_fee_percent': 0.0,
        'profit_margin_percent': 70.0
    },
    "Prototipagem Rápida": {
        'design_hours': 1.0, 'design_rate': 100.0,
        'slice_hours': 0.5, 'slice_rate': 40.0,
        'assembly_hours': 0.0, 'assembly_rate': 30.0,
        'post_process_h': 0.0, 'labor_rate_h': 30.0,
        'print_time_h': 3.0,
        'material_weight_g': 50.0, 'filament_cost_kg': 120.0,
        'printer_consumption_w': 150.0, 'kwh_cost': 0.78,
        'printer_wear_rate_h': 1.50,
        'failure_rate_percent': 5.0,
        'complexity_factor': 1.0,
        'urgency_fee_percent': 0.0,
        'profit_margin_percent': 40.0
    },
    "Serviço Urgente": {
        'design_hours': 1.0, 'design_rate': 100.0,
        'slice_hours': 0.5, 'slice_rate': 40.0,
        'assembly_hours': 0.0, 'assembly_rate': 30.0,
        'post_process_h': 0.5, 'labor_rate_h': 30.0,
        'print_time_h': 2.0,
        'material_weight_g': 30.0, 'filament_cost_kg': 120.0,
        'printer_consumption_w': 150.0, 'kwh_cost': 0.78,
        'printer_wear_rate_h': 1.50,
        'failure_rate_percent': 5.0,
        'complexity_factor': 1.0,
        'urgency_fee_percent': 25.0,
        'profit_margin_percent': 50.0
    }
}

def load_presets():
    """Carrega as predefinições do arquivo JSON ou retorna as padrão."""
    if os.path.exists(PRESETS_FILE):
        with open(PRESETS_FILE, 'r') as f:
            saved_presets = json.load(f)
            if saved_presets: # Se houver predefinições salvas, use-as
                return saved_presets
    # Se o arquivo não existir ou estiver vazio, use as predefinições padrão
    return DEFAULT_PRESETS

def save_presets(presets):
    """Salva as predefinições no arquivo JSON."""
    # Garante que o diretório 'data' exista
    os.makedirs(os.path.dirname(PRESETS_FILE), exist_ok=True)
    with open(PRESETS_FILE, 'w') as f:
        json.dump(presets, f, indent=4)

# --- Título e Interface de Predefinições ---
st.title("💰 Calculadora de Preço para Impressão 3D")
st.markdown("Preencha os campos abaixo e clique em 'Calcular' para gerar o preço de venda.")

with st.expander("💾 Gerenciar Predefinições", expanded=True):
    presets = load_presets()
    
    col_select, col_load, col_delete = st.columns([0.7, 0.15, 0.15]) # Ajusta as proporções das colunas
    
    with col_select:
        preset_options = [""] + list(presets.keys())
        selected_preset = st.selectbox("Selecione uma predefinição:", options=preset_options, label_visibility="collapsed")

    with col_load:
        if st.button("Carregar", use_container_width=True, disabled=not selected_preset): # Corrigido use_container_width
            st.session_state.calc_inputs = presets[selected_preset]
            if 'calc_results' in st.session_state:
                del st.session_state.calc_results
            st.success(f"Predefinição '{selected_preset}' carregada!")
            st.rerun()
    
    with col_delete:
        # Usando modal para confirmação de exclusão
        delete_modal = Modal(title=f"Confirmar Exclusão: {selected_preset}", key="delete_preset_modal")
        if st.button("🗑️", use_container_width=True, disabled=not selected_preset, help="Excluir predefinição selecionada"): # Corrigido use_container_width
            if selected_preset in presets:
                delete_modal.open()
            else:
                st.error("Predefinição não encontrada para exclusão.")
        
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
                        st.rerun() # Reruns to update the selectbox
                with col_cancel:
                    st.button("Cancelar", on_click=delete_modal.close)
            
    st.markdown("---")

    # --- Lógica para Salvar Predefinição com Modal ---
    save_modal = Modal("Salvar Predefinição", key="save_preset_modal")
    if st.button("💾 Salvar Configuração Atual", use_container_width=True):
        save_modal.open()

    if save_modal.is_open():
        with save_modal.container():
            new_preset_name = st.text_input("Nome da nova predefinição:", placeholder="Ex: Peça Pequena PLA")
            if st.button("Salvar", type="primary"):
                if new_preset_name:
                    # Salva os valores que estão atualmente nos inputs do formulário
                    presets[new_preset_name] = st.session_state.calc_inputs
                    save_presets(presets)
                    st.success(f"Predefinição '{new_preset_name}' salva!")
                    save_modal.close()
                    st.rerun()
                else:
                    st.warning("Por favor, dê um nome para a predefinição.")


# --- Dicionário para guardar todos os inputs ---
if 'calc_inputs' not in st.session_state:
    # Inicializa com valores neutros para que nenhum cálculo seja exibido na primeira carga
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
    cost_per_gram = inputs['filament_cost_kg'] / 1000 if inputs['filament_cost_kg'] > 0 else 0
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

st.markdown("---")
st.subheader("⚙️ Insira os Dados do Projeto")

# Envolve todos os inputs em um formulário
with st.form("price_calculator_form"):
    with st.container(border=True):
        with st.expander("👨‍💻 Custos de Mão de Obra e Tempo", expanded=True):
            c1, c2 = st.columns(2)
            # Os widgets são definidos e seus valores lidos em variáveis locais.
            # O valor inicial é sempre lido do 'inputs' (que vem do st.session_state).
            design_hours = c1.number_input("Horas de design (SolidWorks)", min_value=0.0, step=0.5, value=inputs['design_hours'])
            design_rate = c2.number_input("Valor da hora de design (R$)", min_value=0.0, step=5.0, value=inputs['design_rate'])
            slice_hours = c1.number_input("Horas de preparo/fatiamento", min_value=0.0, step=0.25, value=inputs['slice_hours'])
            slice_rate = c2.number_input("Valor da hora de preparo (R$)", min_value=0.0, step=5.0, value=inputs['slice_rate'])
            assembly_hours = c1.number_input("Horas de montagem", min_value=0.0, step=0.25, value=inputs['assembly_hours'])
            assembly_rate = c2.number_input("Valor da hora de montagem (R$)", min_value=0.0, step=5.0, value=inputs['assembly_rate'])
            post_process_h = c1.number_input("Horas de pós-processamento", min_value=0.0, step=0.25, value=inputs['post_process_h'])
            labor_rate_h = c2.number_input("Valor da hora de pós-processamento (R$)", min_value=0.0, step=5.0, value=inputs['labor_rate_h'])

        with st.expander("🖨️ Custos de Impressão e Material"):
            c1, c2 = st.columns(2)
            print_time_h = c1.number_input("Tempo de impressão (horas)", min_value=0.0, step=0.25, value=inputs['print_time_h'])
            material_weight_g = c1.number_input("Peso do material (gramas)", min_value=0.0, step=1.0, value=inputs['material_weight_g'])
            filament_cost_kg = c2.number_input("Custo do filamento (R$ por kg)", min_value=0.0, step=10.0, value=inputs['filament_cost_kg'])
            printer_consumption_w = c1.number_input("Consumo da impressora (Watts)", min_value=0.0, step=10.0, value=inputs['printer_consumption_w'])
            kwh_cost = c2.number_input("Custo da eletricidade (R$ por kWh)", min_value=0.0, step=0.01, format="%.2f", value=inputs['kwh_cost'])
            printer_wear_rate_h = c2.number_input("Desgaste da impressora (R$ por hora)", min_value=0.0, step=0.50, format="%.2f", value=inputs['printer_wear_rate_h'])

        with st.expander("📈 Fatores de Negócio e Risco"):
            c1, c2 = st.columns(2)
            failure_rate_percent = c1.number_input("Taxa de falha (%)", min_value=0.0, max_value=100.0, step=1.0, value=inputs['failure_rate_percent'])
            complexity_factor = c2.number_input("Fator de complexidade (multiplicador)", min_value=1.0, step=0.1, help="Use 1.0 para normal, 1.5 para complexo, etc.", value=inputs['complexity_factor'])
            urgency_fee_percent = c1.number_input("Taxa de urgência (%)", min_value=0.0, max_value=200.0, step=5.0, value=inputs['urgency_fee_percent'])
            profit_margin_percent = c2.number_input("Margem de lucro (%)", min_value=0.0, step=5.0, value=inputs['profit_margin_percent'])
    
    # Botão de submit para o formulário
    submitted = st.form_submit_button("Calcular Preço", type="primary", use_container_width=True)

# O botão de limpar deve ficar fora do formulário
if st.button("🧹 Limpar Formulário", use_container_width=True):
    st.session_state.clear_calc_form = True
    st.rerun()

# --- Lógica de Cálculo e Exibição ---
if submitted:
    # Apenas quando o formulário é enviado, criamos o dicionário com os valores atuais dos widgets
    current_inputs = {
        'design_hours': design_hours, 'design_rate': design_rate, 'slice_hours': slice_hours, 'slice_rate': slice_rate,
        'assembly_hours': assembly_hours, 'assembly_rate': assembly_rate, 'post_process_h': post_process_h, 'labor_rate_h': labor_rate_h,
        'print_time_h': print_time_h, 'material_weight_g': material_weight_g, 'filament_cost_kg': filament_cost_kg,
        'printer_consumption_w': printer_consumption_w, 'kwh_cost': kwh_cost, 'printer_wear_rate_h': printer_wear_rate_h,
        'failure_rate_percent': failure_rate_percent, 'complexity_factor': complexity_factor, 'urgency_fee_percent': urgency_fee_percent,
        'profit_margin_percent': profit_margin_percent
    }
    # Salvamos o estado atual e calculamos os resultados
    st.session_state.calc_inputs = current_inputs
    st.session_state.calc_results = calculate_costs(current_inputs)

# Exibe os resultados apenas se eles existirem no estado da sessão
if 'calc_results' in st.session_state:
    results = st.session_state.calc_results
    final_price = results["Preço de Venda Final"]

    st.markdown("---")
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
            st.metric("Custo com Fator de Complexidade", f"R$ {results['Custo com Complexidade']:.2f}", help=f"Multiplicador de {st.session_state.calc_inputs['complexity_factor']}x aplicado.")
            st.metric("Custo com Taxa de Falha", f"R$ {results['Custo com Taxa de Falha']:.2f}", help=f"{st.session_state.calc_inputs['failure_rate_percent']}% adicionado ao custo.")
            st.metric("Custo com Taxa de Urgência", f"R$ {results['Custo com Taxa de Urgência']:.2f}", help=f"{st.session_state.calc_inputs['urgency_fee_percent']}% adicionado ao custo.")
            st.divider()
            st.metric("Preço de Venda Final (com Lucro)", f"R$ {final_price:.2f}", help=f"{st.session_state.calc_inputs['profit_margin_percent']}% de margem de lucro adicionada.")
