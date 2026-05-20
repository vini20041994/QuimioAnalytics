# Documentação: Integração Frontend fron_test com QuimioAnalytics

**Data**: Maio 2026  
**Status**: Guia de Integração  
**Versão**: 1.0

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura Geral](#arquitetura-geral)
3. [Pré-requisitos](#pré-requisitos)
4. [Fase 1: Setup Inicial](#fase-1-setup-inicial)
5. [Fase 2: Desenvolvimento da API Backend](#fase-2-desenvolvimento-da-api-backend)
6. [Fase 3: Integração Frontend](#fase-3-integração-frontend)
7. [Fase 4: Testes e Deployment](#fase-4-testes-e-deployment)
8. [Referência de Endpoints](#referência-de-endpoints)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

### O que é fron_test?

Um dashboard React-Vite para análise interativa de dados metabolômicos. Possui 4 páginas principais:

| Página | Função |
|--------|--------|
| **Dashboard** | Estatísticas gerais: features, candidates, compostos |
| **Top 5 Ranking** | Visualização de features com ranking probabilístico dos 5 melhores candidatos |
| **Upload** | Ingestão de arquivos Excel/CSV (Identification + Abundance) |
| **Chemical Reference** | Busca integrada em bases públicas (PubChem, ChEBI, ChemSpider) |

### O que é QuimioAnalytics?

Uma plataforma Python com:
- **Pipeline ETL** completo (spreadsheets → PostgreSQL)
- **Banco PostgreSQL** com schema 3-camadas (staging, core, reference)
- **Algoritmos de Ranking** probabilístico (ranking de candidatos candidatos)
- **Integração com bases públicas** (PubChem, ChEBI, ChemSpider, HMDB, FooDB, LOTUS, ClassyFire)

### Desafio Atual

✅ **Backend**: Pipeline Python + DB pronto  
❌ **API REST**: Não existe (precisa criar)  
❌ **Frontend**: Mock data apenas (precisa conectar)

### Resultado Esperado

```
[fron_test Frontend] 
      ↓ HTTP/JSON
  [Flask/FastAPI Backend] 
      ↓ SQL
  [PostgreSQL Database]
```

---

## 🏗️ Arquitetura Geral

### 1. Fluxo de Upload (ETL Trigger)

```
User (fron_test)
   ↓ POST /api/v1/upload + {identification.xlsx, abundance.xlsx}
Backend (Flask/FastAPI)
   ↓ Salva arquivos temporários
   ↓ Dispara: run_pipeline_frontend.py
PostgreSQL
   ↓ Carrega em stg.* (staging)
   ↓ Transforma → core.*
   ↓ Calcula ranking de candidatos
Status returned to frontend (batch_id, status, rows)
```

### 2. Fluxo de Dashboard

```
fron_test (ao abrir Dashboard)
   ↓ GET /api/v1/stats
Backend
   ↓ SELECT COUNT(*) FROM core.feature, ...
   ↓ SELECT COUNT(DISTINCT source) FROM ref.*
PostgreSQL
   ↓ Retorna agregações
   ↓ {total_features: 1248, total_candidates: 6240, ...}
Frontend renderiza gráficos
```

### 3. Fluxo de Ranking

```
fron_test (Top5 Ranking page)
   ↓ GET /api/v1/features?search=m/z_123
Backend
   ↓ SELECT * FROM core.feature WHERE m/z ~ search
   ↓ SELECT * FROM core.candidate WHERE feature_id IN (...)
   ↓ ORDER BY probability DESC LIMIT 5
PostgreSQL
   ↓ Retorna estrutura: [feature, [candidate1, candidate2, ...]]
Frontend renderiza tabela interativa
```

---

## ✅ Pré-requisitos

### Backend
- [ ] Python 3.10+
- [ ] PostgreSQL 15 (local ou Docker)
- [ ] Virtual environment criado
- [ ] `requirements.txt` instalado
- [ ] Database inicializado com schema

### Frontend
- [ ] Node.js v18+
- [ ] npm ou yarn
- [ ] fron_test já clonado/criado

### Ambos
- [ ] Git para versionamento
- [ ] Postman/curl para testes de API
- [ ] Docker Compose (recomendado para PostgreSQL)

### Verificar Setup Atual

```bash
# Backend
cd ~/Documents/QuimioAnalytics
python3 --version  # Deve ser 3.10+
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
pip list | grep -i postgres  # Verificar psycopg2-binary

# Frontend
cd ~/Documents/fron_test
node --version  # Deve ser v18+
npm --version

# Database
docker ps  # Se usando Docker
psql -U quimio_user -d quimioanalytics -c "SELECT version();"
```

---

## 🚀 Fase 1: Setup Inicial

### 1.1 Garantir Database Running

```bash
# Se usando Docker (recomendado)
cd ~/Documents/QuimioAnalytics
docker compose up -d

# Verificar
docker ps
# Deve mostrar: quimio_postgres (postgres:15-alpine)

# Se local
psql -U quimio_user -h localhost -d quimioanalytics -c "SELECT 1;"
```

### 1.2 Ativar Virtual Environment Backend

```bash
cd ~/Documents/QuimioAnalytics
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows PowerShell

pip list | grep -E 'pandas|flask|psycopg2'
# Deve listar pacotes instalados
```

### 1.3 Instalar Dependências Backend Adicionais

Será necessário adicionar um framework web. Recomendações:

**Opção A: FastAPI (Recomendado - Moderno, Type Hints)**
```bash
pip install fastapi uvicorn pydantic python-multipart
```

**Opção B: Flask (Simples, Maduro)**
```bash
pip install flask flask-cors
```

**Opção C: Django (Completo, Pesado)**
```bash
pip install django djangorestframework django-cors-headers
```

→ **Recomendação**: FastAPI é ideal para metabolômicos (schemas automáticos, validação)

### 1.4 Setup Frontend

```bash
cd ~/Documents/fron_test

# Instalar dependências
npm install

# Verificar que Vite está configurado
cat vite.config.js  # Deve ter:
# - server.port: 3000
# - plugins: [react()]

# Configurar proxy API (vide Fase 3.2)
```

---

## 🔌 Fase 2: Desenvolvimento da API Backend

### 2.1 Estrutura Recomendada

```
QuimioAnalytics/
├── api/                          # ← CRIAR
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Configurações (DB, CORS, etc)
│   ├── dependencies.py           # Dependências (DB connection)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── dashboard.py          # GET /api/v1/stats
│   │   ├── features.py           # GET /api/v1/features, /features/<id>/ranking
│   │   ├── compounds.py          # GET /api/v1/compounds
│   │   ├── upload.py             # POST /api/v1/upload, GET /api/v1/batches/<id>/status
│   │   └── sources.py            # GET /api/v1/sources
│   ├── models/                   # Pydantic models para request/response
│   │   ├── __init__.py
│   │   ├── feature.py
│   │   ├── compound.py
│   │   └── batch.py
│   ├── services/                 # Lógica de negócio
│   │   ├── __init__.py
│   │   ├── feature_service.py    # Queries ao DB
│   │   ├── upload_service.py     # Dispara ETL
│   │   └── compound_service.py   # Queries compostos
│   └── utils/
│       ├── __init__.py
│       └── db.py                 # Pool de conexões PostgreSQL
└── scripts/
    ├── run/
    │   └── run_pipeline_frontend.py  # ← MANTER (usado pelo API)
    ...
```

### 2.2 Template FastAPI - main.py

Criar `~/Documents/QuimioAnalytics/api/main.py`:

```python
"""
FastAPI Backend para QuimioAnalytics
Conecta frontend React com pipeline Python + PostgreSQL
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import tempfile
import subprocess
import uuid
from datetime import datetime
from typing import Optional

# Importar modelos e serviços (criar em Fase 2.3-2.5)
# from api.routes import dashboard, features, compounds, upload, sources
# from api.config import get_db_connection

# ============================================================================
# SETUP INICIAL
# ============================================================================

# Estados globais para rastreamento
batch_status = {}  # {batch_id: {"status": "processing|completed|error", "message": "...", "created_at": "..."}}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown logic"""
    print("🚀 QuimioAnalytics API iniciando...")
    yield
    print("🛑 QuimioAnalytics API encerrando...")

app = FastAPI(
    title="QuimioAnalytics API",
    description="Backend para dashboard metabolômico",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# CORS - Permitir requisições do frontend
# ============================================================================

ORIGINS = [
    "http://localhost:3000",      # Dev frontend
    "http://localhost:5173",      # Vite default
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    # "https://yourdomain.com",   # Production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ROTAS DE SAÚDE
# ============================================================================

@app.get("/api/v1/health")
async def health_check():
    """Verificar se API está online"""
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "service": "QuimioAnalytics API v1"
    }

# ============================================================================
# ROTA: DASHBOARD STATS
# ============================================================================

@app.get("/api/v1/stats")
async def get_dashboard_stats():
    """
    Retorna estatísticas gerais para Dashboard
    
    Response:
    {
        "total_features": 1248,
        "total_candidates": 6240,
        "total_compounds": 950,
        "sources": {
            "PubChem": 250,
            "ChEBI": 300,
            "ChemSpider": 200,
            "HMDB": 150,
            "FooDB": 50
        },
        "last_updated": "2026-05-19T10:30:00",
        "ingestion_batches": 5
    }
    """
    try:
        # ⚠️ TODO: Substituir por queries ao PostgreSQL
        # conn = get_db_connection()
        # cursor = conn.cursor()
        # cursor.execute("SELECT COUNT(*) FROM core.feature;")
        # total_features = cursor.fetchone()[0]
        # ...
        
        # Por enquanto, mock
        return {
            "total_features": 1248,
            "total_candidates": 6240,
            "total_compounds": 950,
            "sources": {
                "PubChem": 250,
                "ChEBI": 300,
                "ChemSpider": 200,
                "HMDB": 150,
                "FooDB": 50
            },
            "last_updated": "2026-05-19T10:30:00",
            "ingestion_batches": 5
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar stats: {str(e)}")

# ============================================================================
# ROTA: FEATURES COM RANKING
# ============================================================================

@app.get("/api/v1/features")
async def get_features(
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Listar features com seus top 5 candidatos
    
    Query params:
    - search: Buscar por feature_id, m/z, RT (opcional)
    - limit: Número de resultados (default 50)
    - offset: Paginação (default 0)
    
    Response:
    [
        {
            "feature_id": 1,
            "mz": 123.4567,
            "retention_time": 5.2,
            "candidates": [
                {
                    "rank": 1,
                    "compound_name": "Glucose",
                    "formula": "C6H12O6",
                    "probability": 0.92,
                    "mass_error_ppm": 2.1,
                    "source": "PubChem"
                },
                ...
            ]
        },
        ...
    ]
    """
    try:
        # ⚠️ TODO: Implementar queries ao PostgreSQL
        # Exemplo:
        # SELECT f.id, f.mz, f.retention_time
        # FROM core.feature f
        # WHERE f.mz::text LIKE search OR f.id::text LIKE search
        # ORDER BY f.id
        # LIMIT limit OFFSET offset;
        
        # Mock data por enquanto
        return [
            {
                "feature_id": 1,
                "mz": 123.4567,
                "retention_time": 5.2,
                "candidates": [
                    {
                        "rank": 1,
                        "compound_name": "Glucose",
                        "formula": "C6H12O6",
                        "probability": 0.92,
                        "mass_error_ppm": 2.1,
                        "source": "PubChem"
                    }
                ]
            }
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar features: {str(e)}")

@app.get("/api/v1/features/{feature_id}/ranking")
async def get_feature_ranking(feature_id: int):
    """
    Retorna top 5 candidatos para uma feature específica
    
    Response:
    {
        "feature_id": 1,
        "mz": 123.4567,
        "retention_time": 5.2,
        "candidates": [
            {
                "rank": 1,
                "compound_name": "Glucose",
                "formula": "C6H12O6",
                "probability": 0.92,
                "mass_error_ppm": 2.1,
                "source": "PubChem",
                "external_links": {
                    "pubchem_cid": "5793",
                    "chebi_id": "CHEBI:4167",
                    "chemspider_id": "3675"
                }
            },
            ...
        ]
    }
    """
    try:
        # ⚠️ TODO: Query ao PostgreSQL
        # SELECT ... FROM core.candidate
        # WHERE feature_id = feature_id
        # ORDER BY probability DESC
        # LIMIT 5;
        
        return {
            "feature_id": feature_id,
            "mz": 123.4567,
            "retention_time": 5.2,
            "candidates": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar ranking: {str(e)}")

# ============================================================================
# ROTA: SEARCH COMPOSTOS
# ============================================================================

@app.get("/api/v1/compounds")
async def search_compounds(
    search: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 20
):
    """
    Buscar compostos na base integrada
    
    Query params:
    - search: Nome, fórmula, InChiKey (obrigatório)
    - source: Filtrar por fonte (PubChem, ChEBI, ChemSpider, etc.) - opcional
    - limit: Max resultados (default 20)
    
    Response:
    [
        {
            "compound_id": 1,
            "name": "Glucose",
            "formula": "C6H12O6",
            "molecular_weight": 180.16,
            "inchi_key": "WQZGKKKJIJEPHE-GASJEMHNSA-N",
            "classification": "Monosaccharide",
            "external_ids": {
                "pubchem_cid": "5793",
                "chebi_id": "CHEBI:4167",
                "chemspider_id": "3675"
            }
        },
        ...
    ]
    """
    try:
        if not search:
            raise HTTPException(status_code=400, detail="Parameter 'search' é obrigatório")
        
        # ⚠️ TODO: Query ao PostgreSQL com FULL TEXT SEARCH
        # SELECT ... FROM ref.compound
        # WHERE name ILIKE '%search%' OR formula LIKE search
        # AND (source = source OR source IS NULL)
        # LIMIT limit;
        
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar compostos: {str(e)}")

# ============================================================================
# ROTA: UPLOAD + ETL TRIGGER
# ============================================================================

@app.post("/api/v1/upload")
async def upload_files(
    background_tasks: BackgroundTasks,
    identification: UploadFile = File(...),
    abundance: UploadFile = File(...)
):
    """
    Upload de arquivos Identification + Abundance
    Dispara pipeline ETL em background
    
    Form data:
    - identification: Arquivo .xlsx ou .csv (features + formulas)
    - abundance: Arquivo .xlsx ou .csv (abundance per replicate)
    
    Response:
    {
        "batch_id": "uuid-xxx",
        "status": "processing",
        "message": "ETL iniciado",
        "created_at": "2026-05-19T10:30:00",
        "files": {
            "identification": "identification.xlsx",
            "abundance": "abundance.xlsx"
        }
    }
    """
    try:
        batch_id = str(uuid.uuid4())
        
        # Salvar arquivos temporários
        temp_dir = tempfile.mkdtemp()
        id_path = os.path.join(temp_dir, identification.filename)
        ab_path = os.path.join(temp_dir, abundance.filename)
        
        with open(id_path, "wb") as f:
            f.write(await identification.read())
        
        with open(ab_path, "wb") as f:
            f.write(await abundance.read())
        
        # Registrar batch
        batch_status[batch_id] = {
            "status": "processing",
            "message": "Iniciando ETL...",
            "created_at": datetime.now().isoformat(),
            "identification_file": identification.filename,
            "abundance_file": abundance.filename,
            "temp_dir": temp_dir
        }
        
        # Disparar ETL em background
        background_tasks.add_task(
            run_etl_pipeline,
            batch_id=batch_id,
            identification_path=id_path,
            abundance_path=ab_path
        )
        
        return {
            "batch_id": batch_id,
            "status": "processing",
            "message": "ETL iniciado",
            "created_at": batch_status[batch_id]["created_at"],
            "files": {
                "identification": identification.filename,
                "abundance": abundance.filename
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro no upload: {str(e)}")

def run_etl_pipeline(batch_id: str, identification_path: str, abundance_path: str):
    """Executa pipeline ETL em background"""
    try:
        batch_status[batch_id]["status"] = "running"
        batch_status[batch_id]["message"] = "Processando dados..."
        
        # ⚠️ TODO: Adaptar para chamar seu script ETL
        # subprocess.run([
        #     "python3",
        #     "scripts/run/run_pipeline_frontend.py",
        #     "--identificacao", identification_path,
        #     "--abundancia", abundance_path,
        #     "--batch-id", batch_id
        # ], check=True)
        
        batch_status[batch_id]["status"] = "completed"
        batch_status[batch_id]["message"] = "ETL concluído com sucesso"
        batch_status[batch_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        batch_status[batch_id]["status"] = "error"
        batch_status[batch_id]["message"] = f"Erro no ETL: {str(e)}"

@app.get("/api/v1/batches/{batch_id}/status")
async def get_batch_status(batch_id: str):
    """
    Verificar status de um ETL batch
    
    Response:
    {
        "batch_id": "uuid-xxx",
        "status": "processing|completed|error",
        "message": "...",
        "created_at": "2026-05-19T10:30:00",
        "completed_at": "2026-05-19T10:35:00" (opcional)
    }
    """
    if batch_id not in batch_status:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} não encontrado")
    
    return batch_status[batch_id]

# ============================================================================
# ROTA: FONTES DISPONÍVEIS
# ============================================================================

@app.get("/api/v1/sources")
async def get_sources():
    """
    Retorna lista de fontes integradas
    
    Response:
    [
        {"name": "PubChem", "code": "pubchem", "total_compounds": 250},
        {"name": "ChEBI", "code": "chebi", "total_compounds": 300},
        ...
    ]
    """
    return [
        {"name": "PubChem", "code": "pubchem", "total_compounds": 250},
        {"name": "ChEBI", "code": "chebi", "total_compounds": 300},
        {"name": "ChemSpider", "code": "chemspider", "total_compounds": 200},
        {"name": "HMDB", "code": "hmdb", "total_compounds": 150},
        {"name": "FooDB", "code": "foodb", "total_compounds": 50},
    ]

# ============================================================================
# RUN SERVER (DEV)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True  # Hot reload em dev
    )
```

### 2.3 Criar Modelos Pydantic

Criar `~/Documents/QuimioAnalytics/api/models/feature.py`:

```python
from pydantic import BaseModel
from typing import List, Optional

class Candidate(BaseModel):
    rank: int
    compound_name: str
    formula: str
    probability: float
    mass_error_ppm: float
    source: str
    external_links: Optional[dict] = None

class Feature(BaseModel):
    feature_id: int
    mz: float
    retention_time: float
    candidates: List[Candidate]

class FeatureResponse(BaseModel):
    data: List[Feature]
    total: int
    limit: int
    offset: int
```

### 2.4 Criar Serviço de Database

Criar `~/Documents/QuimioAnalytics/api/services/feature_service.py`:

```python
import psycopg2
from typing import Optional, List, Dict
import os

class FeatureService:
    def __init__(self):
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "database": os.getenv("DB_NAME", "quimioanalytics"),
            "user": os.getenv("DB_USER", "quimio_user"),
            "password": os.getenv("DB_PASS", "")
        }
    
    def get_connection(self):
        """Estabelecer conexão com PostgreSQL"""
        return psycopg2.connect(**self.db_config)
    
    def get_all_features(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Buscar features com top 5 candidatos"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                f.id,
                f.mz,
                f.retention_time,
                json_agg(
                    json_build_object(
                        'rank', ROW_NUMBER() OVER (PARTITION BY f.id ORDER BY c.probability DESC),
                        'compound_name', c.compound_name,
                        'formula', c.formula,
                        'probability', c.probability,
                        'mass_error_ppm', c.mass_error_ppm,
                        'source', c.source
                    ) ORDER BY c.probability DESC
                ) AS candidates
            FROM core.feature f
            LEFT JOIN core.candidate c ON f.id = c.feature_id
            GROUP BY f.id
            LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, (limit, offset))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return results
        
        except Exception as e:
            raise Exception(f"Erro ao buscar features: {str(e)}")
    
    def search_compounds(self, search: str, source: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Buscar compostos por nome/fórmula"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                id,
                name,
                formula,
                molecular_weight,
                inchi_key,
                classification
            FROM ref.compound
            WHERE name ILIKE %s OR formula ILIKE %s
            """
            params = [f"%{search}%", f"%{search}%"]
            
            if source:
                query += " AND source = %s"
                params.append(source)
            
            query += " LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return results
        
        except Exception as e:
            raise Exception(f"Erro ao buscar compostos: {str(e)}")
    
    def get_stats(self) -> Dict:
        """Retornar estatísticas gerais"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            queries = {
                "total_features": "SELECT COUNT(*) FROM core.feature;",
                "total_candidates": "SELECT COUNT(*) FROM core.candidate;",
                "total_compounds": "SELECT COUNT(DISTINCT id) FROM ref.compound;",
            }
            
            stats = {}
            for key, query in queries.items():
                cursor.execute(query)
                stats[key] = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return stats
        
        except Exception as e:
            raise Exception(f"Erro ao buscar stats: {str(e)}")
```

### 2.5 Configurar Environment

Criar `~/Documents/QuimioAnalytics/.env`:

```bash
# Backend API
API_HOST=0.0.0.0
API_PORT=8000
API_ENVIRONMENT=development

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quimioanalytics
DB_USER=quimio_user
DB_PASS=your_secure_password_here

# Frontend (para CORS)
FRONTEND_URL=http://localhost:3000

# Logging
LOG_LEVEL=INFO
```

### 2.6 Testar API

```bash
cd ~/Documents/QuimioAnalytics

# Ativar venv
source .venv/bin/activate

# Instalar FastAPI
pip install fastapi uvicorn

# Rodar API
python3 api/main.py

# Em outro terminal, testar
curl http://localhost:8000/api/v1/health
# Response: {"status":"online","timestamp":"...","service":"QuimioAnalytics API v1"}

# Testar stats
curl http://localhost:8000/api/v1/stats
```

---

## 💻 Fase 3: Integração Frontend

### 3.1 Configurar Proxy API

Editar `~/Documents/fron_test/vite.config.js`:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/api/, '/api')  // Se precisar remapear
      }
    }
  }
})
```

### 3.2 Criar Serviço API no Frontend

Criar `~/Documents/fron_test/src/services/api.js`:

```javascript
/**
 * Cliente HTTP para QuimioAnalytics API
 * Substitui mock data por chamadas reais
 */

const API_BASE = "/api/v1";

class QuimioAnalyticsAPI {
  constructor() {
    this.baseURL = API_BASE;
  }

  // =========================================================================
  // HEALTH CHECK
  // =========================================================================

  async health() {
    return this._fetch(`/health`);
  }

  // =========================================================================
  // DASHBOARD
  // =========================================================================

  async getStats() {
    /**
     * GET /api/v1/stats
     * Retorna: { total_features, total_candidates, total_compounds, sources, ... }
     */
    return this._fetch(`/stats`);
  }

  // =========================================================================
  // FEATURES & RANKING
  // =========================================================================

  async getFeatures(search = "", limit = 50, offset = 0) {
    /**
     * GET /api/v1/features?search=...&limit=50&offset=0
     * Retorna: [{ feature_id, mz, retention_time, candidates: [...] }, ...]
     */
    const params = new URLSearchParams({
      search: search || "",
      limit,
      offset,
    });
    return this._fetch(`/features?${params}`);
  }

  async getFeatureRanking(featureId) {
    /**
     * GET /api/v1/features/{feature_id}/ranking
     * Retorna: { feature_id, mz, retention_time, candidates: [...] }
     */
    return this._fetch(`/features/${featureId}/ranking`);
  }

  // =========================================================================
  // COMPOSTOS (Chemical Reference)
  // =========================================================================

  async searchCompounds(search, source = null, limit = 20) {
    /**
     * GET /api/v1/compounds?search=...&source=...&limit=20
     * Retorna: [{ compound_id, name, formula, molecular_weight, external_ids, ... }, ...]
     */
    const params = new URLSearchParams({
      search: search || "",
      limit,
    });
    if (source) params.append("source", source);
    return this._fetch(`/compounds?${params}`);
  }

  // =========================================================================
  // UPLOAD & ETL
  // =========================================================================

  async uploadFiles(identificationFile, abundanceFile) {
    /**
     * POST /api/v1/upload
     * Multipart form data: identification, abundance
     * Retorna: { batch_id, status, message, created_at, files }
     */
    const formData = new FormData();
    formData.append("identification", identificationFile);
    formData.append("abundance", abundanceFile);

    return fetch(`${this.baseURL}/upload`, {
      method: "POST",
      body: formData,
      // NÃO incluir Content-Type: FormData faz automaticamente
    }).then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    });
  }

  async getBatchStatus(batchId) {
    /**
     * GET /api/v1/batches/{batch_id}/status
     * Retorna: { batch_id, status, message, created_at, completed_at }
     */
    return this._fetch(`/batches/${batchId}/status`);
  }

  // =========================================================================
  // SOURCES
  // =========================================================================

  async getSources() {
    /**
     * GET /api/v1/sources
     * Retorna: [{ name, code, total_compounds }, ...]
     */
    return this._fetch(`/sources`);
  }

  // =========================================================================
  // UTILITÁRIOS
  // =========================================================================

  async _fetch(endpoint, options = {}) {
    /**
     * Wrapper comum para fetch com error handling
     */
    const url = `${this.baseURL}${endpoint}`;

    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(
        error.detail || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    return response.json();
  }
}

export const quimioAPI = new QuimioAnalyticsAPI();
export default quimioAPI;
```

### 3.3 Atualizar Dashboard.jsx

Substituir mock data por API calls:

```javascript
// src/pages/Dashboard.jsx
import { useEffect, useState } from "react";
import { Database, Beaker, FileCheck, Activity } from "lucide-react";
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import quimioAPI from "../services/api";
import "../styles/Dashboard.css";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await quimioAPI.getStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error("Erro ao carregar stats:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="dashboard">Carregando...</div>;
  if (error) return <div className="dashboard">Erro: {error}</div>;
  if (!stats) return <div className="dashboard">Sem dados</div>;

  const sourceData = Object.entries(stats.sources || {}).map(([name, value]) => ({
    name,
    value,
  }));

  const abundanceData = [
    { name: "Sample 1", abundance: 4000 },
    { name: "Sample 2", abundance: 3000 },
    { name: "Sample 3", abundance: 2000 },
  ];

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

      <div className="stats-cards">
        <StatCard
          icon={<Beaker size={24} />}
          label="Total Features"
          value={stats.total_features || 0}
        />
        <StatCard
          icon={<Activity size={24} />}
          label="Total Candidates"
          value={stats.total_candidates || 0}
        />
        <StatCard
          icon={<Database size={24} />}
          label="Total Compounds"
          value={stats.total_compounds || 0}
        />
        <StatCard
          icon={<FileCheck size={24} />}
          label="Batches Ingestados"
          value={stats.ingestion_batches || 0}
        />
      </div>

      <div className="charts">
        <div className="chart-container">
          <h3>Abundance per Sample</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={abundanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="abundance" fill="#04BDA2" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Source Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sourceData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
              >
                {sourceData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={["#04BDA2", "#016FE1", "#BD0404", "#FFA500", "#8B00FF"][index]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <button onClick={loadStats} className="refresh-btn">
        Atualizar
      </button>
    </div>
  );
}

function StatCard({ icon, label, value }) {
  return (
    <div className="stat-card">
      <div className="icon">{icon}</div>
      <div>
        <p>{label}</p>
        <h2>{value}</h2>
      </div>
    </div>
  );
}
```

### 3.4 Atualizar Top5Ranking.jsx

```javascript
// src/pages/Top5Ranking.jsx
import { useEffect, useState } from "react";
import quimioAPI from "../services/api";
import "../styles/Top5Ranking.css";

export default function Top5Ranking() {
  const [features, setFeatures] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [error, setError] = useState(null);

  useEffect(() => {
    loadFeatures();
  }, []);

  const loadFeatures = async (searchTerm = "") => {
    try {
      setLoading(true);
      const data = await quimioAPI.getFeatures(searchTerm, 50);
      setFeatures(Array.isArray(data) ? data : data.data || []);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error("Erro ao carregar features:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    const term = e.target.value;
    setSearch(term);
    loadFeatures(term);
  };

  if (loading) return <div className="page">Carregando features...</div>;
  if (error) return <div className="page">Erro: {error}</div>;

  return (
    <div className="page">
      <h1>Top 5 Ranking</h1>

      <input
        type="text"
        placeholder="Buscar por Feature ID ou Composto..."
        value={search}
        onChange={handleSearch}
        className="search-input"
      />

      {features.map((feature) => (
        <div key={feature.feature_id} className="feature-card">
          <div className="feature-header">
            <h3>Feature {feature.feature_id}</h3>
            <span className="mz">m/z: {feature.mz.toFixed(4)}</span>
            <span className="rt">RT: {feature.retention_time.toFixed(2)}min</span>
          </div>

          <table className="ranking-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Compound</th>
                <th>Formula</th>
                <th>Probability</th>
                <th>Mass Error (ppm)</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {feature.candidates && feature.candidates.map((cand) => (
                <tr key={cand.rank} className={getProbabilityClass(cand.probability)}>
                  <td>{cand.rank}</td>
                  <td>{cand.compound_name}</td>
                  <td>{cand.formula}</td>
                  <td>{(cand.probability * 100).toFixed(1)}%</td>
                  <td>{cand.mass_error_ppm.toFixed(2)}</td>
                  <td>{cand.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

function getProbabilityClass(prob) {
  if (prob >= 0.8) return "high-prob";
  if (prob >= 0.6) return "medium-prob";
  return "low-prob";
}
```

### 3.5 Atualizar Upload.jsx

```javascript
// src/pages/Upload.jsx
import { useState } from "react";
import quimioAPI from "../services/api";
import "../styles/Upload.css";

export default function Upload() {
  const [identification, setIdentification] = useState(null);
  const [abundance, setAbundance] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState(null);
  const [batchId, setBatchId] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async () => {
    if (!identification || !abundance) {
      setError("Ambos os arquivos são necessários");
      return;
    }

    try {
      setUploading(true);
      setError(null);

      const response = await quimioAPI.uploadFiles(identification, abundance);
      setBatchId(response.batch_id);
      setStatus(response.status);

      // Polling status
      const pollStatus = async () => {
        try {
          const batch = await quimioAPI.getBatchStatus(response.batch_id);
          setStatus(batch.status);

          if (batch.status === "processing") {
            setTimeout(pollStatus, 2000); // Re-poll a cada 2s
          } else if (batch.status === "completed") {
            setStatus("✅ ETL concluído!");
          }
        } catch (err) {
          console.error("Erro ao polling status:", err);
        }
      };

      if (response.status === "processing") {
        setTimeout(pollStatus, 2000);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page">
      <h1>Upload Dados</h1>

      <div className="upload-area">
        <div className="file-input">
          <label>Arquivo Identification</label>
          <input
            type="file"
            accept=".xlsx,.csv"
            onChange={(e) => setIdentification(e.target.files?.[0])}
            disabled={uploading}
          />
          {identification && <p>✓ {identification.name}</p>}
        </div>

        <div className="file-input">
          <label>Arquivo Abundance</label>
          <input
            type="file"
            accept=".xlsx,.csv"
            onChange={(e) => setAbundance(e.target.files?.[0])}
            disabled={uploading}
          />
          {abundance && <p>✓ {abundance.name}</p>}
        </div>
      </div>

      <button
        onClick={handleUpload}
        disabled={uploading || !identification || !abundance}
        className="submit-btn"
      >
        {uploading ? "Enviando..." : "Enviar e Processar"}
      </button>

      {error && <div className="error-msg">❌ {error}</div>}
      {status && <div className="status-msg">📊 Status: {status}</div>}
      {batchId && <div className="batch-id">Batch ID: {batchId}</div>}
    </div>
  );
}
```

### 3.6 Atualizar ChemicalRef.jsx

```javascript
// src/pages/ChemicalRef.jsx
import { useState, useEffect } from "react";
import quimioAPI from "../services/api";
import { ExternalLink, Search } from "lucide-react";
import "../styles/ChemicalRef.css";

export default function ChemicalRef() {
  const [search, setSearch] = useState("");
  const [compounds, setCompounds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sourceFilter, setSourceFilter] = useState(null);
  const [sources, setSources] = useState([]);

  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      const sourceList = await quimioAPI.getSources();
      setSources(sourceList);
    } catch (err) {
      console.error("Erro ao carregar sources:", err);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!search.trim()) return;

    try {
      setLoading(true);
      const results = await quimioAPI.searchCompounds(search, sourceFilter, 50);
      setCompounds(Array.isArray(results) ? results : []);
    } catch (err) {
      console.error("Erro na busca:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <h1>Chemical Reference</h1>

      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          placeholder="Buscar por nome, fórmula ou InChiKey..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          <Search size={20} /> Buscar
        </button>
      </form>

      <div className="source-filters">
        <button
          className={!sourceFilter ? "active" : ""}
          onClick={() => setSourceFilter(null)}
        >
          Todas
        </button>
        {sources.map((source) => (
          <button
            key={source.code}
            className={sourceFilter === source.code ? "active" : ""}
            onClick={() => setSourceFilter(source.code)}
          >
            {source.name}
          </button>
        ))}
      </div>

      {loading && <p>Carregando...</p>}

      <div className="compounds-grid">
        {compounds.map((compound) => (
          <CompoundCard key={compound.compound_id} compound={compound} />
        ))}
      </div>

      {compounds.length === 0 && !loading && (
        <p className="no-results">Nenhum composto encontrado</p>
      )}
    </div>
  );
}

function CompoundCard({ compound }) {
  return (
    <div className="compound-card">
      <h3>{compound.name}</h3>
      <p className="formula">{compound.formula}</p>
      <p className="mw">MW: {compound.molecular_weight}</p>
      <p className="inchi">{compound.inchi_key}</p>
      <p className="classification">{compound.classification}</p>

      <div className="external-links">
        {compound.external_ids?.pubchem_cid && (
          <a
            href={`https://pubchem.ncbi.nlm.nih.gov/compound/${compound.external_ids.pubchem_cid}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            PubChem <ExternalLink size={14} />
          </a>
        )}
        {compound.external_ids?.chebi_id && (
          <a
            href={`https://www.ebi.ac.uk/chebi/searchId.do?chebiId=${compound.external_ids.chebi_id}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            ChEBI <ExternalLink size={14} />
          </a>
        )}
      </div>
    </div>
  );
}
```

---

## 🧪 Fase 4: Testes e Deployment

### 4.1 Testes Locais E2E

```bash
# Terminal 1: Backend
cd ~/Documents/QuimioAnalytics
source .venv/bin/activate
python3 api/main.py
# Deve rodar em http://localhost:8000

# Terminal 2: Frontend
cd ~/Documents/fron_test
npm run dev
# Deve abrir em http://localhost:3000

# Terminal 3: Database (se Docker)
cd ~/Documents/QuimioAnalytics
docker compose ps
```

**Testes manuais:**

1. Abrir Dashboard → deve mostrar stats do banco
2. Ir a Top5 Ranking → buscar por feature
3. Upload → enviar arquivos e ver status
4. Chemical Reference → buscar compostos

### 4.2 Testes com Postman

```bash
# Import as rotas JSON no Postman:

POST http://localhost:8000/api/v1/upload
Content-Type: multipart/form-data
identification: (arquivo.xlsx)
abundance: (arquivo.xlsx)

GET http://localhost:8000/api/v1/stats

GET http://localhost:8000/api/v1/features?search=&limit=50

GET http://localhost:8000/api/v1/compounds?search=glucose

GET http://localhost:8000/api/v1/sources
```

### 4.3 Deployment Production

#### Backend (Docker)

Criar `~/Documents/QuimioAnalytics/Dockerfile.api`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
COPY api/ ./api/
COPY scripts/ ./scripts/

RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Atualizar `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: quimio_postgres
    environment:
      POSTGRES_DB: quimioanalytics
      POSTGRES_USER: quimio_user
      POSTGRES_PASSWORD: ${DB_PASS}
    ports:
      - "5432:5432"
    volumes:
      - quimio_postgres_data:/var/lib/postgresql/data

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: quimio_api
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: quimioanalytics
      DB_USER: quimio_user
      DB_PASS: ${DB_PASS}
      FRONTEND_URL: https://yourdomain.com
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    command: python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000

volumes:
  quimio_postgres_data:
```

Rodar:

```bash
docker compose up -d
# API em http://yourserver:8000
```

#### Frontend (Vercel/Netlify)

```bash
cd ~/Documents/fron_test

# Build
npm run build

# Deploy no Vercel
npm install -g vercel
vercel deploy

# Ou Netlify
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

---

## 📚 Referência de Endpoints

### Health & Meta

| Método | Endpoint | Response |
|--------|----------|----------|
| `GET` | `/api/v1/health` | `{status, timestamp, service}` |
| `GET` | `/api/v1/sources` | `[{name, code, total_compounds}...]` |

### Dashboard

| Método | Endpoint | Descrição | Response |
|--------|----------|-----------|----------|
| `GET` | `/api/v1/stats` | Stats gerais | `{total_features, total_candidates, ...}` |

### Features & Ranking

| Método | Endpoint | Query Params | Response |
|--------|----------|--------------|----------|
| `GET` | `/api/v1/features` | `search`, `limit`, `offset` | `[{feature_id, mz, candidates...}...]` |
| `GET` | `/api/v1/features/{id}/ranking` | — | `{feature_id, candidates: [...]}`  |

### Compostos

| Método | Endpoint | Query Params | Response |
|--------|----------|--------------|----------|
| `GET` | `/api/v1/compounds` | `search` (obr.), `source`, `limit` | `[{compound_id, name, formula, ...}...]` |

### Upload & ETL

| Método | Endpoint | Body | Response |
|--------|----------|------|----------|
| `POST` | `/api/v1/upload` | Form: `identification`, `abundance` | `{batch_id, status, ...}` |
| `GET` | `/api/v1/batches/{batch_id}/status` | — | `{batch_id, status, message, ...}` |

---

## 🔧 Troubleshooting

### Frontend não conecta ao Backend

**Problema**: CORS error ou `ERR_CONNECTION_REFUSED`

**Solução**:
```javascript
// Verificar em Browser Console
fetch("http://localhost:8000/api/v1/health")
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)

// Se erro de CORS:
// ✓ Backend tem CORS habilitado em main.py?
// ✓ Frontend URL está em ORIGINS?
// ✓ Porta do backend é 8000?
```

### Database connection error

**Problema**: `psycopg2.OperationalError: could not connect to server`

**Solução**:
```bash
# Verificar se postgres está rodando
docker ps | grep postgres

# Se não, iniciar
docker compose up -d postgres

# Testar conexão
psql -U quimio_user -h localhost -d quimioanalytics -c "SELECT 1;"
```

### ETL timeout no upload

**Problema**: Upload fica em "processing" por muito tempo

**Solução**:
```bash
# Aumentar timeout no frontend
// src/services/api.js
const uploadTimeout = 300000; // 5 minutos

// Ou rodar ETL manualmente
cd ~/Documents/QuimioAnalytics
source .venv/bin/activate
python3 scripts/run/run_pipeline_frontend.py \
  --identificacao path/to/id.xlsx \
  --abundancia path/to/ab.xlsx
```

### Mock data vs Real data

**Se vendo dados mock ao invés de reais:**

1. Verificar Network tab no DevTools
   - `GET /api/v1/stats` → retorna HTTP 200?
   - Response tem dados corretos?

2. Verificar se API chama estão ativas
   ```javascript
   // Em src/services/api.js, adicionar logs
   console.log("Fetching:", url);
   console.log("Response:", data);
   ```

3. Verificar se backend queries estão comentadas/implementadas
   ```python
   # Em api/main.py, linha ~80
   # ⚠️ TODO: Substituir por queries ao PostgreSQL ← se vir isto, não está implementado
   ```

---

## 📊 Próximos Passos

1. **[FASE 2]** Completar implementação dos endpoints FastAPI
2. **[FASE 2]** Testar queries PostgreSQL com dados reais
3. **[FASE 3]** Completar integração frontend com todos endpoints
4. **[FASE 4]** Implementar autenticação (JWT ou OAuth2)
5. **[FASE 4]** Setup CI/CD (GitHub Actions)
6. **[FASE 4]** Deploy em staging/production

---

## 👥 Contato & Suporte

Para dúvidas sobre a integração:
- Verificar este documento
- Consultar `docs/` para docs de cada componente
- Rodar testes com Postman/curl
- Ativar logs em `api/main.py`

**Última atualização**: Maio 2026  
**Versão**: 1.0
