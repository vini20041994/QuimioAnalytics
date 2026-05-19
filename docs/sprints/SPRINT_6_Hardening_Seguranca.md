# Sprint 6 — Hardening de Segurança

**Status**: 🔴 Todo  
**Capacidade**: 16 pontos  
**Objetivo**: Eliminar vetores de ataque identificados e preparar o projeto para ambiente de produção seguro.

---

## Contexto

O projeto tem vulnerabilidades que, embora ainda em desenvolvimento, devem ser eliminadas antes de qualquer produção:
- Credenciais em variáveis de ambiente (visíveis em `ps aux`)
- Path traversal possível em leitura de arquivo de usuário
- Serialização JSON insegura
- Controle de acesso ao banco sem roles granulares
- Porta de banco exposta (parcialmente resolvida em Sprint 5)

Sprint 6 implementa hardening defensivo para proteger dados e infraestrutura.

---

## Principais Pontos Levantados

### 1. PGPASSWORD exposto em variáveis de ambiente
- **Arquivo**: `scripts/config.py`, variáveis do container
- **Problema**: `ps aux` mostra `PGPASSWORD=senha123` para qualquer processo no mesmo host
- **Impacto**: Segurança crítica — qualquer usuário local consegue colar senha do banco

```bash
# ANTES — ❌ Inseguro:
export PGPASSWORD="minha_senha"
psql -h localhost -U user -d database
# $ ps aux | grep psql
# user      1234  0.5  0.1 ... PGPASSWORD=minha_senha psql ...
```

### 2. Path traversal em leitura de arquivo de usuário
- **Arquivo**: `scripts/run/run_etl_user_input.py`
- **Problema**: Sem validação, usuário poderia passar `../../etc/passwd`
- **Impacto**: Leitura de arquivos sensíveis do sistema

```python
# ANTES — ❌ Vulnerável:
file_path = request.args.get("file")  # Usuário passa "../../etc/passwd"
with open(file_path) as f:
    data = f.read()
```

### 3. Serialização JSON insegura
- **Arquivo**: `scripts/load/load_stg_transformed.py`
- **Problema**: `to_json()` pode falhar com tipos especiais; falta `default=str`
- **Impacto**: Falha silenciosa ou corrupção de JSONB no banco

### 4. Sem roles granulares no banco
- **Problema**: Todo loader usa credenciais de super-user
- **Impacto**: Se uma conta é comprometida, acesso é total — sem segmentação

### 5. Sem logs de acesso ao banco
- **Problema**: Impossível auditar quem acessou o quê
- **Impacto**: Compliance impossível; detecção de invasão tardia

---

## O Que Deve Ser Feito

### 1. Remover PGPASSWORD — Usar `.pgpass`

```bash
# ANTES — ❌ Inseguro:
export PGPASSWORD="minha_senha"
psql -h localhost -U quimio_etl -d quimio_analytics

# DEPOIS — ✓ Seguro:
# Criar ~/.pgpass (modo 600):
# localhost:5432:quimio_analytics:quimio_etl:minha_senha
chmod 600 ~/.pgpass
psql -h localhost -U quimio_etl -d quimio_analytics
# Sem PGPASSWORD exposto em ps aux
```

Alternativamente, usar `libpq service file`:

```ini
# ~/.pg_service.conf
[quimio_prod]
host=localhost
port=5432
dbname=quimio_analytics
user=quimio_etl
password=minha_senha

# Conexão:
psql service=quimio_prod
```

**Código em Python**:

```python
# scripts/config.py
import os
from pathlib import Path

class DatabaseConfig:
    @staticmethod
    def get_connection_string():
        # NÃO ler PGPASSWORD
        # Usar .pgpass ou service file
        return f"postgresql://{os.getenv('PGUSER', 'quimio_etl')}@localhost/quimio_analytics"
        # psycopg conectará usando .pgpass automaticamente
```

### 2. Validar path — Prevenir traversal

```python
# scripts/run/run_etl_user_input.py
import os
from pathlib import Path

def validate_input_file(file_path: str) -> Path:
    """
    Valida que o arquivo está dentro de RAW_INPUTS_DIR.
    Previne path traversal.
    """
    base_dir = Path(os.getenv("RAW_INPUTS_DIR", "./data/raw_inputs")).resolve()
    target_path = (base_dir / file_path).resolve()
    
    # Garante que target está dentro de base
    if not str(target_path).startswith(str(base_dir)):
        raise ValueError(f"Path fora de {base_dir}: {file_path}")
    
    if not target_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {target_path}")
    
    return target_path

# Uso:
try:
    user_file = request.args.get("file")
    safe_path = validate_input_file(user_file)
    df = pd.read_csv(safe_path)
except ValueError as e:
    logger.error(f"Tentativa de path traversal: {e}")
    return {"error": "Arquivo inválido"}, 403
```

### 3. Serialização JSON segura

```python
# scripts/load/load_stg_transformed.py
import json

def serialize_to_jsonb(obj):
    """Serializa objeto para JSONB seguro."""
    return json.dumps(obj, default=str, ensure_ascii=False)

# Uso em DataFrame → JSON:
df["metadata"] = df["metadata"].apply(serialize_to_jsonb)

# Insérir em JSONB:
cur.execute(
    "INSERT INTO stg.row (metadata) VALUES (%s)",
    (serialize_to_jsonb({"chave": "valor"}),),
)
```

### 4. Criar roles granulares no banco

```sql
-- database/schema_postgresql_mvp_entrega2.sql
-- Roles de acesso mínimo

-- Role apenas para LEITURA (analista)
CREATE ROLE quimio_analyst WITH LOGIN PASSWORD 'analyst_pass';
GRANT CONNECT ON DATABASE quimio_analytics TO quimio_analyst;
GRANT USAGE ON SCHEMA core, ref TO quimio_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA core, ref TO quimio_analyst;

-- Role para ETL (extrator + loader)
CREATE ROLE quimio_etl WITH LOGIN PASSWORD 'etl_pass';
GRANT CONNECT ON DATABASE quimio_analytics TO quimio_etl;
GRANT ALL PRIVILEGES ON SCHEMA stg TO quimio_etl;
GRANT USAGE ON SCHEMA core, ref TO quimio_etl;
GRANT SELECT ON TABLE ref.* TO quimio_etl;
GRANT INSERT, UPDATE ON TABLE core.* TO quimio_etl;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA core TO quimio_etl;

-- Role para administrador (poucos)
CREATE ROLE quimio_admin WITH LOGIN PASSWORD 'admin_pass';
GRANT quimio_admin TO postgres;  -- superuser delegado
```

**Configurar loaders para usar role correto**:

```python
# scripts/load/load_pubchem.py
conn = psycopg.connect(
    host="localhost",
    user="quimio_etl",      # ← Role com permissão mínima
    password=get_password_from_pgpass(),
    dbname="quimio_analytics",
)
```

### 5. Habilitar audit log no PostgreSQL

```ini
# postgresql.conf
log_statement = 'all'
log_connections = on
log_disconnections = on
log_duration = on
log_statement_sample_rate = 0.1
log_min_duration_statement = 1000  # log queries > 1s
```

---

## Critérios de Aceite

| ID | Tarefa | Critério |
|---|---|---|
| S6-01 | Remover PGPASSWORD | Arquivo `.pgpass` criado; `ps aux` não mostra senha |
| S6-02 | Validar path de entrada | Tentativa de `../../etc/passwd` lança erro 403 |
| S6-03 | JSON seguro | `json.dumps(..., default=str)` usado em todas as serializações |
| S6-04 | Roles granulares | 3 roles criadas (analyst, etl, admin) com permissões restritas |
| S6-05 | Porta restrita | `nmap 127.0.0.1 5432` não mostra porta; `nmap <external_ip> 5432` também não |
| S6-06 | Audit log | PostgreSQL log contém `log_statement = 'all'` e conexões registradas |

---

## Lições Aprendidas (Antecipadas)

- Credenciais nunca devem ir em variáveis de ambiente — sempre `.pgpass` ou vault.
- Path traversal é fácil de esquecer — validar SEMPRE com `.resolve()` e `startswith()`.
- Roles granulares não são só compliance — protegem contra compromisso de conta.

---

## Próximos Passos

- [ ] **Dia 1**: Criar `.pgpass` e testar conexão sem PGPASSWORD
- [ ] **Dia 2**: Implementar `validate_input_file()` em `run_etl_user_input.py`
- [ ] **Dia 3**: Refatorar serializações JSON com `default=str`
- [ ] **Dia 4**: Criar roles no banco; testar permissões
- [ ] **Dia 5**: Habilitar audit log no PostgreSQL
- [ ] **Dia 6**: Testes de segurança — tentar path traversal, ler PGPASSWORD, etc.
- [ ] **Dia 7**: Documentar procedimento de credenciais seguras

---

**Referência**: [AUDITORIA_E_QUADRO_SPRINT.md — Sprint 6](../AUDITORIA_E_QUADRO_SPRINT.md#sprint-6--hardening-de-segurança)
