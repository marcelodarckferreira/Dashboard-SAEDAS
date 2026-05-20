# Runbook de Recuperação: Tela Assistência Social

## Objetivo
Documento operacional para restaurar rapidamente a tela `Assistência Social` (`app/app_pages/assistencia_social.py`) em caso de regressão visual/funcional.

> Esta tela segue o blueprint comum em `docs/similar_screens_blueprint.md`.

## Escopo Funcional
- Seletor temporal mestre idêntico ao da Home (`massive_year_selector`).
- Filtros de sidebar: Ano, URG, Escola, Tipo.
- Três cards de indicadores: Total de Alunos, Alunos Atendidos, Atend. Assist. Social.
- Tabela de performance por URG (seleção mestre).
- Tabela comparativa Top Escolas por URG (seleção mestre, multiseleção).
- Gráfico de distribuição por URG (Plotly barras agrupadas por Ano).
- Detalhamento por aluno em AgGrid com filtros inline (Aluno, Série, Turma).

## Fontes de Dados
- `data/DashboardAssistenciaSocial.csv`
- `data/DashboardAssistenciaSocialAluno.csv`
- `data/DashboardAssistenciaSocialAno.csv`
- `data/DashboardHome.csv` (para Total de Alunos / Alunos Atendidos)
- Schemas: `SCHEMA_ASSISTENCIA_SOCIAL`, `SCHEMA_ASSISTENCIA_SOCIAL_ALUNO`, `SCHEMA_ASSISTENCIA_SOCIAL_ANO`, `SCHEMA_HOME`.

## Fonte de Verdade de Estado
- Globais: `global_years`, `global_urgs`
- Sidebar: `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`
- Pendências: `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`
- Controle de origem: `last_interaction_source`
- Seleção escola na tabela: `escola_table_selection_assistencia_social__selected_values`
- Stale-guard URG: `_prev_urg_table_key_assistencia_social`

## Regras de Filtro
- `df_filt` é a base final filtrada (Tipo, Ano, Escola, URG) usada para cards de atendimento e gráficos.
- Ano: via `global_years` (seletor mestre).
- URG: via `global_urgs`.
- Escola e Tipo: via `selections` da sidebar.
- Não existe filtro de Atendimento (foi removido); `atendimentos_selecionados` permanece `[]`.

## Exceções Intencionais (componentes de seleção)
- Tabela URG (seleção mestre): sensível **apenas a Ano**.
- Tabela Top Escolas (seleção mestre): imune ao filtro da própria escola (base `df_filt_no_escola`).
- Cards "Total de Alunos" e "Alunos Atendidos": calculados a partir de `DashboardHome.csv`, não do dataset principal.

## Sincronismo Obrigatório
- Sidebar → Tabela Escola:
  - mudança em `sidebar_escola_filter` reflete via `sync_sidebar_escola_selection("escola_table_selection_assistencia_social")`.
- Tabela Escola → Sidebar:
  - seleção atualiza `pending_sidebar_escola_filter`, define `last_interaction_source="table_escola"` e dispara `rerun`.
- URG segue o mesmo padrão com `pending_sidebar_urg_filter` e `last_interaction_source="table"`.
- `last_interaction_source` é zerado (`""`) ao final do bloco de sync de escola para evitar sobrescrita cruzada.

## Estilos Críticos (não remover)
- Seletor de ano: `.st-key-massive_year_selector` (mesmo da Home).
- Cards:
  - `.home-metric-card`
  - `.metric-card-static`
  - `.home-metric-label`
  - `.home-metric-value`
- KPIs clicáveis (residual de toggle):
  - `div[class*="st-key-btn_kpi_"] button`
  - formatação em `p` e `strong`.
- Toolbars AgGrid agrupadas (CSS escopado por key):
  - `assistencia_social_urg_actions_toolbar`
  - `escola_table_selection_assistencia_social_actions_toolbar`
  - `assistencia_social_cobertura_actions_toolbar` (declarada no CSS; não instanciada)
  - `assistencia_social_aluno_actions_toolbar`

## Padrão AgGrid Obrigatório
- Sempre usar `render_saedas_aggrid(...)` ou `render_aluno_detalhamento_aggrid(...)`.
- Sempre preceder com `render_table_toolbar(...)` (no caso do detalhamento por aluno, a toolbar é integrada pelo próprio helper).
- Tabelas mestre com `.selection-master-table`.
- Tabela URG usa `pinnedBottomRowData` (linha TOTAL).
- Key dinâmico em tabelas mestre para stale-guard.

## Regras Específicas
- Ordenação do gráfico de URG por numeral romano via `_urg_sort_key` / `_roman_to_int`.
- Texto das barras formatado em pt-BR (`"3.235"`).
- Link de perfil do aluno: `?menu=Aluno&aluno=Nome&nasc=YYYY-MM-DD` via `build_perfil_link`.
- Limite de preview: 500 linhas no detalhamento; aviso quando excede.
- Coluna `Menu` é renomeada para `Perfil` na exibição final.

## Checklist de Recuperação
1. Validar carga dos 3 datasets de Assistência Social + Home.
2. Validar seletor de ano com mesmo visual/comportamento da Home.
3. Validar três cards de KPI (Total Alunos, Alunos Atendidos, Atend. Assist. Social).
4. Validar tabela Performance por URG sensível apenas a Ano.
5. Validar sync URG tabela ↔ sidebar (selecionar e remover).
6. Validar sync Escola tabela ↔ sidebar (selecionar e remover).
7. Validar gráfico de Distribuição por URG (ordenação romana + cores por Ano).
8. Validar detalhamento por aluno com filtros inline (Aluno, Série, Turma) e link de Perfil.
9. Validar toolbars agrupadas em todas as tabelas AgGrid ativas.

## Comandos Úteis
- `streamlit run app/main.py`
- `python -m py_compile app/app_pages/assistencia_social.py app/utils/page_helpers.py app/components/sidebar_filters.py`
- `rg -n "render_saedas_aggrid\(|render_table_toolbar\(|render_aluno_detalhamento_aggrid\(|escola_table_selection_assistencia_social__selected_values" app/app_pages/assistencia_social.py app/utils/page_helpers.py`
