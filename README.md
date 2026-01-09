# App de Cadastro de Clientes com Streamlit

Este é um simples aplicativo web para cadastrar, visualizar, editar e deletar clientes. O front-end foi construído com Streamlit e os dados são armazenados em um banco de dados SQLite.

## Pré-requisitos

- Python 3.8 ou superior

## Como Instalar e Rodar o Projeto

1.  **Clone o Repositório:**
    Se você estiver baixando o projeto de outra forma, apenas certifique-se de estar dentro da pasta do projeto no seu terminal.
    ```bash
    git clone https://github.com/felipegatoloko10/streamlit-customer-app.git
    cd streamlit-customer-app
    ```

2.  **Crie um Ambiente Virtual (Recomendado):**
    Isso cria um ambiente isolado para o seu projeto, evitando conflitos com outras bibliotecas do seu sistema.
    ```bash
    # No Windows
    python -m venv venv
    .\venv\Scripts\activate

    # No macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as Dependências:**
    O projeto tem um arquivo `requirements.txt` com tudo que você precisa.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Rode o Aplicativo Streamlit:**
    ```bash
    streamlit run app.py
    ```

Seu navegador deve abrir automaticamente com a aplicação rodando!
