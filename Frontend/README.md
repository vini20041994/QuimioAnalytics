# QuimioAnalytics | Inteligência em Dados Químicos

[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

O **QuimioAnalytics** é uma plataforma analítica avançada desenvolvida para o **IST Ambiental**, focada no processamento e visualização de dados provenientes de pipelines ETL de espectrometria de massa. O sistema integra resultados complexos de identificação química em uma interface intuitiva para suporte à tomada de decisão.


<br><br>
##  Visão Geral da Solução

O sistema atua na camada de apresentação (Frontend) de um ecossistema ETL, permitindo que pesquisadores e analistas interajam com dados de identificação de compostos, verifiquem probabilidades analíticas e gerenciem o fluxo de dados brutos para processamento.

### Principais Módulos:
- **Core Dashboard:** Métricas de performance de identificação e distribuição de fontes.
- **Top 5 Ranking Engine:** Visualização hierárquica de candidatos moleculares com filtros dinâmicos.
- **ETL Management (Upload):** Interface para ingestão de datasets de Abundância e Identificação.
- **Chemical Knowledge Base:** Consultas rápidas a referências integradas (PubChem, ChEBI, ChemSpider).


<br><br>
##  Stack Tecnológica

### Frontend & Core
- **React 18:** Com hooks customizados para gerenciamento de estado.
- **Vite:** Ferramenta de build de próxima geração para performance superior.
- **React Router DOM:** Gestão de roteamento Single Page Application (SPA).

### Visualização de Dados & UI
- **Recharts:** Renderização de gráficos vetoriais (SVG) responsivos.
- **Lucide React:** Conjunto de ícones consistentes para interfaces técnicas.
- **CSS3 Variables:** Arquitetura de estilos baseada em design tokens (Paleta IST Ambiental).


<br><br>
##  Design System (Tokens de Cor)

A interface utiliza um tema **Dark Mode** de alto contraste, otimizado para longos períodos de análise laboratorial:

| Categoria | Hex Code | Aplicação |
| :--- | :--- | :--- |
| **Accent Primary** | `#04BDA2` | Sucesso, Químicos identificados, botões principais. |
| **Primary Blue** | `#016FE1` | Identidade visual, Links, Informações neutras. |
| **Alert Red** | `#BD0404` | Erros de massa críticos, Falhas de processamento. |
| **Surface Dark** | `#0D0D0D` | Fundo principal da aplicação. |
| **Surface Elevated**| `#191919` | Cards, modais e containers de tabelas. |


<br><br>
##  Instalação e Execução

### Pré-requisitos
- Node.js (v18 ou superior)
- Gerenciador de pacotes (npm ou yarn)

### Passo a Passo

1.  **Clonar o repositório:**
    ```bash
    git clone [https://github.com/GuiZamb32/fron_test.git](https://github.com/GuiZamb32/fron_test.git)
    ```

2.  **Instalar dependências:**
    ```bash
    npm install
    ```

3.  **Ambiente de Desenvolvimento:**
    ```bash
    npm run dev
    ```

4.  **Compilação de Produção:**
    ```bash
    npm run build
    ```


<br><br>
##  Arquitetura de Diretórios

```text
src/
├── components/          # Componentes globais reutilizáveis
│   ├── Navbar.jsx       # Navegação principal
│   └── Navbar.css       # Estilização modular da Navbar
├── pages/               # Views principais da aplicação
│   ├── ChemicalRef.jsx  # Base de dados químicos
│   ├── ChemicalRef.css  # Estilos da Base de dados
│   ├── Dashboard.jsx    # Analytics e Gráficos Recharts
│   ├── Dashboard.css    # Estilos do Dashboard e Grids
│   ├── Top5Ranking.jsx  # Tabelas de probabilidade
│   ├── Top5Ranking.css  # Estilos do Ranking e Badges
│   ├── Upload.jsx       # Gestão de arquivos e ETL
│   └── Upload.css       # Estilos da área de dropzone
├── App.jsx              # Configuração de rotas (React Router)
├── App.css              # Estilos globais de layout e containers
├── index.css            # Design Tokens (Variáveis de cores e fontes)
└── main.jsx             # Ponto de entrada da aplicação
