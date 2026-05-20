# Especificação Técnica — Página Nutrição

A página Nutrição (`app/app_pages/nutricao.py`, função `page_nutricao()`) monitora o estado nutricional dos alunos (Peso, Altura, IMC) e classifica as ocorrências por Situação Nutricional na rede SAEDAS, com suporte a navegação cruzada entre URG, Escola e KPIs.

---

## 1. Visão Geral e Propósito
- **Objetivo:** Identificar e monitorar alunos em risco nutricional por URG, Escola e categoria.
- **Foco:** Distribuição antropométrica por Situação Nutricional, com prevalência por ano e detalhamento aluno a aluno.
- **Título:** "Visão Geral da Nutrição".

---

## 2. Fontes de Dados e Schemas
Datasets carregados em `carregar_dados_nutricao()` com cache Redis (`redis_cache.get_dataframe_with_timestamp` / `set_dataframe_with_timestamp`):

| Key | CSV | Schema | Redis Key |
|---|---|---|---|
| `principal` | `data/DashboardNutricao.csv` | `SCHEMA_NUTRICAO` | `saedas:nutricao:dataset:main` |
| `aluno` | `data/DashboardNutricaoAluno.csv` | `SCHEMA_NUTRICAO_ALUNO` | `saedas:nutricao:dataset:aluno` |
| `ano` | `data/DashboardNutricaoAno.csv` | `SCHEMA_NUTRICAO_ANO` | `saedas:nutricao:dataset:ano` |
| `home` | `data/DashboardHome.csv` | `SCHEMA_HOME` | `saedas:home:dataset:main` |

### 2.1 Colunas relevantes
- `SCHEMA_NUTRICAO`: `Ano, URG, Escola, Tipo, Nutricao, Qtd, IdUrg` (renomeada `Qtd → Quantidade`).
- `SCHEMA_NUTRICAO_ALUNO`: `Ano, Aluno, DtNasc, Sexo, Peso, Altura, IMC, Nutricao, IdUrg, URG, Escola, Tipo, Serie, Turma` (renomeada `DtNasc → DataNascimento`; `Peso → Peso (kg)`; `Altura → Altura (m)`).
- `SCHEMA_NUTRICAO_ANO`: `URG, Escola, Nutricao, 2022..2026, Total`.
- `SCHEMA_HOME`: usado para `QtdAlunoEscola` e `QtdAluno` (denominadores demográficos).

---

## 3. Filtros e Estado

### 3.1 Sidebar (`sidebar_filters`)
Chamada com `{"ano": True, "urg": True, "escola": True, "tipo": True}`. Título: "Filtros - Nutrição".

### 3.2 Filtro específico de Nutrição
- Widget: `st.sidebar.multiselect(... key="nutricao_situacao_multiselect", on_change=sync_local_nutricao_situacao)`.
- Opções: valores únicos da coluna `Nutricao`.
- Persistência cross-page: `persistent_nutricao_situacao` (restaurada quando o Streamlit poda o widget).

### 3.3 Seletor Temporal Mestre
- Container `key="massive_year_selector"`, widget `st.segmented_control` com `key="home_year_buttons"`.
- Opções: ano corrente e os 4 anteriores (`current_year - i for i in range(5)`).
- Callback: `sync_home_to_sidebar` → atualiza `global_years` e `sidebar_year_filter`.

### 3.4 Estado Global (`init_global_state`, `state_manager`)
- `global_years`, `global_urgs` — fontes únicas de verdade.
- `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`.
- Pendências de tabela: `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter` (consumidas por `apply_pending_table_filters`).
- Controle de origem: `last_interaction_source` (`sidebar`, `table`, `table_escola`).
- Sincronismo Escola: `sync_sidebar_escola_selection("escola_table_selection_nutricao")`.
- KPI / sidebar Nutrição: `nutricao_situacao_multiselect` ↔ `persistent_nutricao_situacao`.
- Chave dinâmica AgGrid URG: `urg_table_nutricao_{anos}_{nuts}_{urgs}` com guarda `_prev_urg_table_key_nutricao` e `_is_page_first_run`.

### 3.5 Bases derivadas
- `df_base_sem_escola`: aplica `Tipo` e `Ano`. Base do indicador URG (imune a Escola/URG).
- `df_base_final`: `df_base_sem_escola` + Escola.
- `df_master_no_nut`: `df_base_final` + URG (sem aplicar `Nutricao`).
- `df_master_filtrado` / `df_filt`: `df_master_no_nut` + `nutricoes_selecionadas`.
- `df_filt_no_escola`: `df_base_sem_escola` + URG (para Top Escolas).
- `df_filt_no_nut`: alias de `df_master_no_nut` para cards/tabela comparativa.

---

## 4. Componentes de Interface

### 4.1 Filtros Aplicados (Header)
- `filters_placeholder.markdown` no topo via `format_filters_applied(selections, df, [...ano, urg, escola, tipo, nutricao...])`.
- Subtítulo dinâmico `### Indicadores Gerais ({filtro_titulo})` no formato `Anos: X / URGs: Y / Escolas: Z / Nutrição: W`.

### 4.2 Cards Demográficos (Estáticos)
Via `render_metric_cards`, lendo `df_home_filt = filter_by_sidebar_selections(df_home, selections)`:
- TOTAL DE ALUNOS — soma `QtdAlunoEscola`.
- ALUNOS ATENDIDOS — soma `QtdAluno`.
- TOTAL DE REGISTROS DE NUTRIÇÃO — soma `Quantidade` em `df_master_no_nut` (imune ao filtro de Situação).

### 4.3 KPI Toggle por Situação Nutricional
- Base: `df_filt_no_nut.groupby("Nutricao")["Quantidade"].sum()` ordenada desc, filtrando `>0`.
- Renderização em chunks de 5 via `render_metric_cards(..., is_toggle=True, active_labels=[...uppercase], on_click_callback=toggle_nutricao)`.
- `toggle_nutricao` usa `toggle_multiselect_value` e propaga para `persistent_nutricao_situacao`.

### 4.4 Tabela Comparativa de Performance por ANO (Nutrição)
- Base: `build_comparativo_anual(df_filt, "Nutricao", value_col="Quantidade", pct_label="Total")`.
- Reordenação para espelhar a ordem dos KPIs gerais (`_ordem_kpi`) e fixar `TOTAL` no final (`_is_total`).
- Toolbar container: `nutricao_ano_actions_toolbar`; key da tabela: `ano_perf_table_nutricao` / `ano_perf_table_nutricao_aggrid`.
- Export: `comparativo_performance_ano_nutricao.csv`.
- Wrapper: `.st-table-with-total`; `pinnedBottomRowData` via `split_aggrid_footer`.
- Caption: explica "% Total" (percentual no ano) e "Var%" (variação ano anterior).

### 4.5 Tabela Performance por URG (Mestre)
- Base: `df_for_urg_table = df_base_sem_escola` + filtro `Nutricao` (imune ao próprio filtro de URG/Escola).
- `build_comparativo_anual(df_for_urg_table, "URG", active_row_value=current_selected_urgs)`.
- `rowSelection: "multiple"`, `rowMultiSelectWithClick: True`.
- Sync visual: `onFirstDataRendered` (JsCode) marca linhas conforme `global_urgs`.
- Toolbar container: `nutricao_urg_actions_toolbar`; export: `performance_urg_nutricao.csv`.
- Key dinâmica AgGrid: `urg_table_nutricao_{years}_{nuts}_{urgs}`.
- Cross-filter → atualiza `global_urgs`, agenda `pending_sidebar_urg_filter`, marca `last_interaction_source = "table"` e `st.rerun()`.
- Wrapper: `.selection-master-table`.

### 4.6 Top Escolas por URG
- Função: `render_top_por_urg(df_for_top_escolas[...], "Quantidade", "Principais Escolas por URG", "Escola", table_key="escola_table_selection_nutricao", selection_mode="multiple", active_row_value=sidebar_escola_filter)`.
- Base: `df_filt_no_escola` + `nutricoes_selecionadas` + filtro de anos `selected_years_comp`.
- Sync seleção → `pending_sidebar_escola_filter`, `last_interaction_source = "table_escola"`, `st.rerun()`.
- Toolbar container gerado automaticamente: `escola_table_selection_nutricao_actions_toolbar`.

### 4.7 Gráficos
- "Comparativo Anual de Nutrição por URG" — `render_grouped_bar_anual(df_filt, "Quantidade", "", orientation="h")`.
- "Distribuição por Situação Nutricional" — `render_grouped_bar_anual(df_filt, "Quantidade", "", x_col="Nutricao", orientation="h")`.

### 4.8 Detalhamento por Aluno
- Base: `filter_by_sidebar_selections(df_aluno, selections)` + filtro `Ano in selected_years_comp` + filtro `Nutricao` (se houver).
- Filtros locais (multiselect): Aluno, Série, Turma (cascateados sobre `df_aluno_filtrado`).
- Caption com contagem: "{n} registros após filtros da sidebar [e de nutrição]".
- Construção de link de perfil (`build_perfil_link`): URL `?menu=Aluno&aluno={nome}[&nasc=YYYY-MM-DD]`.
- Preparação via `prepare_nutricao_aluno_table(df_aluno_filtrado, build_perfil_link, selected_nuts=selected_nuts_from_table)`:
  - Pivot por `Ano` das métricas `Peso (kg)`, `Altura (m)`, `IMC`, `Idade`, `Nutricao`.
  - `Idade = Ano - year(DataNascimento)`.
  - Formatação BR (vírgula decimal) para Peso/Altura/IMC; inteiro para Idade.
  - `Nutricao` em UPPERCASE quando ∈ `selected_nuts`; caso contrário capitalizada.
  - Colunas estáticas: `Aluno, DataNascimento, Sexo, URG, Escola, Serie, Turma, Menu` (Menu→`Perfil`).
- Render: `render_aluno_detalhamento_aggrid(df_aluno_final, key="aluno_table_nutricao", csv_name="detalhes_alunos_nutricao.csv", toolbar_key="nutricao_aluno_actions_toolbar")`.

---

## 5. Regras de Negócio
- **Imunidade dos cards de Situação:** usam `df_filt_no_nut` para preservar o catálogo de categorias mesmo com filtro ativo.
- **Imunidade do indicador "TOTAL DE REGISTROS DE NUTRIÇÃO":** soma `Quantidade` em `df_master_no_nut`.
- **Tabela mestre URG:** imune aos filtros de URG e Escola; sensível a Ano, Tipo e Situação Nutricional.
- **Tabela mestre Escola:** imune ao próprio filtro de Escola.
- **Tabela comparativa ANO (Nutrição):** ordem dos KPIs preservada; `TOTAL` no final.
- **Demográficos:** `total_alunos_escola`/`total_alunos_atendidos` extraídos de `df_home_filt`.
- **Cobertura via Var%/% Total:** delegados a `build_comparativo_anual`.

---

## 6. Observações Técnicas
- **CSS escopado:** estilos `.home-metric-card`, `.metric-card-static`, `.home-metric-label`, `.home-metric-value`, `div[class*="st-key-btn_kpi_"] button`, e regras para os containers `nutricao_urg_actions_toolbar`, `nutricao_ano_actions_toolbar`, `escola_table_selection_nutricao_actions_toolbar`, `nutricao_aluno_actions_toolbar`, `nutricao_simple_actions_toolbar`.
- **Toolbars:** sempre via `render_table_toolbar` agrupando `Copiar` + `CSV` (exportação `;` + `utf-8-sig`).
- **AgGrid:** `render_saedas_aggrid` com altura adaptativa (cap 20 linhas), `split_aggrid_footer` para `TOTAL`.
- **Wrappers:** `.selection-master-table` (URG e Top Escolas), `.st-table-with-total` (Comparativo ANO).
- **Schemas:** importados de `app.utils.schemas`.

---

## 7. Cache e Performance
- **Redis Integration:** ver [Redis Cache Spec](redis_cache_spec.md).
- **Smart Cache:** invalidação automática via timestamp do CSV (`get_dataframe_with_timestamp`).
- **Chaves em Nutrição:**
    - `saedas:nutricao:dataset:main`
    - `saedas:nutricao:dataset:aluno`
    - `saedas:nutricao:dataset:ano`
    - `saedas:home:dataset:main` (reaproveitado)
