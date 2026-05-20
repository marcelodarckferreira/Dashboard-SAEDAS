# Especificação Técnica — Página Consulta (Encaminhamentos / Regulação)

- **Arquivo:** `app/app_pages/consulta.py`
- **Função de entrada:** `page_consulta()`
- **Título:** `Visão Geral do Encaminhamento (Regulação)`
- **Subtítulo:** `Resumo consolidado das ações realizadas por ano, URG e equipe técnica.`

---

## 1. Visão Geral

A página consolida os encaminhamentos (regulações) realizados pelas equipes técnicas, oferecendo:

- KPIs gerais (totais de alunos, atendidos e encaminhamentos).
- KPIs por tipo de encaminhamento, clicáveis (toggle).
- Tabela comparativa de performance por ano.
- Tabela mestre de performance por URG (com cross-filter para a sidebar).
- Tabela mestre de Top Escolas por URG (com cross-filter para a sidebar).
- Gráficos de distribuição por URG e por Encaminhamento.
- Detalhamento por aluno em AgGrid com link para perfil.

---

## 2. Fontes de Dados

Carregamento por `carregar_dados_consulta()` com cache Redis (TTL controlado por `redis_cache.get_dataframe_with_timestamp`).

| Chave interna | CSV | Schema | Chave Redis |
|---|---|---|---|
| `principal` | `data/DashboardConsulta.csv` | `SCHEMA_CONSULTA` | `saedas:consulta:dataset:main` |
| `aluno` | `data/DashboardConsultaAluno.csv` | `SCHEMA_CONSULTA_ALUNO` | `saedas:consulta:dataset:aluno` |
| `ano` | `data/DashboardConsultaAno.csv` | `SCHEMA_CONSULTA_ANO` | `saedas:consulta:dataset:ano` |
| `home` | `data/DashboardHome.csv` | `SCHEMA_HOME` | `saedas:home:dataset:main` (reuso) |

### 2.1 Renomeação de colunas após carga

| CSV original | Nome interno |
|---|---|
| `Consulta` | `Encaminhamento` |
| `tipo` | `Tipo` |
| `Qtd` | `Quantidade` |
| `DtNasc` | `DataNascimento` |

`DataNascimento` é convertida para `datetime` com `errors="coerce"`.

---

## 3. Filtros

### 3.1 Sidebar (via `sidebar_filters`)

```python
sidebar_filters(df, {"ano": True, "urg": True, "escola": True, "tipo": True})
```

| Filtro | Chave session_state | Sincronismo |
|---|---|---|
| Ano(s) | `sidebar_year_filter` | `sync_sidebar_to_home` |
| URG(s) | `sidebar_urg_filter` | `sync_sidebar_urg_to_home` |
| Escola(s) | `sidebar_escola_filter` | `sync_sidebar_escola_to_global` |
| Tipo(s) | `sidebar_tipo_filter` | — |

### 3.2 Filtro local da página

| Filtro | Chave session_state | Callback |
|---|---|---|
| Encaminhamento(s) | `consulta_encaminhamento_multiselect` | `sync_local_consulta_encaminhamento` |
| Persistência | `persistent_consulta_encaminhamento` | restaurada quando o widget some |

### 3.3 Seletor Temporal Mestre

- Container: `massive_year_selector`
- Widget: `st.segmented_control(... key="home_year_buttons", on_change=sync_home_to_sidebar)`
- Opções: últimos 5 anos a partir de `datetime.datetime.now().year`.
- Fonte de verdade: `st.session_state["global_years"]`.

Ver também: [Shared Components Spec — Seletor Temporal Mestre](shared_components_spec.md#2-seletor-temporal-mestre-botoes-de-ano).

### 3.4 Filtros locais do bloco de alunos

- Multiselect Aluno
- Multiselect Série
- Multiselect Turma

---

## 4. Hierarquia de Bases de Dados

```
df (bruto, renomeado)
 └─► df_base_sem_escola  [Tipo, Ano]
      └─► df_base_final  [Tipo, Ano, Escola]
           └─► df_master_no_enc  [Tipo, Ano, Escola, URG]
                └─► df_filt  [Tipo, Ano, Escola, URG, Encaminhamento]
                └─► df_filt_no_enc  [= df_master_no_enc]

df_base_sem_escola
 └─► df_filt_no_escola  [Tipo, Ano, URG, Encaminhamento] (imune a Escola)
```

### 4.1 Matriz de imunidade

| Base | Tipo | Ano | URG | Escola | Encaminhamento |
|---|---|---|---|---|---|
| `df_base_sem_escola` | OK | OK | — | — | — |
| `df_base_final` | OK | OK | — | OK | — |
| `df_master_no_enc` | OK | OK | OK | OK | — |
| `df_filt` | OK | OK | OK | OK | OK |
| `df_filt_no_enc` | OK | OK | OK | OK | imune |
| `df_filt_no_escola` | OK | OK | OK | imune | OK |

---

## 5. Componentes

### 5.1 Placeholder "Filtros aplicados"

- `st.empty()` criado antes do conteúdo.
- Preenchido com `format_filters_applied(selections, df, [...])`.
- Campos: Ano, URG, Escola, Tipo, Regulação (label do Encaminhamento).

### 5.2 Indicadores Gerais (cards estáticos)

Renderizados por `render_metric_cards([...])`:

| Card | Cálculo | Base |
|---|---|---|
| TOTAL DE ALUNOS | `df_home_filt["QtdAlunoEscola"].sum()` | `df_home_filt` |
| ALUNOS ATENDIDOS | `df_home_filt["QtdAluno"].sum()` | `df_home_filt` |
| ENCAMINHAMENTOS | `df_master_no_enc["Quantidade"].sum()` | `df_master_no_enc` |

`df_home_filt` aplica Ano, URG, Escola e Tipo sobre `df_home` (todos imunes ao filtro de Encaminhamento).

### 5.3 KPIs de Encaminhamento (toggle)

- Base: `df_filt_no_enc.groupby("Encaminhamento")["Quantidade"].sum()` (apenas `> 0`, ordenados desc).
- Renderização em blocos de 5 colunas via `render_metric_cards(chunk, is_toggle=True, active_labels=[...], on_click_callback=toggle_regulacao, fixed_columns=5)`.
- Clique invoca `toggle_regulacao(reg_name)` → alterna em `consulta_encaminhamento_multiselect` e espelha em `persistent_consulta_encaminhamento`.
- Card ativo recebe estilo `primary`.

Sem dados: exibe `st.info("Selecione ao menos um ano para visualizar os indicadores.")`.

### 5.4 Tabela Comparativa de Performance por ANO (Encaminhamentos)

- Base: `df_filt` (todos os filtros, inclusive Encaminhamento).
- Gerada por `build_comparativo_anual(df_filt, "Encaminhamento", value_col="Quantidade", pct_label="Total")`.
- Sem coluna de seleção (`include_selection_column=False`).
- Ordenação das linhas: segue a ordem dos KPI cards (`encaminhamentos_sum`); `TOTAL` sempre por último.
- Rodapé fixo via `pinnedBottomRowData`.
- Toolbar container key: `consulta_ano_actions_toolbar`.
- Render: `render_saedas_aggrid(..., key="ano_perf_table_consulta_aggrid", min_height=140)`.
- Wrapper CSS: `st-table-with-total`.
- Caption explica `% Total` e `Var%`.

### 5.5 Tabela Performance por URG (Mestre)

- Base: `df_for_urg_table` = `df` filtrado por Tipo + Ano + Encaminhamento (sem filtro de URG e Escola).
- Gerada por `build_comparativo_anual(df_for_urg_table, "URG", active_row_value=current_selected_urgs, pct_label="Cobertura")`.
- DataFrame salvo em `last_df_cmp_urg_consulta` (debug/callback).
- `rowSelection: "multiple"`, `rowMultiSelectWithClick: True`.
- Sincronização visual via JS (`onFirstDataRendered`) baseada em `global_urgs`.
- Key dinâmico: `urg_table_consulta_{years}_{encs}_{urgs}` (stale-guard); valor anterior em `_prev_urg_table_key_consulta`.
- Toolbar container key: `consulta_urg_actions_toolbar`.
- Wrapper CSS: `selection-master-table`.
- Caption: "Sensível aos filtros de Ano, Tipo e Encaminhamento."

**Propagação Tabela → Sidebar (URG):** quando `set(new_urgs) != set(current_urgs)` e a key da tabela não mudou no render atual, define `global_urgs`, `pending_sidebar_urg_filter`, `last_interaction_source = "table"` e dispara `st.rerun()`.

### 5.6 Top Escolas por URG (Mestre)

- Função: `render_top_por_urg(...)`.
- Base: `df_filt_no_escola` filtrado por `selected_years_comp`.
- Parâmetros:
  - `table_key="escola_table_selection_consulta"`
  - `active_row_value=st.session_state.get("sidebar_escola_filter", [])`
  - `selection_mode="multiple"`
- Toolbar interna: `escola_table_selection_consulta_actions_toolbar`.
- Chave AgGrid: `escola_table_selection_consulta_aggrid_top_urg_{sufixo}`.

**Propagação Tabela → Sidebar (Escola):** após o render, compara `escola_table_selection_consulta__selected_values` com `sidebar_escola_filter`. Se diferentes → define `pending_sidebar_escola_filter`, `last_interaction_source = "table_escola"` e `st.rerun()`. Ao final do bloco, `last_interaction_source` é zerado (`""`).

### 5.7 Gráfico — Comparativo Anual por URG

- Base: `df_filt`.
- `render_grouped_bar_anual(df_filt, "Quantidade", "", orientation="h")`.

### 5.8 Gráfico — Distribuição por Encaminhamentos

- Base: `df_filt`.
- `render_grouped_bar_anual(df_filt, "Quantidade", "", x_col="Encaminhamento", orientation="h")`.

### 5.9 Detalhamento por Aluno (AgGrid)

**Construção do DataFrame base (`df_aluno_filtrado`):**

1. `filter_by_sidebar_selections(df_aluno, selections)` (Ano, URG, Escola, Tipo).
2. Restringe a `selected_years_comp`.
3. Aplica `selections["escola"]` se houver.
4. Aplica `encaminhamentos_selecionados` se houver (em `Encaminhamento`).
5. (Bloco preservado, atualmente inerte) merge por `selected_encs_from_table` — sempre `[]` no fluxo atual.

**Filtros inline:** Multiselect Aluno, Série, Turma.

**Pipeline de pivot/agregação:**

- `df_static`: `groupby(["Aluno","DataNascimento"]).last()` em `["Sexo","URG","Escola","Serie","Turma"]`.
- `df_desc`: por `(Aluno, DataNascimento, Ano)`, lista de encaminhamentos formatada (`UPPER` para selecionados, `Capitalize` demais).
- `df_pivot_ano`: pivot com anos em colunas, valores = descrição textual.
- `df_counts_total`: total de registros por aluno → coluna `Total`.
- `Menu` (renomeada para `Perfil`): URL `?menu=Aluno&aluno=<Nome>&nasc=YYYY-MM-DD` via `build_perfil_link`.
- `DataNascimento` formatada `dd/mm/YYYY`.

**Ordem das colunas:**
`Aluno | DataNascimento | Sexo | URG | Escola | Serie | Turma | <anos...> | Total | Perfil`

**Render:** `render_aluno_detalhamento_aggrid(df, key="aluno_table_consulta", csv_name="detalhes_alunos_consulta.csv", toolbar_key="consulta_aluno_actions_toolbar")`.

Mensagens vazias:
- Dados ausentes: `"Dados de alunos não estão disponíveis ou houve erro na leitura do CSV."`
- Filtro sem resultado: `"Nenhum registro de aluno para os filtros selecionados."`

---

## 6. Título Dinâmico dos Indicadores

```
### Indicadores Gerais (Anos: X / URGs: X / Escolas: X / Regulações: X)
```

- Função local: `get_filter_display_string_for_title(...)`.
- `"Todos"` quando todos os itens disponíveis estão selecionados ou nenhum está selecionado.

---

## 7. Estado Global e Chaves de Session State

### 7.1 Chaves globais (compartilhadas)

| Chave | Descrição |
|---|---|
| `global_years` | Anos selecionados (fonte de verdade) |
| `global_urgs` | URGs selecionadas (fonte de verdade) |
| `sidebar_year_filter` | Espelho do multiselect de anos |
| `sidebar_urg_filter` | Espelho do multiselect de URGs |
| `sidebar_escola_filter` | Espelho do multiselect de Escolas |
| `home_year_buttons` | Estado do `segmented_control` (paridade com `global_years`) |
| `last_interaction_source` | `""`, `"sidebar"`, `"table"`, `"table_escola"` |
| `pending_sidebar_urg_filter` | Pendência URG (tabela → sidebar) |
| `pending_sidebar_escola_filter` | Pendência Escola (tabela → sidebar) |

### 7.2 Chaves locais da página

| Chave | Descrição |
|---|---|
| `consulta_encaminhamento_multiselect` | Encaminhamentos selecionados (sidebar/toggle) |
| `persistent_consulta_encaminhamento` | Persistência entre navegações |
| `escola_table_selection_consulta__selected_values` | Escolas selecionadas na tabela mestre |
| `escola_table_selection_consulta__aggrid_key` | Stale-guard da AgGrid de escolas |
| `escola_table_selection_consulta__prev_sidebar_escola_filter` | Prev value (sync sidebar→tabela) |
| `_prev_urg_table_key_consulta` | Stale-guard da AgGrid de URG |
| `last_df_cmp_urg_consulta` | DataFrame do comparativo URG (debug) |
| `trigger_<toolbar_key>` | Trigger oculto da toolbar (quando há `leading_action`) |

---

## 8. Regras de Sincronismo (Fluxo Resumido)

```
RENDER
  ├─ init_global_state()
  ├─ apply_pending_table_filters()
  │    ├─ pending_sidebar_urg_filter → sidebar_urg_filter + global_urgs (last="table")
  │    └─ pending_sidebar_escola_filter → sidebar_escola_filter (last="table_escola")
  ├─ sidebar_filters(...)
  ├─ sync_sidebar_escola_selection("escola_table_selection_consulta")
  │    └─ se sidebar_escola mudou → atualiza {key}__selected_values, last="sidebar"
  ├─ render componentes
  ├─ URG table response → se mudou: pending_sidebar_urg_filter + global_urgs + rerun
  ├─ Escola sync check → se mudou: pending_sidebar_escola_filter + rerun
  └─ last_interaction_source = ""
```

---

## 9. Exportação de Dados

- Toolbars de tabela via `render_table_toolbar`, exportando corpo + rodapé.
- Botão "Copiar": TSV via `navigator.clipboard` (executado dentro de iframe HTML).
- Botão "CSV": download via Blob (JS) com BOM UTF-8.
- Arquivos gerados:
  - `comparativo_performance_ano_encaminhamentos.csv`
  - `performance_urg_consulta.csv`
  - `top_escola_por_urg.csv`
  - `detalhes_alunos_consulta.csv`

Ver [Shared Components Spec — Toolbar Unificada](shared_components_spec.md#1-toolbar-unificada-copiar--csv).

---

## 10. Estilos Críticos (escopo da página)

Bloco `<style>` injetado no início de `page_consulta()`:

- Cards: `.home-metric-card`, `.metric-card-static`, `.home-metric-link`, `.home-metric-label`, `.home-metric-value`.
- KPIs toggle: `div[class*="st-key-btn_kpi_"] button` (incluindo regras para `p`, `strong`, `kind="primary"`).
- Toolbars agrupadas (Copiar + CSV) para as keys:
  - `consulta_urg_actions_toolbar`
  - `consulta_ano_actions_toolbar`
  - `consulta_reg_actions_toolbar`
  - `consulta_aluno_actions_toolbar`
  - `escola_table_selection_consulta_actions_toolbar`
  - `encaminhamento_simple_actions_toolbar`

---

## 11. Cache e Performance

- Cache Redis via `redis_cache.get_dataframe_with_timestamp` / `set_dataframe_with_timestamp`.
- Invalidação por timestamp do CSV em disco; fallback para `load_csv` quando ausente.
- Datasets cacheados: `principal`, `aluno`, `ano`, `home`.
- Ver [Redis Cache Spec](redis_cache_spec.md).
