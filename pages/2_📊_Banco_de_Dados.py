import streamlit as st
import pandas as pd
import datetime

import math
import logging
import urllib.parse
import integration_services as services
from services.customer_service import CustomerService, DatabaseError, DuplicateEntryError
import base64

# Inicializa o serviço
customer_service = CustomerService()
import os
import validators

# --- Configurações da Página e Constantes ---
st.set_page_config(
    page_title="Banco de Dados de Clientes",
    page_icon="📊",
    layout="centered"
)
EXPORT_LIMIT = 20000

@st.cache_data
def load_whatsapp_icon_b64():
    """Lê a imagem do ícone do WhatsApp e a converte para base64, com cache."""
    image_path = os.path.join(os.path.dirname(__file__), '..', 'whatsapp.png')
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        st.warning("Arquivo 'whatsapp.png' não encontrado. O ícone do WhatsApp não será exibido.")
        return None

WHATSAPP_ICON = load_whatsapp_icon_b64()

# --- Lógica de Roteamento via URL ---
if "id" in st.query_params:
    try:
        customer_id_from_url = int(st.query_params["id"])
        st.session_state.selected_customer_id = customer_id_from_url
        st.session_state.came_from_url = True
        st.query_params.clear()
    except (ValueError, TypeError):
        st.query_params.clear()

# --- Funções Auxiliares de UI ---

def display_field_with_copy(label, value, is_date=False, is_text_area=False):
    """Exibe um campo de texto não editável com um botão para copiar."""
    display_value = ""
    if is_date and isinstance(value, (datetime.date, datetime.datetime)):
        display_value = value.strftime("%d/%m/%Y")
    elif value is not None:
        display_value = str(value)
    
    st.text(label)
    if display_value:
        st.code(display_value, language=None)

def editable_field(label: str, value: any, key: str, is_date=False, is_text_area=False, help_text=None, is_phone=False):
    """
    Exibe um campo editável ou estático, com tratamento especial para campos de telefone.
    """
    if st.session_state.get('edit_mode', False):
        display_value = value if value is not None else ""
        if is_date:
            st.session_state.edited_data[key] = st.date_input(label, value=value, key=f"edit_{key}", help=help_text, format="DD/MM/YYYY")
        elif is_text_area:
            st.session_state.edited_data[key] = st.text_area(label, value=display_value, key=f"edit_{key}", help=help_text)
        elif is_phone:
            # Unformat phone number for editing
            unformatted_value = validators.unformat_whatsapp(display_value)
            st.session_state.edited_data[key] = st.text_input(label, value=unformatted_value, key=f"edit_{key}", help=help_text)
            if WHATSAPP_ICON and unformatted_value:
                 whatsapp_url = validators.get_whatsapp_url(unformatted_value)
                 st.markdown(
                     f"""
                     <div style="text-align: right; margin-top: -30px; margin-bottom: 20px;">
                         <a href="{whatsapp_url}" target="_blank">
                             <img src="data:image/png;base64,{WHATSAPP_ICON}" width="25">
                         </a>
                     </div>
                     """, 
                     unsafe_allow_html=True
                 )
        else:
            st.session_state.edited_data[key] = st.text_input(label, value=display_value, key=f"edit_{key}", help=help_text)
    else:
        # View mode (original logic)
        if is_phone:
            col_text, col_icon = st.columns([0.9, 0.1])
            with col_text:
                display_field_with_copy(label, value, is_date, is_text_area)
            with col_icon:
                if value and WHATSAPP_ICON:
                    unformatted_phone = validators.unformat_whatsapp(value)
                    whatsapp_url = validators.get_whatsapp_url(unformatted_phone)
                    st.markdown(
                        f"""
                        <div style="padding-top: 45px;">
                            <a href="{whatsapp_url}" target="_blank">
                                <img src="data:image/png;base64,{WHATSAPP_ICON}" width="25">
                            </a>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
        else:
            display_field_with_copy(label, value, is_date, is_text_area)

# --- Título e Mensagens de Status ---
st.title("📊 Banco de Dados de Clientes")

if 'db_status' in st.session_state:
    status = st.session_state.pop('db_status')
    if status.get('success'):
        st.success(status['message'])
    else:
        st.error(status['message'])

# --- Sidebar Filters ---
with st.sidebar:
    services.show_cloud_status()
    st.header("Filtros e Ações")
    search_query = st.text_input("Buscar por Nome ou CPF")
    
    try:
        all_states_list = customer_service.get_unique_states()
        state_options = ["Todos"] + all_states_list
        state_filter = st.selectbox("Filtrar por Estado", options=state_options)
    except Exception:
        st.error("Filtros indisponíveis.")
        st.stop()

    st.markdown("---")
    st.subheader("Configuração da Tabela")
    
    # Mapa de colunas amigáveis
    COLUMN_OPTIONS = {
        "id": "ID",
        "nome_completo": "Nome/Razão Social",
        "tipo_documento": "Tipo Doc.",
        "cpf": "CPF",
        "cnpj": "CNPJ",
        "telefone1": "Telefone 1",
        "link_wpp_1": "WhatsApp 🔗",
        "email": "E-mail",
        "cargo": "Cargo",
        "contato1": "Nome Contato",
        "data_nascimento": "Nascimento/Fundação",
        "data_cadastro": "Data Cadastro",
        "cidade": "Cidade",
        "estado": "Estado",
        "cep": "CEP",
        "endereco": "Endereço",
        "numero": "Nº",
        "bairro": "Bairro",
        "observacao": "Observações"
    }

    default_cols = ["id", "nome_completo", "link_wpp_1", "telefone1", "cidade", "estado"]
    selected_col_labels = st.multiselect(
        "Colunas visíveis:", 
        options=list(COLUMN_OPTIONS.values()),
        default=[COLUMN_OPTIONS[c] for c in default_cols]
    )
    
    # Inverter o mapa para pegar as chaves técnicas
    selected_columns = [k for k, v in COLUMN_OPTIONS.items() if v in selected_col_labels]

    st.markdown("---")
    page_size = st.selectbox("Itens por página", options=[10, 25, 50, 100], index=0)
    total_records = customer_service.count_customers(search_query, state_filter)
    total_pages = math.ceil(total_records / page_size) if total_records > 0 else 1
    page_number = st.number_input('Página', min_value=1, max_value=total_pages, value=1, step=1)
    st.markdown("---")

# --- Functions for Displaying Content ---

def show_customer_details(customer_id):
    try:
        customer = customer_service.get_customer_details(customer_id)
    except DatabaseError as e:
        st.error(f"Erro ao buscar dados do cliente: {e}")
        customer = None

    if customer:
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False
        if 'edited_data' not in st.session_state:
            st.session_state.edited_data = {}

        st.subheader(f"Detalhes de: {customer.get('nome_completo')}")

        col_close, col_map, col_edit, col_delete = st.columns([0.4, 0.2, 0.2, 0.2])
        
        with col_close:
            if st.button("⬅️ Fechar Detalhes", use_container_width=True):
                st.session_state.edit_mode = False
                st.session_state.confirming_delete = False
                del st.session_state.selected_customer_id
                st.rerun()

        with col_map:
            address_parts = [
                customer.get('endereco'),
                customer.get('numero'),
                customer.get('bairro'),
                customer.get('cidade'),
                customer.get('estado'),
                customer.get('cep')
            ]
            
            full_address_for_maps = ", ".join(filter(None, address_parts))
            
            if full_address_for_maps:
                query_address_encoded = urllib.parse.quote_plus(full_address_for_maps)
                google_maps_url = f"https://www.google.com/maps/search/?api=1&query={query_address_encoded}"
                st.link_button("📍 Abrir no Mapa", url=google_maps_url, help="Abrir endereço do cliente no Google Maps", type="secondary", use_container_width=True)
            else:
                st.button("📍 Abrir no Mapa", help="Endereço não disponível para navegação", disabled=True, use_container_width=True)
        
        with col_edit:
            if st.session_state.edit_mode:
                if st.button("💾 Salvar Alterações", use_container_width=True, type="primary"):
                    try:
                        # Constrói o endereço completo para geocodificação
                        current_address = st.session_state.edited_data.get('endereco', '')
                        current_numero = st.session_state.edited_data.get('numero', '')
                        current_bairro = st.session_state.edited_data.get('bairro', '')
                        current_cidade = st.session_state.edited_data.get('cidade', '')
                        current_estado = st.session_state.edited_data.get('estado', '')
                        current_cep = st.session_state.edited_data.get('cep', '')

                        full_address = f"{current_address}, {current_numero}, {current_bairro}, {current_cidade}, {current_estado}"
                        latitude, longitude = services.get_coords_for_address(full_address, current_cep)

                        st.session_state.edited_data['latitude'] = latitude
                        st.session_state.edited_data['longitude'] = longitude

                        customer_service.update_customer(customer_id, st.session_state.edited_data)
                        st.session_state['db_status'] = {'success': True, 'message': "Cliente atualizado com sucesso!"}
                        
                        st.session_state.edit_mode = False
                        st.session_state.edited_data = {}
                        st.rerun()

                    except (DatabaseError, DuplicateEntryError) as e:
                        st.session_state['db_status'] = {'success': False, 'message': str(e)}
                        st.rerun()

            else:
                if st.button("✏️ Editar Cliente", use_container_width=True):
                    st.session_state.edit_mode = True
                    st.session_state.edited_data = customer.copy()
                    st.rerun()

        with col_delete:
            # Initialize confirmation state
            if 'confirming_delete' not in st.session_state:
                st.session_state.confirming_delete = False

            # Se o modo de edição estiver ativo, não mostre o botão de exclusão
            if not st.session_state.edit_mode:
                if st.session_state.confirming_delete:
                    st.warning(f"Tem certeza que deseja excluir **{customer.get('nome_completo')}**? Esta ação não pode ser desfeita.")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Sim, excluir permanentemente", type="primary", use_container_width=True):
                            try:
                                customer_service.delete_customer(customer_id)
                                st.session_state['db_status'] = {'success': True, 'message': "Cliente excluído com sucesso!"}
                                st.session_state.confirming_delete = False
                                del st.session_state.selected_customer_id
                                st.rerun()
                            except DatabaseError as e:
                                st.session_state['db_status'] = {'success': False, 'message': str(e)}
                                st.session_state.confirming_delete = False
                                st.rerun()
                    with c2:
                        if st.button("Cancelar", use_container_width=True):
                            st.session_state.confirming_delete = False
                            st.rerun()
                else:
                    if st.button("🗑️ Excluir Cliente", use_container_width=True):
                        st.session_state.confirming_delete = True
                        st.rerun()

        st.markdown("---")

        with st.container(border=True):
            st.subheader("Dados Principais")
            tipo_doc = customer.get('tipo_documento')
            label_doc = "CPF" if tipo_doc == "CPF" else "CNPJ"
            valor_doc = customer.get('cpf') or customer.get('cnpj')

            editable_field('Nome Completo / Razão Social', customer.get('nome_completo'), 'nome_completo')
            editable_field(label_doc, valor_doc, 'cpf' if tipo_doc == 'CPF' else 'cnpj')
            
            col_email, col_data = st.columns(2)
            with col_email:
                editable_field('E-mail', customer.get('email'), 'email')
            with col_data:
                editable_field('Data de Nascimento / Fundação', customer.get('data_nascimento'), 'data_nascimento', is_date=True)

        with st.expander("Contatos", expanded=True):
            editable_field("Nome do Contato 1", customer.get('contato1'), 'contato1')
            editable_field('Telefone 1', customer.get('telefone1'), 'telefone1', is_phone=True)
            editable_field("Cargo do Contato 1", customer.get('cargo'), 'cargo')
            
            st.markdown("---")
            editable_field("Nome do Contato 2", customer.get('contato2'), 'contato2')
            editable_field('Telefone 2', customer.get('telefone2'), 'telefone2', is_phone=True)

        with st.expander("Endereço", expanded=True):
            editable_field("CEP", customer.get("cep"), 'cep')
            col_end, col_num = st.columns([3, 1])
            with col_end:
                editable_field('Endereço', customer.get('endereco'), 'endereco')
            with col_num:
                editable_field('Número', customer.get('numero'), 'numero')

            col_bairro, col_comp = st.columns(2)
            with col_bairro:
                editable_field('Bairro', customer.get('bairro'), 'bairro')
            with col_comp:
                editable_field('Complemento', customer.get('complemento'), 'complemento')

            col_cidade, col_estado = st.columns([3, 1])
            with col_cidade:
                editable_field('Cidade', customer.get('cidade'), 'cidade')
            with col_estado:
                editable_field('UF', customer.get('estado'), 'estado')

        with st.expander("Observações", expanded=True):
            editable_field("Observações", customer.get('observacao'), 'observacao', is_text_area=True)

        with st.container(border=True):
            st.subheader("Informações do Sistema")
            display_field_with_copy("Data de Cadastro", customer.get("data_cadastro"), is_date=True)
            display_field_with_copy("ID do Cliente", customer.get("id"))

    else:
        st.error(f"Cliente com ID {customer_id} não encontrado.")
        if st.button("⬅️ Voltar para a lista"):
            del st.session_state.selected_customer_id
            st.rerun()

def show_customer_grid(search_query, state_filter, page_number, page_size, total_records, total_pages, selected_columns, column_labels_map):
    grid_data = customer_service.get_customer_grid_data(search_query, state_filter, page_number, page_size)
    df_page = pd.DataFrame(grid_data)
    if not df_page.empty:
        st.info("Selecione um cliente na tabela para ver seus detalhes completos.")
        
        # Configuração dinâmica de colunas
        column_config = {
            "id": st.column_config.NumberColumn("ID"),
            "link_wpp_1": st.column_config.LinkColumn("WhatsApp", display_text="🔗 Abrir"),
            "data_nascimento": st.column_config.DateColumn("Nascimento"),
            "data_cadastro": st.column_config.DateColumn("Cadastro")
        }
        
        # Adiciona os nomes amigáveis para as colunas que não têm config especial
        for col in selected_columns:
            if col not in column_config:
                column_config[col] = column_labels_map.get(col, col)

        st.dataframe(
            df_page[[col for col in selected_columns if col in df_page.columns]],
            key="customer_grid", on_select="rerun", selection_mode="single-row",
            hide_index=True, column_config=column_config, width='stretch'
        )
        st.markdown(f"Mostrando **{len(df_page)}** de **{total_records}** registros. Página **{page_number}** de **{total_pages}**.")
        
        if st.session_state.customer_grid['selection']['rows']:
            selected_id = int(df_page.iloc[st.session_state.customer_grid['selection']['rows'][0]]['id'])
            st.session_state.selected_customer_id = selected_id
            st.rerun()

    else:
        st.info("Nenhum cliente cadastrado corresponde aos filtros aplicados.")
        if st.button("➕ Cadastrar Novo Cliente"):
            st.switch_page("pages/1_📝_Cadastro.py")

# --- Main Application Logic ---
if "selected_customer_id" in st.session_state and st.session_state.selected_customer_id:
    show_customer_details(st.session_state.selected_customer_id)
else:
    show_customer_grid(search_query, state_filter, page_number, page_size, total_records, total_pages, selected_columns, COLUMN_OPTIONS)