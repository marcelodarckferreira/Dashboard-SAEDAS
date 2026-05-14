# Arquitetura do Sistema SAEDAS

Organização modular, responsabilidades dos módulos e governança de código.

---

## Relação com PRD/SPEC

- Este arquivo define arquitetura e contratos estruturais de nível sistema (transversal).
- PRDs (`docs/superpowers/prd/`) definem problema, objetivo, escopo e critérios de sucesso por iniciativa.
- SPECs (`docs/superpowers/specs/`) detalham a implementação técnica de cada iniciativa.
- Regra de governança: mudanças locais nascem em PRD/SPEC; quando viram padrão global, são consolidadas aqui.

---

## 1. Estrutura de Pastas

```text
app/
├── app.py                    # Ponto de entrada, roteamento e configuração global
├── app_pages/                # Uma função page_*() por módulo funcional
│   ├── home.py               # Visão geral — usa AgGrid para tabela principal
│   ├── consulta.py           # Encaminhamentos
│   ├── exame.py              # Exames
│   ├── vacinacao.py          # Vacinação
│   ├── nutricao.py           # Nutrição
│   ├── medico.py             # Atendimentos médicos
│   └── aluno.py              # Perfil individual do aluno (deep-link)
├── components/               # Componentes reutilizáveis de UI
│   ├── sidebar_filters.py    # Filtros configuráveis da sidebar
│   └── footer_personal.py    # Rodapé fixo da prefeitura
├── utils/                    # Camada de lógica — nunca importar entre pages diretamente
│   ├── styles.py             # Motor de design: SAEDAS_PALETTE, apply_saedas_design
│   ├── page_helpers.py       # Funções de agregação, tabelas e gráficos
│   ├── state_manager.py      # Sincronização bidirecional e estados globais
│   ├── data_loader.py        # Carregamento e validação de CSVs
│   └── schemas.py            # Schemas esperados de cada dataset
├── data/                     # Datasets CSV (não versionados)
└── assets/
    ├── styles.css            # Design System global (tokens CSS, regras de tabela)
    ├── logo-pcni.png         # Logo na sidebar
    └── favicon.ico
```

---

## 2. Responsabilidades dos Módulos

### `app.py`

- Configura `st.set_page_config` (deve ser a primeira chamada Streamlit).
- Chama `init_global_state()` antes de qualquer renderização.
- Processa parâmetros de URL (`?menu=`, `?aluno=`, `?nasc=`) para deep-linking.
- Renderiza a sidebar com o menu de navegação (`streamlit_option_menu`).
- Roteia para a `page_*()` correspondente ao item selecionado.

### `app_pages/home.py`

- Centraliza as tabelas `AgGrid` da Home (seleção URG, seleção Escola, comparativo geral e detalhamento).
- Define o padrão de ações por tabela no topo direito com botões agrupados.
- Para tabelas de seleção, implementa sincronismo bidirecional com a sidebar (estado global + parâmetros de filtro).
- Ordem padrão dos botões:
  - com seletor de colunas: `⚙️ Colunas` → `📋 Copiar` → `⬇️ CSV`
  - sem seletor de colunas: `📋 Copiar` → `⬇️ CSV`
- Exportação CSV deve usar separador `;` e encoding `utf-8-sig`.

### `utils/styles.py`

- **`SAEDAS_PALETTE`** — dicionário com valores hex para light/dark. Fonte de verdade Python para cores de dataframe (linha ativa). Deve estar em sincronia com `styles.css`.
- **`apply_global_css()`** — injeta `styles.css` via `st.markdown`. Chamada no início de cada `page_*()`.
- **`apply_saedas_design(styler, categoria_col, active_items)`** — estiliza qualquer Pandas Styler com header, footer (Pro Footer) e linha ativa. Retorna um Styler pronto para `st.dataframe`.
- **`render_metric_cards(metrics, is_toggle, active_labels, on_click_callback, fixed_columns)`** — renderiza KPI cards estáticos ou interativos (toggle) no padrão global de grid com 5 colunas por linha (com quebra automática em novas linhas quando necessário).

### `utils/page_helpers.py`

- **`build_comparativo_anual(df, categoria_col, value_col, active_row_value)`** — agrega dados por ano e categoria, gera MultiIndex com colunas de Qtd / % Total / Var%, insere linha TOTAL e aplica `apply_saedas_design`. Retorna um Pandas Styler pronto.
- **`filter_by_sidebar_selections(df, selections)`** — aplica filtros de ano, URG, escola e tipo a um DataFrame.
- **`render_grouped_bar_anual(df, value_col, titulo)`** — gráfico de barras agrupadas por ano.
- **`render_top_por_urg(df, value_col, titulo, label_col)`** — gráfico horizontal para uma única URG selecionada.
- **`format_filters_applied(selections, df, mapping)`** — string compacta de filtros para breadcrumb.

### Regras de Ordenação de KPI x Tabela ANO

- Em páginas com cards de indicadores por categoria (Consulta e Exame), a tabela **Comparativa de Performance por ANO** deve usar a mesma ordem dos cards (indicadores gerais).
- A linha `TOTAL` permanece fixada ao final.
- A ordenação é aplicada no DataFrame da grade antes de `split_aggrid_footer(...)`, garantindo consistência visual e na exportação.

### `utils/state_manager.py`

- **`init_global_state()`** — inicializa todas as chaves do `session_state` na primeira execução. Deve ser chamada no topo de `app.py` e de cada `page_*()`.
- Funções de callback de sincronização (ver `data_interaction.md`).

### `utils/data_loader.py`

- **`load_csv(path, expected_cols)`** — carrega um CSV validando as colunas obrigatórias definidas em `schemas.py`. Retorna `(DataFrame, info_dict)` onde `info_dict` contém listas de `erros` e `alertas`. Nunca lança exceção — erros são retornados no dict.

### `utils/schemas.py`

- Define constantes com as colunas esperadas de cada dataset (ex: `SCHEMA_HOME`, `SCHEMA_CONSULTA_ALUNO`). Usado por `load_csv` para validação na carga.

### `components/sidebar_filters.py`

- **`sidebar_filters(df, filter_config)`** — renderiza filtros de Ano, URG, Escola e Tipo na sidebar com base em `filter_config`. Respeita a cascata: URG filtra as opções de Escola. Retorna `(df_filtrado, selections_dict)`.

### `components/footer_personal.py`

- **`footer_personal()`** — insere um rodapé fixo (`position: fixed; bottom: 0`) com o nome da prefeitura. Deve ser chamado no final de cada `page_*()`.

---

## 3. Padrões de Desenvolvimento

### DRY (Don't Repeat Yourself)

- Lógica de estilização → `styles.py`. Nunca hardcode cores ou estilos nas páginas.
- Lógica de filtro → `sidebar_filters.py` ou `filter_by_sidebar_selections`.
- Lógica de tabela comparativa → `build_comparativo_anual`.

### Regra Geral — Tabelas de Seleção

- Sempre que uma nova tabela de seleção for solicitada, aplicar o padrão da Home.
- Filtros criados devem ser refletidos em todos os componentes dependentes (tabelas, gráficos, KPIs e exportações).
- Tabela de seleção não pode ser filtrada pela própria seleção que ela gera.
- Implementar sincronismo bidirecional com sidebar (estado global <-> tabela) com proteção anti-loop.

### SOLID

- Funções pequenas e com responsabilidade única.
- `page_*()` orquestra; `utils/` executa.
- Nenhuma `page_*()` importa outra `page_*()`.

### Idioma

| Contexto | Idioma |
| :--- | :--- |
| Código-fonte (variáveis, funções, classes) | Inglês |
| Comentários e docstrings | Português Brasileiro |
| Interface do usuário | Português Brasileiro |
| Documentação (`docs/`) | Português Brasileiro |

---

## 4. Ciclo de Vida de uma Página

Toda `page_*()` segue este fluxo:

```text
1. init_global_state()          → garante chaves no session_state
2. apply_global_css()           → injeta styles.css
3. load_csv(path, schema)       → carrega e valida dados
4. sidebar_filters(df, config)  → filtra df e retorna selections
5. build_comparativo_anual()    → agrega + estiliza (retorna Styler)
6. st.dataframe(styled_df)      → renderiza com Pro Footer automático
7. footer_personal()            → rodapé fixo
```

### Tratamento de erro padrão

```python
df, info = load_csv("data/DashboardXxx.csv", expected_cols=SCHEMA_XXX)

if info["erros"]:
    st.error("; ".join(info["erros"]))
    footer_personal()
    return  # interrompe renderização da página

if info["alertas"]:
    st.warning("; ".join(info["alertas"]))
```

---

## 5. Deep-linking (Parâmetros de URL)

O `app.py` suporta navegação direta por URL:

| Parâmetro | Exemplo | Efeito |
| :--- | :--- | :--- |
| `?menu=Encaminhamentos` | Qualquer página do menu | Abre a página correspondente |
| `?aluno=NOME&nasc=AAAA-MM-DD` | Perfil do aluno | Abre a página Aluno com busca automática |

Os parâmetros são consumidos e removidos da URL após o processamento para evitar loops de rerun.

---

## 6. Dependências Externas Relevantes

| Biblioteca | Uso |
| :--- | :--- |
| `streamlit` | Framework principal |
| `streamlit_option_menu` | Menu lateral com ícones |
| `st_aggrid` | Tabela avançada na Home (AgGrid) |
| `plotly.express` | Gráficos de barras e análises |
| `pandas` | Manipulação de dados e Styler |
| `Pillow` | Carregamento do logo na sidebar |
---
+
+## 7. Governança de Infraestrutura e Dependências
+
+### Padrão de Execução
+
+- **Docker First:** O ambiente Docker é a referência oficial para comportamento do sistema. Conflitos de bibliotecas de sistema (shared objects, fontes, charset) devem ser resolvidos no `Dockerfile`.
+- **Isolamento:** O uso de `pip install` local sem venv é estritamente proibido para evitar poluição do ambiente e conflitos globais.
+
+### Gestão de Conflitos de Bibliotecas
+
+- **Streamlit vs Componentes:** Bibliotecas de terceiros (como `streamlit-aggrid` ou `streamlit-option-menu`) devem ser validadas quanto à compatibilidade com a versão do core do Streamlit antes da atualização do `requirements.txt`.
+- **Frontend-Backend Parity:** Funcionalidades que dependem de hardware ou SO (como áudio, câmera ou clipboard) devem sempre priorizar APIs de navegador (JS) para garantir que funcionem de forma idêntica dentro de containers Docker headless.
+- **Verificação de Regressão:** Qualquer mudança no `requirements.txt` exige um rebuild completo da imagem Docker (`docker compose build --no-cache`) para validar que não há conflitos de dependências transitivas.
+
