import streamlit as st
import pandas as pd
import database
import altair as alt
from datetime import datetime

st.set_page_config(
    page_title="Dashboard",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Dashboard de Clientes")

# --- Carregar Dados ---
try:
    df = database.fetch_data(page_size=10000) # Busca um número grande para as métricas gerais
except database.DatabaseError as e:
    st.error(f"Não foi possível carregar os dados do dashboard: {e}")
    st.stop()


if df.empty:
    st.info(
        "Ainda não há clientes cadastrados. "
        "Vá para a página de '📝 Cadastro' na barra lateral para começar."
    )
else:
    # --- Preparação dos Dados ---
    df['data_cadastro'] = pd.to_datetime(df['data_cadastro'])
    
    # --- Métricas Principais ---
    total_clientes = len(df)
    cliente_recente = df.sort_values(by='data_cadastro', ascending=False).iloc[0]
    
    # Novos clientes no mês atual
    now = datetime.now()
    novos_clientes_mes = len(df[df['data_cadastro'].dt.month == now.month])
    
    # Estado com mais clientes
    estado_mais_comum = df['estado'].mode()[0] if not df['estado'].empty else "N/A"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total de Clientes", value=total_clientes)
    with col2:
        st.metric(label="Cliente Mais Recente", 
                  value=cliente_recente['nome_completo'],
                  help=f"Cadastrado em: {cliente_recente['data_cadastro'].strftime('%d/%m/%Y')}")
    with col3:
        st.metric(label="Novos Clientes este Mês", value=novos_clientes_mes)
    with col4:
        st.metric(label="Estado Principal", value=estado_mais_comum)

    st.markdown("---")

    # --- Gráficos ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Novos Clientes por Mês")
        df_chart = df.copy()
        df_chart['mes_cadastro'] = df_chart['data_cadastro'].dt.to_period('M').astype(str)
        clientes_por_mes = df_chart.groupby('mes_cadastro').size().reset_index(name='contagem')
        clientes_por_mes = clientes_por_mes.set_index('mes_cadastro')
        st.bar_chart(clientes_por_mes)

    with col2:
        st.subheader("Clientes por Estado")
        clientes_por_estado = df['estado'].value_counts().reset_index()
        clientes_por_estado.columns = ['estado', 'contagem']
        
        pie_chart = alt.Chart(clientes_por_estado).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="contagem", type="quantitative"),
            color=alt.Color(field="estado", type="nominal", title="Estado"),
            tooltip=['estado', 'contagem']
        ).properties(
            width=300,
            height=300
        )
        st.altair_chart(pie_chart, use_container_width=True)

    st.markdown("---")
    
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Top 5 Cidades")
        top_5_cidades = df['cidade'].value_counts().nlargest(5)
        st.bar_chart(top_5_cidades)

    with col4:
        st.subheader("Últimos 5 Clientes Cadastrados")
        st.dataframe(
            df[['nome_completo', 'email', 'cidade', 'data_cadastro']]
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
