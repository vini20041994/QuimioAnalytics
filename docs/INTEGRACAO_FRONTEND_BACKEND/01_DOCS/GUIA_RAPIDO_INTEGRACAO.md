# Guia Rápido de Integração Frontend-Backend
## QuimioAnalytics - Resumo Executivo

---

## 1. Arquitetura em 30 segundos

```
┌──────────────────────┐
│   Frontend (React)   │  ← Você estrutura aqui
└──────┬───────────────┘
       │ HTTP REST
       ↓
┌──────────────────────┐
│   API (FastAPI)      │  ← Criar novo
└──────┬───────────────┘
       │ SQL
       ↓
┌──────────────────────┐
│   PostgreSQL         │  ← Já existe
└──────────────────────┘
```

---

## 2. Endpoints Essenciais (Implementar na ordem)

### 🔴 CRÍTICOS (Semana 1-2)
```
1. GET  /api/v1/batches              → Listar todos os batches
2. POST /api/v1/batches              → Criar novo batch
3. GET  /api/v1/batches/{id}         → Detalhe de 1 batch
4. POST /api/v1/batches/upload       → Upload de arquivos Excel
```

### 🟡 IMPORTANTES (Semana 3-4)
```
5. GET  /api/v1/batches/{id}/features    → Features do batch
6. GET  /api/v1/batches/{id}/top5        → Ranking Top 5
7. GET  /api/v1/features/{id}            → Detalhes da feature
8. GET  /api/v1/batches/{id}/stats       → Estatísticas
```

### 🟢 COMPLEMENTARES (Semana 5-6)
```
9. GET  /api/v1/compounds/external       → Compostos enriquecidos
10. POST /api/v1/compounds/search        → Buscar compostos
11. GET  /api/v1/health                  → Status da API
```

---

## 3. Stack Tecnológico Recomendado

| Componente      | Recomendação      | Alternativa     |
|-----------------|-------------------|-----------------|
| **Backend API** | FastAPI (Python)  | Flask, Django   |
| **Frontend**    | React 18+         | Vue 3, Svelte   |
| **Banco Dados** | PostgreSQL 15     | (já existe)     |
| **Cache**       | Redis             | Memcached       |
| **Deploy**      | Docker Compose    | K8s, AWS        |

---

## 4. Fluxos de Dados

### Fluxo 1: Upload → Análise → Resultados
```
User Upload (Frontend)
       ↓
POST /api/v1/batches/upload
       ↓
Salvar arquivos + criar batch no DB
       ↓
Executar scripts/run/run_pipeline_frontend.py (async)
       ↓
Persistir resultados no schema 'core'
       ↓
GET /api/v1/batches/{batch_id}/top5
       ↓
Exibir Top 5 no Dashboard
```

### Fluxo 2: Enriquecimento com Bases Externas
```
User seleciona Top 5 + fontes (PubChem, ChEBI)
       ↓
API inicia job de enriquecimento (async)
       ↓
Scripts executam ETLs externos
       ↓
Dados persistem no schema 'ref'
       ↓
Frontend notificado (WebSocket/polling)
       ↓
Exibir dados enriquecidos
```

---

## 5. Estrutura de Pastas (Proposta)

```
QuimioAnalytics/
├── backend/                          # ✨ NOVO
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # Entry point FastAPI
│   │   ├── database.py               # Conexão PostgreSQL
│   │   ├── models.py                 # Pydantic models
│   │   ├── routes/
│   │   │   ├── batches.py            # CRUD batches
│   │   │   ├── features.py           # Features queries
│   │   │   ├── compounds.py          # External compounds
│   │   │   └── upload.py             # File upload
│   │   └── services/
│   │       ├── etl_service.py        # Integração com ETL
│   │       └── cache_service.py      # Redis operations
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                         # ✨ NOVO
│   ├── src/
│   │   ├── components/
│   │   │   ├── BatchSelector.jsx
│   │   │   ├── Top5Table.jsx
│   │   │   ├── FileUploader.jsx
│   │   │   └── Dashboard.jsx
│   │   ├── pages/
│   │   │   ├── BatchesPage.jsx
│   │   │   ├── AnalysisPage.jsx
│   │   │   └── CompoundsPage.jsx
│   │   ├── services/
│   │   │   └── api.js               # Axios config + endpoints
│   │   ├── store/
│   │   │   └── Redux or Zustand
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── Dockerfile
│
├── scripts/                          # ✅ EXISTENTE
│   ├── run/
│   │   └── run_pipeline_frontend.py
│   ├── features/
│   │   └── analytics.py
│   └── ... (outros)
│
├── database/                         # ✅ EXISTENTE
│   └── schema_postgresql_mvp_entrega2.sql
│
├── docker-compose.yml                # 🔄 ATUALIZAR
└── docs/
    ├── INTEGRACAO_FRONTEND_BACKEND.md  # ✨ Plano completo
    └── ... (outros)
```

---

## 6. Timeline Sugerida

| Semana | Fase | Tarefas |
|--------|------|---------|
| **1-2** | Setup | Projeto backend + frontend, conexão DB, models |
| **3-4** | Endpoints críticos | Batches, features, top5 |
| **5-6** | Integração ETL | Upload, pipeline, persistência |
| **7-8** | Dashboard | UI, visualizações, filtros |
| **9** | Testes | Unit tests, integration tests |
| **10** | Deploy | Docker, staging, produção |

---

## 7. Exemplos Rápidos

### Backend: Criar Batch
```python
# backend/app/routes/batches.py
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

@router.post("/")
async def create_batch(batch_data: dict, db: Session):
    batch = Batch(
        batch_name=batch_data['batch_name'],
        solvent=batch_data.get('solvent'),
        ionization_mode=batch_data.get('ionization_mode')
    )
    db.add(batch)
    db.commit()
    return {"status": "success", "batch_id": batch.batch_id}
```

### Frontend: Listar Batches
```jsx
// frontend/src/pages/BatchesPage.jsx
import { useEffect, useState } from 'react';
import api from '../services/api';

export function BatchesPage() {
  const [batches, setBatches] = useState([]);

  useEffect(() => {
    api.get('/api/v1/batches')
      .then(res => setBatches(res.data.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <ul>
      {batches.map(b => <li key={b.batch_id}>{b.batch_name}</li>)}
    </ul>
  );
}
```

### Frontend: Serviço de API
```javascript
// frontend/src/services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000
});

export const batchesAPI = {
  list: () => api.get('/api/v1/batches'),
  create: (data) => api.post('/api/v1/batches', data),
  getById: (id) => api.get(`/api/v1/batches/${id}`),
  getTop5: (id) => api.get(`/api/v1/batches/${id}/top5`),
  upload: (formData) => api.post('/api/v1/batches/upload', formData),
};

export default api;
```

---

## 8. Checklist de Implementação

### ✅ Fase 1: Setup (Semana 1-2)
```
[ ] mkdir backend && cd backend
[ ] pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic redis
[ ] Criar app/main.py com rota GET /health
[ ] npm create react-app frontend
[ ] Criar frontend/src/services/api.js
[ ] Atualizar docker-compose.yml com serviços api, frontend, redis
```

### ✅ Fase 2: Endpoints Críticos (Semana 3-4)
```
[ ] Implementar GET /api/v1/batches
[ ] Implementar POST /api/v1/batches
[ ] Implementar GET /api/v1/batches/{id}
[ ] Implementar GET /api/v1/batches/{id}/features
[ ] Implementar GET /api/v1/batches/{id}/top5
[ ] Criar componentes React para listar batches
[ ] Criar componentes React para exibir Top 5
```

### ✅ Fase 3: Upload e ETL (Semana 5-6)
```
[ ] Implementar POST /api/v1/batches/upload
[ ] Integrar com scripts/run/run_pipeline_frontend.py
[ ] Criar etl_service.py para executar pipeline async
[ ] Testar upload de arquivos
[ ] Testar persistência em schema 'core'
```

### ✅ Fase 4: Dashboard (Semana 7-8)
```
[ ] Criar Dashboard.jsx
[ ] Listar batches com status
[ ] Exibir Top 5 em tabela/gráfico
[ ] Implementar filtros
[ ] Implementar paginação
```

### ✅ Fase 5: Qualidade (Semana 9)
```
[ ] Testes unitários backend (pytest)
[ ] Testes unitários frontend (jest)
[ ] Testes de integração API
[ ] Validar tratamento de erros
[ ] Testar edge cases
```

### ✅ Fase 6: Deploy (Semana 10)
```
[ ] Build Docker da API
[ ] Build Docker do Frontend
[ ] Testar docker-compose
[ ] Deployment em staging
[ ] Validação em produção
[ ] Monitoramento ativo
```

---

## 9. Comandos Úteis

### Backend
```bash
# Setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Executar API em desenvolvimento
uvicorn app.main:app --reload --port 8000

# Executar com hot-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
# Setup
cd frontend
npm install

# Desenvolvimento
npm start

# Build de produção
npm run build
```

### Docker
```bash
# Subir todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Parar tudo
docker-compose down

# Limpar volumes
docker-compose down -v
```

### Testes
```bash
# Backend
pytest backend/tests/

# Frontend
npm test

# Coverage
pytest --cov=app backend/tests/
```

---

## 10. Variáveis de Ambiente

### Backend `.env`
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quimioanalytics
DB_USER=quimio_user
DB_PASS=sua_senha
REDIS_URL=redis://localhost:6379
JWT_SECRET=sua_chave_secreta
DEBUG=False
```

### Frontend `.env`
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENV=development
```

---

## 11. Possíveis Armadilhas e Soluções

| Problema | Causa | Solução |
|----------|-------|---------|
| CORS error | Backend e Frontend em portas diferentes | Configurar CORS no FastAPI |
| 404 not found | Rota não existe | Verificar nome exato da rota |
| Connection refused | PostgreSQL não está rodando | `docker-compose up -d postgres` |
| Timeout na API | Query muito lenta | Adicionar índices, paginação, cache |
| Erro de autenticação | JWT inválido ou expirado | Verificar SECRET_KEY e validade do token |

---

## 12. Perguntas Frequentes

**P: Por que FastAPI e não Flask?**  
R: FastAPI é mais rápido, melhor validação automática com Pydantic, documentação Swagger integrada.

**P: Por que React e não Vue?**  
R: Ambos são válidos. React é mais popular, maior comunidade. Vue é mais simples.

**P: Como integrar com o ETL existente?**  
R: Criar wrapper que executa `subprocess.run()` com scripts/run/run_pipeline_frontend.py

**P: Preciso usar Redis?**  
R: Não é crítico na fase 1. Adicione depois para otimizar cache do Top 5.

**P: Como lidar com uploads grandes?**  
R: Chunked uploads, validação de tamanho, armazenamento em S3/object storage.

---

## 13. Recursos Úteis

### Documentação
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

### Ferramentas
- Postman: Teste de APIs
- DBeaver: Gerenciamento DB
- VS Code: Editor recomendado
- Docker Desktop: Orquestração local

### Padrões
- [RESTful API Design](https://restfulapi.net/)
- [12 Factor App](https://12factor.net/)
- [Clean Code](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)

---

## 14. Próximas Etapas

1. **Discuta com o time** o stack recomendado
2. **Setup do repositório** backend e frontend
3. **Configure Docker** com novos serviços
4. **Implemente Fase 1** (endpoints críticos)
5. **Teste com Postman** antes de conectar frontend
6. **Integre componentes React** progressivamente

---

**Documento: Guia Rápido de Integração**  
**Data:** 2026-05-10  
**Responsável:** Frontend Developer  
**Status:** 🟢 Pronto para iniciar desenvolvimento
