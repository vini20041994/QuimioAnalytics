# Sprint 5 — Performance e Observabilidade

**Status**: 🔴 Todo  
**Capacidade**: 37 pontos  
**Objetivo**: Aumentar throughput 10× com COPY, padronizar logging por batch e criar relatório de qualidade de dados.

---

## Contexto

Atualmente o pipeline leva 45–60 minutos para processar 50 K linhas. Pesquisadores não conseguem iterar; não há visibilidade sobre quantos dados foram perdidos em cada etapa.

Sprint 5 implementa:
1. **COPY em vez de INSERT row-by-row** — speedup de 10×
2. **Cliente HTTP unificado** com retry, backoff, timeout
3. **Relatório de qualidade** — quantas linhas perdidas em cada transformação
4. **Logging estruturado** — rastreabilidade por batch_id

---

## Principais Pontos Levantados

### 1. INSERTs row-by-row são inescaláveis
- **Arquivo**: `scripts/load/load_stg_transformed.py`, `scripts/features/database_candidates.py`
- **Problema**: Loop `for i, row in df.iterrows()` faz 50 K viagens de rede
- **Impacto**: 45–60 min para 50 K linhas; 3–5 horas para 500 K

```python
# ANTES — row-by-row:
for i, row in df.iterrows():
    cur.execute("INSERT INTO stg.identification_row VALUES (%s, %s, ...)", row)
# Resultado: 50 K roundtrips de rede

# DEPOIS — COPY:
buffer = io.StringIO()
df[colunas].to_csv(buffer, index=False, header=False, sep="\t", na_rep="\\N")
buffer.seek(0)
cur.copy_from(buffer, "stg.identification_row", columns=colunas, null="\\N")
# Resultado: 1 roundtrip de rede para 50 K linhas
```

### 2. Extratores legados não têm retry nem timeout
- **Arquivos**: `scripts/extract/extract_foodb.py`, `extract_hmdb.py`, `extract_classyfire.py`, `extract_lotus.py`
- **Problema**: 1 timeout mata todo o extrator; sem retry de API instável
- **Impacto**: Taxa de sucesso < 80%; pesquisador tem que reexecutar manualmente

### 3. Sem visibilidade de perda de dados
- **Problema**: `transform_stg_xlsx.py` descarta ~1–5% das linhas silenciosamente
- **Impacto**: Pesquisador não sabe que projeto tem 5% menos features do que esperado

### 4. Logging não-estruturado
- **Problema**: Logs estão espalhados; impossível agrupar por batch_id
- **Impacto**: Debugging leva horas em vez de minutos

### 5. Porta 5432 exposta sem restrição
- **Arquivo**: `docker-compose.yml`
- **Problema**: `ports: ["5432:5432"]` expõe banco para toda a rede
- **Impacto**: Segurança em risco; acesso não-autorizado possível

---

## O Que Deve Ser Feito

### 1. Refatorar `load_stg_transformed.py` com COPY

```python
# scripts/load/load_stg_transformed.py — NOVO
import io
import psycopg

def bulk_insert_csv(
    conn: psycopg.Connection,
    df: pd.DataFrame,
    table: str,
    columns: list[str],
) -> int:
    """
    Insere DataFrame no banco usando COPY (10× mais rápido).
    
    Retorna número de linhas inseridas.
    """
    buffer = io.StringIO()
    df[columns].to_csv(
        buffer, 
        index=False, 
        header=False,
        sep="\t",
        na_rep="\\N",
        quoting=csv.QUOTE_MINIMAL,
    )
    buffer.seek(0)
    
    with conn.cursor() as cur:
        cur.copy_from(buffer, table, columns=columns, null="\\N")
    
    conn.commit()
    return len(df)
```

### 2. Criar `scripts/extract/http_client.py`

```python
"""Cliente HTTP unificado com retry, backoff, timeout."""
import time
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class HTTPClientWithRetry:
    """
    Cliente HTTP com retry automático, backoff exponencial e timeout.
    
    Uso:
        client = HTTPClientWithRetry(timeout=30, max_retries=3)
        response = client.get("https://api.example.com/data")
    """
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ):
        self.timeout = timeout
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response
    
    def post(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        response = self.session.post(url, **kwargs)
        response.raise_for_status()
        return response
    
    def close(self):
        self.session.close()
```

### 3. Criar `scripts/loggers/quality_reporter.py`

```python
"""Relatório de qualidade de dados por estágio do pipeline."""
from dataclasses import dataclass, asdict
from typing import Dict, List
import json
from datetime import datetime


@dataclass
class StageMetrics:
    stage: str           # "extract_pubchem", "transform_stg_xlsx", etc.
    rows_input: int
    rows_output: int
    rows_lost: int
    loss_reasons: Dict[str, int]  # {"missing_mz": 5, "invalid_formula": 2}
    duration_seconds: float
    timestamp: str


class QualityReporter:
    def __init__(self):
        self.stages: List[StageMetrics] = []
    
    def record_stage(
        self,
        stage: str,
        rows_input: int,
        rows_output: int,
        loss_reasons: Optional[Dict[str, int]] = None,
        duration: float = 0.0,
    ) -> None:
        """Registra métricas de uma etapa do pipeline."""
        loss_reasons = loss_reasons or {}
        rows_lost = rows_input - rows_output
        
        metrics = StageMetrics(
            stage=stage,
            rows_input=rows_input,
            rows_output=rows_output,
            rows_lost=rows_lost,
            loss_reasons=loss_reasons,
            duration_seconds=duration,
            timestamp=datetime.now().isoformat(),
        )
        
        self.stages.append(metrics)
    
    def to_json(self) -> str:
        """Retorna relatório em JSON."""
        return json.dumps(
            [asdict(s) for s in self.stages],
            indent=2,
            default=str,
        )
    
    def to_csv(self, filename: str) -> None:
        """Exporta relatório em CSV."""
        import csv
        with open(filename, "w") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "stage", "rows_input", "rows_output", "rows_lost",
                "loss_reasons", "duration_seconds", "timestamp"
            ])
            writer.writeheader()
            for metrics in self.stages:
                row = asdict(metrics)
                row["loss_reasons"] = json.dumps(row["loss_reasons"])
                writer.writerow(row)
    
    def summary(self) -> Dict:
        """Retorna resumo consolidado."""
        total_input = sum(s.rows_input for s in self.stages)
        total_output = sum(s.rows_output for s in self.stages)
        
        return {
            "total_rows_input": total_input,
            "total_rows_output": total_output,
            "total_rows_lost": total_input - total_output,
            "loss_percentage": 100 * (total_input - total_output) / total_input if total_input > 0 else 0,
            "stages_count": len(self.stages),
            "total_duration_seconds": sum(s.duration_seconds for s in self.stages),
        }
```

### 4. Padronizar logging estruturado

```python
# scripts/run/run_pipeline_frontend.py — adicionar ao início
import logging
import sys
from uuid import uuid4

# Logging estruturado com batch_id
batch_id = str(uuid4())[:8]
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s | {batch_id} | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

logger.info(f"Pipeline iniciado — batch_id={batch_id}")

# Em cada carregamento:
logger.info(f"Carregando dados em {table} — batch_id={batch_id}, rows={len(df)}")
```

### 5. Restringir porta 5432 em Docker

```yaml
# docker-compose.yml — ANTES:
services:
  postgres:
    ports:
      - "5432:5432"  # ❌ Exposto para toda a rede

# DEPOIS:
services:
  postgres:
    ports:
      - "127.0.0.1:5432:5432"  # ✓ Apenas localhost
    # Ou usar variável:
    # - "${EXPOSE_DB_PORT:-127.0.0.1}:5432:5432"
```

---

## Critérios de Aceite

| ID | Tarefa | Critério |
|---|---|---|
| S5-01 | COPY em staging | Tempo ≥ 10× menor (< 5 min para 50 K linhas) |
| S5-02 | COPY em Ranking de candidatos core | Redução mensurável vs baseline |
| S5-03 | Cliente HTTP | Todos os extratores usam `HTTPClientWithRetry`; timeout e retry funcionam |
| S5-04 | Quality reporter | `to_json()` outputs `rows_lost`, `loss_reasons` corretos |
| S5-05 | Logging estruturado | Logs contêm `timestamp`, `batch_id`, `stage`, `level` |
| S5-06 | Porta restrita | `nmap 127.0.0.1 5432` não mostra porta aberta |
| S5-07 | Runbook documentado | Documento descreve backup, restore, rollback |

---

## Lições Aprendidas (Antecipadas)

- COPY é ~10× mais rápido que INSERT row-by-row — troca fácil e dramática.
- Retry automático com backoff exponencial reduz taxa de falha de 20% para < 1%.
- Quality reporter deve ser obrigatório — pesquisador precisa saber o que foi perdido.

---

## Próximos Passos

- [ ] **Dia 1–2**: Refatorar `load_stg_transformed.py` com COPY; medir baseline → otimizado
- [ ] **Dia 3**: Refatorar `database_candidates.py` com COPY
- [ ] **Dia 4**: Criar `http_client.py`; integrar em `extract_pubchem.py` e `extract_chebi.py`
- [ ] **Dia 5**: Criar `quality_reporter.py`; integrar em transformações
- [ ] **Dia 6**: Padronizar logging; adicionar batch_id a todos os runners
- [ ] **Dia 7**: Testar restrição de porta; documentar runbook
- [ ] **Semana 2**: Validar performance em dataset de 500 K linhas

---

**Referência**: [AUDITORIA_E_QUADRO_SPRINT.md — Sprint 5](../AUDITORIA_E_QUADRO_SPRINT.md#sprint-5--performance-e-observabilidade)
