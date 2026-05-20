# Runbook de Recuperação: Tela Enfermagem

## Objetivo
Documento operacional para restaurar rapidamente a tela `Enfermagem` (`app/app_pages/enfermagem.py`) em caso de regressão visual ou funcional. Segue o blueprint `docs/similar_screens_blueprint.md`.

## Escopo Funcional
- Seletor temporal mestre idêntico ao da Home.
- Filtros de sidebar: Ano, URG, Escola, Tipo.
- Cards de indicadores: Total de Alunos, Alunos Atendidos, Atend. Enfermagem.
- Tabela Performance por URG (seleção mestre, sensível apenas a Ano).
- Tabela Principais Escolas por URG (seleção mestre, multiseleção).
- Gráfico Distribuição por URG (barras agrupadas por Ano).
- Detalhamento por Aluno em AgGrid (com filtros locais Aluno/Série/Turma).

## Fontes de Dados
- `data/DashboardEnfermagem.csv` (`SCHEMA_ENFERMAGEM`)
- `data/DashboardEnfermagemAluno.csv` (`SCHEMA_ENFERMAGEM_ALUNO`)
- `data/DashboardEnfermagemAno.csv` (`SCHEMA_ENFERMAGEM_ANO`)
- `data/DashboardHome.csv` (`SCHEMA_HOME`) — usado para cards de alunos.

## Fonte de Verdade de Estado
- Globais: `global_years`, `global_urgs`.
- Sidebar: `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`, `sidebar_tipo_filter`.
- Pendências: `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`.
- Controle de origem: `last_interaction_source`.
- Seleção escola na tabela: `escola_table_selection_enfermagem__selected_values`.
- Stale-guard URG: `_prev_urg_table_key_enfermagem`.

## Filtros Locais
- `enfermagem_aluno_multiselect`
- `enfermagem_serie_multiselect`
- `enfermagem_turma_multiselect`
- `enfermagem_atendimento_multiselect` (declarado, sem widget visível — `atendimentos_selecionados = []`).

## Regras de Filtro
- `df_filt` é a base filtrada final (Tipo + Ano + Escola + URG).
- `df_filt_no_escola` é a base para "Principais Escolas por URG" (sem filtro de Escola).
- `df_for_urg_table` para Performance por URG: somente filtrado por Ano.
- `df_home` para cards: aplica Ano, URG e Escola da sidebar.

## Exceções Intencionais
- Tabela URG (mestre): sensível apenas a Ano. Caption explícita.
- Tabela Escola (mestre): imune ao filtro da própria escola.
- Cards de Total de Alunos e Alunos Atendidos: vêm de `DashboardHome.csv`, não de `DashboardEnfermagem.csv`.

## Sincronismo Obrigatório
- Sidebar -> Tabela URG: via `apply_pending_table_filters()` + JS `onFirstDataRendered`.
- Tabela URG -> Sidebar: seta `global_urgs`, `pending_sidebar_urg_filter`, `last_interaction_source="table"` e dispara `st.rerun()`.
- Sidebar -> Tabela Escola: `sync_sidebar_escola_selection("escola_table_selection_enfermagem")`.
- Tabela Escola -> Sidebar: seta `pending_sidebar_escola_filter`, `last_interaction_source="table_escola"` e dispara `st.rerun()`.
- Sempre zera `last_interaction_source = ""` após o bloco de sync de escola.

## Estilos Críticos (não remover)
- Seletor de ano: container `massive_year_selector`.
- Cards:
  - `.home-metric-card`
  - `.metric-card-static`
  - `.home-metric-label`
  - `.home-metric-value`
- KPIs clicáveis: `div[class*="st-key-btn_kpi_"] button` (CSS preservado mesmo sem KPIs ativos).
- Toolbars AgGrid agrupadas:
  - `enfermagem_urg_actions_toolbar`
  - `escola_table_selection_enfermagem_actions_toolbar`
  - `enfermagem_cobertura_actions_toolbar`
  - `enfermagem_aluno_actions_toolbar`

## Padrão AgGrid Obrigatório
- Sempre `render_saedas_aggrid(...)`.
- Sempre preceder com `render_table_toolbar(...)` (ou usar `render_aluno_detalhamento_aggrid` que já encapsula).
- Tabela mestre URG: wrapper `.selection-master-table`, `pinnedBottomRowData` com TOTAL.
- Detalhamento Aluno: limite de 500 linhas (`preview_limit`), aviso quando excedido.
- Altura inteligente com cap de 20 linhas.

## Checklist de Recuperação
1. Validar carga dos 4 datasets (principal, aluno, ano, home).
2. Validar seletor de ano com mesmo visual/comportamento da Home.
3. Validar cards: TOTAL DE ALUNOS, ALUNOS ATENDIDOS, ATEND. ENFERMAGEM.
4. Validar sync URG tabela <-> sidebar (selecionar e remover).
5. Validar que tabela URG ignora filtros de Escola/Tipo (sensível só a Ano).
6. Validar sync Escola tabela <-> sidebar.
7. Validar gráfico Distribuição por URG (ordenação por romano, agrupamento por Ano).
8. Validar Detalhamento por Aluno: pivot de anos como colunas + coluna `Total` + link `Perfil`.
9. Validar toolbars agrupadas em todas as tabelas AgGrid.
10. Validar exportações `performance_urg_enfermagem.csv` e `detalhes_alunos_enfermagem.csv`.

## Comandos Úteis
- `streamlit run app/app.py`
- `python -m py_compile app/app_pages/enfermagem.py app/utils/page_helpers.py app/components/sidebar_filters.py`
- `rg -n "render_saedas_aggrid\\(|render_table_toolbar\\(|escola_table_selection_enfermagem__selected_values|enfermagem_urg_actions_toolbar" app/app_pages/enfermagem.py app/utils/page_helpers.py`
