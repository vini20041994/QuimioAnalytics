# 🎨 FRONTEND - Pasta 02_FRONTEND

**Tudo sobre frontend em um único lugar.**

Esta pasta contém:
- 📖 Documentação específica do frontend
- 💻 Boilerplate React pronto para copiar
- 📝 Exemplos de componentes
- ✅ Checklist de implementação frontend

---

## 📚 Documentação Frontend

### Referência Rápida
```
Tecnologia: React 18+
State Management: Redux
HTTP Client: Axios
Styling: CSS/Tailwind
Testing: Jest + React Testing Library
```

### Arquitetura Frontend

```
src/
├── components/        # Componentes React
├── pages/            # Páginas
├── services/         # API calls (Axios)
├── store/            # Redux store
├── hooks/            # Custom hooks
├── utils/            # Utilitários
└── App.jsx          # App principal
```

---

## 💻 Boilerplate

Copie de `boilerplate/` para seu projeto:

```bash
cp -r boilerplate/* ~/seu_projeto/frontend/
cd ~/seu_projeto/frontend
npm install
npm start
```

### O que está incluído:

✅ React 18+ setup  
✅ Redux para state management  
✅ Axios com interceptors  
✅ Components exemplo (Batches, Top5, etc)  
✅ Services API prontos  
✅ Docker Compose integração  
✅ Tests básicos  

---

## 🔗 Como Integrar com Backend

1. **API URL:** Configure em `services/api.js` ou `.env`
   ```javascript
   const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1'
   ```

2. **Endpoints:** Consulte `services/api.js`
   ```javascript
   - getBatches()
   - getFeatures(batchId)
   - getTop5Candidates(featureId)
   - postFeature(data)
   ```

3. **Redux Store:** Use `store/batchSlice.js`
   ```javascript
   - setCurrentBatch()
   - addFeature()
   - loadCandidates()
   ```

4. **Componentes:** Use `components/`
   ```javascript
   - <BatchesPage /> - Lista de batches
   - <Top5Page /> - Top 5 candidates
   - <FeatureForm /> - Adicionar feature
   ```

---

## 🧪 Testando

```bash
# Teste local
npm start

# Teste com backend
docker-compose up -d
npm start
# Acesse: http://localhost:3000

# Teste dos endpoints
npm test
```

---

## 📋 Checklist Frontend

- [ ] Copiar boilerplate
- [ ] Instalar dependências (`npm install`)
- [ ] Configurar API URL (.env)
- [ ] Testar localmente (`npm start`)
- [ ] Testar com backend (docker-compose)
- [ ] Implementar components customizados
- [ ] Adicionar validações
- [ ] Testar endpoints (curl ou Postman)
- [ ] Build para produção (`npm run build`)
- [ ] Deploy

---

## 🚀 Próximas Ações

1. Leia documentação geral em `01_DOCS/`
2. Copie `boilerplate/` para seu projeto
3. Configure backend URL em `.env`
4. Execute `npm install && npm start`
5. Teste endpoints com curl/Postman
6. Comece a customizar!

---

**Tudo que você precisa para frontend está aqui nesta pasta.**
