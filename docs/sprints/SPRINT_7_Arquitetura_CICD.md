# Sprint 7 — Arquitetura e CI/CD

**Status**: 🔴 Todo  
**Capacidade**: 34 pontos  
**Objetivo**: Introduzir padrões de projeto (Repository, Service Layer), pipeline de CI/CD automatizado e preparar infraestrutura para múltiplos ambientes.

---

## Contexto

Até aqui o projeto tem:
- ✅ Ranking correto (Sprint 2)
- ✅ Testes robustos (Sprint 3)
- ✅ Banco com integridade (Sprint 4)
- ✅ Performance e observabilidade (Sprint 5)
- ✅ Segurança endereçada (Sprint 6)

Sprint 7 institucionaliza essas melhorias numa arquitetura escalável:
1. **Repository Pattern** — SQL centralizado, fácil manter
2. **Service Layer** — lógica de negócio separada de I/O
3. **CI/CD Pipeline** — validação automática em cada push
4. **Multi-ambiente** — dev/staging/prod com configurações distintas
5. **Type hints** — MyPy strict para detecção de erro estática

---

## Principais Pontos Levantados

### 1. Lógica de negócio espalhada entre arquivos
- **Problema**: SQL está em `analytics.py`, `load_stg_transformed.py`, `database_top_10.py`
- **Impacto**: Change para schema → 3+ arquivos para atualizar; alto risco de inconsistência

### 2. Sem padrão de acesso a dados
- **Problema**: Cada loader escreve queries SQL diferentes para mesma operação
- **Impacto**: Duplicação; diferença de performance; difícil testar

### 3. Sem pipeline de CI/CD
- **Problema**: Testes locais, sem gate automático no repo
- **Impacto**: Código ruim chega ao `main`; Deploy manual é propenso a erro

### 4. Sem suporte a múltiplos ambientes
- **Problema**: `docker-compose.yml` igual para dev/prod
- **Impacto**: Dev expõe porta; prod não expõe; sem diferenciação

### 5. Sem type hints em código crítico
- **Problema**: `def load(df): ...` — tipo de `df` é implícito
- **Impacto**: IDE não ajuda; erros detectados em runtime

### 6. Sem backup automático
- **Problema**: Backup é manual ou inexistente
- **Impacto**: Perda de dados sem recuperação

---

## O Que Deve Ser Feito

### 1. Criar `IdentificationRepository`

```python
# scripts/repositories/identification_repository.py
from typing import List, Optional
import io
import psycopg
import pandas as pd


class IdentificationRepository:
    """Acesso a dados de identificações com operações padrão."""
    
    def __init__(self, conn: psycopg.Connection):
        self.conn = conn
    
    def insert_batch(self, df: pd.DataFrame, columns: List[str]) -> int:
        """Insere batch via COPY. Retorna número de linhas."""
        buffer = io.StringIO()
        df[columns].to_csv(
            buffer,
            index=False,
            header=False,
            sep="\t",
            na_rep="\\N",
        )
        buffer.seek(0)
        
        with self.conn.cursor() as cur:
            cur.copy_from(
                buffer,
                "stg.identification_row",
                columns=columns,
                null="\\N",
            )
        self.conn.commit()
        return len(df)
    
    def get_by_batch(self, batch_id: str) -> pd.DataFrame:
        """Retorna todas as identificações de um batch."""
        query = """
        SELECT * FROM stg.identification_row
        WHERE batch_id = %s
        ORDER BY id
        """
        return pd.read_sql(query, self.conn, params=(batch_id,))
    
    def get_by_feature(self, feature_id: int) -> pd.DataFrame:
        """Retorna candidatos de uma feature com ranking."""
        query = """
        SELECT ci.*, f.mz, f.rt, f.adduct
        FROM core.candidate_identification ci
        JOIN core.feature f ON ci.feature_id = f.id
        WHERE ci.feature_id = %s
        ORDER BY ci.rank_group, ci.is_tied
        """
        return pd.read_sql(query, self.conn, params=(feature_id,))
    
    def mark_deleted(self, identification_id: int) -> None:
        """Soft-delete de uma identificação."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE core.candidate_identification SET deleted_at = NOW() WHERE id = %s",
                (identification_id,),
            )
        self.conn.commit()
```

### 2. Criar `RankingService`

```python
# scripts/services/ranking_service.py
from typing import Tuple
import pandas as pd
from scripts.models.biological_ranking_engine import BiologicalRankingEngine
from scripts.repositories.identification_repository import IdentificationRepository


class RankingService:
    """Orquestra ranking de candidatos."""
    
    def __init__(
        self,
        ranking_engine: BiologicalRankingEngine,
        repository: IdentificationRepository,
    ):
        self.engine = ranking_engine
        self.repo = repository
    
    def rank_and_save(
        self,
        candidates_df: pd.DataFrame,
        batch_id: str,
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Aplica escadinha, salva no banco, retorna resultado + métricas.
        """
        ranked = self.engine.apply_ranking(candidates_df, group_by="feature_id")
        
        # Salvar no banco
        rows_saved = self.repo.insert_batch(
            ranked,
            columns=["batch_id", "feature_id", "fragment_score", "rank_group", "is_tied"],
        )
        
        # Métricas
        tied_groups = (ranked["is_tied"] == True).sum()
        
        return ranked, {
            "rows_saved": rows_saved,
            "tied_groups": tied_groups,
            "batch_id": batch_id,
        }
```

### 3. Centralizar constantes

```python
# scripts/constants.py
"""Constantes centralizadas do projeto."""

# Scoring
MASS_TOLERANCE_PPM = 5.0
ISOTOPE_MIN_SIMILARITY = 0.7
FRAGMENT_MIN_INTENSITY = 10.0

# Rate limiting
PUBCHEM_RATE_LIMIT_DELAY = 0.1  # segundos
CHEBI_RATE_LIMIT_DELAY = 0.1

# HTTP
HTTP_TIMEOUT = 30  # segundos
HTTP_MAX_RETRIES = 3
HTTP_BACKOFF_FACTOR = 0.5

# Database
DB_BATCH_SIZE = 1000
DB_POOL_SIZE = 5
DB_CONNECTION_TIMEOUT = 10

# Paths
RAW_INPUTS_DIR = "./data/raw_inputs"
STAGING_DIR = "./data/staging"
REPORTS_DIR = "./runtime/reports"

# Feature extraction
MIN_FEATURES_FOR_ANALYSIS = 10
```

### 4. Adicionar type hints com MyPy strict

```python
# scripts/models/biological_ranking_engine.py — adicionar hints
from typing import Optional, Dict, Tuple
import pandas as pd


class BiologicalRankingEngine:
    RANKING_STEPS: List[Tuple[str, bool]] = [
        ("fragment_score", False),
        ("isotope_similarity", False),
        ("mass_error_ppm", True),
        ("formula", True),
    ]
    
    def apply_ranking(
        self,
        df: pd.DataFrame,
        group_by: str = "feature_group",
    ) -> pd.DataFrame:
        """Retorna DataFrame com colunas rank_group e is_tied."""
        ...
    
    def _rank_group(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica escadinha a um grupo."""
        ...
    
    def format_for_display(self, ranked_df: pd.DataFrame) -> str:
        """Retorna texto formatado com empates."""
        ...
```

**Configurar MyPy**:

```ini
# mypy.ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
```

### 5. Criar CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: quimio_test
          POSTGRES_USER: quimio_etl
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run linter (ruff)
        run: ruff check scripts/ tests/
      
      - name: Run type checker (mypy)
        run: mypy --strict scripts/models scripts/services
      
      - name: Run tests with coverage
        run: |
          pytest --cov=scripts --cov=tests --cov-report=xml --cov-report=term-missing
      
      - name: Enforce coverage minimum
        run: |
          coverage report --fail-under=60
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### 6. Criar Docker multi-ambiente

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: quimio_analytics
      POSTGRES_USER: quimio_etl
      POSTGRES_PASSWORD: dev_pass
    ports:
      - "127.0.0.1:5432:5432"  # Exposto em dev
    volumes:
      - postgres_data:/var/lib/postgresql/data

  app:
    build: .
    environment:
      ENVIRONMENT: development
      DATABASE_URL: postgresql://quimio_etl:dev_pass@postgres:5432/quimio_analytics
      LOG_LEVEL: DEBUG
    ports:
      - "5000:5000"
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  postgres_data:
```

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: quimio_analytics
      POSTGRES_USER: quimio_etl
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    ports: []  # Sem exposição externa
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    secrets:
      - db_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U quimio_etl"]
      interval: 10s
      timeout: 5s
      retries: 5

  backup:
    image: postgres:15-alpine
    environment:
      PGPASSFILE: /run/secrets/pgpass
    volumes:
      - ./backups:/backups
    command: >
      bash -c 'while true; do
        pg_dump -h postgres -U quimio_etl quimio_analytics | gzip > /backups/backup_$(date +%Y%m%d_%H%M%S).sql.gz;
        sleep 86400;
      done'
    depends_on:
      postgres:
        condition: service_healthy
    secrets:
      - pgpass

secrets:
  db_password:
    file: ./secrets/db_password.txt
  pgpass:
    file: ./secrets/pgpass

volumes:
  postgres_data:
```

---

## Critérios de Aceite

| ID | Tarefa | Critério |
|---|---|---|
| S7-01 | IdentificationRepository | `insert_batch()`, `get_by_batch()`, `get_by_feature()` funcionam |
| S7-02 | RankingService | `rank_and_save()` orquestra engine e repository |
| S7-03 | Constantes centralizadas | `from scripts.constants import *` funciona em todos os loaders |
| S7-04 | Type hints | `mypy --strict` passa sem erros em `models/` e `services/` |
| S7-05 | CI/CD workflow | PR executa lint, type check, testes, cobertura; falha abaixo de 60% |
| S7-06 | Build Docker no CI | Imagem constrói sem erro em cada push |
| S7-07 | Multi-ambiente | `docker-compose.dev.yml` expõe porta; `docker-compose.prod.yml` não expõe |
| S7-08 | Backup automático | Serviço backup cria `.sql.gz` diariamente em `/backups/` |

---

## Lições Aprendidas (Antecipadas)

- Repository Pattern reduz duplicação; Service Layer separa regra de negócio de I/O.
- CI/CD gate é força multiplicadora — força padrões desde o primeiro commit.
- Type hints + MyPy strict previnem 40% dos bugs antes do primeiro teste.

---

## Próximos Passos

- [ ] **Dia 1**: Criar `IdentificationRepository` e testar com dataset de exemplo
- [ ] **Dia 2**: Criar `RankingService`; integrar com `analytics.py`
- [ ] **Dia 3**: Centralizar constantes em `constants.py`
- [ ] **Dia 4**: Adicionar type hints em `models/` e `services/`; rodar MyPy
- [ ] **Dia 5**: Criar `.github/workflows/ci.yml`; testar em PR
- [ ] **Dia 6**: Criar `docker-compose.dev.yml` e `docker-compose.prod.yml`
- [ ] **Dia 7**: Configurar serviço de backup; testar restore
- [ ] **Semana 2**: Refatorar todos os loaders para usar Repository

---

**Referência**: [AUDITORIA_E_QUADRO_SPRINT.md — Sprint 7](../AUDITORIA_E_QUADRO_SPRINT.md#sprint-7--arquitetura-e-cicd)
