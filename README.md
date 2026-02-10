# 📊 Sistema de Gestão de Clientes - Streamlit

Sistema completo de gestão de clientes desenvolvido em Python com Streamlit, featuring moderna arquitetura em camadas com ORM, repositórios e serviços.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-latest-red.svg)](https://streamlit.io/)
[![SQLModel](https://img.shields.io/badge/sqlmodel-latest-green.svg)](https://sqlmodel.tiangolo.com/)

## 🚀 Features

- ✅ **CRUD Completo** de clientes com validação automática
- ✅ **Múltiplos Contatos** e endereços por cliente
- ✅ **Geocodificação** automática de endereços via Nominatim
- ✅ **Dashboard Analítico** com métricas e visualizações
- ✅ **Mapas Interativos** com PyDeck
- ✅ **Sistema de Backup** automático
- ✅ **Audit Trail** de todas as operações
- ✅ **Validação** de CPF/CNPJ
- ✅ **Integração WhatsApp** com links diretos

## 🏗️ Arquitetura

```
UI Layer (Streamlit Pages)
        ↓
Service Layer (Business Logic)
        ↓
Repository Layer (Data Access)
        ↓
Database (SQLite + SQLModel ORM)
```

### Estrutura do Projeto

```
streamlit-customer-app/
├── models.py                    # SQLModel ORM models
├── database_config.py           # Database engine configuration
├── validators.py                # Data validation (CPF, CNPJ, email)
│
├── repositories/
│   ├── base.py                  # Generic BaseRepository
│   └── customer_repository.py   # Customer-specific data access
│
├── services/
│   ├── customer_service.py      # Customer business logic
│   └── integration_services.py  # External API integrations
│
├── pages/
│   ├── 0_🏠_Dashboard.py       # Analytics and metrics
│   ├── 1_📝_Cadastro.py        # Customer registration
│   └── 2_📊_Banco_de_Dados.py  # Customer database grid
│
├── tests/
│   ├── test_customer_repository.py
│   └── test_customer_service.py
│
└── Home.py                      # Main application entry
```

## 📦 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip

### Setup

1. **Clone o repositório:**
```bash
git clone https://github.com/felipegatoloko10/streamlit-customer-app.git
cd streamlit-customer-app
```

2. **Crie um ambiente virtual (recomendado):**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

Principais dependências:
- `streamlit` - Framework web
- `sqlmodel` - ORM (SQLAlchemy + Pydantic)
- `alembic` - Database migrations
- `pandas` - Data manipulation
- `pydeck` - Interactive maps
- `validators` - Email validation
- `validate-docbr` - CPF/CNPJ validation
- `pytest` - Testing framework

## 🚀 Uso

### Executar a Aplicação

```bash
streamlit run Home.py
```

A aplicação abrirá automaticamente em `http://localhost:8501`

### Executar Testes

```bash
# Todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=services --cov=repositories --cov-report=html

# Verificação end-to-end
python verify_refactoring.py
```

## 📚 Documentação das Camadas

### 1. Models (`models.py`)

Define os modelos SQLModel:
- `Cliente` - Dados principais do cliente
- `Contato` - Telefones e emails
- `Endereco` - Endereços completos com geocodificação
- `AuditLog` - Histórico de alterações

### 2. Repository Layer (`repositories/`)

**BaseRepository:**
- CRUD genérico reutilizável
- Type-safe com generics

**CustomerRepository:**
- CRUD específico para clientes
- Eager loading automático (evita N+1 queries)
- Queries analíticas (timeseries, locations, health)
- Audit logging integrado

### 3. Service Layer (`services/`)

**CustomerService:**
- Orquestra lógica de negócio
- Validação automática (CPF/CNPJ)
- Sanitização de dados (Title Case, trim)
- Side-effects (email notifications, backups)
- Formatação de dados para UI

**IntegrationServices:**
- Geocodificação via Nominatim
- Envio de emails
- Geração de links WhatsApp

### 4. UI Layer (`pages/`)

- **Dashboard:** Métricas, gráficos e mapas
- **Cadastro:** Formulário de registro
- **Banco de Dados:** Grid com busca e filtros

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` (opcional):
```env
DATABASE_URL=sqlite:///customers.db
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha
```

### Database Migrations

```bash
# Criar nova migração
alembic revision --autogenerate -m "Description"

# Aplicar migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 📊 Performance

### Otimizações Implementadas

- ✅ **Eager Loading:** Redução de 97% em queries (N+1 eliminado)
- ✅ **Paginação:** Dados carregados sob demanda
- ✅ **Caching:** Streamlit cache para queries pesadas
- ✅ **Lazy Loading:** Componentes carregados conforme necessário

### Benchmarks

| Operação | Queries Antes | Queries Depois | Melhoria |
|----------|---------------|----------------|----------|
| 10 clientes | 21 | 3 | 85% ↓ |
| 50 clientes | 101 | 3 | 97% ↓ |
| Dashboard | ~150 | ~10 | 93% ↓ |

## 🧪 Testing

### Coverage

- **18 testes unitários**
- Fixtures isoladas (SQLite in-memory)
- Mocks para dependências externas
- CRUD completo coberto

### Executar Testes Específicos

```bash
# Apenas repositório
pytest tests/test_customer_repository.py -v

# Apenas serviço
pytest tests/test_customer_service.py -v

# Com marcadores
pytest -m "not slow" -v
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Guidelines

- Seguir PEP 8
- Adicionar testes para novas features
- Atualizar documentação
- Manter cobertura >80%

## 📝 Roadmap

- [ ] Autenticação e autorização
- [ ] API REST com FastAPI
- [ ] Exportação para Excel/PDF
- [ ] Integração com CRM externo
- [ ] Mobile app (Flutter)
- [ ] Notificações push
- [ ] Dashboard em tempo real (WebSockets)

## 🐛 Troubleshooting

### Erro: "No module named 'streamlit'"
```bash
pip install streamlit
```

### Erro: "Database locked"
```bash
# Encerre outras conexões ao banco
# Ou use WAL mode (Write-Ahead Logging)
```

### Performance lenta
```bash
# Verifique queries com logging
# Em database_config.py, adicione:
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👤 Autor

**Felipe Gato Loko**

- GitHub: [@felipegatoloko10](https://github.com/felipegatoloko10)
- LinkedIn: [Felipe Gato Loko](https://www.linkedin.com/in/felipegatoloko)

## 🙏 Agradecimentos

- [Streamlit](https://streamlit.io/) - Framework web incrível
- [SQLModel](https://sqlmodel.tiangolo.com/) - ORM moderno
- [Nominatim](https://nominatim.org/) - Geocoding service
- Comunidade Python 🐍

---

⭐ Se este projeto foi útil, considere dar uma estrela!