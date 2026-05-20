# Runbook de Recuperação: Tela Psicólogo

## Objetivo
Documento operacional para restaurar rapidamente a tela `Psicólogo` (`app/app_pages/psicologo.py`) em caso de regressão visual/funcional.

> Esta tela segue o blueprint geral: `docs/similar_screens_blueprint.md`.

## Escopo Funcional
- Seletor temporal mestre idêntico ao da Home (`massive_year_selector`).
- Filtros de sidebar: Ano, URG, Escola, Tipo.
- Indicadores estáticos: Total de Alunos, Alunos Atendidos, Atend. Psicólogo.
- Tabela de performance por URG (seleção mestre, multipla).
- Tabela mestre de Top Escolas por URG (multiseleção, via `render_top_por_urg`).
- Gráfico de Distribuição por URG (barras agrupadas por ano).
- Detalhamento por Aluno em AgGrid com link de perfil.

## Fontes de Dados
- `data/DashboardPsicologo.csv` (`SCHEMA_PSICOLOGO`)
- `data/DashboardPsicologoAluno.csv` (`SCHEMA_PSICOLOGO_ALUNO`)
- `data/DashboardPsicologoAno.csv` (`SCHEMA_PSICOLOGO_ANO`)
- `data/DashboardHome.csv` (`SCHEMA_HOME`) — para cards de alunos.

## Fonte de Verdade de Estado
- Globais: `global_years`, `global_urgs`
- Sidebar: `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`
- Pendências: `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`
- Controle de origem: `last_interaction_source`
- Seleção escola na tabela: `escola_table_selection_psicologo__selected_values`
- Stale-guard URG: `_prev_urg_table_key_psicologo`

## Regras de Filtro
- `df_filt` (= `df_master_filtrado`) é a base filtrada final para análise.
- Ano: via `global_years` (`selected_years_comp`).
- URG: via `global_urgs` (`current_urgs`).
- Escola e Tipo: via `selections` da sidebar.
- Atendimento: filtro removido visualmente (`atendimentos_selecionados = []`).

## Exceções Intencionais (componentes de seleção)
- Tabela URG (mestre): sensível apenas a Ano (`df_for_urg_table`).
- Tabela Escola (mestre): base `df_filt_no_escola` (imune ao filtro da própria escola), recortada por Ano.
- Cards (Total de Alunos, Alunos Atendidos): vêm de `df_home`, não de `df_filt`.
- Card "ATEND. PSICÓLOGO": usa `df_filt["Quantidade"].sum()`.

## Sincronismo Obrigatório
- Sidebar → Tabela Escola:
  - `sync_sidebar_escola_selection("escola_table_selection_psicologo")` reflete a sidebar na tabela.
- Tabela Escola → Sidebar:
  - bloco pós-renderização seta `pending_sidebar_escola_filter` + `last_interaction_source = "table_escola"` + `rerun()`.
- Sidebar ↔ Tabela URG:
  - `apply_pending_table_filters()` na entrada;
  - resposta da AgGrid de URG dispara `pending_sidebar_urg_filter` + `last_interaction_source = "table"` + `rerun()` quando seleção mudar.
- Ao final do sync de escola: `last_interaction_source = ""`.

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
- Toolbars AgGrid agrupadas:
  - `psicologo_urg_actions_toolbar`
  - `psicologo_aluno_actions_toolbar`
  - `psicologo_cobertura_actions_toolbar`
  - `escola_table_selection_psicologo_actions_toolbar`

## Padrão AgGrid Obrigatório
- Sempre usar `render_saedas_aggrid(...)`.
- Sempre preceder com `render_table_toolbar(...)` (no caso do detalhamento, encapsulado por `render_aluno_detalhamento_aggrid`).
- Tabelas mestre com `.selection-master-table`.
- Altura inteligente com cap de 20 linhas.

## Checklist de Recuperação
1. Validar carga dos 3 datasets de psicólogo + dataset Home.
2. Validar seletor de ano com mesmo visual/comportamento da Home.
3. Validar render dos 3 cards estáticos com valores corretos.
4. Validar tabela mestre URG (sensível apenas a Ano) e sync bidirecional URG.
5. Validar tabela mestre Escola (multiseleção) e sync bidirecional Escola.
6. Validar ordenação por numeral romano no gráfico de Distribuição por URG.
7. Validar detalhamento por aluno:
   - filtros locais (Aluno, Série, Turma);
   - colunas estáticas + colunas por Ano + Total + Perfil;
   - limite de 500 linhas com aviso;
   - link de perfil clicável (`?menu=Aluno&aluno=...`).
8. Validar toolbars agrupadas em todas as tabelas AgGrid.

## Comandos Úteis
- `streamlit run app/app.py`
- `python -m py_compile app/app_pages/psicologo.py app/utils/page_helpers.py app/components/sidebar_filters.py`
- `rg -n "render_saedas_aggrid\(|render_table_toolbar\(|escola_table_selection_psicologo__selected_values|psicologo_urg_actions_toolbar" app/app_pages/psicologo.py app/utils/page_helpers.py`
