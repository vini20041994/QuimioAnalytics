# 🐳 INFRA - Pasta 04_INFRA

**DevOps e infrastructure em um único lugar.**

Esta pasta contém:
- 📖 Documentação de deployment
- 🐳 docker-compose.yml
- 🔧 Configurações de ambiente
- 🌐 Proxy reverso (nginx)

---

## 📚 Documentação Infra

### Stack Tecnológico
```
Containers: Docker + Docker Compose
Database: PostgreSQL 15+
Cache: Redis
Reverse Proxy: nginx
Orquestração: Docker Compose (dev)
```

### Serviços Inclusos

```
PostgreSQL
├─ Porta: 5432
├─ Dados: volume postgresql_data
└─ Backup: volume postgresql_backups

Redis
├─ Porta: 6379
├─ TTL: 24 horas

FastAPI Backend
├─ Porta: 8000
├─ Hot reload: ✅
└─ Docs: /docs

React Frontend
├─ Porta: 3000
├─ Hot reload: ✅
└─ Proxy: nginx

nginx (Reverse Proxy)
├─ Porta: 80
├─ Frontend: /
└─ Backend: /api/
```

---

## 📁 Arquivos

### docker-compose.yml
Orquestração de todos os serviços (dev)

### .env.example
Template de variáveis de ambiente

### nginx.conf
Configuração do reverse proxy

---

## ⚡ Uso Rápido

### 1. Setup Inicial
```bash
cp .env.example .env
docker-compose up -d
```

### 2. Verificar Serviços
```bash
docker-compose ps
# Deve mostrar 4 serviços rodando
```

### 3. Testar
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Frontend
open http://localhost:3000

# Database
psql -h localhost -U postgres -d quimioanalytics
```

### 4. Parar Tudo
```bash
docker-compose down
```

### 5. Limpar Volumes
```bash
docker-compose down -v
# Isso vai apagar dados do banco!
```

---

## 🔧 Configuração

### .env
```env
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=senha_segura
POSTGRES_DB=quimioanalytics
DATABASE_URL=postgresql://postgres:senha@postgres:5432/quimioanalytics

# API
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development

# Frontend
REACT_APP_API_URL=http://localhost:8000/api/v1

# Redis
REDIS_URL=redis://redis:6379/0
```

---

## 🚀 Deployment

### Desenvolvimento
```bash
docker-compose -f docker-compose.yml up -d
```

### Produção (simplificado)
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Monitoramento
```bash
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f postgres
```

---

## 🐛 Troubleshooting

### Porta já em uso
```bash
# Liberar porta
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### Banco não conecta
```bash
docker-compose down -v
docker-compose up -d postgres
# Aguarde 10 segundos
docker-compose up -d
```

### Rebuild sem cache
```bash
docker-compose build --no-cache
docker-compose up -d
```

---

## 📋 Checklist Infra

- [ ] Docker instalado
- [ ] Docker Compose instalado
- [ ] .env configurado
- [ ] docker-compose up funcionando
- [ ] Todos os 4 serviços running
- [ ] Health check passando
- [ ] Frontend acessível
- [ ] Backend acessível
- [ ] Database conectado
- [ ] Redis conectado
- [ ] Logs monitoráveis
- [ ] Backups configurados

---

## 🚀 Próximas Ações

1. Instale Docker e Docker Compose
2. Copie `.env.example` → `.env`
3. Configure as variáveis em `.env`
4. Execute `docker-compose up -d`
5. Teste `curl http://localhost:8000/api/v1/health`
6. Abra http://localhost:3000
7. Pronto para desenvolver!

---

**Toda a infraestrutura está pronta nesta pasta.**
