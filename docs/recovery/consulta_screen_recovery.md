# Runbook de Recuperação: Tela Consulta

## Objetivo
Documento operacional para restaurar rapidamente a tela `Consulta` (`app/app_pages/consulta.py`) em caso de regressão visual/funcional.

> Para aplicar este mesmo escopo em Nutrição, Vacinação e Exames, seguir o blueprint: `docs/similar_screens_blueprint.md`.

## Escopo Funcional
- Seletor temporal mestre idêntico ao da Home.
- Filtros de sidebar: Ano, URG, Escola, Tipo, Encaminhamento.
- Indicador total + cards de encaminhamento (clicáveis).
- Tabela de performance por URG (seleção mestre).
- Tabela comparativa de escola por ano (seleção mestre, multiseleção).
- Gráficos de distribuição.
- Detalhamento por aluno em AgGrid.

## Fontes de Dados
- `data/DashboardConsulta.csv`
- `data/DashboardConsultaAluno.csv`
- `data/DashboardConsultaAno.csv`
- Schemas: `SCHEMA_CONSULTA`, `SCHEMA_CONSULTA_ALUNO`, `SCHEMA_CONSULTA_ANO`.

## Fonte de Verdade de Estado
- Globais: `global_years`, `global_urgs`
- Sidebar: `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`
- Pendências: `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`
- Controle de origem: `last_interaction_source`
- Seleção escola na tabela: `escola_table_selection_consulta__selected_values`

## Regras de Filtro
- `df_filt` é a base filtrada final para componentes de análise.
- Ano: via `global_years`.
- URG: via `global_urgs`.
- Escola e Tipo: via `selections` da sidebar.
- Encaminhamento: via `consulta_encaminhamento_multiselect`.

## Exceções Intencionais (componentes de seleção)
- Tabela URG (seleção mestre): sensível apenas a Ano.
- Tabela Escola (seleção mestre): imune ao filtro da própria escola.
- Cards de encaminhamento: base `df_filt_no_enc` (imunes ao filtro de encaminhamento para exibir opções completas).
- Regra de KPI: card total usa `df_filt`; cards de categoria não se auto-filtram.
- Não existe mais bloco de "Principais Encaminhamentos por URG".
- Não existe mais "Tabela Comparativa de Encaminhamento por Ano".

## Sincronismo Obrigatório
- Sidebar -> Tabela Escola:
  - mudança em `sidebar_escola_filter` deve refletir seleção visual na tabela.
- Tabela Escola -> Sidebar:
  - seleção atualiza `pending_sidebar_escola_filter` e dispara `rerun`.
- URG segue o mesmo padrão de paridade com `pending_sidebar_urg_filter`.
- Evitar sobrescrita cruzada com `last_interaction_source`.

## Estilos Críticos (não remover)
- Seletor de ano: `.st-key-massive_year_selector ...` (mesmo da Home).
- Cards:
  - `.home-metric-card`
  - `.metric-card-static`
  - `.home-metric-label`
  - `.home-metric-value`
- KPIs clicáveis:
  - `div[class*="st-key-btn_kpi_"] button`
  - formatação de texto em `p` e `strong`.
- Toolbar AgGrid agrupada:
  - `consulta_urg_actions_toolbar`
  - `consulta_aluno_actions_toolbar`
  - `escola_table_selection_consulta_actions_toolbar`

## Padrão AgGrid Obrigatório
- Sempre usar `render_saedas_aggrid(...)`.
- Sempre preceder com `render_table_toolbar(...)`.
- Tabelas mestre com `.selection-master-table`.
- Tabelas padrão com `.st-table-with-total`.
- Altura inteligente com cap de 20 linhas.

## Checklist de Recuperação
1. Validar carga dos 3 datasets de consulta.
2. Validar seletor de ano com mesmo visual/comportamento da Home.
3. Validar sync URG tabela <-> sidebar.
4. Validar sync Escola tabela <-> sidebar (selecionar e remover).
5. Validar filtros de sidebar aplicados em gráficos e tabelas não-mestre.
6. Validar cards de encaminhamento clicáveis e estilo.
7. Validar toolbars agrupadas em todas as tabelas AgGrid ativas.

## Comandos Úteis
- `streamlit run app/app.py`
- `python -m py_compile app/app_pages/consulta.py app/utils/page_helpers.py app/components/sidebar_filters.py`
- `rg -n "st\\.dataframe\\(|render_saedas_aggrid\\(|render_table_toolbar\\(|escola_table_selection_consulta__selected_values" app/app_pages/consulta.py app/utils/page_helpers.py`
