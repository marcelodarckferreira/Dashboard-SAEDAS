# Runbook de Recuperação: Tela Home

## Objetivo
Documento operacional para restaurar rapidamente a tela `Home` (`app/app_pages/home.py`) em caso de regressão visual/funcional.

> Para replicar este padrão em novas telas semelhantes, usar também: `docs/similar_screens_blueprint.md`.

## Escopo Funcional
- Seletor temporal mestre (`massive_year_selector`) sincronizado com sidebar.
- Filtros de sidebar: Ano, URG, Escola.
- Indicadores gerais em cards (inclui links de navegação para páginas).
- Tabelas AgGrid:
  - Comparativo geral por ano.
  - Seleção mestre por URG.
  - Seleção mestre por Escola.
  - Detalhamento.
- Gráficos e comparativos anuais.

## Fontes de Dados
- `data/DashboardHome.csv`
- `data/DashboardHomeAno.csv`
- `data/DashboardHomeURGAno.csv`
- `data/DashboardHomeEscolaAno.csv`
- Schemas: `SCHEMA_HOME`, `SCHEMA_HOME_ANO`, `SCHEMA_HOME_URG_ANO`, `SCHEMA_HOME_ESCOLA_ANO`.

## Fonte de Verdade de Estado
- `global_years`, `global_urgs`
- `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`
- `home_year_buttons`
- `last_interaction_source`
- Pendências: `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`

## Regras de Filtro
- Ano: obrigatório para todos os componentes de análise.
- URG/Escola: aplicados conforme hierarquia da sidebar (cascata).
- Tabelas de seleção mestre não podem ser filtradas pela própria seleção que controlam.

## Sincronismos Obrigatórios
- Ano: `sync_sidebar_to_home()` e `sync_home_to_sidebar()`.
- URG: tabela -> `global_urgs` -> `pending_sidebar_urg_filter` -> sidebar.
- Escola: tabela -> `pending_sidebar_escola_filter` -> sidebar.
- Evitar loop com `last_interaction_source` (`sidebar` vs `table`).

## Estilos Críticos (não remover)
- Seletor de ano: `.st-key-massive_year_selector ...`
- Cards:
  - `.home-metric-card`
  - `.metric-card-static`
  - `.home-metric-link`
  - `.home-metric-label`
  - `.home-metric-value`
- Toolbar AgGrid agrupada:
  - `home_urg_actions_toolbar`
  - `home_escola_actions_toolbar`
  - `home_ano_actions_toolbar`
  - `home_detail_toolbar`

## Padrão AgGrid Obrigatório
- Sempre usar `render_saedas_aggrid(...)` (não usar `st.dataframe`).
- Sempre preceder com `render_table_toolbar(...)`.
- Linha TOTAL em `pinnedBottomRowData` quando aplicável.
- Altura inteligente com cap de 20 linhas (wrapper padrão).

## Checklist de Recuperação
1. Confirmar carregamento dos CSVs e schemas.
2. Validar sincronismo Ano (sidebar <-> segmented).
3. Validar sincronismo URG (tabela <-> sidebar).
4. Validar sincronismo Escola (tabela <-> sidebar).
5. Validar toolbar agrupada em todas as tabelas.
6. Validar card styles e links.
7. Validar ausência de `st.dataframe` na Home.

## Comandos Úteis
- `streamlit run app/app.py`
- `python -m py_compile app/app_pages/home.py app/utils/page_helpers.py app/components/sidebar_filters.py`
- `rg -n "st\\.dataframe\\(|render_saedas_aggrid\\(|render_table_toolbar\\(" app/app_pages/home.py app/utils/page_helpers.py`
