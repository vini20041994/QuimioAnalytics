# 💻 BACKEND - Pasta 03_BACKEND

**Tudo sobre backend em um único lugar.**

Esta pasta contém:
- 📖 Documentação específica do backend
- 💻 Boilerplate FastAPI pronto para copiar
- 📝 Exemplos de endpoints
- ✅ Checklist de implementação backend

---

## 📚 Documentação Backend

### Referência Rápida
```
Framework: FastAPI
Database: PostgreSQL
ORM: SQLAlchemy
Auth: JWT (Phase 2+)
Cache: Redis
Testing: pytest
```

### Arquitetura Backend

```
app/
├── main.py           # Aplicação FastAPI
├── database.py       # Conexão PostgreSQL
├── models.py         # SQLAlchemy models
├── schemas.py        # Pydantic schemas
├── routes/           # Endpoints
│   ├── batches.py
│   ├── features.py
│   ├── candidates.py
│   └── health.py
└── services/         # Lógica de negócio
```

---

## 💻 Boilerplate

Copie de `boilerplate/` para seu projeto:

```bash
cp -r boilerplate/* ~/seu_projeto/backend/
cd ~/seu_projeto/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### O que está incluído:

✅ FastAPI setup  
✅ SQLAlchemy + PostgreSQL  
✅ Modelos de dados (Batch, Feature, Candidate)  
✅ 15+ endpoints  
✅ CORS configurado  
✅ Docker Compose integração  
✅ Tests básicos  

---

## 🔌 Endpoints Principais

### Health Check
```
GET /api/v1/health
```

### Batches
```
GET /api/v1/batches              # Listar batches
POST /api/v1/batches             # Criar batch
GET /api/v1/batches/{batch_id}   # Detalhes
```

### Features
```
GET /api/v1/features/{batch_id}      # Listar features
POST /api/v1/features                # Criar feature
GET /api/v1/features/{feature_id}    # Detalhes
```

### Candidates (Top 5)
```
GET /api/v1/candidates/{feature_id}  # Top 5 candidates
POST /api/v1/candidates              # Ranking
```

---

## 🧪 Testando

```bash
# Teste local
python main.py
# API em: http://localhost:8000

# Docs interativa
# http://localhost:8000/docs

# Teste com frontend
docker-compose up -d
curl http://localhost:8000/api/v1/health
```

---

## 📋 Checklist Backend

- [ ] Copiar boilerplate
- [ ] Criar virtual environment
- [ ] Instalar dependências (`pip install -r requirements.txt`)
- [ ] Configurar PostgreSQL
- [ ] Rodar migrations
- [ ] Testar localmente
- [ ] Testar endpoints (curl)
- [ ] Testar com frontend
- [ ] Implementar lógica de negócio
- [ ] Adicionar validações
- [ ] Tests automatizados
- [ ] Documentação de API
- [ ] Deploy

---

## 🚀 Próximas Ações

1. Leia documentação geral em `01_DOCS/`
2. Copie `boilerplate/` para seu projeto
3. Setup Python virtual environment
4. Instale dependências
5. Configure PostgreSQL
6. Execute `python main.py`
7. Teste health check: `curl http://localhost:8000/api/v1/health`
8. Abra Swagger: http://localhost:8000/docs
9. Comece a implementar!

---

**Tudo que você precisa para backend está aqui nesta pasta.**
