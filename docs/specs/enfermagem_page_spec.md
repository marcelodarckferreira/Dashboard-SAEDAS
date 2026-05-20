# Spec: Página de Enfermagem

**Arquivo:** `app/app_pages/enfermagem.py`
**Função de entrada:** `page_enfermagem()`
**Título:** Visão Geral dos Atendimentos de Enfermagem

---

## 1. Visão Geral e Propósito
- **Objetivo:** Apresentar o resumo consolidado dos atendimentos de enfermagem realizados por Ano, URG e Escola.
- **Subtítulo:** "Resumo consolidado dos atendimentos de enfermagem realizados por ano, URG e escola."

---

## 2. Fontes de Dados e Schemas

Carregadas em `carregar_dados_enfermagem()`:

| Variável | Arquivo CSV | Schema |
|---|---|---|
| `df` (principal) | `data/DashboardEnfermagem.csv` | `SCHEMA_ENFERMAGEM` |
| `df_aluno_raw` | `data/DashboardEnfermagemAluno.csv` | `SCHEMA_ENFERMAGEM_ALUNO` |
| `df_ano` | `data/DashboardEnfermagemAno.csv` | `SCHEMA_ENFERMAGEM_ANO` |
| `df_home` | `data/DashboardHome.csv` | `SCHEMA_HOME` |

### Renomeação de colunas após carga

| CSV original | Nome interno |
|---|---|
| `Descricao` | `Atendimento` |
| `Qtd` | `Quantidade` |
| `DtNasc` (aluno) | `DataNascimento` |

`DataNascimento` é convertido via `pd.to_datetime(..., errors="coerce")`.

---

## 3. Filtros da Sidebar

Ativados via `sidebar_filters(df, {"ano": True, "urg": True, "escola": True, "tipo": True})`.

| Filtro | Chave session_state |
|---|---|
| Ano(s) | `sidebar_year_filter` |
| URG(s) | `sidebar_urg_filter` |
| Escola(s) | `sidebar_escola_filter` |
| Tipo(s) | `sidebar_tipo_filter` |

O filtro de Atendimento foi removido (`atendimentos_selecionados = []`); apenas a função `toggle_atendimento` está declarada, sem KPIs clicáveis ativos.

---

## 4. Seletor Temporal Mestre

- Container `massive_year_selector` com `st.segmented_control` em modo `multi`.
- Opções: últimos 5 anos (incluindo o atual), em ordem decrescente.
- Key: `home_year_buttons`; callback: `sync_home_to_sidebar`.
- Fonte de verdade: `st.session_state["global_years"]`.

---

## 5. Hierarquia de Bases de Dados

```
df (bruto)
 └─► df_base_sem_escola  [filtros: Tipo, Ano]
      └─► df_base_final  [filtros: + Escola]
           └─► df_master_no_atend  [filtros: + URG]
                └─► df_master_filtrado / df_filt  [filtros: + Atendimento]

df_base_sem_escola
 └─► df_filt_no_escola  [filtros: + URG  (sem Escola)]

df_master_no_atend
 └─► df_filt_no_atend  [= df_master_no_atend]
```

Quando `selected_years_comp` está vazio, `df_base_sem_escola` torna-se `pd.DataFrame()` (vazio).

---

## 6. Componentes de Interface

### 6.1 Filtros Aplicados (placeholder)

- `st.empty()` renderizado no topo, preenchido por `format_filters_applied(selections, df, [("ano","Ano"),("urg","URG"),("escola","Escola"),("tipo","Tipo")])`.

### 6.2 Título Dinâmico dos Indicadores

```
### Indicadores Gerais (Anos: X / URGs: X / Escolas: X)
```

Construído por `get_filter_display_string_for_title` — exibe `"Todos"` quando seleção vazia ou igual ao total disponível.

### 6.3 Cards de Indicadores

Renderizados via `render_metric_cards([...])`:

| Card | Origem | Base |
|---|---|---|
| TOTAL DE ALUNOS | `df_home["QtdAlunoEscola"].sum()` | `df_home` filtrado por Ano, URG, Escola |
| ALUNOS ATENDIDOS | `df_home["QtdAluno"].sum()` | `df_home` filtrado por Ano, URG, Escola |
| ATEND. ENFERMAGEM | `df_filt["Quantidade"].sum()` | `df_filt` (todos os filtros) |

Quando `df_filt` está vazio, exibe `st.info("Selecione ao menos um ano para visualizar os indicadores.")`.

### 6.4 Tabela Performance por URG (Mestre)

- **Subtítulo:** "Performance por URG"
- **Caption:** "Sensível apenas ao filtro de Ano."
- **Base:** `df_for_urg_table` = `df` filtrado apenas por `selected_years_comp`.
- Gerada com `build_comparativo_anual(df_for_urg_table, "URG", active_row_value=current_selected_urgs)`.
- `rowSelection: "multiple"`, `rowMultiSelectWithClick: true`.
- `pinnedBottomRowData` com linha TOTAL.
- Sync inicial via JS `onFirstDataRendered` lendo `global_urgs`.
- Key dinâmico: `urg_table_enfermagem_{urgs_selecionadas}`; guarda em `_prev_urg_table_key_enfermagem`.
- Wrapper: `<div class="selection-master-table">`.
- Toolbar container: `enfermagem_urg_actions_toolbar` → `performance_urg_enfermagem.csv`.

**Sync URG (bidirecional):**

| Origem | Ação |
|---|---|
| Sidebar → Tabela | `apply_pending_table_filters()` + JS `onFirstDataRendered` |
| Tabela → Sidebar | Detecta mudança → seta `global_urgs`, `pending_sidebar_urg_filter`, `last_interaction_source="table"` → `st.rerun()` |

### 6.5 Tabela Top Escolas por URG (Mestre)

- Via `render_top_por_urg(df_filt_no_escola, "Quantidade", "Principais Escolas por URG", "Escola", table_key="escola_table_selection_enfermagem", active_row_value=st.session_state["sidebar_escola_filter"], selection_mode="multiple")`.
- Base filtrada adicionalmente por `selected_years_comp`.
- Toolbar: `escola_table_selection_enfermagem_actions_toolbar` (gerada internamente).

**Sync Escola (bidirecional):**

| Origem | Ação |
|---|---|
| Sidebar → Tabela | `sync_sidebar_escola_selection("escola_table_selection_enfermagem")` |
| Tabela → Sidebar | Se `escola_table_selection_enfermagem__selected_values` difere de `sidebar_escola_filter` → seta `pending_sidebar_escola_filter`, `last_interaction_source="table_escola"` → `st.rerun()` |

Ao final do bloco, `last_interaction_source = ""`.

### 6.6 Gráfico Distribuição por URG

- **Subtítulo:** "Distribuição por URG"
- **Base:** `df_filt.groupby(["URG","Ano"])["Quantidade"].sum()`.
- Ordenação por numeral romano da URG (`_urg_sort_key`) e por Ano.
- `Ano` como string categórica; rótulos em formato `"3.235"`.
- `px.bar(..., x="URG", y="Quantidade", color="Ano", barmode="group", text="_text_fmt")`.
- `hovermode="x unified"`.

### 6.7 Detalhamento por Aluno

**Base de construção:**
1. `filter_by_sidebar_selections(df_aluno, selections)`.
2. Filtra por `selected_years_comp`.

**Filtros locais (multiselect inline):**

| Widget | Key |
|---|---|
| Filtrar por Aluno | `enfermagem_aluno_multiselect` |
| Filtrar por Série | `enfermagem_serie_multiselect` |
| Filtrar por Turma | `enfermagem_turma_multiselect` |

**Construção da tabela (`df_aluno_final`):**
1. Estáticos por (`ID`,`Aluno`) via `groupby(...).last()` em `DataNascimento, Sexo, Profissional, URG, Escola, Serie, Turma`.
2. Contagem por (`ID`,`Ano`) → `Qtd`.
3. Pivot dos anos como colunas.
4. Coluna `Total` = soma das colunas de ano.
5. Zeros viram string vazia; valores positivos formatados como inteiros.
6. Coluna `Menu` via `build_perfil_link` (renomeada para `Perfil`).
7. `DataNascimento` formatada `%d/%m/%Y`.

**Ordem das colunas:** `ID, Aluno, DataNascimento, Sexo, Profissional, URG, Escola, Serie, Turma, [Anos...], Total, Perfil`.

- Caption: `"{N} registros após filtros da sidebar"`.
- Limite de exibição: `preview_limit = 500` linhas.
- Renderização: `render_aluno_detalhamento_aggrid(df_aluno_head, key="aluno_table_enfermagem", csv_name="detalhes_alunos_enfermagem.csv", toolbar_key="enfermagem_aluno_actions_toolbar")`.

`build_perfil_link` gera `?menu=Aluno&aluno=Nome&nasc=YYYY-MM-DD` via `urlencode`.

---

## 7. Estado Global e Chaves de Session State

### Chaves globais
- `global_years`, `global_urgs`
- `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`, `sidebar_tipo_filter`
- `last_interaction_source` (`""`, `"sidebar"`, `"table"`, `"table_escola"`)
- `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`

### Chaves locais da página
| Chave | Descrição |
|---|---|
| `enfermagem_atendimento_multiselect` | Estado (não exibido) de toggle de atendimento |
| `enfermagem_aluno_multiselect` | Multiselect de alunos |
| `enfermagem_serie_multiselect` | Multiselect de séries |
| `enfermagem_turma_multiselect` | Multiselect de turmas |
| `escola_table_selection_enfermagem__selected_values` | Escolas selecionadas na tabela mestre |
| `_prev_urg_table_key_enfermagem` | Stale-guard da AgGrid URG |

---

## 8. Regras de Negócio e Cálculos
- **Atendimentos:** soma de `Quantidade` em `df_filt`.
- **Total de Alunos / Atendidos:** lidos do dataset `DashboardHome.csv`, filtrados pelos mesmos Ano/URG/Escola da sidebar.
- **Ordenação de URGs:** numeral romano via `_roman_to_int` / `_urg_sort_key`.
- **Tabela URG é imune** aos filtros de URG, Escola, Tipo e Atendimento (sensível apenas a Ano).
- **Tabela Escola** usa `df_filt_no_escola` (imune ao próprio filtro de Escola).

---

## 9. Estilos Críticos (injetados na página)
- `.home-metric-label`, `.home-metric-value`, `.home-metric-card`, `.metric-card-static`
- `div[class*="st-key-btn_kpi_"] button` (KPIs clicáveis)
- Toolbars agrupadas:
  - `.st-key-enfermagem_urg_actions_toolbar`
  - `.st-key-escola_table_selection_enfermagem_actions_toolbar`
  - `.st-key-enfermagem_cobertura_actions_toolbar`
  - `.st-key-enfermagem_aluno_actions_toolbar`

---

## 10. Exportação de Dados
- Tabela URG: `performance_urg_enfermagem.csv` (toolbar `enfermagem_urg_actions_toolbar`).
- Tabela Aluno: `detalhes_alunos_enfermagem.csv` (toolbar `enfermagem_aluno_actions_toolbar`).
- Top Escolas: CSV gerado por `render_top_por_urg`.

---

## 11. Cache e Performance
- **Redis Integration:** Utiliza a camada de cache definida em [Redis Cache Spec](redis_cache_spec.md).
- **Estratégia em Enfermagem:**
    - **Datasets:** Cachear os 4 DataFrames base (`Principal`, `Aluno`, `Ano`, `Home`).
    - **Chaves:**
        - `saedas:enfermagem:dataset:main`
        - `saedas:enfermagem:dataset:aluno`
        - `saedas:enfermagem:dataset:ano`
        - `saedas:home:dataset:main` (Reaproveitado)
    - **Invalidação:** TTL de 12 horas ou via scripts de integração.
