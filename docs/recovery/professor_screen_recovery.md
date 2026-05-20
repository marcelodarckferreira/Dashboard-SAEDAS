# Runbook de Recuperação: Tela Professor

## Objetivo
Documento operacional para restaurar rapidamente a tela `Professor`
(`app/app_pages/professor.py`) em caso de regressão visual/funcional.

> Referência de padrão estrutural: `docs/similar_screens_blueprint.md`.

## Escopo Funcional
- Seletor temporal mestre idêntico ao da Home (`massive_year_selector`).
- Filtros de sidebar: Ano, URG, Escola, Tipo (sem filtro de Atendimento na UI).
- 3 cards de indicador: TOTAL DE ALUNOS, ALUNOS ATENDIDOS, ATEND. PROFESSOR.
- Tabela de Performance por URG (seleção mestre, multiseleção).
- Tabela Top Escolas por URG (seleção mestre, multiseleção) via `render_top_por_urg`.
- Gráfico Distribuição por URG (barras agrupadas por Ano).
- Detalhamento por Aluno em AgGrid com pivot por Ano.

## Fontes de Dados
- `data/DashboardProfessor.csv`
- `data/DashboardProfessorAluno.csv`
- `data/DashboardProfessorAno.csv`
- `data/DashboardHome.csv` (reaproveitado para cards de alunos)
- Schemas: `SCHEMA_PROFESSOR`, `SCHEMA_PROFESSOR_ALUNO`, `SCHEMA_PROFESSOR_ANO`, `SCHEMA_HOME`.

## Fonte de Verdade de Estado
- Globais: `global_years`, `global_urgs`
- Sidebar: `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`
- Pendências: `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`
- Controle de origem: `last_interaction_source`
- Seleção escola na tabela: `escola_table_selection_professor__selected_values`
- Anti-stale URG: `_prev_urg_table_key_professor`

## Regras de Filtro
- `df_filt` é a base filtrada final para componentes analíticos.
- Ano: via `global_years` (`selected_years_comp`).
- URG: via `global_urgs`.
- Escola e Tipo: via `selections` da sidebar.
- Atendimento: `atendimentos_selecionados = []` (filtro de Atendimento removido da UI).
- Se nenhum ano for selecionado, `df_base_sem_escola` vira `pd.DataFrame()` vazio.

## Exceções Intencionais (componentes de seleção)
- Tabela URG (seleção mestre): sensível apenas a Ano.
- Tabela Escola (seleção mestre): imune ao filtro da própria escola
  (`df_filt_no_escola`).
- Cards são puramente informativos (sem toggle ativo nesta tela).
- Função `toggle_atendimento` existe no código mas não é cabeada à UI.

## Sincronismo Obrigatório
- Sidebar → Tabela Escola: `sync_sidebar_escola_selection("escola_table_selection_professor")`.
- Tabela Escola → Sidebar: atualiza `pending_sidebar_escola_filter` e dispara `rerun`.
- URG segue paridade com `pending_sidebar_urg_filter` e `global_urgs`.
- Evitar sobrescrita cruzada com `last_interaction_source` (zerado ao final do bloco de escola).

## Estilos Críticos (não remover)
- Seletor de ano: `.st-key-massive_year_selector ...` (mesmo da Home).
- Cards:
  - `.home-metric-card`
  - `.metric-card-static`
  - `.home-metric-label`
  - `.home-metric-value`
- KPIs clicáveis (CSS reservado):
  - `div[class*="st-key-btn_kpi_"] button`
- Toolbars AgGrid agrupadas:
  - `professor_urg_actions_toolbar`
  - `escola_table_selection_professor_actions_toolbar`
  - `professor_cobertura_actions_toolbar`
  - `professor_aluno_actions_toolbar`

## Padrão AgGrid Obrigatório
- Sempre usar `render_saedas_aggrid(...)`.
- Sempre preceder com `render_table_toolbar(...)` (ou via wrappers como
  `render_top_por_urg` e `render_aluno_detalhamento_aggrid`).
- Tabela URG: wrapper `.selection-master-table` + `pinnedBottomRowData` para linha TOTAL.
- Altura inteligente com cap de 20 linhas via `calcular_altura_aggrid`.

## Estrutura do Detalhamento por Aluno
- Agrupamento estático por `["ID", "Aluno"]` (último valor das colunas estáticas).
- Pivot de contagens por Ano (`Qtd`) com coluna `Total`.
- `DataNascimento` formatada como `dd/mm/yyyy`.
- Coluna `Menu`/`Perfil` com link `?menu=Aluno&aluno={Nome}&nasc=YYYY-MM-DD`.
- Limite de preview: 500 linhas (`preview_limit`).

## Checklist de Recuperação
1. Validar carga dos 4 datasets (Professor, ProfessorAluno, ProfessorAno, Home).
2. Validar seletor de ano com mesmo visual/comportamento da Home.
3. Validar sync URG tabela ↔ sidebar (selecionar e remover).
4. Validar sync Escola tabela ↔ sidebar (selecionar e remover).
5. Validar cards: TOTAL DE ALUNOS, ALUNOS ATENDIDOS, ATEND. PROFESSOR.
6. Validar ordenação por numeral romano em URG (gráfico e tabela).
7. Validar toolbars agrupadas em todas as tabelas AgGrid.
8. Validar detalhamento por aluno: filtros locais (Aluno/Série/Turma), pivot por Ano, link `Perfil`.

## Comandos Úteis
- `streamlit run app/app.py`
- `python -m py_compile app/app_pages/professor.py app/utils/page_helpers.py app/components/sidebar_filters.py`
- `rg -n "render_saedas_aggrid\\(|render_table_toolbar\\(|escola_table_selection_professor__selected_values|professor_urg_actions_toolbar" app/app_pages/professor.py app/utils/page_helpers.py`
