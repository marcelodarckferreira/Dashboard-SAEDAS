# Spec: Página de Atendimentos de Psicólogo

**Arquivo:** `app/app_pages/psicologo.py`
**Função de entrada:** `page_psicologo()`
**Título:** Visão Geral dos Atendimentos de Psicólogo

---

## 1. Fontes de Dados

Carregadas em `carregar_dados_psicologo()`.

| Variável | Arquivo CSV | Schema |
|---|---|---|
| `df` (principal) | `data/DashboardPsicologo.csv` | `SCHEMA_PSICOLOGO` |
| `df_aluno_raw` | `data/DashboardPsicologoAluno.csv` | `SCHEMA_PSICOLOGO_ALUNO` |
| `df_ano` | `data/DashboardPsicologoAno.csv` | `SCHEMA_PSICOLOGO_ANO` |
| `df_home` | `data/DashboardHome.csv` | `SCHEMA_HOME` |

### Renomeação de colunas após carga

Principal (`df`):

| CSV original | Nome interno |
|---|---|
| `Ano` | `Ano` |
| `URG` | `URG` |
| `Escola` | `Escola` |
| `Descricao` | `Atendimento` |
| `Qtd` | `Quantidade` |
| `Tipo` | `Tipo` |

Aluno (`df_aluno`):

| CSV original | Nome interno |
|---|---|
| `DtNasc` | `DataNascimento` (convertida via `pd.to_datetime`) |
| `Profissional` | `Profissional` |

---

## 2. Filtros da Sidebar

Ativados via `sidebar_filters(df, {"ano": True, "urg": True, "escola": True, "tipo": True})`.

| Filtro | Chave session_state |
|---|---|
| Ano(s) | `sidebar_year_filter` |
| URG(s) | `sidebar_urg_filter` |
| Escola(s) | `sidebar_escola_filter` |
| Tipo(s) | `sidebar_tipo_filter` |

> Observação: o filtro de Atendimento foi removido da página conforme comentário no código (`atendimentos_selecionados = []`). Existe ainda o callback interno `toggle_atendimento` (atrelado à chave `psicologo_atendimento_multiselect`), porém não está vinculado a nenhum widget renderizado.

---

## 3. Seletor Temporal Mestre

- Container `massive_year_selector` com `st.segmented_control` (multi).
- Chave do widget: `home_year_buttons`.
- Callback: `sync_home_to_sidebar` (espelha em `global_years` e `sidebar_year_filter`).
- Opções: últimos 5 anos calculados a partir de `datetime.datetime.now().year`.

---

## 4. Hierarquia de Bases de Dados

```
df (bruto, renomeado)
 └─► df_base_sem_escola  [filtros: Tipo, Ano]
      └─► df_base_final  [filtros: + Escola]
           └─► df_master_no_atend  [filtros: + URG]
                └─► df_master_filtrado / df_filt  [filtros: + Atendimento (vazio na prática)]

df_base_sem_escola
 └─► df_filt_no_escola  [filtros: + URG (sem Escola)]
df_master_no_atend
 └─► df_filt_no_atend  [= df_master_no_atend]
```

### Matriz de imunidade por base

| Base | Tipo | Ano | URG | Escola | Atendimento |
|---|---|---|---|---|---|
| `df_base_sem_escola` | OK | OK | — | — | — |
| `df_base_final` | OK | OK | — | OK | — |
| `df_master_no_atend` | OK | OK | OK | OK | — |
| `df_filt` | OK | OK | OK | OK | OK |
| `df_filt_no_escola` | OK | OK | OK | IMUNE | — |
| `df_filt_no_atend` | OK | OK | OK | OK | IMUNE |

---

## 5. Componentes e Regras de Filtro

### 5.1 Filtros Aplicados (placeholder)

- Renderizado com `st.empty()` antes do divisor de seção.
- Preenchido por `format_filters_applied(selections, df, [...])` cobrindo Ano, URG, Escola e Tipo.

### 5.2 Indicadores Gerais (Cards Estáticos)

`render_metric_cards([...])` com três cards:

| Card | Origem |
|---|---|
| TOTAL DE ALUNOS | `df_home["QtdAlunoEscola"].sum()` (após filtros Ano, URG, Escola sobre `df_home`) |
| ALUNOS ATENDIDOS | `df_home["QtdAluno"].sum()` (mesmos filtros) |
| ATEND. PSICÓLOGO | `df_filt["Quantidade"].sum()` |

Se `df_filt` estiver vazio: exibe `st.info("Selecione ao menos um ano para visualizar os indicadores.")`.

### 5.3 Tabela Performance por URG (Mestre de Seleção)

- **Base:** `df_for_urg_table` = `df` filtrado apenas por `selected_years_comp`.
- Gerada com `build_comparativo_anual(df_for_urg_table, "URG", active_row_value=current_selected_urgs)`.
- AgGrid via `render_saedas_aggrid` + `prepare_comparativo_aggrid_data` + `split_aggrid_footer`.
- `rowSelection: "multiple"`, `rowMultiSelectWithClick: True`.
- `onFirstDataRendered` (JS) sincroniza linhas com `global_urgs`.
- Key dinâmico: `urg_table_psicologo_{urgs_concatenadas|none}`; stale-guard via `_prev_urg_table_key_psicologo`.
- Toolbar: container `psicologo_urg_actions_toolbar`, arquivo `performance_urg_psicologo.csv`.
- Wrapper: `selection-master-table`.
- Caption: "Esta tabela é sensível apenas ao filtro de Ano."

**Sync URG (tabela → sidebar):** se `set(new_urgs) != set(current_urgs)` → seta `global_urgs`, `pending_sidebar_urg_filter`, `last_interaction_source = "table"` → `st.rerun()`.

### 5.4 Tabela Top Escolas por URG (Mestre de Seleção)

- Renderizada via `render_top_por_urg(...)`:
  - **Base:** `df_filt_no_escola` filtrada também por `selected_years_comp`.
  - `value_col="Quantidade"`, `label_col="Escola"`, `titulo="Principais Escolas por URG"`.
  - `table_key="escola_table_selection_psicologo"`.
  - `active_row_value=st.session_state.get("sidebar_escola_filter", [])`.
  - `selection_mode="multiple"`.
- Toolbar gerada automaticamente: `escola_table_selection_psicologo_actions_toolbar`.

**Sync Escola (tabela → sidebar):** se `set(escolas_tabela_atual) != set(current_sidebar_escolas)` → seta `pending_sidebar_escola_filter`, `last_interaction_source = "table_escola"` → `st.rerun()`. Ao final, `last_interaction_source = ""`.

### 5.5 Distribuição por URG (Gráfico)

- **Base:** `df_filt` agregado por `["URG", "Ano"]` somando `Quantidade`.
- Ordenação por numeral romano de URG (`_urg_sort_key`) e por Ano.
- `px.bar` agrupado (`barmode="group"`), cor por Ano.
- Texto formatado com separador de milhar (`"3.235"`).
- `hovertemplate` customizado; `hovermode="x unified"`.

### 5.6 Detalhamento por Aluno

**Base de construção:**
1. `filter_by_sidebar_selections(df_aluno, selections)` (Ano, URG, Escola, Tipo).
2. Filtro adicional por `selected_years_comp`.

**Filtros locais (multiselect):**

| Widget | Chave |
|---|---|
| Filtrar por Aluno | `psicologo_aluno_multiselect` |
| Filtrar por Série | `psicologo_serie_multiselect` |
| Filtrar por Turma | `psicologo_turma_multiselect` |

**Construção da tabela final:**
1. `static_cols` = `["DataNascimento", "Sexo", "Profissional", "URG", "Escola", "Serie", "Turma"]` agregados por `(ID, Aluno)` via `.last()`.
2. Contagem de registros por `(ID, Ano)` → pivot com Anos como colunas.
3. Merge dos estáticos com o pivot por `ID`.
4. Coluna `Total` = soma dos anos.
5. Zeros são limpos (string vazia); valores convertidos para `int`.
6. Coluna `Menu` gerada por `build_perfil_link` → `?menu=Aluno&aluno=Nome[&nasc=YYYY-MM-DD]`.
7. `DataNascimento` formatada como `dd/mm/yyyy`.
8. Renomeada para `Perfil` na exibição.

**Ordem de colunas:**
`ID | Aluno | DataNascimento | Sexo | Profissional | URG | Escola | Serie | Turma | [Anos...] | Total | Perfil`

- Limite de exibição: `preview_limit = 500` linhas (aviso se exceder).
- Renderização via `render_aluno_detalhamento_aggrid(...)` com:
  - `key="aluno_table_psicologo"`
  - `csv_name="detalhes_alunos_psicologo.csv"`
  - `toolbar_key="psicologo_aluno_actions_toolbar"`

---

## 6. Título Dinâmico dos Indicadores

```
### Indicadores Gerais (Anos: X / URGs: X / Escolas: X)
```

- Gerado por `get_filter_display_string_for_title(...)`.
- `"Todos"` quando seleção vazia ou igual ao conjunto total disponível.
- Lista separada por `, ` em seleções parciais.

---

## 7. Estado Global e Chaves de Session State

### Globais (compartilhadas)

| Chave | Tipo |
|---|---|
| `global_years` | `list[int]` |
| `global_urgs` | `list[str]` |
| `sidebar_year_filter` | `list[int]` |
| `sidebar_urg_filter` | `list[str]` |
| `sidebar_escola_filter` | `list[str]` |
| `home_year_buttons` | `list[int]` (widget mestre) |
| `last_interaction_source` | `str` (`""`, `"sidebar"`, `"table"`, `"table_escola"`) |
| `pending_sidebar_urg_filter` | `list[str]` |
| `pending_sidebar_escola_filter` | `list[str]` |

### Locais da página

| Chave | Descrição |
|---|---|
| `_prev_urg_table_key_psicologo` | Stale-guard da AgGrid de URG |
| `escola_table_selection_psicologo__selected_values` | Escolas selecionadas na tabela |
| `escola_table_selection_psicologo__aggrid_key` | Key atual da AgGrid de escolas |
| `escola_table_selection_psicologo__prev_sidebar_escola_filter` | Prev value de escola da sidebar |
| `psicologo_atendimento_multiselect` | Reservado (filtro não renderizado) |
| `psicologo_aluno_multiselect` | Multiselect de aluno (detalhamento) |
| `psicologo_serie_multiselect` | Multiselect de série |
| `psicologo_turma_multiselect` | Multiselect de turma |

---

## 8. Regras de Sincronismo — Fluxo

```
RENDER
  │
  ├─ init_global_state()
  ├─ apply_pending_table_filters()
  │    ├─ pending_sidebar_urg_filter   → sidebar_urg_filter + global_urgs
  │    └─ pending_sidebar_escola_filter → sidebar_escola_filter
  │
  ├─ sidebar_filters() [renderiza widgets]
  ├─ sync_sidebar_escola_selection("escola_table_selection_psicologo")
  │
  ├─ Seletor mestre de Ano → sync_home_to_sidebar
  │
  ├─ URG table response
  │    └─ se seleção mudou → global_urgs + pending_sidebar_urg_filter
  │                       → last_interaction_source = "table" → rerun()
  │
  └─ Escola sync check
       ├─ se escolas_tabela != sidebar → pending_sidebar_escola_filter
       │                              → last_interaction_source = "table_escola" → rerun()
       └─ final: last_interaction_source = ""
```

---

## 9. Exportação de Dados

- Toolbars padrão via `render_table_toolbar` (Copiar TSV + Download CSV via JS Blob).
- CSVs gerados:
  - `performance_urg_psicologo.csv` (tabela mestre URG)
  - `top_escola_por_urg.csv` (gerado dentro de `render_top_por_urg`)
  - `detalhes_alunos_psicologo.csv` (detalhamento por aluno)

---

## 10. Estilos Críticos

Bloco CSS local injetado no início da página inclui:

- `.home-metric-card`, `.metric-card-static`, `.home-metric-label`, `.home-metric-value`
- `div[class*="st-key-btn_kpi_"] button` (KPIs clicáveis, padrão Home)
- Toolbars agrupadas:
  - `.st-key-psicologo_urg_actions_toolbar`
  - `.st-key-escola_table_selection_psicologo_actions_toolbar`
  - `.st-key-psicologo_cobertura_actions_toolbar`
  - `.st-key-psicologo_aluno_actions_toolbar`

---

## 11. Cache e Performance

- **Redis Integration:** ver [Redis Cache Spec](redis_cache_spec.md).
- **Estratégia em Psicólogo:**
    - **Datasets:** Cachear os 4 DataFrames base (`Principal`, `Aluno`, `Ano`, `Home`).
    - **Chaves sugeridas:**
        - `saedas:psicologo:dataset:main`
        - `saedas:psicologo:dataset:aluno`
        - `saedas:psicologo:dataset:ano`
        - `saedas:home:dataset:main` (reaproveitado)
    - **Invalidação:** TTL de 12 horas ou via scripts de integração.
