# Customer Management CRM & 3D Printing Price Calculator

Este é um aplicativo web multifuncional construído com Streamlit, projetado para atuar como um pequeno CRM para gerenciamento de clientes e uma ferramenta especializada para cálculo de preços de impressão 3D.

## ✨ Features

### Gerenciamento de Clientes (CRM)
- **Dashboard Interativo:** Visualize métricas chave como total de clientes, novos registros por período, e distribuição geográfica (estado/cidade).
- **Cadastro Completo:** Formulário de cadastro dinâmico para pessoas físicas (CPF) e jurídicas (CNPJ).
  - **Busca Automática de CNPJ:** Preenchimento automático de razão social, e-mail e endereço ao inserir um CNPJ válido (via BrasilAPI).
  - **Busca Automática de CEP:** Preenchimento automático do endereço ao inserir um CEP (via ViaCEP).
- **Banco de Dados de Clientes:**
  - Interface para visualizar, buscar e filtrar todos os clientes cadastrados.
  - Edição de informações diretamente na página.
  - Exclusão de clientes com diálogo de confirmação.
  - Links diretos para WhatsApp e Google Maps.
- **Backup e Restauração:** Funcionalidade para baixar uma cópia de segurança do banco de dados (SQLite) e restaurá-lo a partir de um arquivo.

### Ferramentas de Negócio
- **Calculadora de Preços para Impressão 3D:**
  - Modelo de custos detalhado que inclui mão de obra, material, custos de impressão e fatores de negócio (lucro, falha, urgência).
  - Sistema de **Predefinições (Presets)** para salvar e carregar configurações de cálculo comuns.
- **Emissão de NFS-e (Placeholder):** Página com link para o portal nacional de emissão de Nota Fiscal de Serviço eletrônica.

## 🚀 Getting Started

Siga as instruções abaixo para configurar e rodar o projeto em seu ambiente local.

### Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes do Python)

### Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/felipegatoloko10/streamlit-customer-app.git
   cd streamlit-customer-app
   ```

2. **Crie e ative um ambiente virtual (recomendado):**
   ```bash
   # Para Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Para macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

### Executando o Aplicativo

Para iniciar o servidor do Streamlit, execute o seguinte comando no seu terminal:

```bash
streamlit run app.py
```

O aplicativo será aberto automaticamente no seu navegador padrão.

## 🏛️ Arquitetura do Projeto

O projeto é estruturado de forma modular para separar as responsabilidades:

- `app.py`: O ponto de entrada principal do aplicativo. Apenas redireciona para a página do Dashboard.
- `/pages`: Contém os arquivos de cada página da aplicação. O Streamlit usa os nomes dos arquivos para criar a navegação na barra lateral.
  - `0_🏠_Dashboard.py`: Dashboard principal com gráficos e métricas.
  - `1_📝_Cadastro.py`: Formulário de cadastro de clientes.
  - `2_📊_Banco_de_Dados.py`: Interface de visualização e edição da base de dados.
  - `3_💰_Calculadora_de_Preços.py`: Calculadora de preços para impressão 3D.
  - `4_💸_Emitir_NFS-e.py`: Placeholder para emissão de notas fiscais.
  - `5_💾_Backup.py`: Página de backup e restauração.
- `database.py`: Contém toda a lógica de interação com o banco de dados SQLite. Define o esquema da tabela e as funções CRUD (Create, Read, Update, Delete).
- `services.py`: Lógica para interagir com APIs externas (ViaCEP, BrasilAPI) e para enviar e-mails de notificação.
- `validators.py`: Funções para validar e formatar dados como CPF, CNPJ, e-mail e telefone.
- `requirements.txt`: Lista de todas as bibliotecas Python necessárias para o projeto.
- `customers.db`: Arquivo do banco de dados SQLite onde os dados dos clientes são armazenados.
- `presets.json`: Arquivo JSON onde as predefinições da calculadora de preços são salvas.

## 🔮 Melhorias Futuras e Sugestões

Esta é uma lista de melhorias e refatorações sugeridas para tornar o aplicativo mais robusto e manutenível:

- **Banco de Dados:**
  - **Persistência dos Presets:** Mover as predefinições da calculadora de `presets.json` para uma nova tabela no banco de dados `customers.db` para garantir a persistência em ambientes de nuvem.
- **Segurança:**
  - **Backup Automático:** Na página de Backup, implementar um backup automático do banco de dados atual antes de executar uma restauração, como uma camada extra de segurança.
- **Código e Arquitetura:**
  - **Remover Dependências Inutilizadas:** Remover `psycopg2-binary` do `requirements.txt`.
  - **Configuração Centralizada:** Mover configurações como a URL da aplicação (atualmente fixa no `services.py`) para um arquivo de configuração ou para o `st.secrets`.
  - **Refatorar Páginas Complexas:** Simplificar o gerenciamento de estado e a lógica de UI nas páginas `1_📝_Cadastro.py` e `2_📊_Banco_de_Dados.py` para reduzir a complexidade e o uso de `st.rerun()`. Adotar componentes como `st.data_editor` pode ser uma boa alternativa.
- **Novas Funcionalidades:**
  - **Integração com NFS-e:** Desenvolver a integração real com a API da NFS-e para permitir a emissão de notas fiscais diretamente pelo sistema.