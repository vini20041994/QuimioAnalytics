# Prompt — Auditoria Técnica, Científica e Avaliação Completa de Integridade do Projeto

Você atuará simultaneamente como:

- Arquiteto de Software Sênior;
- Engenheiro de Qualidade (QA);
- Especialista DevOps;
- Revisor de Código;
- Engenheiro de Dados;
- Especialista em Sistemas Científicos/Laboratoriais;
- Especialista em Governança e Integridade de Dados;
- Especialista em Segurança de Aplicações;
- Especialista em Arquitetura Escalável.

Sua missão é realizar uma AVALIAÇÃO COMPLETA, CRÍTICA E PROFUNDA do projeto fornecido pela equipe.

A análise deve avaliar:

- qualidade técnica;
- integridade científica;
- arquitetura;
- rastreabilidade;
- governança de dados;
- confiabilidade;
- segurança;
- performance;
- escalabilidade;
- estruturação do projeto;
- qualidade do código;
- integridade dos pipelines;
- maturidade de engenharia;
- aderência às boas práticas;
- capacidade de evolução futura.

O objetivo NÃO é apenas validar funcionamento.

O objetivo é determinar:

- se o sistema é tecnicamente sustentável;
- se é cientificamente confiável;
- se preserva integridade dos dados laboratoriais;
- se é auditável;
- se possui riscos ocultos;
- se pode evoluir para produção científica real.

---

# CONTEXTO DO PROJETO

A aplicação possui foco em:

- análise metabolômica;
- curadoria laboratorial;
- processamento de compostos químicos;
- enriquecimento molecular;
- pipelines ETL científicos;
- visualização científica;
- análise de abundância;
- integração com bases laboratoriais.

Os dados podem conter:

- Compound
- Compound ID
- Adducts
- Formula
- Score
- Fragmentation Score
- Mass Error (ppm)
- Isotope Similarity
- Neutral Mass
- m/z
- Retention Time
- abundâncias
- amostras
- rankings
- enriquecimentos.

O projeto pode utilizar:

- Python
- Pandas
- PostgreSQL
- Docker
- APIs científicas
- CSV
- Excel
- pipelines
- containers
- dashboards
- serviços REST.

Possíveis integrações:

- :contentReference[oaicite:0]{index=0}
- :contentReference[oaicite:1]{index=1}
- :contentReference[oaicite:2]{index=2}
- :contentReference[oaicite:3]{index=3}

---

# PREMISSAS CIENTÍFICAS OBRIGATÓRIAS

O sistema NÃO pode agir como ETL corporativo tradicional.

O domínio científico exige:

- preservação total dos dados;
- nenhuma exclusão silenciosa;
- nenhuma deduplicação automática;
- nenhuma transformação destrutiva;
- nenhuma substituição arbitrária de valores;
- rastreabilidade integral;
- manutenção dos dados RAW;
- preservação dos IDs originais;
- transparência total das transformações.

O sistema NÃO deve decidir automaticamente qual molécula é correta.

O sistema deve apenas:

- organizar;
- priorizar;
- ranquear;
- enriquecer;
- facilitar curadoria humana.

---

# OBJETIVO DA AVALIAÇÃO

Você deve:

1. auditar completamente o código;
2. validar integridade científica;
3. avaliar arquitetura;
4. avaliar segurança;
5. avaliar confiabilidade;
6. avaliar qualidade de engenharia;
7. detectar riscos futuros;
8. detectar gargalos;
9. detectar antipatterns;
10. detectar ETLs destrutivos;
11. detectar riscos de perda de rastreabilidade;
12. detectar problemas de governança;
13. avaliar maturidade do sistema;
14. sugerir refatorações;
15. sugerir arquitetura ideal;
16. sugerir melhorias escaláveis;
17. validar readiness para produção.

---

# 1. AVALIAÇÃO DA ARQUITETURA

Analise profundamente:

- modularização;
- separação de responsabilidades;
- acoplamento;
- coesão;
- reutilização;
- estrutura de diretórios;
- organização do projeto;
- responsabilidades das camadas;
- padrões arquiteturais;
- estrutura de serviços;
- pipelines;
- APIs;
- persistência;
- rastreabilidade.

Verifique aderência a:

- Clean Architecture
- SOLID
- DRY
- KISS
- Repository Pattern
- Service Layer
- DTOs
- PEP8
- princípios de escalabilidade.

Detecte:

- código duplicado;
- acoplamento excessivo;
- classes God Object;
- funções gigantes;
- responsabilidades misturadas;
- pipelines inseguros;
- lógica científica espalhada;
- dependências inadequadas.

---

# 2. AVALIAÇÃO DE INTEGRIDADE CIENTÍFICA

Verifique se o sistema:

- preserva dados RAW;
- mantém IDs originais;
- evita perda de informação;
- preserva empates científicos;
- mantém rastreabilidade;
- registra transformações;
- evita simplificações indevidas;
- evita decisões automáticas;
- evita ETL destrutivo;
- mantém consistência laboratorial.

Detecte:

- deduplicação automática;
- filtros destrutivos;
- normalizações perigosas;
- rankings inadequados;
- médias simplificadas;
- sobrescrita de dados;
- alterações irreversíveis.

---

# 3. AVALIAÇÃO DE CONFIABILIDADE

Gerar índice de confiabilidade de 0–100.

Critérios:

| Critério | Peso |
|---|---|
| Cobertura de testes | 20 |
| Tratamento de erros | 15 |
| Integridade científica | 15 |
| Segurança | 15 |
| Performance | 10 |
| Arquitetura | 10 |
| Legibilidade | 5 |
| Escalabilidade | 5 |
| Observabilidade | 5 |

Classificação:

- 0–39 → Crítico
- 40–59 → Baixo
- 60–79 → Moderado
- 80–100 → Confiável

Explicar detalhadamente cada nota.

---

# 4. AVALIAÇÃO DE SEGURANÇA

Verifique:

- credenciais expostas;
- variáveis sensíveis;
- chaves API;
- SQL Injection;
- Path Traversal;
- RCE;
- serialização insegura;
- subprocess inseguros;
- upload inseguro;
- permissões incorretas;
- falhas Docker;
- exposição de portas;
- falhas RBAC;
- ausência de logs;
- ausência de auditoria;
- vazamentos de memória;
- riscos de corrupção de dados.

Avalie:

- autenticação;
- autorização;
- governança;
- rastreabilidade.

---

# 5. AVALIAÇÃO DO BANCO DE DADOS

Avalie:

- modelagem;
- normalização;
- versionamento;
- integridade;
- índices;
- constraints;
- chaves;
- rastreabilidade;
- tabelas RAW;
- auditoria;
- escalabilidade.

Detecte:

- perda de rastreabilidade;
- sobrescrita destrutiva;
- ausência de auditoria;
- baixa performance;
- queries inadequadas.

---

# 6. AVALIAÇÃO DE ETL E PIPELINES

Verifique:

- ETL destrutivo;
- transformação irreversível;
- perda de linhas;
- perda de colunas;
- alteração de tipos;
- normalizações inadequadas;
- substituições arbitrárias;
- perda de metadados.

Avalie:

- rastreabilidade;
- reversibilidade;
- auditabilidade;
- segurança.

---

# 7. AVALIAÇÃO DE PERFORMANCE

Analise:

- loops desnecessários;
- DataFrames ineficientes;
- excesso de memória;
- gargalos;
- queries lentas;
- ausência de índices;
- repetição de processamento;
- falta de paginação;
- falta de cache;
- processamento serial inadequado.

Sugira:

- vetorização Pandas;
- lazy loading;
- async;
- batch processing;
- multiprocessing;
- parquet;
- cache;
- otimização SQL.

Explique ganhos esperados.

---

# 8. AVALIAÇÃO DE TESTES

Verifique existência e qualidade de:

## Testes Unitários

Validar:

- ETLs;
- parsing;
- cálculos;
- rankings;
- validators;
- persistência;
- enriquecimento.

---

## Testes de Integração

Validar:

- PostgreSQL;
- APIs;
- Docker;
- pipelines;
- persistência;
- dashboard;
- autenticação.

---

## Testes Científicos

Validar:

- mass error;
- isotope similarity;
- retention time;
- ranking;
- preservação de empates;
- consistência laboratorial.

---

## Testes de Rastreabilidade

Garantir:

- preservação RAW;
- auditoria;
- versionamento;
- reversibilidade.

---

# 9. AVALIAÇÃO DO DASHBOARD

Verifique se o dashboard é:

- científico;
- rastreável;
- explicável;
- interpretável.

Avalie:

- heatmaps;
- filtros;
- rankings;
- comparação molecular;
- abundância;
- visualização de empates;
- indicadores laboratoriais.

Detecte:

- simplificações excessivas;
- visualizações corporativas inadequadas;
- ausência de transparência.

---

# 10. AVALIAÇÃO DEVOPS

Analise:

- Dockerfile;
- docker-compose;
- persistência;
- volumes;
- logs;
- observabilidade;
- CI/CD;
- pipelines;
- healthcheck;
- versionamento;
- build;
- deploy;
- isolamento.

Avalie readiness para:

- Linux;
- Windows;
- containers;
- futura transformação em executável (.exe).

---

# 11. OBSERVABILIDADE E GOVERNANÇA

Verifique:

- logs estruturados;
- auditoria;
- tracing;
- métricas;
- monitoramento;
- rastreabilidade;
- histórico de alterações.

Detecte:

- ausência de logs;
- ausência de histórico;
- perda de rastreabilidade;
- alterações silenciosas.

---

# 12. PADRÕES DE CÓDIGO

Avalie:

- legibilidade;
- modularização;
- clareza;
- nomenclatura;
- separação de responsabilidades;
- robustez;
- tratamento de exceções;
- documentação;
- consistência.

---

# 13. QUALIDADE DOS DADOS

Verifique:

- consistência;
- schema;
- encoding;
- duplicidade lógica;
- colunas obrigatórias;
- integridade relacional;
- tipos incorretos;
- valores inválidos;
- dados ausentes.

---

# RESULTADO ESPERADO

Ao final da auditoria:

1. Identifique todos os riscos críticos.
2. Identifique problemas científicos.
3. Identifique problemas arquiteturais.
4. Identifique riscos de perda de integridade.
5. Gere índice de confiabilidade.
6. Sugira arquitetura ideal.
7. Sugira reorganização completa.
8. Gere exemplos de refatoração.
9. Gere exemplos de testes.
10. Sugira melhorias de segurança.
11. Sugira melhorias de performance.
12. Sugira melhorias DevOps.
13. Sugira governança científica.
14. Sugira estratégia de escalabilidade.
15. Gere roadmap evolutivo.
16. Gere backlog técnico prioritário.
17. Gere checklist de produção.
18. Gere checklist científico.
19. Gere checklist de rastreabilidade.
20. Gere checklist de segurança.

---

# FORMATO DA RESPOSTA

A resposta deve conter:

# 1. Resumo Executivo

- situação geral;
- maturidade;
- riscos críticos;
- nível de confiabilidade.

---

# 2. Problemas Críticos

Classificar:

- severidade;
- impacto;
- risco;
- prioridade.

---

# 3. Problemas Científicos

- ETL destrutivo;
- perda de rastreabilidade;
- rankings inadequados;
- inconsistências laboratoriais.

---

# 4. Problemas Arquiteturais

- acoplamento;
- duplicidade;
- baixa escalabilidade;
- ausência de modularização.

---

# 5. Índice de Confiabilidade

Tabela detalhada.

---

# 6. Refatorações Recomendadas

Mostrar exemplos práticos.

---

# 7. Arquitetura Recomendada

Mostrar estrutura modular ideal.

---

# 8. Melhorias de Banco

Explicar modelagem ideal.

---

# 9. Melhorias de Segurança

Listar vulnerabilidades e correções.

---

# 10. Melhorias de Performance

Explicar ganhos esperados.

---

# 11. Estratégia de Testes

Mostrar estrutura recomendada.

---

# 12. Estratégia DevOps

Mostrar pipeline ideal.

---

# 13. Estratégia de Governança Científica

Explicar auditoria e rastreabilidade.

---

# 14. Roadmap Evolutivo

Curto, médio e longo prazo.

---

# RESTRIÇÕES IMPORTANTES

NÃO aceitar:

- exclusão silenciosa;
- deduplicação automática;
- score simplificado;
- alteração destrutiva;
- perda de dados RAW;
- IA decidindo moléculas;
- simplificações científicas inadequadas.

O sistema deve ser:

- científico;
- auditável;
- transparente;
- explicável;
- rastreável;
- modular;
- escalável;
- centrado no pesquisador.