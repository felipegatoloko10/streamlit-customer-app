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
tab_overview, tab_geo, tab_health, tab_bot = st.tabs([
    "Visão Geral", 
    "Análise Geográfica", 
    "Saúde dos Dados",
    "🤖 Bot Atendimento"
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

with tab_bot:
    st.header("🤖 Configuração e Logs do Bot")
    
    # Carregar configuração
    CONFIG_FILE = "bot_config.json"
    config = {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        pass
    
    # Toggle de Ativação
    col_status, col_conf = st.columns([1, 2])
    
    with col_status:
        st.subheader("Status")
        
        # Carrega configuração atual
        bot_active = st.toggle("Bot Ativo", value=config.get("bot_active", False))
        
        # Salva se mudou
        if bot_active != config.get("bot_active", False):
            config["bot_active"] = bot_active
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            st.rerun()
            
        # --- Lógica de Thread Nativa ---
        from services.bot_engine import BotRunner, get_bot_runner
        
        runner = get_bot_runner()
        
        if bot_active:
            if not runner:
                st.info("Iniciando motor do bot...")
                try:
                    runner = BotRunner()
                    runner.start()
                    st.rerun() # Recarrega para mostrar status atualizado
                except Exception as e:
                    st.error(f"Erro ao iniciar bot: {e}")
            else:
                st.success("🟢 Bot Rodando (Nativo)")
                st.caption(f"Thread ID: {runner.ident}")
                if st.button("🔄 Reiniciar Motor", help="Use se o bot parar de responder"):
                    runner.stop()
                    st.rerun()
        else:
            if runner:
                st.warning("🟡 Bot Pausado (Dormindo)")
                if st.button("🛑 Parar Motor"):
                    runner.stop()
                    st.rerun()
            else:
                st.error("🔴 Bot Parado")


    with col_conf:
        with st.expander("Configurações da API"):
            new_evo_url = st.text_input("Evolution API URL", value=config.get("evolution_api_url", ""))
            new_evo_token = st.text_input("Evolution API Token", value=config.get("evolution_api_token", ""), type="password")
            new_evo_instance = st.text_input("Evolution Instance Name", value=config.get("evolution_instance_name", "BotFeh"))
            new_gemini_key = st.text_input("Gemini API Key", value=config.get("gemini_key", ""), type="password")
            
            if st.button("Salvar Configurações"):
                config["evolution_api_url"] = new_evo_url
                config["evolution_api_token"] = new_evo_token
                config["evolution_instance_name"] = new_evo_instance
                config["gemini_key"] = new_gemini_key
                config["bot_active"] = bot_active # Mantém o estado
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config, f, indent=4)
                st.success("Configurações salvas!")

    st.markdown("---")
    
    # Visualizador de Logs e Histórico
    col_logs, col_chat = st.columns([1, 1])
    
    with col_logs:
        st.subheader("Logs do Sistema (bot.log)")
        if st.button("Atualizar Logs"):
            st.rerun()
        
        log_content = "Nenhum log encontrado."
        try:
            with open("bot.log", "r", encoding="utf-8") as f:
                lines = f.readlines()
                log_content = "".join(lines[-20:]) # Últimas 20 linhas
        except FileNotFoundError:
            pass
            
        st.code(log_content, language="text")

    with col_chat:
        st.subheader("Últimas Conversas")
        import database
        try:
            recent_chats = database.get_recent_chats_summary(limit=10)
            if not recent_chats.empty:
                st.dataframe(recent_chats, hide_index=True)
            else:
                st.info("Nenhuma conversa registrada ainda.")
        except Exception as e:
            st.error(f"Erro ao carregar conversas: {e}")