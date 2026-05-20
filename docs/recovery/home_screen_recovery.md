# Runbook de Recuperação: Tela Home

## Objetivo

Documento operacional para restaurar rapidamente a tela `Home` (`app/app_pages/home.py`, função `page_home()`) em caso de regressão visual ou funcional. Mantém paridade com `docs/specs/home_page_spec.md`.

> Para replicar este padrão em novas telas, ver `docs/similar_screens_blueprint.md`.

## Escopo Funcional

- Seletor temporal mestre (`massive_year_selector`, widget `home_year_buttons`) sincronizado com a sidebar.
- Filtros de sidebar via `sidebar_filters(df, {"ano": True, "urg": True, "escola": True, "tipo": True})`.
- Breadcrumb "Filtros aplicados" + título dinâmico `filtro_titulo`.
- KPIs em 3 linhas de cards (Primary, Professional, Service) com links `/?menu={Menu}` nos cards de serviço/profissionais.
- Tabelas AgGrid (via `render_saedas_aggrid`):
  - Comparativo geral por Ano (`home_ano_comparativo_aggrid`).
  - Seleção mestre por URG (`urg_home_aggrid_*`).
  - Seleção mestre por Escola (`escola_home_aggrid_*`).
  - Detalhamento (`home_detalhamento_aggrid`).
- Gráficos Plotly: donut Cobertura por ano, donut Profissional por ano, barras Comparativo Anual Geral, barras Profissional × URG (faceta por Ano), barras Tipo de Ação × URG, barras Distribuição por Profissional × URG.
- Detalhamento com filtros locais (Status da Escola, Colunas zeradas), painel de seleção de colunas e radio de altura (10/20/50/100).

## Fontes de Dados

Carregadas em `carregar_dados_home()` com cache Redis (chaves `saedas:home:dataset:{main|escola|ano|urg}`):

- `data/DashboardHome.csv` — `SCHEMA_HOME` (master).
- `data/DashboardHomeAno.csv` — `SCHEMA_HOME_ANO`.
- `data/DashboardHomeURGAno.csv` — `SCHEMA_HOME_URG_ANO`.
- `data/DashboardHomeEscolaAno.csv` — `SCHEMA_HOME_ESCOLA_ANO`.

Apenas o `df` master é consumido nos cálculos atuais; os 3 agregados são carregados/cacheados como reserva.

## Fonte de Verdade de Estado

Globais (criadas por `init_global_state`):

- `global_years`, `global_urgs`.

Widgets sidebar:

- `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`.

Widget Home:

- `home_year_buttons`.

Auxiliares:

- `last_interaction_source` (`sidebar` | `table` | `table_school` | `table_escola`).
- `_is_page_first_run`.
- `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`.
- `_prev_urg_grid_key_home`, `_prev_escola_grid_key_home`, `_suppress_escola_key_change`.
- `last_df_cmp_urg_home`.

Detalhamento:

- `home_table_height_option`, `home_show_column_selector`, `home_hidden_columns`.
- `selected_schools_detalhamento`, `closing_date_filter_option`, `inicio_sem_fechamento_option`, `zero_value_cols_selected`.
- `home_toolbar_column_toggle`.

## Regras de Filtro

- Anos: obrigatórios. Sem ano selecionado, `df_base_final` é vazio e KPIs/gráficos zeram.
- Ano default: maior ano disponível em `DashboardHome.csv` via `get_max_year_from_data()` (fallback: ano corrente do sistema).
- URG: filtro global propagado entre sidebar e tabela mestre.
- Escola: cascata via sidebar; respeita seleção da tabela mestre Escola quando uma URG está ativa.
- Tipo: filtra `df_master_filtrado` (não afeta `df_for_performance_table`).
- Tabelas mestre (URG, Escola) usam `df_for_performance_table` (imune a URG/Escola/Tipo, filtra só por Ano).
- Tabela Comparativa por ANO usa `df_home_ano_source` (todos os filtros aplicados, exceto a própria comparação).

## Sincronismos Obrigatórios

- Ano: callback `sync_home_to_sidebar` em `home_year_buttons` → atualiza `global_years` e `sidebar_year_filter`.
- URG (sidebar → tabela): `onFirstDataRendered` em JsCode pré-seleciona linhas em `urg_home_aggrid_*` a partir de `global_urgs`.
- URG (tabela → sidebar): clique grava `global_urgs`, `pending_sidebar_urg_filter`, zera `pending_sidebar_escola_filter`, marca `last_interaction_source="table"` e dispara `st.rerun()`.
- Escola (sidebar → tabela): `onFirstDataRendered` (JsCode) pré-seleciona via `sidebar_escola_filter`.
- Escola (tabela → sidebar): grava `pending_sidebar_escola_filter`, marca `last_interaction_source="table_school"`, define `_suppress_escola_key_change=True` e `st.rerun()`.
- `apply_pending_table_filters()` deve ser chamado ANTES de `sidebar_filters` para resolver pendências.

## Estilos Críticos (não remover)

- Seletor de ano: `.st-key-massive_year_selector ...` (ver `shared_components_spec.md` §2).
- Cards:
  - `.home-metric-card`
  - `.metric-card-static`
  - `.home-metric-link` / `.home-metric-link:hover`
  - `.home-metric-link-wrapper`
  - `.home-metric-label`
  - `.home-metric-value`
- Painel de colunas: `.home-columns-panel-title`, `.home-columns-panel-subtitle`, `.st-key-home_columns_panel`, `.st-key-home_columns_grid`, `.column-toggle-active button`.
- Legendas: `.home-legend-grid`, `.home-legend-item`.
- Wrappers AgGrid: `.selection-master-table`, `.st-table-with-total`.
- Toolbars agrupadas (containers): `home_ano_actions_toolbar`, `home_urg_actions_toolbar`, `home_escola_actions_toolbar`, `home_detail_toolbar`.

## Padrão AgGrid Obrigatório

- Sempre `render_saedas_aggrid(...)` (proibido `st.dataframe` na Home).
- Sempre preceder com `render_table_toolbar(...)` dentro de `st.container(key="{prefix}_actions_toolbar")`.
- Linha TOTAL em `pinnedBottomRowData` quando aplicável (tabelas comparativas e Detalhamento).
- Altura inteligente com mínimo de 5 linhas e cap configurável (`max_rows`: 10 nas tabelas comparativas, 10/20/50/100 no Detalhamento via radio).
- Keys dinâmicas incluindo o hash do estado de seleção (`urg_home_aggrid_{years}_{urgs}`, `escola_home_aggrid_{years}_{urgs}_{escolas}`).

## Checklist de Recuperação

1. Confirmar carregamento dos 4 CSVs via `carregar_dados_home()` e ausência de erros em `info["erros"]`.
2. Validar `init_global_state()` e `apply_pending_table_filters()` rodando antes da sidebar.
3. Validar sincronismo Ano (sidebar ⇄ `massive_year_selector`).
4. Validar sincronismo URG (tabela mestre ⇄ sidebar) — selecionar, deselecionar e múltiplas linhas.
5. Validar sincronismo Escola (tabela mestre ⇄ sidebar) — requer URG ativa.
6. Validar 3 linhas de KPIs e links `/?menu=...` (`ENCAMINHAMENTOS`, `EXAMES`, `VACINADOS/APLICAÇÃO`, `ATEND. *`).
7. Validar tabela ANO (12 métricas, `% Cobertura YY`, `Var% AA-BB`, linha TOTAL, super-header por ano).
8. Validar gráficos: donut Cobertura, donut Profissional, barras Comparativo, barras Profissional × URG, barras Tipo de Ação × URG, barras Profissional/URG.
9. Validar Detalhamento: filtros locais, painel de colunas (`Colunas`), radio de altura, colunas PAE/PAA/PAP/PAPS/PAAS/PAENF/PAM/PAV, linha TOTAL.
10. Validar ausência de `st.dataframe` em `home.py`.
11. Validar invalidação Redis por timestamp do CSV.

## Comandos Úteis

- `streamlit run app/main.py`
- `python -m py_compile app/app_pages/home.py app/utils/page_helpers.py app/utils/state_manager.py app/utils/redis_client.py`
- `rg -n "st\\.dataframe\\(|render_saedas_aggrid\\(|render_table_toolbar\\(" app/app_pages/home.py app/utils/page_helpers.py`
- `rg -n "global_years|global_urgs|pending_sidebar|home_year_buttons|home_hidden_columns|inicio_sem_fechamento_option" app/app_pages/home.py app/utils/state_manager.py`
