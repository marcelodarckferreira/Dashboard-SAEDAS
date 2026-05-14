# Runbook de Recuperação: Tela Médico

## Objetivo
Documento operacional para restaurar e alinhar a tela `Médico` (`app/app_pages/medico.py`) ao blueprint oficial em caso de regressão visual/funcional.

> Referência-base obrigatória: `docs/similar_screens_blueprint.md`.

## Escopo Funcional
- Seletor temporal mestre (mesmo padrão da Home).
- Filtros de sidebar: Ano, URG, Escola, Tipo.
- Indicadores gerais de atendimentos e alunos.
- Tabela de performance por URG (seleção mestre).
- Tabela comparativa por ANO (Atendimento Médico).
- Gráficos de distribuição por URG, Escola e Atendimento.
- Detalhamento por aluno.

## Fontes de Dados
- `data/DashboardMedico.csv`
- `data/DashboardMedicoAluno.csv`
- `data/DashboardMedicoAno.csv`
- `data/DashboardHome.csv` (base de apoio para total de alunos).
- Schemas: `SCHEMA_MEDICO`, `SCHEMA_MEDICO_ALUNO`, `SCHEMA_MEDICO_ANO`, `SCHEMA_HOME`.

## Fonte de Verdade de Estado
- Globais: `global_years`, `global_urgs`
- Sidebar: `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`
- Pendências de sync: `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`
- Controle de origem: `last_interaction_source`

## Contrato de Sincronismo (Obrigatório)
- Two-way binding entre Sidebar e tabelas de seleção.
- Fluxo obrigatório:
  - `Sidebar -> estado global -> seleção visual da tabela`
  - `Tabela -> estado global -> sidebar_*_filter`
- Anti-loop obrigatório:
  - quando origem for `"sidebar"`, não sobrescrever imediatamente via callback de tabela;
  - quando origem for `"table"`, atualizar `pending_sidebar_*` e aplicar `st.rerun()`.
- Nunca usar widget isolado como fonte de verdade; usar sempre `global_years` e `global_urgs`.

## Regras de Filtro
- `df_filt` é a base final para os componentes analíticos.
- Ano vem de `global_years`.
- URG vem de `global_urgs`.
- Escola e Tipo vêm de `selections` da sidebar.

## Exceções Intencionais
- Tabela URG (seleção mestre): sensível apenas ao filtro de Ano.
- Tabela Escola (seleção mestre): imune ao próprio filtro de escola.
- Regra de KPI:
  - indicadores totais usam `df_filt`;
  - componentes de seleção usam bases imunes dedicadas.

## Regras Obrigatórias de UI
- Seletor temporal: mesmo padrão visual/estrutura da Home (`massive_year_selector`).
- Indicadores gerais em grid fixo de 5 colunas por linha.
- Tabela comparativa por ANO deve seguir a mesma ordem dos indicadores gerais, com `TOTAL` no final.
- Toolbars de tabela devem usar padrão agrupado (`Copiar` + `CSV`) com `render_table_toolbar(...)`.
- Tabelas com total devem usar wrapper visual `.st-table-with-total`.
- Tabelas mestre devem usar `.selection-master-table`.
- Classes críticas de card/KPI:
  - `.home-metric-card`, `.metric-card-static`, `.home-metric-label`, `.home-metric-value`
  - `div[class*="st-key-btn_kpi_"] button`

## Padrão Técnico de Tabelas
- Usar obrigatoriamente `render_saedas_aggrid(...)` nas tabelas analíticas e de seleção.
- Evitar `st.dataframe(...)` em componentes padronizados da tela.
- Sempre separar corpo e rodapé com `split_aggrid_footer(...)` quando houver total.
- Exportação CSV com `;` e `utf-8-sig`.
- Linha `TOTAL`:
  - deve permanecer na última posição;
  - não pode ser selecionável na tabela mestre.

## Checklist de Recuperação
1. Validar carga dos datasets principal, aluno, ano e base Home.
2. Validar seletor de ano no padrão da Home.
3. Validar sync URG tabela <-> sidebar (seleção e remoção).
4. Validar sync Escola tabela <-> sidebar (seleção e remoção).
5. Validar proteção anti-loop com `last_interaction_source`.
6. Validar indicadores e cards (estilo e consistência dos totais).
7. Validar ordem da tabela ANO igual aos indicadores gerais.
8. Validar `TOTAL` no final e não selecionável.
9. Validar presença de toolbar nas tabelas analíticas.
10. Validar wrappers `.selection-master-table` e `.st-table-with-total`.
11. Validar detalhamento por aluno após filtros cruzados.

## Comandos Úteis
- `streamlit run app/app.py`
- `python -m py_compile app/app_pages/medico.py app/utils/page_helpers.py app/components/sidebar_filters.py`
- `rg -n "render_saedas_aggrid\\(|render_table_toolbar\\(|split_aggrid_footer\\(|global_urgs|global_years" app/app_pages/medico.py app/utils/page_helpers.py`
- `rg -n "st\\.dataframe\\(|last_interaction_source|pending_sidebar_|selection-master-table|st-table-with-total" app/app_pages/medico.py app/utils/page_helpers.py`
