# Setup do Banco de Dados - QuimioAnalytics

## 📋 Pré-requisitos

- Docker e Docker Compose v2 instalados (comando `docker compose`)
- Python 3.8+ (para scripts de gerenciamento)
- DBeaver ou outro cliente PostgreSQL (opcional)

### Instalação do Docker (Ubuntu/Debian)

```bash
# Atualizar repositórios
sudo apt update

# Instalar Docker
sudo apt install docker.io docker-compose -y

# Adicionar usuário ao grupo docker (para não precisar de sudo)
sudo usermod -aG docker $USER

# Relogar ou executar:
newgrp docker
```

## 🚀 Início Rápido

### 1. Iniciar o Banco de Dados

```bash
# Opção 1: Usar o script Python (recomendado)
python3 scripts/manage_db.py start

# Opção 2: Usar docker compose diretamente
docker compose up -d
```

### 2. Criar Schemas e Tabelas

```bash
python3 scripts/manage_db.py init-schema
```

### 3. Verificar Status

```bash
python3 scripts/manage_db.py status
```

## 🔧 Comandos Disponíveis

```bash
# Gerenciamento do Container
python3 scripts/manage_db.py start        # Inicia o banco
python3 scripts/manage_db.py stop         # Para o banco
python3 scripts/manage_db.py restart      # Reinicia o banco
python3 scripts/manage_db.py status       # Status do container

# Operações no Banco
python3 scripts/manage_db.py init-schema  # Cria schemas e tabelas
python3 scripts/manage_db.py psql         # Shell interativo
python3 scripts/manage_db.py logs         # Ver logs (Ctrl+C para sair)

# Manutenção
python3 scripts/manage_db.py clean        # Remove tudo (⚠️ apaga dados!)
```

## 🔌 Conexão no DBeaver

### Passo 1: Nova Conexão
1. Abra o DBeaver
2. Clique em **Database** → **New Database Connection**
3. Selecione **PostgreSQL**

### Passo 2: Configurar Conexão

```
Host:     localhost
Port:     5432
Database: quimioanalytics
User:     quimio_user
Password: quimio_pass_2024
```

### Passo 3: Testar e Conectar
1. Clique em **Test Connection**
2. Se necessário, baixe o driver PostgreSQL (DBeaver faz automaticamente)
3. Clique em **Finish**

### Passo 4: Explorar Schemas

Após conectar, você verá três schemas:
- **core**: Tabelas principais (features, measurements, batches)
- **stg**: Staging/dados brutos importados
- **ref**: Dados de referência (bibliotecas externas)

## 🗄️ Estrutura do Banco de Dados

```
quimioanalytics/
├── core.*              # Schema principal
│   ├── ingestion_batch
│   ├── feature
│   ├── sample_group
│   ├── replicate
│   ├── abundance_measurement
│   └── candidate_identification
│
├── stg.*               # Schema de staging
│   ├── identification_row
│   ├── abundance_row
│   ├── curated_catalog_row
│   ├── pubchem_compound_raw
│   ├── chebi_compound_raw
│   ├── hmdb_compound_raw
│   ├── foodb_compound_raw
│   ├── classyfire_compound_raw
│   ├── chemspider_compound_raw
│   └── lotus_compound_raw
│
└── ref.*               # Schema de referência
    ├── external_source
    ├── external_compound
    ├── external_identifier
    ├── compound_property
    ├── taxonomy_node
    ├── compound_taxonomy
    └── chemical_class
```

## 🐍 Uso em Scripts Python

### Exemplo com psycopg2

```python
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='quimioanalytics',
    user='quimio_user',
    password='quimio_pass_2024'
)

# Exemplo de consulta
with conn.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute("SELECT * FROM core.ingestion_batch LIMIT 10")
    batches = cur.fetchall()
    for batch in batches:
        print(batch)

conn.close()
```

### Exemplo com SQLAlchemy

```python
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://quimio_user:quimio_pass_2024@localhost:5432/quimioanalytics"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM core.ingestion_batch"))
    for row in result:
        print(row)
```

## 🔍 Consultas Úteis

```sql
-- Listar todos os schemas
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name IN ('core', 'stg', 'ref');

-- Listar todas as tabelas de um schema
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'core';

-- Ver estrutura de uma tabela
\d core.feature

-- Contar registros em todas as tabelas do core
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
WHERE schemaname = 'core'
ORDER BY n_live_tup DESC;
```

## 🛠️ Troubleshooting

### Porta 5432 já está em uso

```bash
# Verificar o que está usando a porta
sudo lsof -i :5432

# Parar PostgreSQL local (se houver)
sudo systemctl stop postgresql

# Tentar novamente
python3 scripts/manage_db.py start

# Ou usar outra porta no docker-compose.yml
ports:
  - "5433:5432"  # Mapeia para 5433 no host
```

### Container não inicia

```bash
# Ver logs detalhados
docker logs quimio_postgres

# Remover e recriar
python3 scripts/manage_db.py clean
python3 scripts/manage_db.py start
```

### Erro de permissão ao executar Docker

```bash
# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Relogar ou executar
newgrp docker
```

### Schema não foi criado

```bash
# Executar manualmente
docker exec -i quimio_postgres psql -U quimio_user -d quimioanalytics < database/schema_postgresql_mvp_entrega2.sql

# Ou usar o script
python3 scripts/manage_db.py init-schema
```

## 🔐 Segurança

⚠️ **IMPORTANTE**: As credenciais padrão são para desenvolvimento local!

Para produção:
1. Altere as senhas no `docker-compose.yml`
2. Use variáveis de ambiente
3. Não commite credenciais no Git
4. Configure backup regular

## 📊 Backup e Restore

### Backup

```bash
# Backup completo
docker exec quimio_postgres pg_dump -U quimio_user quimioanalytics > backup_$(date +%Y%m%d).sql

# Backup compactado
docker exec quimio_postgres pg_dump -U quimio_user quimioanalytics | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore

```bash
# Restore
docker exec -i quimio_postgres psql -U quimio_user quimioanalytics < backup_20260426.sql

# Restore de arquivo compactado
gunzip -c backup_20260426.sql.gz | docker exec -i quimio_postgres psql -U quimio_user quimioanalytics
```

## 📚 Recursos Adicionais

- [Documentação PostgreSQL 15](https://www.postgresql.org/docs/15/)
- [DBeaver Documentation](https://dbeaver.io/docs/)
- [Docker Compose](https://docs.docker.com/compose/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verifique os logs: `python scripts/manage_db.py logs`
2. Consulte este documento
3. Entre em contato com a equipe QuimioAnalytics
