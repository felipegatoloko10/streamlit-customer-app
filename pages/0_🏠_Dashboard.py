import streamlit as st
import pandas as pd
import pydeck as pdk
import json
import datetime
import integration_services as services
from services.customer_service import CustomerService

customer_service = CustomerService()

st.set_page_config(
    page_title="Dashboard",
    page_icon="🏠",
    layout="wide"
)

# Exibe o status da nuvem na sidebar
services.show_cloud_status()

# --- Lógica de Filtro de Data ---
with st.sidebar:
    st.subheader("Filtro de Período")
    period_choice = st.radio("Exibir clientes de:", ["Todo o Período", "Este Ano", "Últimos 30 Dias"], index=0)

today = datetime.date.today()
if period_choice == "Este Ano":
    start_date = datetime.date(today.year, 1, 1)
elif period_choice == "Últimos 30 Dias":
    start_date = today - datetime.timedelta(days=30)
else:
    start_date = datetime.date(2000, 1, 1) # Todo o período

st.info(f"📊 Exibindo dados de **{start_date.strftime('%d/%m/%Y')}** até **{today.strftime('%d/%m/%Y')}**")


# --- Estrutura de Abas ---
tab_overview, tab_geo, tab_health = st.tabs([
    "Visão Geral", 
    "Análise Geográfica", 
    "Saúde dos Dados"
])

with tab_overview:
    st.header("Visão Geral do Crescimento de Clientes")

    # Adicionar KPIs
    total_geral = customer_service.count_customers()
    
    ts_df_kpi = customer_service.get_new_customers_timeseries(start_date, today, period='D')
    novos_no_periodo = ts_df_kpi['count'].sum() if not ts_df_kpi.empty else 0


    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total de Clientes (Base)", value=total_geral)
    with col2:
        st.metric(label="Clientes no Período Selecionado", value=novos_no_periodo)
    with col3:
        st.metric(label="Saúde da Base", value=f"{customer_service.get_data_health_summary().get('email_completeness', 0):.1f}%", help="Porcentagem de clientes com e-mail cadastrado")

    st.markdown("---")

    # Gráfico de Série Temporal Interativo
    st.subheader("Novos Clientes ao Longo do Tempo")
    
    periodo = st.selectbox(
        "Agregar por:",
        options=['Diário', 'Semanal', 'Mensal'],
        index=0 if period_choice == "Últimos 30 Dias" else 2
    )

    period_map = {'Diário': 'D', 'Semanal': 'W', 'Mensal': 'M'}
    ts_data = customer_service.get_new_customers_timeseries(start_date, today, period=period_map[periodo])
    
    if not ts_data.empty:
        ts_data = ts_data.set_index('time_period')
        st.line_chart(ts_data)
    else:
        st.info("Não há dados de novos clientes no período selecionado.")

with tab_geo:
    st.header("Mapa de Distribuição de Clientes")

    # Filtramos as localizações também pelo período no banco de dados
    # Para isso, precisamos atualizar a função get_customer_locations no database.py em um passo futuro, 
    # mas por agora vamos filtrar o DF aqui para ser mais rápido.
    customer_locations_df = customer_service.get_customer_locations()
    
    # Nota: Como get_customer_locations não recebe data, vamos mostrar TODOS no mapa por padrão 
    # para garantir que você veja seus pontos.
    
    if not customer_locations_df.empty:
        # Calculate initial view state based on customer locations
        avg_lat = customer_locations_df['latitude'].mean()
        avg_lon = customer_locations_df['longitude'].mean()

        st.pydeck_chart(pdk.Deck(
            initial_view_state=pdk.ViewState(
                latitude=avg_lat,
                longitude=avg_lon,
                zoom=3.5,
                pitch=40,
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=customer_locations_df,
                    get_position='[longitude, latitude]',
                    get_color='[0, 104, 201, 160]', # Azul Streamlit
                    get_radius=20000, 
                    pickable=True,
                ),
            ],
            tooltip={
                "html": "<b>{nome_completo}</b><br/>{cidade} - {estado}",
                "style": {"backgroundColor": "#0068c9", "color": "white"}
            }
        ))
        
        st.bar_chart(customer_locations_df['estado'].value_counts()) 
    else:
        st.info("Não há dados de localização para exibir.")

with tab_health:
    st.header("Análise da Qualidade dos Dados dos Clientes")

    health_summary = customer_service.get_data_health_summary()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Completude de E-mail",
            value=f"{health_summary.get('email_completeness', 0):.2f}%"
        )
    with col2:
        st.metric(
            label="Completude de Telefone",
            value=f"{health_summary.get('phone_completeness', 0):.2f}%"
        )
    with col3:
        st.metric(
            label="Completude de CEP",
            value=f"{health_summary.get('cep_completeness', 0):.2f}%"
        )
    
    st.markdown("---")

    st.subheader("Clientes com Dados Incompletos")
    incomplete_data = customer_service.get_incomplete_customers()

    if not incomplete_data.empty:
        st.dataframe(incomplete_data, hide_index=True)
    else:
        st.success("Parabéns! Todos os seus clientes têm dados essenciais completos.")