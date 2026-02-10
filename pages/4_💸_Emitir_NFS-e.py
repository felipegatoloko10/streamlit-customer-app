import streamlit as st
import integration_services as services

st.set_page_config(
    page_title="Emitir NFS-e",
    page_icon="💸",
    layout="centered"
)

# Exibe o status da nuvem na sidebar
services.show_cloud_status()

st.title("💸 Emitir Nota Fiscal de Serviço eletrônica (NFS-e)")

st.write("Você será redirecionado para o portal nacional de emissão de NFS-e.")

st.link_button("Acessar Portal da NFS-e", "https://www.nfse.gov.br/EmissorNacional/Login?ReturnUrl=%2fEmissorNacional", width='stretch', type="primary")

st.markdown("""
---
**Observação:** O botão acima abrirá o site oficial do governo em uma nova aba do seu navegador. 
A futura integração para emissão direta pelo sistema ainda está em planejamento.
""")

