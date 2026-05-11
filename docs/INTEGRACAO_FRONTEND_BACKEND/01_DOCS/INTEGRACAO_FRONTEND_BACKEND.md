# Plano de Integração Front-end e Back-end
## QuimioAnalytics - Estruturação para Produção

**Documento de Integração | Data:** 2026-05-10  
**Objetivo:** Orientar a implementação do front-end com integração eficiente ao back-end existente

---

## 1. Visão Geral da Arquitetura

O QuimioAnalytics possui um back-end robusto baseado em Python com pipeline ETL modular e banco PostgreSQL. A integração front-end deve ser implementada através de uma **API REST** que exponha os dados do banco de forma estruturada.

### Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React/Vue)                      │
│              UI Responsiva | Dashboard | Interações          │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   API REST (Flask/FastAPI)                   │
│  Endpoints | Autenticação | Validação | Cache                │
│  /api/batches | /api/features | /api/top5 | /api/compounds   │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL (schemas)                       │
│  core (dados operacionais) | ref (referências) | stg (temp)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Stack Tecnológico Recomendado

### Backend (API)
- **Framework:** FastAPI (recomendado) ou Flask
  - FastAPI: performance superior, validação automática com Pydantic
  - Flask: mais simples, mais referências de integração com dados
- **ORM:** SQLAlchemy (já compatível com psycopg2)
- **Autenticação:** JWT (JSON Web Tokens) ou Cognito
- **Cache:** Redis (para Top 5 e resultados frequentes)
- **Documentação:** Swagger/OpenAPI (automático no FastAPI)

### Frontend
- **Framework:** React ou Vue.js
- **State Management:** Redux, Zustand, Pinia
- **Requisições HTTP:** Axios ou Fetch API
- **Visualização:** Plotly, D3.js ou Apache ECharts

### DevOps
- **Docker:** Container para API
- **Orquestração:** Docker Compose (já existe)
- **CI/CD:** GitHub Actions ou GitLab CI

---

## 3. Endpoints da API REST

### 3.1. Gerenciamento de Batches (Ingestão)

#### `GET /api/v1/batches`
Listar todos os batches de ingestão

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "batch_id": 1,
      "batch_name": "TOP5_RANKING",
      "solvent": "MEOH",
      "ionization_mode": "ESI+",
      "feature_count": 245,
      "created_at": "2026-05-10T15:30:00Z",
      "features_analyzed": 240,
      "candidates_total": 1200
    }
  ],
  "pagination": { "total": 1, "page": 1, "size": 50 }
}
```

---

#### `POST /api/v1/batches`
Criar novo batch de ingestão

**Request:**
```json
{
  "batch_name": "BATCH_NOVO",
  "solvent": "ETOH",
  "ionization_mode": "ESI-",
  "source_notes": "Amostra de solo"
}
```

**Response:** `201 Created`
```json
{
  "status": "success",
  "data": {
    "batch_id": 2,
    "batch_name": "BATCH_NOVO",
    "created_at": "2026-05-10T16:00:00Z"
  }
}
```

---

#### `GET /api/v1/batches/{batch_id}`
Obter detalhes completos de um batch

**Response:**
```json
{
  "status": "success",
  "data": {
    "batch_id": 1,
    "batch_name": "TOP5_RANKING",
    "solvent": "MEOH",
    "ionization_mode": "ESI+",
    "created_at": "2026-05-10T15:30:00Z",
    "features": [
      {
        "feature_id": 101,
        "feature_code": "F001",
        "neutral_mass_da": 234.5678,
        "mz": 235.5756,
        "retention_time_min": 3.45,
        "candidate_count": 5
      }
    ]
  }
}
```

---

### 3.2. Features (Características Espectrométricas)

#### `GET /api/v1/batches/{batch_id}/features`
Listar todas as features de um batch

**Query Parameters:**
- `page`: número da página (default: 1)
- `size`: itens por página (default: 50)
- `sort_by`: campo de ordenação (default: feature_id)
- `order`: asc ou desc (default: asc)

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "feature_id": 101,
      "feature_code": "F001",
      "batch_id": 1,
      "neutral_mass_da": 234.5678,
      "mz": 235.5756,
      "retention_time_min": 3.45,
      "chrom_peak_width_min": 0.12,
      "source_identification_count": 3,
      "candidates_count": 5,
      "top_candidate": {
        "candidate_id": 501,
        "source_compound_id": "ASPIRIN",
        "adducts": "[M+H]+",
        "molecular_formula": "C9H8O4",
        "score_final": 0.92,
        "probabilidade": 0.85,
        "rank": 1
      }
    }
  ],
  "pagination": { "total": 245, "page": 1, "size": 50 }
}
```

---

#### `GET /api/v1/features/{feature_id}`
Obter detalhes de uma feature específica

**Response:**
```json
{
  "status": "success",
  "data": {
    "feature_id": 101,
    "feature_code": "F001",
    "batch_id": 1,
    "neutral_mass_da": 234.5678,
    "mz": 235.5756,
    "retention_time_min": 3.45,
    "chrom_peak_width_min": 0.12,
    "candidates": [
      {
        "rank": 1,
        "candidate_id": 501,
        "source_compound_id": "ASPIRIN",
        "adducts": "[M+H]+",
        "molecular_formula": "C9H8O4",
        "score_base": 0.88,
        "score_final": 0.92,
        "probabilidade": 0.85,
        "fragmentation_score": 0.90,
        "mass_error_ppm": 2.5,
        "isotope_similarity": 0.87,
        "abundance_mean": 1500000,
        "abundance_cv": 0.15
      }
    ]
  }
}
```

---

### 3.3. Top 5 Ranking

#### `GET /api/v1/batches/{batch_id}/top5`
Obter ranking Top 5 de um batch

**Response:**
```json
{
  "status": "success",
  "data": {
    "batch_id": 1,
    "batch_name": "TOP5_RANKING",
    "total_features": 245,
    "candidates_top5": 1225,
    "ranking": [
      {
        "rank": 1,
        "feature_id": 101,
        "feature_code": "F001",
        "compound_name": "Aspirin",
        "adducts": "[M+H]+",
        "molecular_formula": "C9H8O4",
        "neutral_mass_da": 234.5678,
        "score_final": 0.92,
        "probabilidade": 0.85,
        "abundance_mean": 1500000
      },
      {
        "rank": 2,
        "feature_id": 101,
        "feature_code": "F001",
        "compound_name": "Acetylsalicylic Acid",
        "adducts": "[M+Na]+",
        "molecular_formula": "C9H8O4Na",
        "neutral_mass_da": 256.5497,
        "score_final": 0.78,
        "probabilidade": 0.10,
        "abundance_mean": 1200000
      }
    ]
  }
}
```

---

### 3.4. Compostos Externos (Enriquecimento)

#### `GET /api/v1/compounds/external`
Listar compostos enriquecidos com dados externos

**Query Parameters:**
- `source`: filtrar por fonte (pubchem, chebi, chemspider, hmdb)
- `search`: busca por nome ou fórmula
- `batch_id`: filtrar por batch

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "external_compound_id": 1001,
      "source": "PubChem",
      "external_accession": "CID:2244",
      "preferred_name": "Aspirin",
      "molecular_formula": "C9H8O4",
      "exact_mass": 180.0423,
      "canonical_smiles": "CC(=O)Oc1ccccc1C(=O)O",
      "inchi": "InChI=1S/C9H8O4/c1-6(10)9(12)8-5-3-2-4-7(8)11/h2-5,11H,1H3,(H,10,12)",
      "inchikey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
      "properties": [
        {
          "property_name": "Molecular Weight",
          "property_value_num": 180.0424,
          "unit": "g/mol"
        }
      ],
      "identifiers": [
        {
          "identifier_type": "InChIKey",
          "identifier_value": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
          "is_primary": true
        }
      ]
    }
  ],
  "pagination": { "total": 1200, "page": 1, "size": 50 }
}
```

---

#### `GET /api/v1/compounds/external/{external_compound_id}`
Obter detalhes completos de um composto externo

**Response:**
```json
{
  "status": "success",
  "data": {
    "external_compound_id": 1001,
    "source": "PubChem",
    "external_accession": "CID:2244",
    "preferred_name": "Aspirin",
    "molecular_formula": "C9H8O4",
    "exact_mass": 180.0423,
    "canonical_smiles": "CC(=O)Oc1ccccc1C(=O)O",
    "inchi": "InChI=1S/C9H8O4/...",
    "inchikey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
    "properties": [
      {
        "property_name": "Molecular Weight",
        "property_value_num": 180.0424,
        "unit": "g/mol"
      },
      {
        "property_name": "LogP",
        "property_value_num": 1.19,
        "unit": "dimensionless"
      }
    ],
    "identifiers": [
      {
        "identifier_type": "InChIKey",
        "identifier_value": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
        "is_primary": true
      },
      {
        "identifier_type": "CAS",
        "identifier_value": "50-78-2",
        "is_primary": false
      }
    ],
    "cross_references": [
      {
        "source": "ChEBI",
        "external_id": "CHEBI:15365"
      }
    ]
  }
}
```

---

### 3.5. Busca de Compostos

#### `POST /api/v1/compounds/search`
Buscar compostos por nome ou estrutura

**Request:**
```json
{
  "query": "Aspirin",
  "search_type": "name",
  "sources": ["pubchem", "chebi"],
  "limit": 10
}
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "source": "PubChem",
      "external_compound_id": 1001,
      "external_accession": "CID:2244",
      "preferred_name": "Aspirin",
      "molecular_formula": "C9H8O4",
      "relevance_score": 0.98
    }
  ]
}
```

---

### 3.6. Análise e Estatísticas

#### `GET /api/v1/batches/{batch_id}/stats`
Obter estatísticas gerais de um batch

**Response:**
```json
{
  "status": "success",
  "data": {
    "batch_id": 1,
    "batch_name": "TOP5_RANKING",
    "created_at": "2026-05-10T15:30:00Z",
    "summary": {
      "total_features": 245,
      "features_with_candidates": 240,
      "total_candidates": 1200,
      "avg_candidates_per_feature": 4.9,
      "avg_probability_top1": 0.82
    },
    "source_distribution": {
      "pubchem": 350,
      "chebi": 280,
      "chemspider": 220,
      "hmdb": 200,
      "other": 150
    },
    "score_distribution": {
      "min": 0.15,
      "max": 0.98,
      "mean": 0.72,
      "median": 0.75
    }
  }
}
```

---

### 3.7. Gerenciamento de Arquivos (Upload/Download)

#### `POST /api/v1/batches/upload`
Fazer upload de arquivo XLSX (Identificação + Abundância)

**Request:** multipart/form-data
- `identification_file`: arquivo XLSX com dados de identificação
- `abundance_file`: arquivo XLSX com dados de abundância
- `batch_name`: nome do batch

**Response:**
```json
{
  "status": "success",
  "data": {
    "batch_id": 2,
    "batch_name": "BATCH_NOVO",
    "features_created": 245,
    "message": "Arquivos processados com sucesso"
  }
}
```

---

#### `GET /api/v1/batches/{batch_id}/export`
Exportar dados do batch em formato CSV/Parquet/Excel

**Query Parameters:**
- `format`: csv, parquet, excel (default: csv)
- `include`: features, candidates, compounds, stats (comma-separated)

**Response:** File download

---

### 3.8. Sistema de Cache e Status

#### `GET /api/v1/health`
Verificar status da API e banco de dados

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "redis",
  "timestamp": "2026-05-10T16:30:00Z"
}
```

---

#### `POST /api/v1/cache/invalidate`
Invalidar cache (recomputar Top 5)

**Response:**
```json
{
  "status": "success",
  "message": "Cache invalidado com sucesso"
}
```

---

## 4. Modelos de Dados (Pydantic/Dataclasses)

### 4.1 Batch
```python
from pydantic import BaseModel
from datetime import datetime

class BatchBase(BaseModel):
    batch_name: str
    solvent: str | None = None
    ionization_mode: str | None = None
    source_notes: str | None = None

class BatchCreate(BatchBase):
    pass

class Batch(BatchBase):
    batch_id: int
    created_at: datetime
    feature_count: int
    
    class Config:
        from_attributes = True
```

### 4.2 Feature
```python
class Feature(BaseModel):
    feature_id: int
    batch_id: int
    feature_code: str
    neutral_mass_da: float | None
    mz: float | None
    retention_time_min: float | None
    chrom_peak_width_min: float | None
    candidate_count: int
    
    class Config:
        from_attributes = True
```

### 4.3 Candidate
```python
class Candidate(BaseModel):
    candidate_id: int
    feature_id: int
    source_compound_id: str
    adducts: str
    molecular_formula: str
    score_base: float
    score_final: float
    probabilidade: float
    rank: int
    
    class Config:
        from_attributes = True
```

### 4.4 External Compound
```python
class ExternalCompound(BaseModel):
    external_compound_id: int
    source: str
    external_accession: str
    preferred_name: str
    molecular_formula: str
    exact_mass: float
    canonical_smiles: str
    inchi: str
    inchikey: str
    
    class Config:
        from_attributes = True
```

---

## 5. Fluxos Principais

### 5.1 Fluxo de Ingestão e Análise

```
1. Frontend: Upload de arquivos (IDENTIFICACAO.xlsx + ABUND.xlsx)
                    ↓
2. API: Validação de arquivo + roteamento
                    ↓
3. Backend: ETL (Extract → Transform → Load)
   - Leitura de planilhas
   - Normalização de dados
   - Persistência no schema 'stg'
                    ↓
4. Backend: Análise e Ranking Probabilístico
   - Cálculo de scores (massa, fragmentação, isotope)
   - Ranking Top 5
   - Persistência no schema 'core'
                    ↓
5. API: Retorna resultado + batch_id
                    ↓
6. Frontend: Exibe Top 5 em dashboard
```

---

### 5.2 Fluxo de Enriquecimento com Bases Externas

```
1. Frontend: Seleciona Top 5 e fontes externas (PubChem, ChEBI, ChemSpider)
                    ↓
2. API: Inicia job de enriquecimento (async)
                    ↓
3. Backend: Executa ETL externo
   - Extract: Consulta APIs (PubChem REST, ChEBI OLS, ChemSpider)
   - Transform: Normalização de dados
   - Load: Persistência no schema 'ref'
                    ↓
4. Backend: Atualiza cache (Redis)
                    ↓
5. API: Notifica frontend (WebSocket ou polling)
                    ↓
6. Frontend: Exibe dados enriquecidos
```

---

### 5.3 Fluxo de Consulta de Dados

```
1. Frontend: Requisita dados (GET /api/v1/batches/{batch_id}/top5)
                    ↓
2. API: Verifica cache (Redis)
   - Se cache hit: retorna imediatamente
   - Se cache miss: consulta banco de dados
                    ↓
3. API: Formata resposta JSON com status
                    ↓
4. Frontend: Atualiza UI com dados
```

---

## 6. Guia de Implementação

### 6.1 Fase 1: Preparação (Semana 1-2)

#### Backend
1. **Criar estrutura da API** (FastAPI recomendado)
   ```bash
   mkdir -p backend/app
   cd backend
   pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic
   ```

2. **Configurar conexão com banco de dados**
   ```python
   # backend/app/database.py
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   
   DATABASE_URL = "postgresql://quimio_user:password@localhost:5432/quimioanalytics"
   engine = create_engine(DATABASE_URL)
   SessionLocal = sessionmaker(bind=engine)
   ```

3. **Implementar modelos Pydantic** para serialização
   ```python
   # backend/app/models.py
   from pydantic import BaseModel
   
   class BatchResponse(BaseModel):
       batch_id: int
       batch_name: str
       created_at: str
   ```

4. **Criar rotas iniciais** (CRUD básico)
   ```python
   # backend/app/main.py
   from fastapi import FastAPI
   
   app = FastAPI(title="QuimioAnalytics API")
   
   @app.get("/api/v1/health")
   async def health_check():
       return {"status": "healthy"}
   ```

#### Frontend
1. **Setup do projeto React/Vue**
   ```bash
   npm create react-app frontend
   # ou
   npm create vue@latest frontend
   ```

2. **Instalar dependências principais**
   ```bash
   npm install axios redux react-router-dom
   ```

3. **Criar estrutura de pastas**
   ```
   frontend/
   ├── src/
   │   ├── components/
   │   ├── pages/
   │   ├── services/
   │   ├── store/
   │   └── utils/
   ```

---

### 6.2 Fase 2: Implementação de Endpoints Críticos (Semana 3-4)

#### Prioridade 1: Endpoints para Gerenciamento de Batches
```python
# backend/app/routes/batches.py
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/batches", tags=["batches"])

@router.get("/")
async def list_batches(db: Session):
    batches = db.query(Batch).all()
    return {"status": "success", "data": batches}

@router.post("/")
async def create_batch(batch: BatchCreate, db: Session):
    new_batch = Batch(**batch.dict())
    db.add(new_batch)
    db.commit()
    return {"status": "success", "data": new_batch}

@router.get("/{batch_id}")
async def get_batch(batch_id: int, db: Session):
    batch = db.query(Batch).filter(Batch.batch_id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch não encontrado")
    return {"status": "success", "data": batch}
```

#### Prioridade 2: Endpoints para Features e Top 5
```python
# backend/app/routes/features.py
@router.get("/{batch_id}/features")
async def list_features(batch_id: int, skip: int = 0, limit: int = 50, db: Session = None):
    features = db.query(Feature).filter(Feature.batch_id == batch_id).offset(skip).limit(limit).all()
    return {"status": "success", "data": features}

@router.get("/{batch_id}/top5")
async def get_top5(batch_id: int, db: Session = None):
    candidates = db.query(Candidate).filter(Candidate.feature.batch_id == batch_id, Candidate.rank <= 5).all()
    return {"status": "success", "data": candidates}
```

#### Frontend: Serviço de API
```javascript
// frontend/src/services/api.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const batchesAPI = {
  list: () => api.get('/api/v1/batches'),
  create: (data) => api.post('/api/v1/batches', data),
  getById: (id) => api.get(`/api/v1/batches/${id}`),
  getStats: (id) => api.get(`/api/v1/batches/${id}/stats`),
  getTop5: (id) => api.get(`/api/v1/batches/${id}/top5`),
};

export default api;
```

#### Frontend: Componente para Listar Batches
```jsx
// frontend/src/pages/BatchesPage.jsx
import { useState, useEffect } from 'react';
import { batchesAPI } from '../services/api';

export function BatchesPage() {
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        setLoading(true);
        const response = await batchesAPI.list();
        setBatches(response.data.data);
      } catch (error) {
        console.error('Erro ao buscar batches:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchBatches();
  }, []);

  if (loading) return <p>Carregando...</p>;

  return (
    <div>
      <h1>Batches</h1>
      <ul>
        {batches.map(batch => (
          <li key={batch.batch_id}>
            {batch.batch_name} - {batch.feature_count} features
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

### 6.3 Fase 3: Integração com ETL Existente (Semana 5-6)

#### Backend: Integração com Scripts ETL

1. **Criar wrapper para executar ETL**
```python
# backend/app/etl_service.py
import subprocess
from pathlib import Path

async def run_etl_pipeline(identificacao_file, abund_file, batch_id):
    """Executa pipeline ETL de forma assíncrona"""
    cmd = [
        "python3",
        str(PROJECT_ROOT / "scripts/run/run_pipeline_frontend.py"),
        "--load-core",
        "--batch-id", str(batch_id),
        "--identificacao", str(identificacao_file),
        "--abundancia", str(abund_file)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "errors": result.stderr
    }
```

2. **Endpoint para upload de arquivos**
```python
# backend/app/routes/upload.py
from fastapi import File, UploadFile, Form
import shutil
from pathlib import Path

UPLOAD_DIR = Path("staging/uploads")

@router.post("/upload")
async def upload_files(
    identification_file: UploadFile = File(...),
    abundance_file: UploadFile = File(...),
    batch_name: str = Form(...),
    db: Session = None
):
    # Salvar arquivos
    id_path = UPLOAD_DIR / f"{batch_name}_identification.xlsx"
    ab_path = UPLOAD_DIR / f"{batch_name}_abundance.xlsx"
    
    with open(id_path, "wb") as f:
        shutil.copyfileobj(identification_file.file, f)
    with open(ab_path, "wb") as f:
        shutil.copyfileobj(abundance_file.file, f)
    
    # Criar batch no banco
    batch = Batch(batch_name=batch_name)
    db.add(batch)
    db.commit()
    
    # Executar ETL em background
    asyncio.create_task(run_etl_pipeline(id_path, ab_path, batch.batch_id))
    
    return {
        "status": "success",
        "batch_id": batch.batch_id,
        "message": "Pipeline iniciado. Verificar status em breve."
    }
```

#### Frontend: Componente de Upload
```jsx
// frontend/src/components/FileUploader.jsx
import { useState } from 'react';
import { batchesAPI } from '../services/api';

export function FileUploader() {
  const [files, setFiles] = useState({ id: null, ab: null });
  const [batchName, setBatchName] = useState('');
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('identification_file', files.id);
    formData.append('abundance_file', files.ab);
    formData.append('batch_name', batchName);

    try {
      setLoading(true);
      const response = await api.post('/api/v1/batches/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert('Arquivos enviados com sucesso!');
    } catch (error) {
      alert('Erro ao enviar arquivos');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleUpload}>
      <input
        type="text"
        placeholder="Nome do batch"
        value={batchName}
        onChange={(e) => setBatchName(e.target.value)}
        required
      />
      <input
        type="file"
        onChange={(e) => setFiles({...files, id: e.target.files[0]})}
        required
      />
      <input
        type="file"
        onChange={(e) => setFiles({...files, ab: e.target.files[0]})}
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Enviando...' : 'Enviar'}
      </button>
    </form>
  );
}
```

---

### 6.4 Fase 4: Dashboard e Visualização (Semana 7-8)

#### Frontend: Dashboard Principal
```jsx
// frontend/src/pages/Dashboard.jsx
import { useState, useEffect } from 'react';
import { batchesAPI } from '../services/api';

export function Dashboard() {
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [top5, setTop5] = useState([]);

  useEffect(() => {
    if (selectedBatch) {
      batchesAPI.getTop5(selectedBatch).then(res => setTop5(res.data.data));
    }
  }, [selectedBatch]);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr' }}>
      <div>
        <h2>Selecionar Batch</h2>
        {/* Lista de batches */}
      </div>
      <div>
        <h2>Top 5 Ranking</h2>
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>Composto</th>
              <th>Fórmula</th>
              <th>Score</th>
              <th>Probabilidade</th>
            </tr>
          </thead>
          <tbody>
            {top5.map(candidate => (
              <tr key={candidate.candidate_id}>
                <td>{candidate.rank}</td>
                <td>{candidate.source_compound_id}</td>
                <td>{candidate.molecular_formula}</td>
                <td>{candidate.score_final.toFixed(3)}</td>
                <td>{(candidate.probabilidade * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

## 7. Infraestrutura e DevOps

### 7.1 Docker Compose (Atualizado)

```yaml
# docker-compose.yml (adicionar serviço API)
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: quimioanalytics
      POSTGRES_USER: quimio_user
      POSTGRES_PASSWORD: ${DB_PASS}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: quimioanalytics
      DB_USER: quimio_user
      DB_PASS: ${DB_PASS}
      REDIS_URL: redis://redis:6379
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
      - ./scripts:/app/scripts

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000
    depends_on:
      - api

volumes:
  postgres_data:
```

### 7.2 Dockerfile da API

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.3 Dockerfile do Frontend

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

---

## 8. Segurança e Performance

### 8.1 Medidas de Segurança

1. **Autenticação JWT**
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(credentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id
```

2. **CORS**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

3. **Rate Limiting**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v1/batches")
@limiter.limit("100/minute")
async def list_batches(request: Request):
    pass
```

### 8.2 Otimização e Cache

1. **Cache com Redis**
```python
from redis import Redis
import json

redis_client = Redis(host='redis', port=6379, db=0)

@app.get("/api/v1/batches/{batch_id}/top5")
async def get_top5(batch_id: int):
    cache_key = f"top5:{batch_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Buscar do banco
    result = db.query(Candidate).filter(...).all()
    redis_client.setex(cache_key, 3600, json.dumps(result))
    return result
```

2. **Paginação**
```python
@app.get("/api/v1/batches/{batch_id}/features")
async def list_features(batch_id: int, skip: int = 0, limit: int = 50):
    limit = min(limit, 100)  # Máximo 100 por página
    features = db.query(Feature).offset(skip).limit(limit).all()
    total = db.query(Feature).count()
    return {
        "data": features,
        "pagination": {
            "total": total,
            "skip": skip,
            "limit": limit
        }
    }
```

3. **Índices no PostgreSQL**
```sql
CREATE INDEX idx_feature_batch ON core.feature(batch_id);
CREATE INDEX idx_candidate_feature ON core.candidate_identification(feature_id);
CREATE INDEX idx_candidate_rank ON core.candidate_identification(candidate_rank_local);
CREATE INDEX idx_external_source ON ref.external_compound(source_id);
```

---

## 9. Monitoramento e Logs

### 9.1 Logging Estruturado
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.get("/api/v1/batches")
async def list_batches():
    logger.info("Listing all batches")
    try:
        batches = db.query(Batch).all()
        logger.info(f"Found {len(batches)} batches")
        return {"status": "success", "data": batches}
    except Exception as e:
        logger.error(f"Error listing batches: {str(e)}")
        raise
```

### 9.2 Métricas com Prometheus
```python
from prometheus_client import Counter, Histogram

request_count = Counter('api_requests_total', 'Total API requests')
request_duration = Histogram('api_request_duration_seconds', 'API request duration')

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start_time = time.time()
    request_count.inc()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    request_duration.observe(process_time)
    
    return response
```

---

## 10. Checklist de Implementação

### Fase 1: Preparação
- [ ] Projeto backend criado (FastAPI)
- [ ] Projeto frontend criado (React/Vue)
- [ ] Conexão com PostgreSQL configurada
- [ ] Models Pydantic definidos
- [ ] Docker Compose atualizado

### Fase 2: Endpoints Críticos
- [ ] GET /api/v1/batches
- [ ] POST /api/v1/batches
- [ ] GET /api/v1/batches/{batch_id}
- [ ] GET /api/v1/batches/{batch_id}/features
- [ ] GET /api/v1/batches/{batch_id}/top5
- [ ] Componentes React/Vue básicos funcionando

### Fase 3: Integração com ETL
- [ ] Endpoint de upload funcionando
- [ ] ETL executável via API
- [ ] Persistência de resultados em banco
- [ ] Status de processamento disponível

### Fase 4: Dashboard e Visualização
- [ ] Dashboard principal implementado
- [ ] Tabelas interativas
- [ ] Gráficos de distribuição
- [ ] Filtros e paginação

### Fase 5: Segurança e Performance
- [ ] Autenticação JWT implementada
- [ ] CORS configurado
- [ ] Rate limiting ativo
- [ ] Cache com Redis
- [ ] Índices do banco otimizados
- [ ] Logs estruturados

### Fase 6: Testes e Deploy
- [ ] Testes unitários backend
- [ ] Testes de integração
- [ ] Testes frontend
- [ ] Build de produção
- [ ] Deploy em staging
- [ ] Deploy em produção

---

## 11. Referências e Recursos

### Documentação Oficial
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Vue.js: https://vuejs.org/
- SQLAlchemy: https://www.sqlalchemy.org/
- PostgreSQL: https://www.postgresql.org/docs/

### Padrões e Boas Práticas
- RESTful API Design: https://restfulapi.net/
- API Versioning: https://semver.org/
- OpenAPI/Swagger: https://swagger.io/

### Ferramentas Recomendadas
- Postman/Insomnia: Teste de APIs
- DBeaver: Gerenciamento PostgreSQL
- VS Code: Editor de código
- Docker Desktop: Orquestração local

---

## 12. Suporte e Dúvidas

### Contatos
- **Backend:** [Responsável Backend]
- **Frontend:** [Seu Nome]
- **DevOps:** [Responsável DevOps]

### Repositórios
- Backend: `/scripts/app/` (será criado)
- Frontend: `/frontend/` (será criado)
- Documentação: `/docs/`

---

**Documento versão 1.0 | Última atualização: 2026-05-10**
