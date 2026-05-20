# Spec: Página de Atendimentos Médicos

**Arquivo:** `app/app_pages/medico.py`
**Função de entrada:** `page_medico()`
**Título:** Visão Geral dos Atendimentos Médicos
**Subtítulo:** Resumo consolidado dos atendimentos médicos realizados por ano, URG e escola.

---

## 1. Visão Geral

A tela apresenta indicadores consolidados de atendimentos médicos, com filtros bidirecionais entre sidebar e tabelas mestres. Diferentemente da tela `Consulta`, **não há filtro de Atendimento (categoria) ativo** — `atendimentos_selecionados` é mantido como lista vazia (comentário no código: "Filtro de Atendimento removido conforme solicitação"). Os KPIs de toggle por categoria de atendimento, portanto, não são renderizados.

---

## 2. Fontes de Dados

| Variável | Arquivo CSV | Schema |
|---|---|---|
| `df` (principal) | `data/DashboardMedico.csv` | `SCHEMA_MEDICO` |
| `df_aluno_raw` | `data/DashboardMedicoAluno.csv` | `SCHEMA_MEDICO_ALUNO` |
| `df_ano` | `data/DashboardMedicoAno.csv` | `SCHEMA_MEDICO_ANO` |
| `df_home` | `data/DashboardHome.csv` | `SCHEMA_HOME` |

### Schemas

- `SCHEMA_MEDICO`: `Ano, IdUrg, URG, Escola, Tipo, Descricao, Qtd`
- `SCHEMA_MEDICO_ALUNO`: `Ano, ID, Aluno, DtNasc, Sexo, Profissional, IdUrg, URG, Escola, Tipo, Serie, Turma`
- `SCHEMA_MEDICO_ANO`: `URG, Escola, Atendimento, 2022, 2023, 2024, 2025, 2026, Total`

### Renomeação de colunas após carga

| CSV original | Nome interno |
|---|---|
| `Descricao` | `Atendimento` |
| `Qtd` | `Quantidade` |
| `DtNasc` | `DataNascimento` |

`DataNascimento` é convertido para `datetime` via `pd.to_datetime(..., errors="coerce")`.

---

## 3. Filtros da Sidebar

Ativados via `sidebar_filters(df, {"ano": True, "urg": True, "escola": True, "tipo": True})`.

| Filtro | Chave session_state |
|---|---|
| Ano(s) | `sidebar_year_filter` |
| URG(s) | `sidebar_urg_filter` |
| Escola(s) | `sidebar_escola_filter` |
| Tipo(s) | `sidebar_tipo_filter` |

Nota: a página define a função `toggle_atendimento(label)` (manipula `medico_atendimento_multiselect`), porém ela não é invocada por nenhum KPI nesta versão.

---

## 4. Seletor Temporal Mestre

- Container `massive_year_selector` com `st.segmented_control(selection_mode="multi", key="home_year_buttons", on_change=sync_home_to_sidebar)`.
- Opções: `[ano_atual, ano_atual-1, ..., ano_atual-4]`, decrescente.
- Sincroniza com `st.session_state["global_years"]` (fonte de verdade).

---

## 5. Hierarquia de Bases de Dados

```
df (bruto)
 └─► df_base_sem_escola  [filtros: Tipo, Ano]
      └─► df_base_final  [filtros: + Escola]
           └─► df_master_no_atend  [filtros: + URG]
                └─► df_master_filtrado = df_filt  [filtros: + Atendimento (inativo)]
                └─► df_filt_no_atend  [= df_master_no_atend]

df_base_sem_escola
 └─► df_filt_no_escola  [filtros: + URG  (sem Escola)]
```

### Matriz de imunidade por base

| Base | Tipo | Ano | URG | Escola |
|---|---|---|---|---|
| `df_base_sem_escola` | sim | sim | — | — |
| `df_base_final` | sim | sim | — | sim |
| `df_master_no_atend` | sim | sim | sim | sim |
| `df_filt` | sim | sim | sim | sim |
| `df_filt_no_escola` | sim | sim | sim | IMUNE |

Regra adicional: se `selected_years_comp` estiver vazio, `df_base_sem_escola` torna-se `pd.DataFrame()` vazio.

---

## 6. Componentes da Página

### 6.1 Filtros Aplicados (placeholder)

- `filters_placeholder = st.empty()` declarado no topo.
- Preenchido com `format_filters_applied(selections, df, [("ano","Ano","Ano"), ("urg","URG","URG"), ("escola","Escola","Escola"), ("tipo","Tipo","Tipo")])`.

### 6.2 Indicadores Gerais (Cards Estáticos)

Renderizados via `render_metric_cards([...])` (três cards):

| Card | Origem |
|---|---|
| TOTAL DE ALUNOS | `df_home_filt["QtdAlunoEscola"].sum()` |
| ALUNOS ATENDIDOS | `df_home_filt["QtdAluno"].sum()` |
| ATEND. MÉDICO | `df_filt["Quantidade"].sum()` |

`df_home_filt` aplica filtros de Ano (`selected_years_comp`), URG (`urgs_aplicadas` = `selections["urg"]`) e Escola (`selections["escola"]`) sobre `df_home`.

Se `df_filt` está vazio: mensagem `"Selecione ao menos um ano para visualizar os indicadores."`.

### 6.3 Tabela Performance por URG (Mestre de Seleção)

**Base:** `df_for_urg_table` = `df` filtrado apenas por `selected_years_comp` (sensível apenas a Ano).

- `build_comparativo_anual(df_for_urg_table, "URG", active_row_value=current_selected_urgs)`.
- `prepare_comparativo_aggrid_data` + `split_aggrid_footer` (rodapé fixo com TOTAL via `pinnedBottomRowData`).
- Seleção múltipla com `rowMultiSelectWithClick`. JS `onFirstDataRendered` (`sync_selection_js`) destaca URGs ativas.
- Wrapper `<div class="selection-master-table">`.
- Toolbar: container `medico_urg_actions_toolbar` → `render_table_toolbar(df, "performance_urg_medico.csv", "urg_table_medico")`.
- Key dinâmico: `urg_table_medico_{join(sorted(urgs))}` ou `urg_table_medico_none`; armazena anterior em `_prev_urg_table_key_medico` (stale-guard).
- Caption: "Clique em qualquer linha de URG para filtrar o restante do dashboard. Esta tabela é sensível apenas ao filtro de Ano."

**Sync URG (bidirecional):**

| Origem | Ação |
|---|---|
| Sidebar → Tabela | `apply_pending_table_filters()` + `onFirstDataRendered` JS |
| Tabela → Sidebar | `set(new_urgs) != set(current_urgs)` → `global_urgs` + `pending_sidebar_urg_filter` + `last_interaction_source="table"` + `rerun()` |

Linha `TOTAL` excluída da propagação (`str(row.get(urg_field)) != "TOTAL"`).

### 6.4 Tabela Top Escolas por URG (Mestre de Seleção)

**Base:** `df_filt_no_escola` filtrado por `selected_years_comp`.

- `render_top_por_urg(..., "Quantidade", "Principais Escolas por URG", "Escola", table_key="escola_table_selection_medico", active_row_value=st.session_state.get("sidebar_escola_filter", []), selection_mode="multiple")`.
- Toolbar gerada internamente com key derivada (`escola_table_selection_medico_actions_toolbar`).

**Sync Escola (bidirecional):**

- `sync_sidebar_escola_selection("escola_table_selection_medico")` propaga sidebar→tabela antes da renderização.
- Pós-render: se `set(escolas_tabela_atual) != set(current_sidebar_escolas)` → `pending_sidebar_escola_filter` + `last_interaction_source="table_escola"` + `rerun()`.
- Ao final: `last_interaction_source = ""` (zera origem).

### 6.5 Distribuição por URG (Gráfico)

**Base:** `df_filt`, agrupado por `["URG","Ano"]` somando `Quantidade`.

- Ordenação por numeral romano via `_urg_sort_key` (utilitário local), depois por Ano.
- `px.bar(..., x="URG", y="Quantidade", color="Ano", barmode="group", text=_text_fmt)`.
- Label formatada com separador de milhar `.` (PT-BR).
- `hovermode="x unified"`, hover customizado `"<b>URG:</b> %{x}<br><b>Quantidade:</b> %{text}"`.

### 6.6 Detalhamento por Aluno (AgGrid)

**Base de construção:**
1. `filter_by_sidebar_selections(df_aluno, selections)` (aplica Ano, URG, Escola, Tipo).
2. Filtra por `selected_years_comp`.
3. Filtros locais inline (multiselect): Aluno, Série, Turma. Chaves: `medico_aluno_multiselect`, `medico_serie_multiselect`, `medico_turma_multiselect`.

**Pipeline de construção (`df_aluno_final`):**
1. `df_static = groupby(["ID","Aluno"]).last()` sobre `[DataNascimento, Sexo, Profissional, URG, Escola, Serie, Turma]`.
2. `df_counts = groupby(["ID","Ano"]).size()` → coluna `Qtd`.
3. `df_pivot_ano = pivot(index="ID", columns="Ano", values="Qtd").fillna(0)`.
4. Merge estático + pivot por `ID`.
5. Coluna `Total = soma das colunas de ano`.
6. Formatação: zeros viram string vazia; inteiros viram texto.
7. `Menu` (renomeado para `Perfil`) gerado por `build_perfil_link(row)` → `?menu=Aluno&aluno=<Nome>&nasc=YYYY-MM-DD`.
8. `DataNascimento` formatada como `dd/mm/yyyy`.

**Ordem de colunas:** `ID | Aluno | DataNascimento | Sexo | Profissional | URG | Escola | Serie | Turma | [anos...] | Total | Perfil`.

**Renderização:** `render_aluno_detalhamento_aggrid(df_aluno_head, key="aluno_table_medico", csv_name="detalhes_alunos_medico.csv", toolbar_key="medico_aluno_actions_toolbar")`.

**Limite:** `preview_limit = 500`; aviso se `total_registros_aluno > preview_limit`.

---

## 7. Título Dinâmico dos Indicadores

```
### Indicadores Gerais (Anos: X / URGs: X / Escolas: X)
```

Construído via `get_filter_display_string_for_title(selected_list, all_available_list)`: `"Todos"` quando seleção corresponde a tudo ou está vazia; senão lista ordenada separada por `, `.

---

## 8. Estado Global e Chaves de Session State

### Chaves globais

| Chave | Tipo | Descrição |
|---|---|---|
| `global_years` | `list[int]` | Anos selecionados (fonte de verdade) |
| `global_urgs` | `list[str]` | URGs selecionadas (fonte de verdade) |
| `sidebar_year_filter` | `list[int]` | Espelho widget Ano |
| `sidebar_urg_filter` | `list[str]` | Espelho widget URG |
| `sidebar_escola_filter` | `list[str]` | Espelho widget Escola |
| `home_year_buttons` | `list[int]` | Estado do segmented_control |
| `last_interaction_source` | `str` | `""`, `"sidebar"`, `"table"`, `"table_escola"` |
| `pending_sidebar_urg_filter` | `list[str]` | Pendência URG tabela→sidebar |
| `pending_sidebar_escola_filter` | `list[str]` | Pendência Escola tabela→sidebar |

### Chaves locais

| Chave | Descrição |
|---|---|
| `medico_atendimento_multiselect` | (Declarada via toggle, sem UI ativa) |
| `medico_aluno_multiselect` | Filtro inline Aluno |
| `medico_serie_multiselect` | Filtro inline Série |
| `medico_turma_multiselect` | Filtro inline Turma |
| `escola_table_selection_medico__selected_values` | Escolas selecionadas na tabela |
| `_prev_urg_table_key_medico` | Stale-guard da AgGrid de URG |
| `_is_page_first_run` | Flag de primeira renderização |
| `massive_year_selector` | Container do seletor mestre |

### Toolbars (containers de UI)

- `medico_urg_actions_toolbar`
- `escola_table_selection_medico_actions_toolbar`
- `medico_cobertura_actions_toolbar` (declarada em CSS; sem container correspondente nesta versão)
- `medico_aluno_actions_toolbar`

---

## 9. Regras de Sincronismo — Fluxo

```
RENDER
  ├─ init_global_state()
  ├─ apply_pending_table_filters()
  │    ├─ pending_sidebar_urg_filter → sidebar_urg_filter + global_urgs
  │    └─ pending_sidebar_escola_filter → sidebar_escola_filter
  ├─ sidebar_filters()
  ├─ sync_sidebar_escola_selection("escola_table_selection_medico")
  ├─ segmented_control on_change=sync_home_to_sidebar
  ├─ [renderiza componentes]
  ├─ URG table response: seleção mudou → pending_sidebar_urg_filter + last="table" → rerun()
  └─ Escola sync: seleções diferem → pending_sidebar_escola_filter + last="table_escola" → rerun()
     final: last_interaction_source = ""
```

---

## 10. Exportação de Dados

- Toolbars usam `render_table_toolbar(df_export, "<nome>.csv", "<key>")` com botões `Copiar` + `CSV` agrupados.
- CSVs por tabela:
  - URG: `performance_urg_medico.csv`
  - Aluno: `detalhes_alunos_medico.csv`
- Export consolida `df_cmp_urg_body + footer_rows` quando há TOTAL.

---

## 11. Cache e Performance

- **Redis Integration:** Conforme [Redis Cache Spec](redis_cache_spec.md).
- **Datasets cacheáveis:**
  - `saedas:medico:dataset:main` → `data/DashboardMedico.csv`
  - `saedas:medico:dataset:aluno` → `data/DashboardMedicoAluno.csv`
  - `saedas:medico:dataset:ano` → `data/DashboardMedicoAno.csv`
  - `saedas:home:dataset:main` (reaproveitado) → `data/DashboardHome.csv`
- **Invalidação:** TTL de 12 horas ou via scripts de integração.

---

## 12. Estilos e CSS Específicos

Injetados via `st.markdown(..., unsafe_allow_html=True)` no início de `page_medico()`:

- Cards: `.home-metric-card`, `.metric-card-static`, `.home-metric-label`, `.home-metric-value`.
- Botões KPI: `div[class*="st-key-btn_kpi_"] button` (com variação `[kind="primary"]`).
- Toolbars (seletores agrupados):
  - `.st-key-medico_urg_actions_toolbar`
  - `.st-key-escola_table_selection_medico_actions_toolbar`
  - `.st-key-medico_cobertura_actions_toolbar`
  - `.st-key-medico_aluno_actions_toolbar`
- Botões Copiar/Download com bordas arredondadas nas extremidades (`6px 0 0 6px` / `0 6px 6px 0`).
