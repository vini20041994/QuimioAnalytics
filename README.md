
# QuimioAnalytics

Plataforma para integração, enriquecimento e análise de dados laboratoriais de metabolômica, com ranking automático de compostos candidatos e visualização simplificada.

---

## Visão Geral
Organize e enriqueça dados laboratoriais de forma automática, integrando bases públicas e gerando ranking dos compostos mais prováveis para cada amostra. Ideal para equipes científicas e técnicas que buscam agilidade, rastreabilidade e confiabilidade operacional.

## Principais Funcionalidades
- Integração de dados laboratoriais e públicos
- Ranking automático dos melhores candidatos por amostra
- Enriquecimento externo sob demanda com PubChem, ChEBI, ChemSpider e ClassyFire
- Dashboard e API para análise e consulta

No fluxo da interface:
- O upload executa ETL interno e ranking.
- A consulta a bases externas é disparada depois, pelo botão da fonte na tela de Ranking.

## Como Começar

### Usuários Linux ou WSL (Windows Subsystem for Linux)
Siga para a seção Plug and Play abaixo.

### Usuários Windows (sem WSL)
1. Instale o [WSL](https://learn.microsoft.com/pt-br/windows/wsl/install) (Subsistema Linux para Windows)
2. Abra o terminal Ubuntu (ou outra distribuição Linux) pelo menu iniciar
3. Siga as instruções para Linux normalmente dentro do WSL


## Plug and Play

Antes de rodar o Plug and Play, clone este repositório em sua máquina:

```sh
git clone https://github.com/SEU_USUARIO/QuimioAnalytics.git
cd QuimioAnalytics
```

O Plug and Play agora verifica e instala automaticamente o Docker e o Docker Compose em sistemas Linux. No Windows, basta garantir que o [Docker Desktop](https://www.docker.com/products/docker-desktop/) e o WSL estejam instalados.

Para rodar tudo automaticamente (inclusive dependências Python, banco, API e frontend):

```sh
chmod +x scripts/run/plug_and_play.sh
./scripts/run/plug_and_play.sh up
```

- Se o Docker não estiver instalado no Linux, o script fará a instalação e pedirá para reiniciar o terminal antes de rodar novamente.
- No Windows, instale manualmente o Docker Desktop e o WSL antes de rodar o script.
- Para parar ou ver logs, use:
  - `./scripts/run/plug_and_play.sh down`
  - `./scripts/run/plug_and_play.sh logs backend`

## Ranking de Candidatos

O sistema analisa os dados laboratoriais e gera automaticamente um ranking dos compostos mais prováveis para cada amostra, considerando critérios como massa, fragmentação e abundância. O resultado é salvo em um arquivo pronto para análise, facilitando a tomada de decisão com foco operacional.

Arquivo gerado: `data/staging/top_candidates.parquet`

## Execução Manual (opcional)
Para quem prefere instalar e rodar manualmente, siga as instruções detalhadas na documentação (`docs/`).

## Documentação e Suporte
Consulte a pasta `docs/` para guias completos e dúvidas frequentes.

---

Projeto acadêmico interno · SENAI Florianópolis · 2026
