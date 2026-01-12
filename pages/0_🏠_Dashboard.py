import streamlit as st
import pandas as pd
import database

st.set_page_config(
    page_title="Dashboard",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Dashboard de Clientes")

# --- Carregar Dados ---
conn = database.get_db_connection()
df = database.fetch_data(conn)
conn.close()

if df.empty:
    st.info(
        "Ainda não há clientes cadastrados. "
        "Vá para a página de '📝 Cadastro' na barra lateral para começar."
    )
else:
    # --- Métricas Principais ---
    total_clientes = len(df)
    # Garante que a coluna de data é do tipo datetime
    df['data_cadastro'] = pd.to_datetime(df['data_cadastro'])
    cliente_recente = df.sort_values(by='data_cadastro', ascending=False).iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total de Clientes", value=total_clientes)
    with col2:
        st.metric(
            label="Cliente Mais Recente", 
            value=cliente_recente['nome_completo'],
            help=f"Cadastrado em: {cliente_recente['data_cadastro'].strftime('%d/%m/%Y')}"
        )

    st.markdown("---")

    # --- Gráfico de Novos Clientes por Mês ---
    st.subheader("Novos Clientes por Mês")
    df['mes_cadastro'] = df['data_cadastro'].dt.to_period('M').astype(str)
    clientes_por_mes = df.groupby('mes_cadastro').size().reset_index(name='contagem')
    clientes_por_mes = clientes_por_mes.set_index('mes_cadastro')
    
    st.bar_chart(clientes_por_mes)

    # --- Últimos Clientes Cadastrados ---
    st.subheader("Últimos 5 Clientes Cadastrados")
    st.dataframe(
        df[['nome_completo', 'email', 'whatsapp', 'cidade', 'data_cadastro']]
        .sort_values(by='data_cadastro', ascending=False)
        .head(5),
        use_container_width=True,
        hide_index=True,
        column_config={
            "nome_completo": "Nome Completo",
            "email": "E-mail",
            "whatsapp": "WhatsApp",
            "cidade": "Cidade",
            "data_cadastro": st.column_config.DateColumn("Data de Cadastro", format="DD/MM/YYYY")
        }
    )
