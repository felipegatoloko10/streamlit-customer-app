# 🚀 Customer-App: CRM Inteligente com Precificação 3D

**Um sistema completo de gestão de clientes (CRM) e precificação para impressão 3D, construído com a agilidade do Streamlit e uma arquitetura robusta e segura.**

Este projeto foi revisado e refatorado para garantir não apenas a funcionalidade, mas também a segurança, manutenibilidade e as melhores práticas de desenvolvimento.

---

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red?style=for-the-badge&logo=streamlit)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<!-- 
💡 **Dica:** Adicione um GIF ou uma screenshot do seu app aqui!
<p align="center">
  <img src="URL_DA_SUA_IMAGEM.gif" alt="Demonstração do App">
</p>
-->

## ✨ Funcionalidades Principais

Este aplicativo é uma ferramenta de negócios interna (Internal Business Tool) multifuncional, dividida nas seguintes seções:

#### 🏠 Dashboard Analítico
- **Visão Geral:** Métricas em tempo real sobre o total de clientes, o cliente mais recente no período selecionado e o estado com maior concentração de clientes.
- **Filtro por Período:** Permite analisar o crescimento e a distribuição dos clientes em intervalos de data específicos.
- **Gráficos Interativos:**
    - Novos clientes por mês (gráfico de barras).
    - Distribuição de clientes por estado (gráfico de rosca).
    - Top 5 cidades com mais clientes.
    - Distribuição entre clientes Pessoa Física (CPF) e Jurídica (CNPJ).

#### 📝 Cadastro Inteligente
- **Busca por CNPJ:** Preenchimento automático de `Razão Social`, `E-mail`, `Telefone` e `Endereço` a partir de um CNPJ, utilizando a BrasilAPI.
- **Busca por CEP:** Preenchimento automático de `Endereço`, `Bairro`, `Cidade` e `Estado` a partir de um CEP, via ViaCEP.
- **Validação de Dados:** Validações robustas para CPF, CNPJ, e-mail e telefone no momento da inserção.

#### 📊 Banco de Dados Interativo
- **Visualização e Filtragem:** Uma grade de dados paginada que permite buscar clientes por nome/documento e filtrar por estado.
- **Detalhes do Cliente:**
    - Seleção de um cliente na grade para ver todos os seus detalhes.
    - Acesso direto a um cliente via URL (ex: `.../Banco_de_Dados?id=123`).
    - **Modo de Edição:** Altere qualquer informação do cliente diretamente na interface.
    - **Exclusão Segura:** Processo de exclusão com dupla confirmação para evitar perdas acidentais.
- **Integrações:**
    - **WhatsApp:** Ícones clicáveis para iniciar conversas com os clientes.
    - **Google Maps:** Botão para abrir o endereço do cliente diretamente no mapa.

#### 💰 Calculadora de Preços 3D
- **Cálculo Detalhado:** Calcule o preço de venda de impressões 3D com base em dezenas de variáveis, como horas de design, tempo de impressão, custo de material, consumo elétrico, taxas de falha, complexidade e margem de lucro.
- **Gerenciamento de Predefinições:**
    - **Salvar:** Salve as configurações atuais da calculadora como uma predefinição nomeada (ex: "Resina de Alta Definição").
    - **Carregar:** Carregue rapidamente configurações salvas para agilizar novos orçamentos.
    - **Excluir:** Remova predefinições que não são mais necessárias.

#### 💾 Backup & Restauração
- **Backup com 1 Clique:** Baixe uma cópia de segurança (`.db`) completa do seu banco de dados a qualquer momento.
- **Restauração Segura:**
    - **Validação de Arquivo:** O sistema verifica se o arquivo enviado é um banco de dados SQLite válido antes de permitir a restauração.
    - **Backup de Segurança:** Antes de restaurar, o sistema cria automaticamente um backup do estado atual, garantindo que nenhuma informação seja perdida em caso de erro.

#### 💸 Portal NFS-e
- Um atalho prático que redireciona o usuário para o portal nacional de emissão de Nota Fiscal de Serviço eletrônica.

## 🏛️ Arquitetura e Boas Práticas

O código foi estruturado em **camadas independentes** para facilitar a manutenção e a evolução do projeto:

- **`pages/` (Interface):** Cada página (`.py`) é um componente isolado, responsável apenas por exibir a interface e lidar com as interações do usuário.
- **`services.py` (Serviços):** Centraliza a comunicação com APIs externas (BrasilAPI, ViaCEP). Foi refatorado para ser desacoplado da interface, retornando dados e exceções em vez de manipular o estado da UI diretamente.
- **`validators.py` (Validação):** O "guardião" dos dados. Garante que nenhuma informação inválida chegue à camada de dados. As funções foram otimizadas para maior eficiência.
- **`database.py` (Dados):** A única fonte da verdade. Abstrai toda a complexidade de interagir com o banco de dados SQLite. **A camada foi refatorada para eliminar vulnerabilidades de segurança (SQL Injection)**, garantindo que todas as queries sejam seguras.

## 💻 Tech Stack

- **Framework Principal:** Streamlit
- **Banco de Dados:** SQLite
- **Componentes de UI:** `streamlit-modal` para confirmações e formulários.
- **Análise de Dados:** Pandas
- **Validação de Documentos:** `validate-docbr`
- **Requisições HTTP:** `requests`

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

4.  **Configure os Segredos (Opcional):**
    Para receber notificações por e-mail quando um novo cliente for cadastrado, crie um arquivo em `.streamlit/secrets.toml` com o seguinte conteúdo:
    ```toml
    # E-mail de onde as notificações serão enviadas
    name = "seu-email@gmail.com" 
    # Senha de App gerada para o e-mail (não use sua senha principal!)
    key = "sua_senha_de_app" 
    
    # URL base da sua aplicação (para os links no e-mail)
    # Ex: "http://localhost:8501" para desenvolvimento local
    app_base_url = "http://localhost:8501"

    # Configurações do servidor SMTP
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    ```

5.  **Execute o app:**
    ```bash
    streamlit run app.py
    ```

---
