import streamlit as st
import pandas as pd
import database as db
import altair as alt
import datetime

st.set_page_config(
    page_title="Dashboard",
    page_icon="🏠"
)

st.title("🏠 Dashboard de Clientes")

# --- Filtro de Data ---
st.subheader("Filtro por Período")
today = datetime.date.today()
start_of_year = datetime.date(today.year, 1, 1)

# Use st.session_state para manter a seleção de data e o estado do filtro
if 'date_range' not in st.session_state:
    st.session_state.date_range = (start_of_year, today)
if 'use_date_filter' not in st.session_state:
    st.session_state.use_date_filter = True # Por padrão, o filtro de data está ativo

# Coloca o checkbox e o date_input lado a lado
col_filter_toggle, col_date_input = st.columns([1, 2])

with col_filter_toggle:
    st.session_state.use_date_filter = st.checkbox(
        "Ativar filtro de data", 
        value=st.session_state.use_date_filter, 
        key="date_filter_checkbox"
    )

current_start_date = None
current_end_date = None

with col_date_input:
    selected_date_range = st.date_input(
        "Selecione o período:",
        value=st.session_state.date_range,
        min_value=datetime.date(2020, 1, 1),
        max_value=today,
        format="DD/MM/YYYY",
        disabled=not st.session_state.use_date_filter
    )

if st.session_state.use_date_filter:
    # Garante que selected_date_range é uma tupla antes de verificar seu comprimento
    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        current_start_date, current_end_date = selected_date_range
        st.session_state.date_range = (current_start_date, current_end_date) # Atualiza o estado da sessão apenas se for válido
    elif isinstance(selected_date_range, datetime.date): # O usuário selecionou apenas uma data
        st.warning("Por favor, selecione um período de início e fim.")
        current_start_date, current_end_date = st.session_state.date_range # Retorna ao intervalo válido anterior
    else: # None ou outra entrada inesperada
        st.warning("Por favor, selecione um período de início e fim.")
        current_start_date, current_end_date = st.session_state.date_range # Retorna ao intervalo válido anterior

st.markdown("---")

# --- Função de Carregamento de Dados ---
@st.cache_data(ttl=600)
def load_data(start, end):
    """Busca todos os dados necessários para o dashboard dentro de um período."""
    try:
        df = db.fetch_dashboard_data(start, end)
        total_count = db.get_total_customers_count() # Sempre o total geral
        # novos_no_periodo será o total de clientes no período *apenas se o filtro de data estiver ativo*
        novos_no_periodo = db.get_new_customers_in_period_count(start, end)
        by_state = db.get_customer_counts_by_state(start, end)
        return df, total_count, novos_no_periodo, by_state
    except db.DatabaseError as e:
        st.error(f"Não foi possível carregar os dados: {e}")
        return pd.DataFrame(), 0, 0, pd.Series()

# --- Carregar Dados ---
df_charts, total_clientes, novos_no_periodo, clientes_por_estado_series = load_data(current_start_date, current_end_date)

if df_charts.empty:
    if st.session_state.use_date_filter:
        st.info(
            f"Ainda não há clientes cadastrados no período de **{current_start_date.strftime('%d/%m/%Y')}** a **{current_end_date.strftime('%d/%m/%Y')}**. "
            "Altere o filtro de data, desative-o ou vá para a página de '📝 Cadastro' para começar."
        )
    else:
        st.info(
            "Ainda não há clientes cadastrados. "
            "Vá para a página de '📝 Cadastro' na barra lateral para começar."
        )
    if st.button("Limpar Cache e Recarregar"):
        st.cache_data.clear()
        st.rerun()
else:
    # --- Métricas Principais ---
    # ... (o restante do código permanece o mesmo)