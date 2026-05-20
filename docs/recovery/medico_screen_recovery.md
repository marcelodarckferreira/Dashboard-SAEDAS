# Runbook de Recuperação: Tela Médico

## Objetivo
Documento operacional para restaurar e alinhar a tela `Médico` (`app/app_pages/medico.py`) ao blueprint oficial em caso de regressão visual/funcional.

> Referência-base obrigatória: `docs/similar_screens_blueprint.md`.
> Especificação técnica: `docs/specs/medico_page_spec.md`.

---

## 1. Escopo Funcional
- Seletor temporal mestre (`massive_year_selector` / `home_year_buttons`) no padrão da Home.
- Filtros de sidebar: Ano, URG, Escola, Tipo.
- Indicadores gerais: TOTAL DE ALUNOS, ALUNOS ATENDIDOS, ATEND. MÉDICO.
- Tabela mestre de Performance por URG (sensível apenas a Ano).
- Tabela mestre Top Escolas por URG (imune ao filtro de Escola).
- Gráfico de Distribuição por URG (ordenado por numeral romano).
- Detalhamento por Aluno via AgGrid com pivot por Ano + coluna Total + link Perfil.

> Observação: nesta versão **não há filtro/KPI de Atendimento ativo** (removido conforme decisão de produto). A função `toggle_atendimento` permanece declarada mas não é acionada.

---

## 2. Fontes de Dados
- `data/DashboardMedico.csv` → `SCHEMA_MEDICO` (`Ano, IdUrg, URG, Escola, Tipo, Descricao, Qtd`)
- `data/DashboardMedicoAluno.csv` → `SCHEMA_MEDICO_ALUNO` (`Ano, ID, Aluno, DtNasc, Sexo, Profissional, IdUrg, URG, Escola, Tipo, Serie, Turma`)
- `data/DashboardMedicoAno.csv` → `SCHEMA_MEDICO_ANO`
- `data/DashboardHome.csv` → `SCHEMA_HOME` (apoio para totais de aluno)

Renomeações: `Descricao → Atendimento`, `Qtd → Quantidade`, `DtNasc → DataNascimento`.

---

## 3. Fonte de Verdade de Estado
- Globais: `global_years`, `global_urgs`
- Sidebar: `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`, `sidebar_tipo_filter`
- Pendências de sync: `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`
- Controle de origem: `last_interaction_source` (`""`, `"sidebar"`, `"table"`, `"table_escola"`)
- Stale-guard de tabelas mestres: `_prev_urg_table_key_medico`, `escola_table_selection_medico__selected_values`

---

## 4. Contrato de Sincronismo (Obrigatório)
- Two-way binding entre sidebar e tabelas mestres (URG e Escola).
- Fluxo:
  - `Sidebar → estado global → seleção visual da tabela` (via `apply_pending_table_filters()` e `sync_sidebar_escola_selection`).
  - `Tabela → estado global → sidebar_*_filter` (via `pending_sidebar_*_filter` + `st.rerun()`).
- Anti-loop:
  - origem `"sidebar"`: tabela não sobrescreve sidebar no mesmo ciclo;
  - origem `"table"` ou `"table_escola"`: aplica pendência e `rerun()`;
  - ao final do bloco de escola, zera `last_interaction_source = ""`.
- Linha `TOTAL` não pode ser selecionável na tabela mestre URG (filtro `str(...) != "TOTAL"`).

---

## 5. Regras de Filtro
- `df_filt` é a base final para componentes analíticos.
- Ano vem de `global_years` (`selected_years_comp`).
- URG vem de `global_urgs` (`current_urgs`).
- Escola e Tipo vêm de `selections` da sidebar.
- Cadeia de bases: `df_base_sem_escola → df_base_final → df_master_no_atend → df_filt`.
- Auxiliar: `df_filt_no_escola` para a tabela mestre de Escolas.

### Exceções intencionais
- Tabela URG (mestre): sensível **apenas** ao filtro de Ano.
- Tabela Escola (mestre): **imune** ao próprio filtro de Escola.
- Cards de indicador combinam `df_home` (alunos) e `df_filt` (atendimentos).

---

## 6. Regras Obrigatórias de UI
- Seletor temporal: container `massive_year_selector`, widget key `home_year_buttons`, `selection_mode="multi"`, `on_change=sync_home_to_sidebar`.
- Indicadores gerais via `render_metric_cards(...)` (3 cards).
- Tabela URG com TOTAL no rodapé fixo (`pinnedBottomRowData`) — não selecionável.
- Toolbars agrupadas (`Copiar` + `CSV`) via `render_table_toolbar(...)`:
  - `medico_urg_actions_toolbar`
  - `escola_table_selection_medico_actions_toolbar` (interno a `render_top_por_urg`)
  - `medico_aluno_actions_toolbar` (interno a `render_aluno_detalhamento_aggrid`)
- Tabelas mestre devem usar wrapper `.selection-master-table`.
- Classes críticas: `.home-metric-card`, `.metric-card-static`, `.home-metric-label`, `.home-metric-value`, `div[class*="st-key-btn_kpi_"] button`.

---

## 7. Padrão Técnico de Tabelas
- `render_saedas_aggrid(...)` para tabelas analíticas e mestres.
- `prepare_comparativo_aggrid_data(...)` + `split_aggrid_footer(...)` quando houver TOTAL.
- `render_aluno_detalhamento_aggrid(...)` para detalhamento por aluno (AgGrid padronizado).
- Exportação CSV com `;` e `utf-8-sig` via helper de toolbar.
- Nomes de CSV exportado:
  - URG → `performance_urg_medico.csv`
  - Aluno → `detalhes_alunos_medico.csv`

---

## 8. Detalhamento por Aluno — Regras
- Pipeline: `groupby([ID,Aluno]).last()` (estáticos) + `pivot(Ano)` (contagens) + `Total`.
- Zeros viram string vazia; inteiros viram texto.
- Coluna `Perfil` (renomeada de `Menu`) via `build_perfil_link` → `?menu=Aluno&aluno=<Nome>&nasc=YYYY-MM-DD`.
- Limite: `preview_limit = 500` linhas.
- Filtros inline: `medico_aluno_multiselect`, `medico_serie_multiselect`, `medico_turma_multiselect`.

---

## 9. Cache (Redis)
- Chaves:
  - `saedas:medico:dataset:main`
  - `saedas:medico:dataset:aluno`
  - `saedas:medico:dataset:ano`
  - `saedas:home:dataset:main`
- TTL padrão: 12h.

---

## 10. Checklist de Recuperação
1. Validar carga dos quatro datasets (main, aluno, ano, home) e ausência de `info["erros"]`.
2. Validar `init_global_state()` e `apply_pending_table_filters()` antes da renderização.
3. Validar seletor de ano (`home_year_buttons`) sincronizando com `global_years`.
4. Validar sync URG tabela ⇄ sidebar (seleção, remoção, multi-seleção).
5. Validar sync Escola tabela ⇄ sidebar via `sync_sidebar_escola_selection("escola_table_selection_medico")`.
6. Validar proteção anti-loop com `last_interaction_source` (zera ao final do bloco escola).
7. Validar indicadores: TOTAL DE ALUNOS (`QtdAlunoEscola`), ALUNOS ATENDIDOS (`QtdAluno`), ATEND. MÉDICO (`Quantidade`).
8. Validar `TOTAL` no final da tabela URG e não selecionável.
9. Validar presença das toolbars `medico_urg_actions_toolbar`, `escola_table_selection_medico_actions_toolbar`, `medico_aluno_actions_toolbar`.
10. Validar wrapper `.selection-master-table` na tabela URG.
11. Validar gráfico Distribuição por URG ordenado por numeral romano (`_urg_sort_key`).
12. Validar detalhamento por aluno: pivot por Ano, coluna Total, coluna Perfil, limite de 500 linhas.

---

## 11. Comandos Úteis
- `streamlit run app/main.py`
- `python -m py_compile app/app_pages/medico.py app/utils/page_helpers.py app/utils/state_manager.py`
- Buscar usos de helpers/chaves:
  - `rg -n "render_saedas_aggrid\\(|render_table_toolbar\\(|split_aggrid_footer\\(|render_aluno_detalhamento_aggrid\\(|global_urgs|global_years" app/app_pages/medico.py app/utils/page_helpers.py`
  - `rg -n "last_interaction_source|pending_sidebar_|selection-master-table|escola_table_selection_medico|_prev_urg_table_key_medico" app/app_pages/medico.py app/utils/page_helpers.py app/utils/state_manager.py`
