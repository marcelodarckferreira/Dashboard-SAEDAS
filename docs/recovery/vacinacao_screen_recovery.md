# Runbook de Recuperação — Tela Vacinação

**Arquivo alvo:** `app/app_pages/vacinacao.py`
**Função de entrada:** `page_vacinacao()`
**Spec de referência:** `docs/specs/vacinacao_page_spec.md`
**Blueprint padrão:** `docs/similar_screens_blueprint.md`

---

## 1. Escopo Funcional

- Seletor temporal mestre (`massive_year_selector`, padrão Home).
- Filtros de sidebar: Ano, URG, Escola, Tipo, Vacina (multiselect próprio).
- Cards demográficos (Total de Alunos, Alunos Atendidos, Vacinados/Aplicação).
- KPI cards por Vacina em toggle (blocos de 5).
- Tabela Comparativa por ANO (Vacina) com ordenação espelhada aos KPIs.
- Tabela mestre Performance por URG (cross-filter).
- Top Escolas por URG (cross-filter de escola).
- Gráficos: comparativo anual por URG e distribuição por Vacina.
- Detalhamento por Aluno com pivô anual de vacinas.

---

## 2. Fontes de Dados

| CSV | Schema |
|---|---|
| `data/DashboardVacinacao.csv` | `SCHEMA_VACINACAO` (`Ano, URG, Escola, Vacina, Qtd, Tipo`) |
| `data/DashboardVacinacaoAluno.csv` | `SCHEMA_VACINACAO_ALUNO` (`Ano, Aluno, DtNasc, Sexo, Vacina, Dose, Lote, IdUrg, URG, Escola, Tipo, Serie, Turma`) |
| `data/DashboardVacinacaoAno.csv` | `SCHEMA_VACINACAO_ANO` (`URG, Escola, Vacina, 2022..2026, Total`) |
| `data/DashboardHome.csv` | `SCHEMA_HOME` (apenas para KPIs demográficos) |

Erros em `info` principal abortam a tela; erros nos demais limpam o DataFrame correspondente.

---

## 3. Fonte de Verdade de Estado

### Globais
- `global_years`, `global_urgs`.

### Sidebar
- `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`, `sidebar_tipo_filter`.
- Seletor mestre: `home_year_buttons` (callback `sync_home_to_sidebar`).

### Pendências (cross-filter tabela → sidebar)
- `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`.
- Aplicadas por `apply_pending_table_filters()` antes da sidebar.

### Origem da última interação
- `last_interaction_source` ∈ {`""`, `"sidebar"`, `"table"`, `"table_escola"`}.

### Filtro local (Vacina)
- Widget: `vacinacao_vacina_multiselect` (com `on_change=sync_local_vacinacao_vacina`).
- Persistência: `persistent_vacinacao_vacina` (inicializada em `init_global_state`).

### Chaves de tabela
- `escola_table_selection_vacinacao__selected_values`
- `escola_table_selection_vacinacao__prev_sidebar_escola_filter`
- `_prev_urg_table_key_vacinacao`
- `_is_page_first_run`

---

## 4. Containers / Toolbars (chaves)

- `massive_year_selector`
- `vacinacao_ano_actions_toolbar` → CSV `comparativo_vacinacao_ano.csv`, key `ano_table_vacinacao`
- `vacinacao_urg_actions_toolbar` → CSV `performance_urg_vacinacao.csv`, key `urg_table_vacinacao`
- `escola_table_selection_vacinacao_actions_toolbar` (auto via `render_top_por_urg`)
- `vacinacao_aluno_actions_toolbar` → CSV `detalhes_alunos_vacinacao.csv`, key `aluno_table_vacinacao`
- `vacina_actions_toolbar` (declarada no CSS, reservada)

---

## 5. Pipeline de Bases

1. `df_base_sem_escola` ← `df` + Tipo + Anos (`global_years`).
2. `df_base_final` ← + Escola.
3. `df_master_no_vac` ← + URG (`global_urgs`) — **imune a vacina**.
4. `df_filt` = `df_master_filtrado` ← + Vacina (base analítica).
5. `df_filt_no_escola` ← `df_base_sem_escola` + URG (Top Escolas).
6. `df_filt_no_vac` = `df_master_no_vac` (cards + KPIs + tabela ANO).
7. `df_for_urg_table` ← `df_base_sem_escola` + Vacina (tabela mestre URG).

---

## 6. Contrato de Sincronismo

- Sidebar Vacina ↔ KPI toggle:
  - Toggle nos cards chama `toggle_vacinacao(vac)` → atualiza `vacinacao_vacina_multiselect` e `persistent_vacinacao_vacina`.
  - Multiselect chama `sync_local_vacinacao_vacina`.
- Sidebar Escola ↔ Tabela Top Escolas:
  - `sync_sidebar_escola_selection("escola_table_selection_vacinacao")` espelha sidebar → tabela.
  - Mudança na tabela grava `pending_sidebar_escola_filter`, marca `last_interaction_source = "table_escola"` e dispara `st.rerun()`. Após, é resetado para `""`.
- Sidebar URG ↔ Tabela URG:
  - Pré-seleção via `onFirstDataRendered` (JsCode com `global_urgs`).
  - Seleção diferente atualiza `global_urgs` + `pending_sidebar_urg_filter` + `st.rerun()`.

### Anti-loop
- `_prev_urg_table_key_vacinacao` evita reprocessar seleção quando a key da grade muda (filtros alteram a key).
- `_is_page_first_run` neutraliza primeira renderização.

---

## 7. Exceções Intencionais

- Tabela URG (mestre): **imune a URG**, sensível a Vacina/Ano/Tipo/Escola.
- Tabela Top Escolas: **imune a Escola**, sensível aos demais.
- Cards demográficos e KPI cards: usam `df_filt_no_vac` (ignoram Vacina).
- Card "Vacinados" (alunos únicos): usa `df_aluno_kpi_global` filtrado por Ano/URG/Escola (ignora Vacina).
- Linha `TOTAL` em `pinnedBottomRowData`, nunca selecionável.

---

## 8. Regras Obrigatórias de UI

- Seletor de Ano idêntico à Home (`st.segmented_control`, modo `multi`).
- Indicadores em grids; KPIs em blocos de 5 colunas.
- Tabela ANO ordenada igual aos KPI cards (`vacinas_sum`); `TOTAL` por último (controlado por `_is_total` + `_ordem_kpi`).
- Toolbars via `render_table_toolbar(...)` dentro de `st.container(key=...)`.
- Wrappers obrigatórios:
  - `.selection-master-table` (URG, detalhamento aluno).
  - `.st-table-with-total` (tabela ANO).
- Classes CSS críticas: `.home-metric-card`, `.metric-card-static`, `.home-metric-label`, `.home-metric-value`, `div[class*="st-key-btn_kpi_"] button`.

---

## 9. Padrão Técnico de Tabelas

- Sempre `render_saedas_aggrid(...)`; nunca `st.dataframe(...)`.
- Sempre `split_aggrid_footer(...)` quando houver TOTAL.
- Exportação CSV: separador `;`, encoding `utf-8-sig` (gerada por `render_table_toolbar`).
- Detalhamento aluno via `render_aluno_detalhamento_aggrid` (inclui toolbar + link Perfil).

---

## 10. Checklist de Recuperação

1. Carga dos 4 datasets (principal, aluno, ano, home) sem erros bloqueantes.
2. Renomeações aplicadas (`Qtd→Quantidade`, `tipo→Tipo`, `DtNasc→DataNascimento`).
3. Seletor mestre `massive_year_selector` no padrão Home.
4. Sidebar com Ano/URG/Escola/Tipo + multiselect Vacina (`vacinacao_vacina_multiselect`).
5. `apply_pending_table_filters()` chamado **antes** de `sidebar_filters`.
6. `sync_sidebar_escola_selection("escola_table_selection_vacinacao")` ativo.
7. Sync URG tabela ↔ sidebar (seleção e remoção total).
8. Sync Escola tabela ↔ sidebar (seleção e remoção total).
9. KPI cards por Vacina em toggle, com `active_labels` e callback `toggle_vacinacao`.
10. Ordem da tabela ANO espelha KPIs; `TOTAL` ao final.
11. Toolbars presentes nas 4 tabelas (ANO, URG, Escola, Aluno).
12. Wrappers `.selection-master-table` e `.st-table-with-total` aplicados.
13. Detalhamento aluno com filtros Aluno/Série/Turma e pivô anual por vacina.
14. Card "Vacinados/Aplicação" no formato `"{alunos_unicos}/{doses}"`.

---

## 11. Comandos Úteis

- Executar app: `streamlit run app/main.py`
- Sintaxe: `python -m py_compile app/app_pages/vacinacao.py app/utils/page_helpers.py app/utils/state_manager.py`
- Validação de chaves:
  - `rg -n "vacinacao_vacina_multiselect|persistent_vacinacao_vacina|escola_table_selection_vacinacao|urg_table_vacinacao|aluno_table_vacinacao" app/app_pages/vacinacao.py`
  - `rg -n "vacinacao_ano_actions_toolbar|vacinacao_urg_actions_toolbar|vacinacao_aluno_actions_toolbar|vacina_actions_toolbar" app/app_pages/vacinacao.py`
  - `rg -n "st\\.dataframe\\(|render_saedas_aggrid\\(|render_table_toolbar\\(|split_aggrid_footer\\(" app/app_pages/vacinacao.py`
  - `rg -n "last_interaction_source|pending_sidebar_|selection-master-table|st-table-with-total" app/app_pages/vacinacao.py`
