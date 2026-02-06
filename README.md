# 📊 Streamlit Customer App - Gestão Inteligente de Clientes

Uma aplicação robusta e moderna desenvolvida com **Streamlit** para gestão completa de clientes, focada em integridade de dados, automação e análise geográfica.

## 🚀 Funcionalidades Principais

### 1. Cadastro Inteligente e Enriquecido
*   **Busca Automática por CNPJ:** Integração com BrasilAPI para preenchimento automático de dados cadastrais, endereço e e-mail.
*   **Enriquecimento de Dados:** Captura automática da Situação Cadastral (Ativa/Inativa) e CNAE Principal diretamente da Receita Federal.
*   **Busca por CEP:** Integração com ViaCEP para preenchimento instantâneo de endereços.
*   **Validação Rigorosa:** Verificação de CPF/CNPJ reais, validação de formato de WhatsApp e bloqueio de e-mails temporários/descartáveis.
*   **Higienização Automática:** O sistema padroniza nomes e endereços (Title Case) e siglas de estados (UF) automaticamente antes de salvar.

### 2. Banco de Dados e Auditoria
*   **Arquitetura SQL:** Banco de Dados SQLite3 com estrutura otimizada (Clientes, Contatos, Endereços).
*   **Trilha de Auditoria (Audit Log):** Histórico completo de todas as ações (Inserção, Edição, Exclusão), registrando o estado anterior e posterior de cada registro.
*   **Grid Dinâmico:** Visualize apenas o que importa. Escolha quais colunas exibir na tabela principal através de um seletor dinâmico na barra lateral.
*   **Edição Avançada:** Edite qualquer campo com validação em tempo real e re-geocodificação automática de endereços.

### 3. Dashboard e Análise Geo
*   **Mapa de Distribuição:** Visualize a localização dos seus clientes em um mapa interativo (PyDeck) com lógica de fallback por CEP caso o endereço completo falhe.
*   **Filtros de Período:** Analise o crescimento da sua base por períodos (Todo o tempo, Este Ano, Últimos 30 Dias).
*   **KPIs de Saúde:** Acompanhe a completude da sua base de dados através de métricas de qualidade de e-mail, telefone e endereço.

### 4. Backup e Segurança
*   **Backup em Nuvem (Google Drive):** Integração total com a API do Google Drive para backups automáticos a cada 5 novos clientes ou manual via botão "Forçar Backup".
*   **Indicação de Status:** Indicador visual de conexão com a nuvem (Online/Offline) presente em todas as páginas do app.
*   **Backup Local:** Opção de download manual do banco de dados a qualquer momento.

## 🛠️ Tecnologias Utilizadas
*   **Linguagem:** Python 3.x
*   **Interface:** Streamlit
*   **Banco de Dados:** SQLite3
*   **Mapas:** PyDeck & Nominatim API
*   **APIs:** BrasilAPI, ViaCEP, Google Drive API
*   **Processamento de Dados:** Pandas

## 📋 Como Instalar e Rodar

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/felipegatoloko10/streamlit-customer-app.git
    cd streamlit-customer-app
    ```

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Execute a aplicação:**
    ```bash
    streamlit run app.py
    ```

4.  **Configuração de Nuvem (Opcional):**
    Para habilitar o backup no Google Drive, suba seu arquivo `credentials.json` na página de Backup do app e siga as instruções na tela.

---
Desenvolvido com 🥒 por [Felipe](https://github.com/felipegatoloko10)