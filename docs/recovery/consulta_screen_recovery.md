# Runbook de Recuperação — Tela Consulta

## Objetivo
Restaurar rapidamente o comportamento e a aparência da tela `Consulta` (`app/app_pages/consulta.py`) em caso de regressão visual ou funcional. Este runbook reflete o estado atual do código e deve ser usado como referência operacional, complementar à [Spec Técnica](../specs/consulta_page_spec.md).

> Para replicar o escopo em Nutrição, Vacinação e Exames, consultar `docs/similar_screens_blueprint.md`.

---

## Escopo Funcional
- Seletor temporal mestre (`massive_year_selector`) idêntico ao da Home.
- Filtros de sidebar: Ano, URG, Escola, Tipo + Encaminhamento (local).
- 3 cards de indicadores gerais + KPIs de encaminhamento (clicáveis em toggle).
- Tabela Comparativa de Performance por ANO (Encaminhamentos).
- Tabela Performance por URG (mestre, cross-filter bidirecional com sidebar).
- Tabela Top Escolas por URG (mestre, cross-filter bidirecional com sidebar).
- 2 gráficos de barras horizontais (URG e Encaminhamento).
- AgGrid de Detalhamento por Aluno com pivot por ano, total e link de perfil.

---

## Fontes de Dados
Carregadas em `carregar_dados_consulta()` com cache Redis:

| Dataset | CSV | Schema |
|---|---|---|
| `principal` | `data/DashboardConsulta.csv` | `SCHEMA_CONSULTA` |
| `aluno` | `data/DashboardConsultaAluno.csv` | `SCHEMA_CONSULTA_ALUNO` |
| `ano` | `data/DashboardConsultaAno.csv` | `SCHEMA_CONSULTA_ANO` |
| `home` | `data/DashboardHome.csv` | `SCHEMA_HOME` |

Renomeação aplicada: `Consulta→Encaminhamento`, `tipo→Tipo`, `Qtd→Quantidade`, `DtNasc→DataNascimento`.

---

## Estado (Fonte de Verdade)

Globais:
- `global_years`, `global_urgs`
- `home_year_buttons` (paridade com `global_years`)

Sidebar:
- `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`

Pendências (cross-filter tabela → sidebar):
- `pending_sidebar_urg_filter`
- `pending_sidebar_escola_filter`

Controle de origem:
- `last_interaction_source` ∈ {`""`, `"sidebar"`, `"table"`, `"table_escola"`}

Locais da página:
- `consulta_encaminhamento_multiselect` + `persistent_consulta_encaminhamento`
- `escola_table_selection_consulta__selected_values`
- `escola_table_selection_consulta__aggrid_key`
- `escola_table_selection_consulta__prev_sidebar_escola_filter`
- `_prev_urg_table_key_consulta`
- `last_df_cmp_urg_consulta`

---

## Filtros (Bases de Dados)

| Base | Imune a |
|---|---|
| `df_base_sem_escola` | URG, Escola, Encaminhamento |
| `df_base_final` | URG, Encaminhamento |
| `df_master_no_enc` / `df_filt_no_enc` | Encaminhamento |
| `df_filt` | nada (todos aplicados) |
| `df_filt_no_escola` | Escola |
| `df_for_urg_table` | URG, Escola (usado na tabela mestre URG) |

Regras:
- Cards estáticos: `df_home_filt` (Alunos) e `df_master_no_enc` (Encaminhamentos) — imunes ao filtro de Encaminhamento.
- KPIs de Encaminhamento: usam `df_filt_no_enc` para manter todas as opções visíveis.
- Componentes analíticos (gráficos, comparativo por ano): usam `df_filt`.
- Tabela URG mestre: usa `df_for_urg_table` (sem URG, sem Escola).
- Tabela Escola mestre: usa `df_filt_no_escola` (sem Escola).

---

## Sincronismos Obrigatórios

**Sidebar ↔ Anos:**
- Sidebar (multiselect) ↔ Seletor mestre (`home_year_buttons`) via `sync_sidebar_to_home` / `sync_home_to_sidebar`.

**Sidebar ↔ URG:**
- Sidebar → Tabela: `apply_pending_table_filters` + JS `onFirstDataRendered`.
- Tabela → Sidebar: `pending_sidebar_urg_filter` + `global_urgs` + `last="table"` + `st.rerun()`.

**Sidebar ↔ Escola:**
- Sidebar → Tabela: `sync_sidebar_escola_selection("escola_table_selection_consulta")`.
- Tabela → Sidebar: bloco pós-render, `pending_sidebar_escola_filter` + `last="table_escola"` + `st.rerun()`.
- Ao final do bloco: `last_interaction_source = ""` (anti-loop).

**Encaminhamento (toggle ↔ multiselect):**
- `toggle_regulacao()` altera `consulta_encaminhamento_multiselect` e espelha em `persistent_consulta_encaminhamento`.
- Restauração: se a chave do widget for podada, recupera de `persistent_consulta_encaminhamento`.

---

## Estilos Críticos (não remover)

- Seletor de ano: `.st-key-massive_year_selector ...` (mesma identidade da Home).
- Cards de métrica:
  - `.home-metric-card`, `.metric-card-static`, `.home-metric-link`
  - `.home-metric-label`, `.home-metric-value`
- KPIs toggle:
  - `div[class*="st-key-btn_kpi_"] button` (e regras de `p`, `strong`, `kind="primary"`)
- Toolbars agrupadas (Copiar + CSV):
  - `st-key-consulta_urg_actions_toolbar`
  - `st-key-consulta_ano_actions_toolbar`
  - `st-key-consulta_reg_actions_toolbar`
  - `st-key-consulta_aluno_actions_toolbar`
  - `st-key-escola_table_selection_consulta_actions_toolbar`
  - `st-key-encaminhamento_simple_actions_toolbar`
- Wrappers de tabela:
  - `.selection-master-table` (tabelas mestre + AgGrid de alunos)
  - `.st-table-with-total` (tabela comparativa por ano)

---

## Padrão Técnico AgGrid

- Render sempre via `render_saedas_aggrid(...)`.
- Toolbar precedente via `render_table_toolbar(...)` dentro de `st.container(key="<toolbar_key>")`.
- Rodapé via `pinnedBottomRowData` em comparativos.
- Altura inteligente com piso de 5 linhas e teto de 20 (`calcular_altura_aggrid`).
- Stale-guard nas tabelas mestre via key composta (URG e Escola).

---

## Checklist de Recuperação

1. Validar carga dos 4 datasets (principal, aluno, ano, home).
2. Validar Redis: cache hit reporta `encoding_usado = "Redis (Cache)"`; fallback grava após `load_csv`.
3. Validar seletor de ano (visual e comportamento) idêntico à Home.
4. Validar os 3 cards estáticos com cálculos corretos e imunidade ao filtro de Encaminhamento.
5. Validar KPIs de Encaminhamento clicáveis (toggle) e card ativo destacado.
6. Validar título dinâmico de Indicadores Gerais (Anos / URGs / Escolas / Regulações).
7. Validar Tabela Comparativa por Ano (ordem dos KPIs respeitada, `TOTAL` ao final, captions).
8. Validar sync bidirecional URG (sidebar ↔ tabela), inclusive limpeza total.
9. Validar sync bidirecional Escola (sidebar ↔ tabela mestre), inclusive limpeza total.
10. Validar gráficos (URG e Encaminhamento) usando `df_filt`.
11. Validar AgGrid de Alunos: pivot por ano, contagem `Total`, link Perfil em nova navegação.
12. Validar toolbars agrupadas em todas as tabelas (Copiar + CSV).

---

## Comandos Úteis

- Execução local: `streamlit run app/main.py`
- Compilação dos módulos afetados:
  ```bash
  python -m py_compile app/app_pages/consulta.py app/utils/page_helpers.py app/utils/state_manager.py app/components/sidebar_filters.py
  ```
- Verificação rápida de chaves de estado/render:
  ```bash
  rg -n "render_saedas_aggrid\(|render_table_toolbar\(|escola_table_selection_consulta__selected_values|consulta_encaminhamento_multiselect|_prev_urg_table_key_consulta" app/app_pages/consulta.py app/utils/page_helpers.py
  ```
- Limpar cache Redis (se aplicável): invalidar chaves `saedas:consulta:dataset:*` e `saedas:home:dataset:main`.
