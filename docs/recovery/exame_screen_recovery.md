# Runbook de Recuperação: Tela Exame

## Objetivo
Documento operacional para restaurar rapidamente a tela `Exame` (`app/app_pages/exame.py`) em caso de regressão visual/funcional. Espec técnica completa: `docs/specs/exame_page_spec.md`.

> Para aplicar este escopo em telas semelhantes, seguir também: `docs/similar_screens_blueprint.md`.

## Escopo Funcional
- Seletor temporal mestre idêntico ao da Home (`massive_year_selector` + `home_year_buttons`).
- Filtros de sidebar: Ano, URG, Escola, Tipo, Regulação.
- 3 cards estáticos: TOTAL DE ALUNOS, ALUNOS ATENDIDOS, TOTAL DE EXAMES.
- Cards toggle de Regulação (clique alterna `exame_regulacao_multiselect`).
- Tabela Comparativa de Performance por ANO (Regulação) com `% Total` e `Var%`.
- Tabela de Performance por URG (seleção mestre múltipla).
- Tabela Top Escolas por URG (seleção mestre múltipla via `render_top_por_urg`).
- Gráfico horizontal: Comparativo Anual por URG.
- Gráfico horizontal: Distribuição por Regulação.
- Detalhamento por Aluno em AgGrid (`render_aluno_detalhamento_aggrid`).

## Fontes de Dados
- `data/DashboardExame.csv` (`SCHEMA_EXAME`)
- `data/DashboardExameAluno.csv` (`SCHEMA_EXAME_ALUNO`)
- `data/DashboardExameAno.csv` (`SCHEMA_EXAME_ANO`)
- `data/DashboardHome.csv` (`SCHEMA_HOME`) — referência demográfica.

Carga única via `carregar_dados_exame()` com Smart Cache Redis e fallback `load_csv`.

## Fonte de Verdade de Estado
- Globais: `global_years`, `global_urgs`.
- Sidebar: `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`.
- Mestre Home: `home_year_buttons`.
- Pendências: `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`.
- Controle de origem: `last_interaction_source` (`""`, `"sidebar"`, `"table"`, `"table_escola"`).
- Regulação: `exame_regulacao_multiselect` + persistência `persistent_exame_regulacao`.
- Seleção escola na tabela: `escola_table_selection_exame__selected_values`.
- Stale-guards: `_prev_urg_table_key_exame`, `escola_table_selection_exame__aggrid_key`, `escola_table_selection_exame__prev_sidebar_escola_filter`.

## Filtros e Bases
- `df_base_sem_escola`: Tipo + Ano.
- `df_base_final`: + Escola.
- `df_master_no_reg`: + URG.
- `df_filt`: + Regulação (base padrão de análise).
- `df_filt_no_reg`: imune a Regulação (cards KPI).
- `df_filt_no_escola`: imune a Escola (Top Escolas).
- `df_filt_no_urg_no_escola`: imune a URG/Escola (tabela mestre URG).

## Sincronismos
- Sidebar → Tabela Escola: `sync_sidebar_escola_selection("escola_table_selection_exame")`.
- Tabela Escola → Sidebar: detecta diff e seta `pending_sidebar_escola_filter` + `rerun()`.
- Sidebar → Tabela URG: `apply_pending_table_filters()` antes dos widgets; JS `onFirstDataRendered` sincroniza visual.
- Tabela URG → Sidebar: diff → `global_urgs` + `pending_sidebar_urg_filter` + `last_interaction_source="table"` + `rerun()`.
- Ano: `sync_home_to_sidebar` (segmented control).
- Regulação: callback `sync_local_exame_regulacao` espelha `exame_regulacao_multiselect` em `persistent_exame_regulacao`.
- Evitar sobrescrita cruzada via `last_interaction_source`; sempre zerar (`""`) ao final do bloco de escola.

## Estilos Críticos (não remover)
- Seletor de ano: container `massive_year_selector`.
- Cards: `.home-metric-card`, `.metric-card-static`, `.home-metric-label`, `.home-metric-value`.
- KPIs clicáveis: `div[class*="st-key-btn_kpi_"] button` (`p`, `strong`, `:hover`, `[kind="primary"]`).
- Toolbars AgGrid agrupadas (containers):
  - `exame_ano_actions_toolbar`
  - `exame_urg_actions_toolbar`
  - `exame_aluno_actions_toolbar`
  - `escola_table_selection_exame_actions_toolbar`
- Wrappers de tabela: `.selection-master-table` (mestre), `.st-table-with-total` (padrão).

## Checklist de Recuperação
1. Validar carga dos 4 datasets (3 de exame + Home) e mensagens de erro/alerta.
2. Validar Smart Cache Redis (hit/miss conforme timestamp do CSV).
3. Validar `massive_year_selector` com paridade visual/comportamental da Home.
4. Validar sync URG tabela ↔ sidebar (selecionar, limpar e remover).
5. Validar sync Escola tabela ↔ sidebar (selecionar, limpar; sem loops).
6. Validar filtros de sidebar em gráficos e tabela ano.
7. Validar cards de Regulação clicáveis com destaque visual (`active_labels`).
8. Validar Tabela Comparativa por ANO: `% Total`, `Var%`, ordem alinhada aos KPIs, TOTAL ao final.
9. Validar toolbars agrupadas em todas as AgGrid (Copiar TSV e CSV).
10. Validar detalhamento de aluno com link "Ver Perfil" (`?menu=Aluno&aluno=...&nasc=...`).

## Comandos Úteis
- `streamlit run app/app.py`
- `python -m py_compile app/app_pages/exame.py app/utils/page_helpers.py app/components/sidebar_filters.py`
- `rg -n "exame_regulacao_multiselect|persistent_exame_regulacao|escola_table_selection_exame|_prev_urg_table_key_exame|exame_ano_actions_toolbar|exame_urg_actions_toolbar|exame_aluno_actions_toolbar" app/app_pages/exame.py app/utils/state_manager.py`
- `rg -n "st\\.dataframe\\(|render_saedas_aggrid\\(|render_table_toolbar\\(" app/app_pages/exame.py app/utils/page_helpers.py`
