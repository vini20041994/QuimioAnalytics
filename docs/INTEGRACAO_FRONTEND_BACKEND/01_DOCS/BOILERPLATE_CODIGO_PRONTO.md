# Boilerplate para Implementação Rápida
## QuimioAnalytics - Templates Prontos para Usar

---

## 1. Backend Setup (FastAPI)

### 1.1 requirements.txt
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
redis==5.0.1
python-jose==3.3.0
passlib==1.7.4
python-multipart==0.0.6
pytest==7.4.3
pytest-asyncio==0.21.1
```

### 1.2 app/main.py
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes import batches, features, compounds, uploads

# Criar tabelas se não existirem
Base.metadata.create_all(bind=engine)

# Inicializar FastAPI
app = FastAPI(
    title="QuimioAnalytics API",
    description="API para integração e análise de dados de metabolômica",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "postgresql",
        "cache": "redis"
    }

# Incluir rotas
app.include_router(batches.router, tags=["batches"])
app.include_router(features.router, tags=["features"])
app.include_router(compounds.router, tags=["compounds"])
app.include_router(uploads.router, tags=["uploads"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

### 1.3 app/database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

DATABASE_URL = (
    f"postgresql://{settings.db_user}:{settings.db_pass}@"
    f"{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 1.4 app/config.py
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "quimioanalytics"
    db_user: str = "quimio_user"
    db_pass: str = "password"
    redis_url: str = "redis://localhost:6379"
    jwt_secret: str = "sua_chave_secreta_aqui"
    debug: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
```

### 1.5 app/models.py (SQLAlchemy)
```python
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Batch(Base):
    __tablename__ = "core.ingestion_batch"
    
    batch_id = Column(Integer, primary_key=True, index=True)
    batch_name = Column(String(120), nullable=False)
    solvent = Column(String(80))
    ionization_mode = Column(String(20))
    source_notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    features = relationship("Feature", back_populates="batch")

class Feature(Base):
    __tablename__ = "core.feature"
    
    feature_id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("core.ingestion_batch.batch_id"))
    feature_code = Column(String(100), nullable=False)
    neutral_mass_da = Column(Float)
    mz = Column(Float)
    retention_time_min = Column(Float)
    chrom_peak_width_min = Column(Float)
    source_identification_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    batch = relationship("Batch", back_populates="features")
    candidates = relationship("Candidate", back_populates="feature")

class Candidate(Base):
    __tablename__ = "core.candidate_identification"
    
    candidate_id = Column(Integer, primary_key=True, index=True)
    feature_id = Column(Integer, ForeignKey("core.feature.feature_id"))
    source_compound_id = Column(String(120))
    adducts = Column(String(255))
    molecular_formula = Column(String(120))
    score = Column(Float)
    fragmentation_score = Column(Float)
    mass_error_ppm = Column(Float)
    isotope_similarity = Column(Float)
    score_base = Column(Float)
    score_final = Column(Float)
    candidate_rank_local = Column(Integer)
    
    feature = relationship("Feature", back_populates="candidates")
```

### 1.6 app/schemas.py (Pydantic)
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class BatchBase(BaseModel):
    batch_name: str
    solvent: Optional[str] = None
    ionization_mode: Optional[str] = None
    source_notes: Optional[str] = None

class BatchCreate(BatchBase):
    pass

class BatchResponse(BatchBase):
    batch_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class FeatureBase(BaseModel):
    feature_code: str
    neutral_mass_da: Optional[float] = None
    mz: Optional[float] = None
    retention_time_min: Optional[float] = None

class FeatureResponse(FeatureBase):
    feature_id: int
    batch_id: int
    
    class Config:
        from_attributes = True

class CandidateResponse(BaseModel):
    candidate_id: int
    feature_id: int
    source_compound_id: str
    molecular_formula: str
    score_final: float
    candidate_rank_local: int
    
    class Config:
        from_attributes = True

class Top5Response(BaseModel):
    rank: int
    candidate_id: int
    feature_id: int
    source_compound_id: str
    molecular_formula: str
    score_final: float
    probabilidade: float
```

### 1.7 app/routes/batches.py
```python
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Batch, Feature, Candidate
from app.schemas import BatchCreate, BatchResponse
from typing import List

router = APIRouter(prefix="/api/v1/batches")

@router.get("/", response_model=dict)
async def list_batches(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Listar todos os batches com paginação"""
    total = db.query(Batch).count()
    batches = db.query(Batch).offset(skip).limit(limit).all()
    
    return {
        "status": "success",
        "data": batches,
        "pagination": {
            "total": total,
            "skip": skip,
            "limit": limit
        }
    }

@router.post("/", response_model=dict, status_code=201)
async def create_batch(
    batch: BatchCreate,
    db: Session = Depends(get_db)
):
    """Criar novo batch"""
    db_batch = Batch(**batch.dict())
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    
    return {
        "status": "success",
        "data": db_batch
    }

@router.get("/{batch_id}", response_model=dict)
async def get_batch(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """Obter detalhes de um batch específico"""
    batch = db.query(Batch).filter(Batch.batch_id == batch_id).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch não encontrado")
    
    feature_count = db.query(Feature).filter(Feature.batch_id == batch_id).count()
    candidate_count = db.query(Candidate).join(
        Feature, Candidate.feature_id == Feature.feature_id
    ).filter(Feature.batch_id == batch_id).count()
    
    return {
        "status": "success",
        "data": {
            **batch.__dict__,
            "feature_count": feature_count,
            "candidate_count": candidate_count
        }
    }

@router.get("/{batch_id}/features", response_model=dict)
async def list_features(
    batch_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Listar features de um batch"""
    features = db.query(Feature).filter(
        Feature.batch_id == batch_id
    ).offset(skip).limit(limit).all()
    
    total = db.query(Feature).filter(Feature.batch_id == batch_id).count()
    
    return {
        "status": "success",
        "data": features,
        "pagination": {"total": total, "skip": skip, "limit": limit}
    }

@router.get("/{batch_id}/top5", response_model=dict)
async def get_top5(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """Obter Top 5 ranking de um batch"""
    candidates = db.query(Candidate).join(
        Feature, Candidate.feature_id == Feature.feature_id
    ).filter(
        Feature.batch_id == batch_id,
        Candidate.candidate_rank_local <= 5
    ).order_by(
        Feature.feature_id,
        Candidate.candidate_rank_local
    ).all()
    
    return {
        "status": "success",
        "data": candidates,
        "total": len(candidates)
    }

@router.get("/{batch_id}/stats", response_model=dict)
async def get_batch_stats(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """Obter estatísticas de um batch"""
    total_features = db.query(Feature).filter(Feature.batch_id == batch_id).count()
    total_candidates = db.query(Candidate).join(
        Feature, Candidate.feature_id == Feature.feature_id
    ).filter(Feature.batch_id == batch_id).count()
    
    return {
        "status": "success",
        "data": {
            "batch_id": batch_id,
            "total_features": total_features,
            "total_candidates": total_candidates,
            "avg_candidates_per_feature": (
                total_candidates / total_features if total_features > 0 else 0
            )
        }
    }
```

---

## 2. Frontend Setup (React)

### 2.1 frontend/package.json
```json
{
  "name": "quimio-analytics-frontend",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.2",
    "react-router-dom": "^6.20.0",
    "redux": "^4.2.1",
    "react-redux": "^8.1.3",
    "@reduxjs/toolkit": "^1.9.7"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
```

### 2.2 frontend/src/services/api.js
```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token JWT (quando implementado)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para tratar erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ===== BATCHES API =====
export const batchesAPI = {
  list: (skip = 0, limit = 50) => 
    api.get('/api/v1/batches', { params: { skip, limit } }),
  
  create: (batchData) => 
    api.post('/api/v1/batches', batchData),
  
  getById: (batchId) => 
    api.get(`/api/v1/batches/${batchId}`),
  
  getFeatures: (batchId, skip = 0, limit = 50) => 
    api.get(`/api/v1/batches/${batchId}/features`, { params: { skip, limit } }),
  
  getTop5: (batchId) => 
    api.get(`/api/v1/batches/${batchId}/top5`),
  
  getStats: (batchId) => 
    api.get(`/api/v1/batches/${batchId}/stats`),
  
  upload: (formData) => 
    api.post('/api/v1/batches/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
};

// ===== FEATURES API =====
export const featuresAPI = {
  getById: (featureId) => 
    api.get(`/api/v1/features/${featureId}`),
};

// ===== COMPOUNDS API =====
export const compoundsAPI = {
  list: (source = null, skip = 0, limit = 50) => 
    api.get('/api/v1/compounds/external', { 
      params: { source, skip, limit } 
    }),
  
  getById: (compoundId) => 
    api.get(`/api/v1/compounds/external/${compoundId}`),
  
  search: (query, searchType = 'name', sources = ['pubchem', 'chebi']) => 
    api.post('/api/v1/compounds/search', {
      query,
      search_type: searchType,
      sources,
    }),
};

// ===== HEALTH CHECK =====
export const healthAPI = {
  check: () => api.get('/api/v1/health'),
};

export default api;
```

### 2.3 frontend/src/store/batchSlice.js (Redux)
```javascript
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { batchesAPI } from '../services/api';

// Thunks assíncronos
export const fetchBatches = createAsyncThunk(
  'batches/fetchBatches',
  async ({ skip = 0, limit = 50 }, { rejectWithValue }) => {
    try {
      const response = await batchesAPI.list(skip, limit);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Erro ao buscar batches');
    }
  }
);

export const fetchBatchById = createAsyncThunk(
  'batches/fetchBatchById',
  async (batchId, { rejectWithValue }) => {
    try {
      const response = await batchesAPI.getById(batchId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Erro ao buscar batch');
    }
  }
);

export const fetchTop5 = createAsyncThunk(
  'batches/fetchTop5',
  async (batchId, { rejectWithValue }) => {
    try {
      const response = await batchesAPI.getTop5(batchId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Erro ao buscar Top 5');
    }
  }
);

const batchSlice = createSlice({
  name: 'batches',
  initialState: {
    list: [],
    currentBatch: null,
    top5: [],
    loading: false,
    error: null,
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchBatches.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBatches.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload.data || [];
      })
      .addCase(fetchBatches.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(fetchBatchById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBatchById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentBatch = action.payload.data || null;
      })
      .addCase(fetchBatchById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(fetchTop5.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTop5.fulfilled, (state, action) => {
        state.loading = false;
        state.top5 = action.payload.data || [];
      })
      .addCase(fetchTop5.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export default batchSlice.reducer;
```

### 2.4 frontend/src/store/index.js
```javascript
import { configureStore } from '@reduxjs/toolkit';
import batchReducer from './batchSlice';

const store = configureStore({
  reducer: {
    batches: batchReducer,
  },
});

export default store;
```

### 2.5 frontend/src/pages/BatchesPage.jsx
```jsx
import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchBatches } from '../store/batchSlice';

export function BatchesPage() {
  const dispatch = useDispatch();
  const { list, loading, error } = useSelector(state => state.batches);

  useEffect(() => {
    dispatch(fetchBatches({ skip: 0, limit: 50 }));
  }, [dispatch]);

  if (loading) return <div>Carregando...</div>;
  if (error) return <div>Erro: {error}</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h1>Batches</h1>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ backgroundColor: '#f0f0f0' }}>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>ID</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Nome</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Solvente</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Data</th>
          </tr>
        </thead>
        <tbody>
          {list.map((batch) => (
            <tr key={batch.batch_id}>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                {batch.batch_id}
              </td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                {batch.batch_name}
              </td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                {batch.solvent || '-'}
              </td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                {new Date(batch.created_at).toLocaleDateString('pt-BR')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### 2.6 frontend/src/pages/Top5Page.jsx
```jsx
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { batchesAPI } from '../services/api';

export function Top5Page() {
  const { batchId } = useParams();
  const [top5, setTop5] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await batchesAPI.getTop5(batchId);
        setTop5(response.data.data || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [batchId]);

  if (loading) return <div>Carregando Top 5...</div>;
  if (error) return <div>Erro: {error}</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h1>Top 5 - Batch {batchId}</h1>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ backgroundColor: '#f0f0f0' }}>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Rank</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Composto</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Fórmula</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Score</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Aduto</th>
          </tr>
        </thead>
        <tbody>
          {top5.map((candidate, idx) => (
            <tr key={candidate.candidate_id}>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                {candidate.candidate_rank_local}
              </td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                {candidate.source_compound_id}
              </td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                {candidate.molecular_formula}
              </td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                {candidate.score_final?.toFixed(4)}
              </td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                {candidate.adducts}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### 2.7 frontend/src/App.jsx
```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { BatchesPage } from './pages/BatchesPage';
import { Top5Page } from './pages/Top5Page';

function App() {
  return (
    <BrowserRouter>
      <div style={{ fontFamily: 'Arial, sans-serif' }}>
        <nav style={{ backgroundColor: '#333', color: '#fff', padding: '10px' }}>
          <h1>QuimioAnalytics</h1>
        </nav>
        <Routes>
          <Route path="/" element={<BatchesPage />} />
          <Route path="/batch/:batchId/top5" element={<Top5Page />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
```

---

## 3. Docker Setup

### 3.1 Dockerfile Backend
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta
EXPOSE 8000

# Comando padrão
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.2 Dockerfile Frontend
```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependências
RUN npm ci

# Copiar código
COPY . .

# Build para produção (opcional)
# RUN npm run build

# Expor porta
EXPOSE 3000

# Comando padrão
CMD ["npm", "start"]
```

### 3.3 docker-compose.yml (Atualizado)
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: quimio_postgres
    environment:
      POSTGRES_DB: quimioanalytics
      POSTGRES_USER: quimio_user
      POSTGRES_PASSWORD: ${DB_PASS:-password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema_postgresql_mvp_entrega2.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U quimio_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: quimio_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: quimio_api
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: quimioanalytics
      DB_USER: quimio_user
      DB_PASS: ${DB_PASS:-password}
      REDIS_URL: redis://redis:6379
      DEBUG: ${DEBUG:-False}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./backend:/app
      - ./scripts:/app/scripts
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: quimio_frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000
    depends_on:
      - api
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  postgres_data:
  redis_data:
```

---

## 4. Arquivos de Configuração

### 4.1 .env (Frontend)
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENV=development
REACT_APP_DEBUG=true
```

### 4.2 .env (Backend)
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quimioanalytics
DB_USER=quimio_user
DB_PASS=sua_senha_segura
REDIS_URL=redis://localhost:6379
JWT_SECRET=sua_chave_secreta_super_segura
DEBUG=True
```

---

## 5. Scripts de Teste

### 5.1 tests/test_batches.py
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_batches_empty():
    response = client.get("/api/v1/batches")
    assert response.status_code == 200
    assert "data" in response.json()

def test_create_batch():
    batch_data = {
        "batch_name": "TEST_BATCH",
        "solvent": "MEOH",
        "ionization_mode": "ESI+"
    }
    response = client.post("/api/v1/batches", json=batch_data)
    assert response.status_code == 201
    assert response.json()["status"] == "success"
```

---

## 6. Guia de Início Rápido

```bash
# 1. Clonar repositório
git clone <repo>
cd QuimioAnalytics

# 2. Setup Backend
mkdir backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 3. Setup Frontend
npm create react-app frontend
cd frontend
npm install axios react-router-dom redux react-redux @reduxjs/toolkit
cd ..

# 4. Copiar arquivos de configuração
cp .env.example .env
docker-compose up -d

# 5. Verificar se está rodando
curl http://localhost:8000/api/v1/health
# Abrir http://localhost:3000 no navegador
```

---

**Boilerplate: Templates Prontos para Usar**  
**Data:** 2026-05-10  
**Status:** 🟢 Pronto para iniciar desenvolvimento
