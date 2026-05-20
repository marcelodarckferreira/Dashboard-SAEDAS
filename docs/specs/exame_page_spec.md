# Spec: Página de Exames (Regulação)

**Arquivo:** `app/app_pages/exame.py`
**Função de entrada:** `page_exame()`
**Título:** Visão Geral dos Exames (Regulação)

---

## 1. Fontes de Dados

Carregadas em `carregar_dados_exame()` com Smart Cache Redis (fallback para disco via `load_csv`).

| Variável | Arquivo CSV | Schema | Chave Redis |
|---|---|---|---|
| `df` (principal) | `data/DashboardExame.csv` | `SCHEMA_EXAME` | `saedas:exame:dataset:main` |
| `df_aluno_raw` | `data/DashboardExameAluno.csv` | `SCHEMA_EXAME_ALUNO` | `saedas:exame:dataset:aluno` |
| `df_ano` | `data/DashboardExameAno.csv` | `SCHEMA_EXAME_ANO` | `saedas:exame:dataset:ano` |
| `df_home` | `data/DashboardHome.csv` | `SCHEMA_HOME` | `saedas:home:dataset:main` (reaproveitado) |

### Renomeação de colunas após carga

| CSV original | Nome interno |
|---|---|
| `Exame` (principal) | `Regulacao` |
| `Qtd` | `Quantidade` |
| `Exame` (aluno) | `Regulacao` |
| `DtNasc` | `DataNascimento` |

`DataNascimento` é convertida via `pd.to_datetime(..., errors="coerce")`.

---

## 2. Filtros da Sidebar

Ativados via `sidebar_filters(df, {"ano": True, "urg": True, "escola": True, "tipo": True})`.

| Filtro | Chave session_state | Origem |
|---|---|---|
| Ano(s) | `sidebar_year_filter` | `sidebar_filters` |
| URG(s) | `sidebar_urg_filter` | `sidebar_filters` |
| Escola(s) | `sidebar_escola_filter` | `sidebar_filters` |
| Tipo(s) | (via `selections["tipo"]`) | `sidebar_filters` |
| Regulação(ões) | `exame_regulacao_multiselect` | multiselect direto na sidebar com callback `sync_local_exame_regulacao` |

O filtro de Regulação é persistido em `persistent_exame_regulacao` (restaurado se o Streamlit podar a chave do widget na navegação).

---

## 3. Seletor Temporal Mestre

- Container `massive_year_selector` com `st.segmented_control` (multi).
- Opções: `[current_year, current_year-1, ..., current_year-4]`.
- Key: `home_year_buttons`; callback: `sync_home_to_sidebar`.
- Fonte de verdade do ano selecionado: `st.session_state["global_years"]`.

---

## 4. Hierarquia de Bases de Dados

```
df (bruto, renomeado)
 └─► df_base_sem_escola      [filtros: Tipo, Ano]
      └─► df_base_final      [filtros: + Escola]
           └─► df_master_no_reg  [filtros: + URG]
                └─► df_filt            [filtros: + Regulação]
                └─► df_filt_no_reg     [= df_master_no_reg, imune a Regulação]

df_base_sem_escola
 └─► df_filt_no_escola         [filtros: + URG (sem Escola, sem Regulação)]
 └─► df_filt_no_urg_no_escola  [= df_base_sem_escola, sem URG e sem Escola]
```

### Matriz de imunidade

| Base | Tipo | Ano | URG | Escola | Regulação |
|---|---|---|---|---|---|
| `df_base_sem_escola` | ✓ | ✓ | — | — | — |
| `df_base_final` | ✓ | ✓ | — | ✓ | — |
| `df_master_no_reg` | ✓ | ✓ | ✓ | ✓ | — |
| `df_filt` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `df_filt_no_reg` | ✓ | ✓ | ✓ | ✓ | **IMUNE** |
| `df_filt_no_escola` | ✓ | ✓ | ✓ | **IMUNE** | — |
| `df_filt_no_urg_no_escola` | ✓ | ✓ | **IMUNE** | **IMUNE** | — |

Se `selected_years_comp` estiver vazio, `df_base_sem_escola` torna-se `pd.DataFrame()` (zerando o restante).

---

## 5. Componentes e Regras

### 5.1 Filtros Aplicados (placeholder)

Renderizado com `st.empty()` antes de qualquer componente; preenchido por `format_filters_applied(selections, df, [...])` com Ano, URG, Escola, Tipo, Regulação.

### 5.2 Indicadores Gerais (Cards Estáticos)

| Card | Origem | Imune a Regulação |
|---|---|---|
| TOTAL DE ALUNOS | `df_home_filt["QtdAlunoEscola"].sum()` | ✓ |
| ALUNOS ATENDIDOS | `df_home_filt["QtdAluno"].sum()` | ✓ |
| TOTAL DE EXAMES | `df_filt_no_reg["Quantidade"].sum()` | ✓ |

`df_home_filt = filter_by_sidebar_selections(df_home, selections)`.

### 5.3 KPI Cards de Regulação (Toggle)

**Base:** `df_filt_no_reg` → `regulacoes_sum = groupby("Regulacao")["Quantidade"].sum()` ordenado desc; apenas `> 0`.

- Renderizados em blocos de 5 por linha via `render_metric_cards(..., is_toggle=True, on_click_callback=toggle_regulacao)`.
- Cards ativos passam `active_labels=[l.upper() for l in regulacoes_selecionadas]`.
- `toggle_regulacao(reg_name)` alterna em `exame_regulacao_multiselect` via `toggle_multiselect_value` e propaga para `persistent_exame_regulacao`.
- Quando `regulacoes_sum` está vazio: `st.info("Selecione ao menos um ano...")`.

### 5.4 Tabela Comparativa de Performance por ANO (Exames)

**Base:** `df_filt`.

- `build_comparativo_anual(df_filt, "Regulacao", value_col="Quantidade", pct_label="Total")`.
- `prepare_comparativo_aggrid_data(..., include_selection_column=False)` + `split_aggrid_footer(...)`.
- Ordenação das linhas: segue ordem dos KPI cards (`regulacoes_sum`), TOTAL sempre ao final (`_is_total` + `_ordem_kpi`).
- `_ajustar_colunas_ano_exames`: renomeia header `Regulacao` para `Regulação`, alinha à esquerda (`saedas-aggrid-left-header`); colunas de ano recebem `saedas-aggrid-centered-header`.
- `pinnedBottomRowData = ano_perf_footer`.
- Toolbar: container `exame_ano_actions_toolbar` com `render_table_toolbar(..., "comparativo_performance_ano_exames.csv", "ano_perf_table_exame")`.
- Render: `render_saedas_aggrid(..., key="ano_perf_table_exame_aggrid", incluir_total=bool(footer), min_height=140)`.
- Caption explica `% Total` e `Var%`.

### 5.5 Tabela Performance por URG (Mestre)

**Base:** `df_for_urg_table = df_filt_no_urg_no_escola` filtrado adicionalmente por Regulação (se houver).

- `build_comparativo_anual(..., "URG", active_row_value=current_urgs)`.
- `prepare_comparativo_aggrid_data(...)` (com coluna de seleção) + `split_aggrid_footer(...)`.
- `rowSelection="multiple"`, `rowMultiSelectWithClick=True`.
- JS `onFirstDataRendered`: sincroniza visualmente seleção a partir de `current_urgs` (set comparando `node.data[urg_field]`).
- Key dinâmico: `urg_table_exame_{years}_{regs}_{urgs}` — stale-guard via `_prev_urg_table_key_exame`.
- Wrapper CSS: `.selection-master-table`.
- Toolbar: container `exame_urg_actions_toolbar`, arquivo `performance_urg_exame.csv`, key prefix `urg_table_exame`.
- Caption: "sensível apenas ao filtro de Ano".

**Sync URG (tabela → sidebar):** se `set(new_urgs) != set(current_urgs)` → seta `global_urgs`, `pending_sidebar_urg_filter`, `last_interaction_source="table"` e `st.rerun()`.

### 5.6 Tabela Top Escolas por URG (Mestre)

**Base:** `df_filt_no_escola` filtrado por Regulação (se houver) e por `selected_years_comp`.

- `render_top_por_urg(..., "Quantidade", "Principais Escolas por URG", "Escola", table_key="escola_table_selection_exame", active_row_value=st.session_state.get("sidebar_escola_filter", []), selection_mode="multiple")`.
- Toolbar gerada internamente: `escola_table_selection_exame_actions_toolbar`.

**Sync Escola (tabela → sidebar):** se `escola_table_selection_exame__selected_values` diferir de `sidebar_escola_filter` → seta `pending_sidebar_escola_filter`, `last_interaction_source="table_escola"`, `st.rerun()`. Ao final do bloco: `last_interaction_source = ""`.

**Sync Escola (sidebar → tabela):** `sync_sidebar_escola_selection("escola_table_selection_exame")` antes da renderização das tabelas.

### 5.7 Gráficos

- **Comparativo Anual de Exames por URG:** `render_grouped_bar_anual(df_filt, "Quantidade", "", orientation="h")`.
- **Distribuição por Regulação:** `render_grouped_bar_anual(df_filt, "Quantidade", "", x_col="Regulacao", orientation="h")`.

### 5.8 Detalhamento por Aluno

**Base de construção:**
1. `filter_by_sidebar_selections(df_aluno, selections)` → Ano, URG, Escola, Tipo.
2. Filtra por `selected_years_comp`.
3. Filtra por `selections["escola"]` (efetiva).
4. Filtra por `regulacoes_selecionadas` (se houver).

**Filtros locais inline (multiselect):** Aluno, Série, Turma.

**Construção:**
- `df_static`: agrupado por `(Aluno, DataNascimento)`, mantém `Sexo, URG, Escola, Serie, Turma` (`.last()`).
- `df_desc`: agrupa `(Aluno, DataNascimento, Ano)` aplicando `format_reg_list` (lista de regulações capitalizadas, separadas por `, `).
- `df_pivot_ano`: pivot Ano × Descrição.
- `df_counts_total`: contagem total de registros por aluno.
- Merge final + coluna `Total` (string formatada) + coluna `Menu` (URL `?menu=Aluno&aluno=Nome&nasc=YYYY-MM-DD`) renomeada para `Perfil`.
- `DataNascimento` formatada `dd/mm/YYYY`.

**Ordem das colunas:** `Aluno | DataNascimento | Sexo | URG | Escola | Serie | Turma | [anos...] | Total | Perfil`.

**Renderização:** `render_aluno_detalhamento_aggrid(df, key="aluno_table_exame", csv_name="detalhes_alunos_exame.csv", toolbar_key="exame_aluno_actions_toolbar")`.

---

## 6. Título Dinâmico dos Indicadores

```
### Indicadores Gerais (Anos: X / URGs: X / Escolas: X / Regulações: X)
```

Construído com `get_filter_display_string_for_title(...)`: `"Todos"` quando seleção vazia ou == universo; lista ordenada caso contrário.

---

## 7. Estado Global e Chaves de Session State

### Globais (compartilhadas entre páginas)

| Chave | Tipo | Descrição |
|---|---|---|
| `global_years` | `list[int]` | Anos selecionados |
| `global_urgs` | `list[str]` | URGs selecionadas |
| `sidebar_year_filter` | `list[int]` | Espelho do widget |
| `sidebar_urg_filter` | `list[str]` | Espelho do widget |
| `sidebar_escola_filter` | `list[str]` | Espelho do widget |
| `home_year_buttons` | `list[int]` | Espelho do segmented control |
| `last_interaction_source` | `str` | `""`, `"sidebar"`, `"table"`, `"table_escola"` |
| `pending_sidebar_urg_filter` | `list[str]` | Pendência tabela→sidebar (URG) |
| `pending_sidebar_escola_filter` | `list[str]` | Pendência tabela→sidebar (Escola) |
| `_is_page_first_run` | `bool` | Flag de primeira renderização |

### Locais da página Exame

| Chave | Descrição |
|---|---|
| `exame_regulacao_multiselect` | Regulações selecionadas (widget) |
| `persistent_exame_regulacao` | Persistência entre navegações (set em `init_global_state`) |
| `escola_table_selection_exame__selected_values` | Escolas selecionadas na tabela mestre |
| `escola_table_selection_exame__aggrid_key` | Stale-guard da AgGrid de escolas |
| `escola_table_selection_exame__prev_sidebar_escola_filter` | Prev value para detecção |
| `_prev_urg_table_key_exame` | Stale-guard da AgGrid de URG |

### Containers/Toolbars (keys CSS)

- `massive_year_selector`
- `exame_ano_actions_toolbar`
- `exame_urg_actions_toolbar`
- `exame_aluno_actions_toolbar`
- `escola_table_selection_exame_actions_toolbar`

---

## 8. Exportação de Dados

- Cada AgGrid possui toolbar `render_table_toolbar` com botões "📋 Copiar" (TSV via clipboard JS) e "⬇️ CSV" (Blob JS, sem rerun).
- Arquivos:
  - Comparativo Ano: `comparativo_performance_ano_exames.csv`
  - Performance URG: `performance_urg_exame.csv`
  - Top Escolas: `top_escola_por_urg.csv` (padrão de `render_top_por_urg`)
  - Detalhamento Aluno: `detalhes_alunos_exame.csv`
- Ver detalhes em [Shared Components Spec](shared_components_spec.md).

---

## 9. Cache e Performance

- **Smart Cache Redis:** `redis_cache.get_dataframe_with_timestamp(redis_key, csv_path)`; em miss, recarrega via `load_csv` e persiste com `set_dataframe_with_timestamp`.
- **Invalidação:** automática por comparação de timestamp do arquivo físico (ver [Redis Cache Spec](redis_cache_spec.md)).
- **Chaves Redis:** `saedas:exame:dataset:main`, `saedas:exame:dataset:aluno`, `saedas:exame:dataset:ano`, `saedas:home:dataset:main`.

---

## 10. Estilos Críticos Injetados

Bloco `<style>` local define:
- Classes `.home-metric-card`, `.metric-card-static`, `.home-metric-label`, `.home-metric-value`.
- Botões KPI: `div[class*="st-key-btn_kpi_"] button` (altura, gradientes, hover, primary).
- Toolbars agrupadas (`gap: 0`, sem padding, raio de borda nas extremidades) para keys:
  `exame_urg_actions_toolbar`, `exame_ano_actions_toolbar`, `exame_aluno_actions_toolbar`, `escola_table_selection_exame_actions_toolbar`.
