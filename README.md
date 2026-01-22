# 🚀 Customer-App: CRM Inteligente com Precificação 3D

**Um sistema completo de gestão de clientes e precificação, construído com a agilidade do Streamlit e uma arquitetura robusta.**

---

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red?style=for-the-badge&logo=streamlit)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> Este projeto vai além de um simples app. É uma demonstração de como o Streamlit pode ser usado para criar ferramentas de negócio internas (Internal Business Tools) poderosas, com uma clara separação entre a interface, as regras de negócio e o acesso a dados.

<!-- 
💡 **Dica:** Adicione um GIF ou uma screenshot do seu app aqui!
<p align="center">
  <img src="URL_DA_SUA_IMAGEM.gif" alt="Demonstração do App">
</p>
-->

## 🏛️ Filosofia e Arquitetura

O código é organizado em **camadas independentes**, facilitando a manutenção e a adição de novas funcionalidades:

- **`pages/` (Interface):** Cada página é um componente isolado, responsável apenas por exibir informações e capturar a entrada do usuário.
- **`services.py` (Serviços):** Centraliza a comunicação com o mundo exterior (APIs como BrasilAPI, ViaCEP e envio de e-mails).
- **`validators.py` (Validação):** O "guardião" dos dados. Garante que nenhuma informação inválida (CPF, CNPJ, e-mail) chegue à camada de dados.
- **`database.py` (Dados):** A única fonte da verdade. Abstrai toda a complexidade de interagir com o banco de dados SQLite.

## ✨ O que ele faz? Funcionalidades Principais

### 📇 Gestão de Clientes (CRM)

- **Dashboard Analítico:** Uma visão geral do seu negócio com métricas de crescimento e distribuição de clientes.
- **Cadastro Inteligente:**
  - **Automático:** Busca dados de **CNPJ** na BrasilAPI para preencher o formulário.
  - **Endereço Fácil:** Preenche o endereço completo a partir de um **CEP**.
- **Banco de Dados Interativo:**
  - Visualize, filtre e edite clientes em tempo real.
  - **Acesso Rápido:** Links diretos para iniciar conversas no **WhatsApp** ou ver o endereço no **Google Maps**.
- **Segurança de Dados:**
  - **Backup com 1 Clique:** Baixe uma cópia de segurança do seu banco de dados a qualquer momento.
  - **Restauração Segura:** Restaure um backup antigo com a tranquilidade de que um backup de segurança do estado atual será criado automaticamente.

### 🛠️ Ferramentas de Negócio

- **Calculadora de Preços 3D:**
  - **Precificação Detalhada:** Calcule o preço de venda de impressões 3D considerando dezenas de variáveis.
  - **Presets Inteligentes:** Salve e carregue configurações de cálculo para diferentes tipos de projeto (ex: "Resina de Alta Definição", "PLA Padrão").
- **Portal de NFS-e:** Um atalho útil para o portal nacional de emissão de notas fiscais.

## 💻 Tech Stack

- **Framework Principal:** Streamlit
- **Banco de Dados:** SQLite
- **Análise de Dados:** Pandas
- **Validação de Documentos:** `validate-docbr`
- **Requisições HTTP:** `requests`
- **Componentes de UI:** `streamlit-modal`

## 🚀 Como Executar

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/felipegatoloko10/streamlit-customer-app.git
    cd streamlit-customer-app
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv .venv
    # Windows: .venv\Scripts\activate
    # macOS/Linux: source .venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute o app:**
    ```bash
    streamlit run app.py
    ```

---