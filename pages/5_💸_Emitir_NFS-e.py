import streamlit as st

st.set_page_config(
    page_title="Emitir NFS-e",
    page_icon="💸"
)

st.title("💸 Emitir Nota Fiscal de Serviço eletrônica (NFS-e)")

st.write("Você será redirecionado para o portal nacional de emissão de NFS-e.")

st.link_button("Acessar Portal da NFS-e", "https://nfse.gov.br/NFS-e/", use_container_width=True, type="primary")

st.markdown("""
---
**Observação:** O botão acima abrirá o site oficial do governo em uma nova aba do seu navegador. 
A futura integração para emissão direta pelo sistema ainda está em planejamento.
""")

