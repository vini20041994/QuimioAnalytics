# 📌 Resumo Visual - Integração Frontend-Backend
## QuimioAnalytics - Uma Página de Referência

---

## 🎯 Arquitetura em 1 Minuto

```
┌─────────────────────────┐
│    USER INTERFACE       │  ← Seu trabalho
│    (React Dashboard)    │
└───────────┬─────────────┘
            │ HTTP REST
            ↓
┌─────────────────────────┐
│   API REST (FastAPI)    │  ← Criar novo
│   15+ endpoints         │
└───────────┬─────────────┘
            │ SQL Queries
            ↓
┌─────────────────────────┐
│   PostgreSQL (Exists)   │  ← Já existe
│   schemas: core,ref,stg │
└─────────────────────────┘
```

---

## ⚡ Os 4 Endpoints Críticos

```bash
# 1. Listar batches
GET /api/v1/batches
Response: { "data": [...], "pagination": {...} }

# 2. Criar batch
POST /api/v1/batches
Body: { "batch_name": "...", "solvent": "..." }

# 3. Obter Top 5
GET /api/v1/batches/{batch_id}/top5
Response: { "data": [candidato1, candidato2, ...] }

# 4. Upload de arquivos
POST /api/v1/batches/upload
Body: multipart form data (Excel files)
```

---

## 📚 Os 4 Documentos Criados

### 1. **INDICE_DOCUMENTACAO.md** 📋
Você está aqui! Guia de navegação central.

### 2. **GUIA_RAPIDO_INTEGRACAO.md** 🚀
Leia PRIMEIRO (10 min)
- Timeline de 10 semanas
- Endpoints prioritários
- Checklist interativo
- FAQs

### 3. **INTEGRACAO_FRONTEND_BACKEND.md** 📖
Referência COMPLETA (1-2 horas)
- Todos os 15+ endpoints com exemplos
- Fluxos de dados
- Segurança, performance, DevOps
- Modelos de dados (Pydantic)

### 4. **BOILERPLATE_CODIGO_PRONTO.md** 💻
Código PRONTOS para COPIAR
- Backend FastAPI (models, routes, schemas)
- Frontend React (components, services, store)
- Docker setup
- Testes

---

## 🚀 Comece Agora em 3 Passos

### Passo 1: Setup (15 min)
```bash
# Backend
mkdir backend && cd backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic redis

# Frontend
cd ..
npm create react-app frontend
cd frontend
npm install axios redux react-redux react-router-dom
```

### Passo 2: Copiar Boilerplate (30 min)
```
De BOILERPLATE_CODIGO_PRONTO.md:
├─ backend/app/main.py
├─ backend/app/database.py
├─ backend/app/models.py
├─ backend/app/routes/batches.py
├─ frontend/src/services/api.js
├─ frontend/src/pages/BatchesPage.jsx
└─ docker-compose.yml
```

### Passo 3: Testar (10 min)
```bash
docker-compose up -d
curl http://localhost:8000/api/v1/health
# Abrir http://localhost:3000
```

---

## 📊 Timeline Visual

```
SEMANA 1-2: Setup Backend + Frontend
├─ [ ] Estrutura FastAPI
├─ [ ] Estrutura React
└─ [ ] Docker funcionando

SEMANA 3-4: Endpoints Críticos
├─ [ ] GET/POST /api/v1/batches
├─ [ ] GET /api/v1/batches/{id}/top5
└─ [ ] Components React básicos

SEMANA 5-6: Integração com ETL
├─ [ ] POST /api/v1/batches/upload
├─ [ ] Execução do pipeline
└─ [ ] Persistência em DB

SEMANA 7-8: Dashboard
├─ [ ] Visualização Top 5
├─ [ ] Filtros e paginação
└─ [ ] Gráficos

SEMANA 9: Testes
├─ [ ] Backend tests
├─ [ ] Frontend tests
└─ [ ] Integration tests

SEMANA 10: Deploy
├─ [ ] Docker build
├─ [ ] Staging
└─ [ ] Produção
```

---

## 🛠️ Stack Tecnológico

| Camada | Tecnologia | Por quê |
|--------|-----------|--------|
| **Frontend** | React 18 | Popular, comunidade |
| **API** | FastAPI | Rápido, validação automática |
| **Banco** | PostgreSQL | Já existe |
| **Cache** | Redis | Performance |
| **Deploy** | Docker | Portável, consistent |

**Alternativas:** Flask (se preferir), Vue (frontend), SQLite (dev)

---

## 📝 Endpoints Mais Usados

```javascript
// Em frontend/src/services/api.js

batchesAPI.list()              // GET /api/v1/batches
batchesAPI.create(data)        // POST /api/v1/batches
batchesAPI.getById(id)         // GET /api/v1/batches/{id}
batchesAPI.getTop5(id)         // GET /api/v1/batches/{id}/top5
batchesAPI.upload(formData)    // POST /api/v1/batches/upload
batchesAPI.getStats(id)        // GET /api/v1/batches/{id}/stats
```

---

## 🐛 Problemas Comuns & Soluções

| Problema | Solução |
|----------|---------|
| CORS error | Adicionar CORS no FastAPI |
| 404 not found | Verificar nome da rota (sem typos) |
| Connection refused | `docker-compose up -d postgres` |
| Timeout na query | Adicionar índices, paginação |
| Frontend não conecta | Verificar `REACT_APP_API_URL` |

Mais em: GUIA_RAPIDO_INTEGRACAO.md seção 11

---

## 📁 Estrutura de Pastas Recomendada

```
QuimioAnalytics/
├── backend/                   ← NOVO
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routes/
│   │   │   ├── batches.py
│   │   │   ├── features.py
│   │   │   └── compounds.py
│   │   └── services/
│   │       └── etl_service.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                  ← NOVO
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── store/
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
│
├── docs/
│   ├── INDICE_DOCUMENTACAO.md        ← Você está aqui
│   ├── GUIA_RAPIDO_INTEGRACAO.md
│   ├── INTEGRACAO_FRONTEND_BACKEND.md
│   └── BOILERPLATE_CODIGO_PRONTO.md
│
└── docker-compose.yml         ← ATUALIZAR
```

---

## 💡 Variáveis de Ambiente

### Backend (.env)
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quimioanalytics
DB_USER=quimio_user
DB_PASS=sua_senha
REDIS_URL=redis://localhost:6379
```

### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENV=development
```

---

## 🎓 Conceitos-Chave

### REST API
- GET: Ler dados
- POST: Criar dados
- PUT: Atualizar dados
- DELETE: Deletar dados

### Exemplo de fluxo:
```
1. Frontend: POST /api/v1/batches/upload
2. Backend: Recebe arquivo, valida, persiste
3. Backend: Executa ETL em background
4. Frontend: Poll GET /api/v1/batches/{id} para status
5. Backend: Retorna resultados quando pronto
```

### JSON Response Pattern
```json
{
  "status": "success|error",
  "data": {...},
  "message": "opcional",
  "pagination": {"total": 100, "page": 1, "size": 50}
}
```

---

## 🔗 Importante: Integração com ETL Existente

O script ETL já existe em:  
`scripts/run/run_pipeline_frontend.py`

Para integrar:
```python
# backend/app/services/etl_service.py
import subprocess
from pathlib import Path

async def run_etl_pipeline(batch_id, id_file, ab_file):
    cmd = [
        "python3",
        "scripts/run/run_pipeline_frontend.py",
        "--load-core",
        "--batch-id", str(batch_id),
        "--identificacao", str(id_file),
        "--abundancia", str(ab_file)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0
```

---

## 📞 Quando Usar Cada Documento

| Situação | Documento |
|----------|-----------|
| "Por onde começo?" | GUIA_RAPIDO_INTEGRACAO.md |
| "Como implementar X endpoint?" | INTEGRACAO_FRONTEND_BACKEND.md |
| "Preciso de código de exemplo" | BOILERPLATE_CODIGO_PRONTO.md |
| "Qual é a timeline?" | GUIA_RAPIDO_INTEGRACAO.md seção 6 |
| "Que endpoints fazem o quê?" | INTEGRACAO_FRONTEND_BACKEND.md seção 3 |
| "Como fazer deploy?" | INTEGRACAO_FRONTEND_BACKEND.md seção 7 |

---

## ✅ Checklist Rápido

- [ ] Leu GUIA_RAPIDO_INTEGRACAO.md (15 min)
- [ ] Criou estrutura backend/ e frontend/
- [ ] Copiou código do BOILERPLATE_CODIGO_PRONTO.md
- [ ] Executou `docker-compose up -d`
- [ ] Testou `curl http://localhost:8000/api/v1/health`
- [ ] Criou primeiro endpoint (GET /api/v1/batches)
- [ ] Conectou frontend ao backend
- [ ] Implementou upload de arquivos
- [ ] Integrou com ETL existente
- [ ] Deploy em staging/produção

---

## 🎯 Sucesso = 

✅ API respondendo em `http://localhost:8000`  
✅ Frontend rodando em `http://localhost:3000`  
✅ Upload de Excel funcionando  
✅ Top 5 sendo calculado  
✅ Dados persistindo no PostgreSQL  

---

## 🚨 Importante!

### Antes de começar, garantir:
- [ ] PostgreSQL rodando (`docker-compose up -d postgres`)
- [ ] Python 3.10+ instalado
- [ ] Node.js 18+ instalado
- [ ] Docker e Docker Compose instalados

### Testar conexão com DB:
```bash
psql -h localhost -U quimio_user -d quimioanalytics
# Password: (seu DB_PASS)
```

### Testar API:
```bash
curl -X GET http://localhost:8000/api/v1/health
# Response: {"status": "healthy", "version": "1.0.0", ...}
```

---

## 📞 Precisa de Ajuda?

1. **"Não entendo a arquitetura"**  
   → Ler INTEGRACAO_FRONTEND_BACKEND.md seção 1-2

2. **"Não sei por onde começar"**  
   → Seguir os 3 passos de "Comece Agora"

3. **"Preciso copiar código"**  
   → Usar BOILERPLATE_CODIGO_PRONTO.md

4. **"Como configurar segurança?"**  
   → INTEGRACAO_FRONTEND_BACKEND.md seção 8

5. **"Como fazer deploy?"**  
   → INTEGRACAO_FRONTEND_BACKEND.md seção 7

---

## 📈 Métricas de Sucesso

| Métrica | Alvo |
|---------|------|
| Endpoints implementados | 15+ |
| Testes unitários | 80%+ cobertura |
| Tempo de resposta API | < 500ms |
| Disponibilidade | 99.9% |
| Deploy time | < 10 min |

---

## 🎓 Recursos Externos

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Official](https://react.dev/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Docker Compose](https://docs.docker.com/compose/)
- [REST API Best Practices](https://restfulapi.net/)

---

## 📝 Notas Finais

> Este é um plano **completo e viável** para integração frontend-backend do QuimioAnalytics.
>
> A documentação foi criada pensando em:
> - ✅ Facilidade de compreensão
> - ✅ Exemplos práticos
> - ✅ Código pronto para usar
> - ✅ Timeline realista
> - ✅ Boas práticas de engenharia
>
> **Tempo total para implementação:** 8-10 semanas
>
> **Suporte:** Consulte os 4 documentos principais

---

**Resumo Visual - QuimioAnalytics**  
**Data:** 2026-05-10  
**Versão:** 1.0  
**Status:** 🟢 Pronto para iniciar
