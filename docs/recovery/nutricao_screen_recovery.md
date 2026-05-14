# Runbook de Recuperação: Tela Nutrição

## Objetivo
Documento operacional para restaurar e alinhar a tela `Nutrição` (`app/app_pages/nutricao.py`) ao blueprint oficial em caso de regressão visual/funcional.

> Referência-base obrigatória: `docs/similar_screens_blueprint.md`.

## Escopo Funcional
- Seletor temporal mestre (mesmo padrão da Home).
- Filtros de sidebar: Ano, URG, Escola, Tipo, Situação Nutricional.
- Indicador total + cards de Situação Nutricional clicáveis.
- Tabela de performance por URG (seleção mestre).
- Tabela comparativa por ANO (Situação Nutricional).
- Gráficos de distribuição por URG e por Situação.
- Detalhamento por aluno.

## Fontes de Dados
- `data/DashboardNutricao.csv`
- `data/DashboardNutricaoAluno.csv`
- `data/DashboardNutricaoAno.csv`
- Schemas: `SCHEMA_NUTRICAO`, `SCHEMA_NUTRICAO_ALUNO`, `SCHEMA_NUTRICAO_ANO`.

## Fonte de Verdade de Estado
- Globais: `global_years`, `global_urgs`
- Sidebar: `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`
- Pendências de sync: `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`
- Controle de origem: `last_interaction_source`
- KPI Nutrição: `nutricao_situacao_multiselect`

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
- Situação Nutricional vem de `nutricao_situacao_multiselect`.

## Exceções Intencionais
- Tabela URG (seleção mestre): sensível apenas ao filtro de Ano.
- Tabela Escola (seleção mestre): imune ao próprio filtro de escola.
- Cards de Situação Nutricional: base imune ao próprio filtro (`df_filt_no_nut`) para manter opções visíveis.
- Regra de KPI:
  - card total usa `df_filt`
  - cards de categoria não se auto-filtram.

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
1. Validar carga dos 3 datasets.
2. Validar seletor de ano no padrão da Home.
3. Validar sync URG tabela <-> sidebar (seleção e remoção).
4. Validar sync Escola tabela <-> sidebar (seleção e remoção).
5. Validar proteção anti-loop com `last_interaction_source`.
6. Validar cards de Situação Nutricional (toggle + estilo).
7. Validar ordem da tabela ANO igual aos indicadores gerais.
8. Validar `TOTAL` no final e não selecionável.
9. Validar presença de toolbar nas tabelas analíticas.
10. Validar wrappers `.selection-master-table` e `.st-table-with-total`.
11. Validar detalhamento por aluno após filtros cruzados.

## Comandos Úteis
- `streamlit run app/app.py`
- `python -m py_compile app/app_pages/nutricao.py app/utils/page_helpers.py app/components/sidebar_filters.py`
- `rg -n "render_saedas_aggrid\\(|render_table_toolbar\\(|split_aggrid_footer\\(|nutricao_situacao_multiselect" app/app_pages/nutricao.py app/utils/page_helpers.py`
- `rg -n "st\\.dataframe\\(|last_interaction_source|pending_sidebar_|selection-master-table|st-table-with-total" app/app_pages/nutricao.py app/utils/page_helpers.py`
