# Especificação Técnica — Página Início (Home)

A página Início é o centro de inteligência do SAEDAS, fornecendo uma visão consolidada de todos os indicadores e servindo como navegador principal para as demais seções do sistema. Implementada em `app/app_pages/home.py` na função `page_home()`.

---

## 1. Visão Geral e Propósito
- **Objetivo:** Fornecer KPIs em tempo real, tabelas comparativas (por Ano, URG e Escola), gráficos de cobertura/distribuição e uma tabela de Detalhamento das escolas.
- **Navegação:** Cards de indicadores (azuis) levam, via querystring `/?menu={Menu}`, às páginas correspondentes (`Encaminhamentos`, `Exames`, `Vacinação`, `Médico`, `Professor`, `Psicólogo`, `Assistente Social`, `Enfermagem`).
- **Cross-Filtering:** Seleção de linhas nas tabelas mestre de URG e Escola filtra todo o dashboard e sincroniza com a sidebar.

---

## 2. Fontes de Dados e Schemas
Carregamento centralizado em `carregar_dados_home()` com suporte a cache via `redis_cache.get_dataframe_with_timestamp()` / `set_dataframe_with_timestamp()`:

| Dataset (key) | Arquivo | Schema | Chave Redis |
|---|---|---|---|
| `home` | `data/DashboardHome.csv` | `SCHEMA_HOME` | `saedas:home:dataset:main` |
| `escola_ano` | `data/DashboardHomeEscolaAno.csv` | `SCHEMA_HOME_ESCOLA_ANO` | `saedas:home:dataset:escola` |
| `home_ano` | `data/DashboardHomeAno.csv` | `SCHEMA_HOME_ANO` | `saedas:home:dataset:ano` |
| `urg_ano` | `data/DashboardHomeURGAno.csv` | `SCHEMA_HOME_URG_ANO` | `saedas:home:dataset:urg` |

### 2.1 Schemas
- **SCHEMA_HOME (master, base de toda análise):** `Ano`, `URG`, `Escola`, `DtInicio`, `DtFechamento`, `QtdAluno`, `QtdProfessor`, `QtdPsicologo`, `QtdAssistSocial`, `QtdEnfermagem`, `QtdMedico`, `QtdVacinacao`, `QtdVacina`, `QtdEncaminhamento`, `QtdExame`, `QtdAlunoEscola`.
- **SCHEMA_HOME_ESCOLA_ANO:** `URG`, `Escola`, `Descricao`, `2022`–`2026`, `Total`.
- **SCHEMA_HOME_URG_ANO:** `URG`, `Descricao`, `2022`–`2026`, `Total`.
- **SCHEMA_HOME_ANO:** `Descricao`, `2022`–`2026`, `Total`.

> Observação: As tabelas exibidas (Performance por ANO/URG/Escola) são construídas dinamicamente a partir do dataset master (`df`). Os 3 datasets agregados (`home_ano`, `urg_ano`, `escola_ano`) são carregados/cacheados mas atualmente não são usados nas agregações renderizadas — servem como base para futuros usos e validação de schema.

---

## 3. Filtros e Estado Global

### 3.1 Inicialização
- `init_global_state()` (de `app.utils.state_manager`) cria as chaves base na primeira execução.
- `apply_pending_table_filters()` resolve pendências (`pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`) ANTES de renderizar a sidebar.

### 3.2 Filtros da Sidebar
- Configuração: `{"ano": True, "urg": True, "escola": True, "tipo": True}` via `sidebar_filters(df, home_filter_config)`.
- Retorna `df_filtrado` e o dict `selections` com chaves `ano`, `urg`, `escola`, `tipo`.

### 3.3 Seletor Temporal Mestre
- Container `st.container(key="massive_year_selector")` + `st.segmented_control` em modo `multi`.
- `options = sorted([current_year - i for i in range(5)], reverse=True)` (janela móvel de 5 anos a partir do ano atual do sistema).
- `key="home_year_buttons"`, `on_change=sync_home_to_sidebar`.
- Sincroniza `global_years` ⇄ `sidebar_year_filter`.

### 3.4 Chaves de `session_state`
- Globais: `global_years`, `global_urgs`.
- Widgets sidebar: `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`.
- Widget Home: `home_year_buttons`.
- Auxiliares: `last_interaction_source`, `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`, `_is_page_first_run`.
- Sincronia de tabelas: `_prev_urg_grid_key_home`, `_prev_escola_grid_key_home`, `_suppress_escola_key_change`, `last_df_cmp_urg_home`.
- Detalhamento: `home_table_height_option`, `home_show_column_selector`, `home_hidden_columns`, `home_toolbar_column_toggle`, `selected_schools_detalhamento`, `closing_date_filter_option`, `inicio_sem_fechamento_option`, `zero_value_cols_selected`.

### 3.5 Construção dos DataFrames de Trabalho
A partir do master `df`:
- `df_base_final`: cópia de `df` com filtros aplicados em cascata — Escola, Ano (`selected_years_comp`), URG (`current_urgs`).
- `df_master_filtrado`: igual a `df_base_final` somado o filtro de `Tipo`; é a fonte de verdade para KPIs, gráficos e detalhamento.
- `df_for_performance_table`: cópia de `df` filtrada apenas por Ano (imunidade a URG/Escola/Tipo) — usada nas tabelas Comparativa por URG e Escola por Ano.
- `df_home_ano_source`: cópia de `df` filtrada por URG + Escola + Tipo + Ano — usada na Tabela Comparativa por ANO.

### 3.6 Breadcrumb de Filtros
- `filters_placeholder` no topo, alimentado por `format_filters_applied(selections, df, [(ano,URG,...),...])`.
- Título dinâmico `filtro_titulo = "Anos: ... / URGs: ... / Escolas: ... / Tipos: ..."` usado em todos os subheaders.

---

## 4. Componentes de Interface

### 4.1 Cards de Métricas (KPIs)
Renderizados via `render_metric_cards(prepare_metrics(...))` em 3 linhas:
- **Primary:** `TOTAL DE ALUNOS` (`QtdAlunoEscola`), `ALUNOS ATENDIDOS` (`QtdAluno`), `ATENDIMENTOS` (soma das 5 especialidades).
- **Professional:** `ATEND. PROFESSOR`, `ATEND. PSICÓLOGO`, `ATEND. ASSIST. SOCIAL`, `ATEND. ENFERMAGEM`, `ATEND. MÉDICO`.
- **Service:** `ENCAMINHAMENTOS`, `EXAMES`, `VACINADOS/APLICAÇÃO` (formato `{QtdVacinacao}/{QtdVacina}`).
- Cards com `link` apontam para `/?menu={Menu}` (mapa `label_to_menu`). Cards sem link (3 primários) usam estilo `.metric-card-static`; os demais usam `.home-metric-link`.

### 4.2 Tabela Comparativa de Performance por ANO
- Construída em memória (linhas = 12 métricas em `metric_definitions`).
- Cálculos: `% Cobertura YY` = métrica/`TOTAL DE ALUNOS` no ano; `Var% AA-BB` = variação interanual.
- Linha `TOTAL` adicionada ao final. MultiIndex header `(Ano, Qtd/% Cobertura/Var%)`.
- Renderizado por `render_saedas_aggrid` (após `prepare_comparativo_aggrid_data` + `split_aggrid_footer`), `max_rows=10`, `pinnedBottomRowData=home_ano_footer_rows`.
- Container toolbar: `home_ano_actions_toolbar`; arquivo CSV: `comparativo_geral_home.csv`; key da grid: `home_ano_comparativo_aggrid`.

### 4.3 Tabela Comparativa de Performance por URG (Mestre — Cross-Filtering)
- Base: `build_comparativo_anual(df_for_performance_table, "URG", value_col="QtdAluno", active_row_value=current_selected_urgs)`.
- `rowSelection="multiple"`, `rowMultiSelectWithClick=True`.
- `onFirstDataRendered`: `JsCode` que pré-seleciona linhas conforme `global_urgs` (sincronização sidebar→tabela).
- Cliques na tabela disparam: `global_urgs`, `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter=[]`, `last_interaction_source="table"` + `st.rerun()`.
- Key dinâmica: `urg_home_aggrid_{years}_{urgs}` (re-render seguro).
- Container toolbar: `home_urg_actions_toolbar`; arquivo CSV: `comparativo_urg_home.csv`.

### 4.4 Tabela Comparativa de Escola por Ano
- Só é exibida se houver URGs selecionadas (`current_selected_urgs`).
- Base: `build_comparativo_anual(df_for_performance_table[URG in current_selected_urgs], "Escola", value_col="QtdAluno", active_row_value=selected_escolas_sidebar)`.
- `rowSelection="multiple"`, `rowMultiSelectWithClick=True`, `max_rows=10`.
- `onFirstDataRendered` pré-seleciona linhas conforme `sidebar_escola_filter`.
- Cliques disparam `pending_sidebar_escola_filter`, `last_interaction_source="table_school"`, `_suppress_escola_key_change=True` + `st.rerun()`.
- Key dinâmica: `escola_home_aggrid_{years}_{urgs}_{escolas}`.
- Container toolbar: `home_escola_actions_toolbar`; arquivo CSV: `comparativo_escola_home.csv`.

### 4.5 Gráficos
- **Cobertura de alunos (donut Plotly, hole=0.55)** — um gráfico por ano selecionado (grid de até 3 colunas). Cores: `#16a34a` (Atendidos), `#9ca3af` (Não atendidos). Legenda unificada manual no topo.
- **Distribuição de Atendimentos por Profissional (donut, hole=0.45)** — um gráfico por ano. Color map fixo (Professor `#38bdf8`, Enfermagem `#0284c7`, Assist. Social `#fca5a5`, Médico `#ef4444`, Psicólogo `#4ade80`).
- **Comparativo Anual Geral (Barras)** — `px.bar` agrupado por Ano em cima de `df_home_ano_exibir` (Descricao × Ano).
- **Total de Alunos Atendidos por Profissional e URG** — `px.bar` agrupado por URG, com `facet_col="Ano"` quando >1 ano.
- **Total por Tipo de Ação e URG** — `px.bar` sobre `Encaminhamento`, `Exame`, `Alunos Vacinados`, `Doses Vacina`, agrupado por URG, faceta por Ano se >1.
- **Distribuição de Atendimentos por Profissional por URG** — `px.bar` agrupado dos 5 atendimentos por URG.

### 4.6 Detalhamento dos Dados (AgGrid)
- Só é exibido se houver URGs selecionadas; caso contrário: "Selecione uma URG para exibir o detalhamento dos dados."
- Filtros locais (acima da tabela):
  - **Multiselect:** "Exibir a escola caso alguma destas colunas contenha o valor zero" (key `zero_value_cols_selected`).
  - **Radio:** "Status da Escola" — `Aberto` (DtInicio not null & DtFechamento null), `Fechado` (DtFechamento not null), `Todas` (default) — key `inicio_sem_fechamento_option`.
- Colunas derivadas calculadas linha-a-linha:
  - `PercentualAlunoEscola` → `PAE (%)` = `QtdAlunoEscola / soma(QtdAlunoEscola por ano em df_master_filtrado) * 100`.
  - `PercentualAlunoAtendido` → `PAA (%)` = `QtdAluno / QtdAlunoEscola * 100`.
  - `PAP/PAPS/PAAS/PAENF/PAM/PAV (%)` = `Qtd{Profissional|Vacinacao} / QtdAlunoEscola * 100`.
- Datas (`DtInicio`, `DtFechamento`) parseadas com formato `%d/%m/%Y` e formatadas para exibição; vazios viram string vazia.
- Linha **TOTAL** somando colunas absolutas (Aluno Escola, Aluno Atend., Atendimentos por profissional, Vacinados, Doses, Encaminhamento, Exame) via `pinnedBottomRowData`.
- Radio de altura visível: `Padrão (10) | 20 | 50 | 100` (`home_table_height_option`) — controla `max_rows` do `render_saedas_aggrid`.
- Toolbar `home_detail_toolbar` com ação `Colunas` (`leading_action_label="Colunas"`) que abre o painel `home_columns_panel` para seleção de colunas visíveis. Persistência em `home_hidden_columns`.
- Formatação de milhar pt-BR aplicada via `valueFormatter` (`thousands_js`) em colunas numéricas.
- Key da grid: `home_detalhamento_aggrid`. Arquivo CSV: `detalhamento_home.csv`.
- Coluna técnica `::auto_unique_id::` é mantida em `EXCLUDED_EXPORT_COLUMNS` e removida do export.
- Legenda das colunas percentuais (PAE, PAA, PAP, PAPS, PAAS, PAENF, PAM, PAV) renderizada abaixo da tabela em grid 2 colunas.

---

## 5. Regras de Negócio e Cálculos
- **Atendimentos Profissionais (KPI e linha `ATENDIMENTOS`):** soma de `QtdProfessor + QtdPsicologo + QtdAssistSocial + QtdEnfermagem + QtdMedico`.
- **% Cobertura (tabela ANO):** `(metric / TOTAL DE ALUNOS no ano) * 100`. Se total = 0, valor 0.
- **Var% (tabela ANO/URG/Escola):** `((curr - prev) / prev) * 100`. Divisões por zero ficam como `NaN`/"-".
- **Imunidade de Filtro:** `df_for_performance_table` ignora URG/Escola/Tipo (só filtra por Ano) para que as tabelas mestre possam mostrar todas as URGs/Escolas e ainda assim refletir a seleção do usuário.
- **Cobertura (donut):** `pct_atendidos = total_atendidos / total_cadastrados * 100`, exibido como subtítulo do gráfico.
- **Janela temporal:** sempre os últimos 5 anos a partir do ano corrente do sistema, default selecionado = `[max_year do CSV]` via `get_max_year_from_data()`.

---

## 6. Toolbars e Padrões Visuais
- Toolbars unificadas em containers nomeados: `home_ano_actions_toolbar`, `home_urg_actions_toolbar`, `home_escola_actions_toolbar`, `home_detail_toolbar`.
- Wrapper `.selection-master-table` para tabelas com seleção; `.st-table-with-total` para tabelas só de visualização.
- CSS injetado no início de `page_home()` define: `.home-metric-card`, `.metric-card-static`, `.home-metric-link`, `.home-metric-link:hover`, `.home-metric-label`, `.home-metric-value`, `.home-metric-link-wrapper`, `.home-columns-panel-title/-subtitle`, `.home-legend-grid/-item`, `.column-toggle-active button`.

---

## 7. Cache e Performance
- Integra `app.utils.redis_client.redis_cache` (ver [Redis Cache Spec](redis_cache_spec.md)).
- Estratégia por dataset: `get_dataframe_with_timestamp(redis_key, csv_path)` antes de cair para `load_csv`; em fallback, regrava com `set_dataframe_with_timestamp`.
- Invalidação automática quando o `mtime` do CSV no disco for mais novo que o registro no Redis.
- TTL padrão: 12h.
- Chaves: `saedas:home:dataset:{main|escola|ano|urg}`.
