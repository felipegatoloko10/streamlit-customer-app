import streamlit as st
import pandas as pd
import database as db
import altair as alt
import datetime

# --- Page and Helper Function Configuration ---

st.set_page_config(
    page_title="Dashboard",
    page_icon="🏠",
    layout="wide"
)

def create_donut_chart(data: pd.DataFrame, category_col: str, value_col: str, title: str) -> alt.Chart:
    """Cria um gráfico de rosca Altair a partir de um dataframe."""
    return alt.Chart(data).mark_arc(innerRadius=80).encode(
        theta=alt.Theta(field=value_col, type="quantitative"),
        color=alt.Color(field=category_col, type="nominal", title=title),
        tooltip=[category_col, value_col]
    ).properties(
        width=300,
        height=300
    )

# --- State Initialization ---
if 'date_range' not in st.session_state:
    today = datetime.date.today()
    st.session_state.date_range = (datetime.date(today.year, 1, 1), today)
# The 'date_filter_checkbox' key will be initialized by the widget itself.
# Default to True if it doesn't exist yet for the first run.
if 'date_filter_checkbox' not in st.session_state:
    st.session_state.date_filter_checkbox = True

# --- UI: Date Filter ---
st.title("🏠 Dashboard de Clientes")
st.subheader("Filtro por Período")

col_filter_toggle, col_date_input = st.columns([1, 2])
with col_filter_toggle:
    st.checkbox(
        "Ativar filtro de data",
        key="date_filter_checkbox"
    )

with col_date_input:
    # When the date_input is used, its value is stored in st.session_state.date_range
    st.date_input(
        "Selecione o período:",
        key='date_range',
        min_value=datetime.date(2020, 1, 1),
        max_value=datetime.date.today(),
        format="DD/MM/YYYY",
        disabled=not st.session_state.date_filter_checkbox
    )

# --- Logic: Determine Date Range ---
current_start_date, current_end_date = (None, None)
if st.session_state.date_filter_checkbox:
    # Ensure selected_range is a valid tuple of two dates before assigning
    if isinstance(st.session_state.date_range, tuple) and len(st.session_state.date_range) == 2:
        current_start_date, current_end_date = st.session_state.date_range
    else:
        # This case might happen if the state gets corrupted, fallback to a default
        st.warning("O período selecionado é inválido, usando o período padrão.")
        today = datetime.date.today()
        current_start_date, current_end_date = (datetime.date(today.year, 1, 1), today)
        st.session_state.date_range = (current_start_date, current_end_date)

st.markdown("---")

# --- Data Loading ---

@st.cache_data(ttl=600)
def load_data(start, end):
    """Busca todos os dados necessários para o dashboard dentro de um período."""
    try:
        df = db.fetch_dashboard_data(start, end)
        total_count = db.get_total_customers_count()
        novos_no_periodo = db.get_new_customers_in_period_count(start, end) if start and end else total_count
        by_state = db.get_customer_counts_by_state(start, end)
        return df, total_count, novos_no_periodo, by_state
    except db.DatabaseError as e:
        st.error(f"Não foi possível carregar os dados: {e}")
        return pd.DataFrame(), 0, 0, pd.Series()

df_charts, total_clientes, novos_no_periodo, clientes_por_estado_series = load_data(current_start_date, current_end_date)

# --- Main Content ---

if df_charts.empty:
    date_text = f"de **{current_start_date.strftime('%d/%m/%Y')}** a **{current_end_date.strftime('%d/%m/%Y')}**" if use_filter and current_start_date and current_end_date else ""
    st.info(
        f"Ainda não há clientes cadastrados no período {date_text}. "
        "Altere o filtro de data, desative-o ou vá para a página de '📝 Cadastro' para começar."
    )
    if st.button("Limpar Cache e Recarregar"):
        st.cache_data.clear()
        st.rerun()
else:
    df_charts['data_cadastro'] = pd.to_datetime(df_charts['data_cadastro'])
    
    # --- Métricas Principais ---
    cliente_recente = df_charts.sort_values(by='data_cadastro', ascending=False).iloc[0]
    estado_mais_comum = clientes_por_estado_series.index[0] if not clientes_por_estado_series.empty else "N/A"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Total de Clientes (Geral)", value=total_clientes)
    col2.metric(
        label="Cliente Mais Recente (no período)",
        value=cliente_recente['nome_completo'],
        help=f"Cadastrado em: {cliente_recente['data_cadastro'].strftime('%d/%m/%Y')}"
    )
    col3.metric(label="Novos Clientes no Período", value=novos_no_periodo)
    col4.metric(label="Estado Principal (no período)", value=estado_mais_comum)

    st.markdown("---")

    # --- Gráficos ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Novos Clientes por Mês")
        df_chart = df_charts.copy()
        df_chart['mes_cadastro'] = df_chart['data_cadastro'].dt.to_period('M').astype(str)
        clientes_por_mes = df_chart.groupby('mes_cadastro').size().reset_index(name='contagem')
        st.bar_chart(clientes_por_mes, x='mes_cadastro', y='contagem')

    with col2:
        st.subheader("Clientes por Estado")
        if not clientes_por_estado_series.empty:
            clientes_por_estado = clientes_por_estado_series.reset_index()
            clientes_por_estado.columns = ['estado', 'contagem']
            pie_chart = create_donut_chart(clientes_por_estado, 'estado', 'contagem', 'Estado')
            st.altair_chart(pie_chart, use_container_width=True)
        else:
            st.info("Não há dados de estado para exibir no período.")

    st.markdown("---")
    
    col3, col4, col5 = st.columns(3)
    with col3:
        st.subheader("Top 5 Cidades (no período)")
        top_5_cidades = df_charts['cidade'].value_counts().nlargest(5)
        st.bar_chart(top_5_cidades)

    with col4:
        st.subheader("Tipo de Cliente (no período)")
        tipo_cliente = df_charts['tipo_documento'].value_counts().reset_index()
        tipo_cliente.columns = ['tipo', 'contagem']
        donut_chart = create_donut_chart(tipo_cliente, 'tipo', 'contagem', 'Tipo')
        st.altair_chart(donut_chart, use_container_width=True)

    with col5:
        st.subheader("Últimos 5 Clientes (no período)")
        st.dataframe(
            df_charts[['nome_completo', 'email', 'cidade', 'data_cadastro']]
            .sort_values(by='data_cadastro', ascending=False)
            .head(5),
            use_container_width=True,
            hide_index=True,
            column_config={
                "nome_completo": "Nome Completo",
                "email": "E-mail",
                "cidade": "Cidade",
                "data_cadastro": st.column_config.DateColumn("Data de Cadastro", format="DD/MM/YYYY")
            }
        )
    
    if st.button("Limpar Cache e Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()