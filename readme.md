# AJUSTA – Data Hub

> Sistema digital de cadastro, visualização e análise de dados psico-socioeconômicos dos beneficiários do [Instituto Antônio Justa](https://www.instagram.com/institutoantoniojusta/).

[![Streamlit](https://img.shields.io/badge/Streamlit-1.50-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Google Sheets](https://img.shields.io/badge/Backend-Google%20Sheets-34A853?logo=googlesheets&logoColor=white)](https://sheets.google.com)

---

## Visão Geral

O AJUSTA Data Hub substitui formulários em papel por um sistema digital centralizado para o Instituto Antônio Justa, organização que atende pacientes de hanseníase e seus familiares no bairro Antônio Justa, em Maracanaú-CE. O sistema permite registrar, consultar e analisar dados psico-socioeconômicos dos beneficiários, bem como estimar o risco clínico de cada indivíduo por meio de um modelo de Machine Learning treinado em dados públicos do SINAN.

---

## Funcionalidades

| Módulo | Descrição |
|---|---|
| **Dashboard** | KPIs e gráficos interativos com filtros por projeto, bairro, gênero, tipo de moradia e status de hanseníase |
| **Beneficiários** | Busca por nome ou CPF, visualização detalhada e edição de registros |
| **Novo Cadastro** | Formulário completo de registro (dados pessoais, residenciais, familiares, histórico clínico e projetos) |
| **Projetos** | CRUD de projetos institucionais com contagem de beneficiários vinculados |
| **Vulnerabilidades** | Ranking de risco clínico baseado em ML (RandomForest treinado no SINAN) |
| **Administração** | Painel de gerenciamento de usuários e configurações |

---

## Stack Técnica

- **Framework:** Streamlit 1.50
- **Backend de dados:** Google Sheets via `streamlit-gsheets`
- **Autenticação:** Google OAuth (nativo do Streamlit) + whitelist de e-mails
- **Visualizações:** Plotly 6 + Altair 5
- **Machine Learning:** scikit-learn 1.6 (RandomForestClassifier)
- **Dados:** Pandas 2 + DuckDB + PyArrow

---

## Arquitetura

```
┌─────────────────────────────────────────┐
│              Streamlit App              │
│  app.py + pages/ (multipage)            │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────────┐
│ Google OAuth│  │  Google Sheets  │
│ (auth)      │  │  (dados)        │
└─────────────┘  └─────────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    ┌────▼────┐   ┌─────▼────┐  ┌─────▼──────────┐
    │  Dados  │   │ Projetos │  │ Autenticação   │
    │(cadastro│   │(projetos │  │(whitelist de   │
    │  geral) │   │ativos)   │  │ e-mails)       │
    └─────────┘   └──────────┘  └────────────────┘
```

### Fluxo de dados

- Leituras: `utils/data.py` → `load_sheet_data(worksheet)` com cache de 5 minutos (`@st.cache_data(ttl=300)`)
- Escritas: `update_sheet_data` / `overwrite_sheet_data` seguidas obrigatoriamente de `refresh_after_sheet_mutation()` para invalidar cache e acionar `st.rerun()`

---

## Estrutura do Projeto

```
AJUSTA-datahub/
├── app.py                        # Home: saudação e navegação rápida
├── requirements.txt
├── readme.md
├── pages/
│   ├── 1_Dashboard.py            # Gráficos agregados com filtros
│   ├── 2_Beneficiarios.py        # Busca e visualização individual
│   ├── 3_Novo_Cadastro.py        # Formulário de cadastro
│   ├── 4_Administração.py        # Painel admin
│   ├── 5_Projetos.py             # Gestão de projetos (CRUD)
│   ├── 6_Vulnerabilidades.py     # Ranking de risco clínico (ML)
│   └── 7_Sobre.py                # Sobre o sistema
├── utils/
│   ├── auth.py                   # Google OAuth + whitelist
│   ├── data.py                   # I/O Google Sheets com cache
│   ├── dashboard_data.py         # Preparação de dados para gráficos
│   ├── colors.py                 # Paleta AJUSTA e estilos Plotly
│   ├── risco_clinico.py          # Wrapper do modelo de ML
│   └── beneficiario_view.py      # Helpers de exibição de beneficiário
├── ml_models/
│   └── modelo_risco_clinico_v2.pkl  # Pipeline scikit-learn (SINAN/CE)
├── data/                         # Dados de exemplo e dicionários
└── .streamlit/
    ├── config.toml               # Tema e configurações do Streamlit
    └── secrets.toml              # Credenciais (git-ignorado)
```

---

## Modelo de Risco Clínico

O módulo **Vulnerabilidades** utiliza um `RandomForestClassifier` treinado em dados públicos do SINAN (Sistema de Informação de Agravos de Notificação) do Ceará para estimar a probabilidade de deficiência física.

**Variáveis de entrada (formato SINAN):**

| Variável | Descrição |
|---|---|
| `NU_IDADE_N` | Idade |
| `CS_SEXO` | Sexo |
| `CS_RACA` | Raça/cor |
| `CS_ESCOL_N` | Escolaridade |
| `NU_LESOES` | Número de lesões |
| `NERVOSAFET` | Nervos afetados |
| `CLASSOPERA` | Classificação operacional |
| `FORMACLINI` | Forma clínica |

**Thresholds de risco:**

| Score | Classificação |
|---|---|
| < 0.3 | Baixo |
| 0.3 – 0.7 | Médio |
| ≥ 0.7 | Alto |

O mapeamento dos valores do formulário AJUSTA para códigos SINAN é feito automaticamente em `utils/risco_clinico.py`. O modelo **não** foi treinado em dados do AJUSTA.

---

## Convenções de Desenvolvimento

- **Autenticação obrigatória:** toda página deve chamar `auth.check_auth()` antes de renderizar qualquer conteúdo.
- **Projetos multi-valorados:** a coluna `projeto_acao` é separada por vírgulas. Use sempre `split_projetos_celula()` / `explode_projetos_series()` de `dashboard_data.py` — nunca faça split manual.
- **Valor nulo:** use `LABEL_NULO = "Não informado"` como sentinel em DataFrames exibíveis. A cor fixa é `COR_NAO_INFORMADO = '#6c757d'`.
- **Estilos:** use `utils/colors.py` (`AJUSTA_COLORS`, `AJUSTA_PALETTE`, `apply_plotly_style()`, `discrete_color_map()`) para todos os gráficos Plotly.
- **Nomenclatura de páginas:** `N_Title.py` — o número controla a ordem na sidebar.
- **Tipos Arrow:** se adicionar nova coluna de texto na sheet `Dados`, inclua-a em `_DADOS_COERCE_TO_STRING` em `utils/data.py`.

---

## Licença

Projeto interno do [Instituto Antônio Justa](https://www.instagram.com/institutoantoniojusta/). Uso restrito.
