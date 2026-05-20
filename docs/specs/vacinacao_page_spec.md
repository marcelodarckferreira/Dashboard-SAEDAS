# Spec: Página de Vacinação

**Arquivo:** `app/app_pages/vacinacao.py`
**Função de entrada:** `page_vacinacao()`
**Título:** Visão Geral da Vacinação

A página monitora a cobertura vacinal e o volume de doses aplicadas por ano, URG, escola e tipo de vacina, com detalhamento por aluno.

---

## 1. Fontes de Dados

Datasets carregados em `carregar_dados_vacinacao()`:

| Variável | Arquivo CSV | Schema |
|---|---|---|
| `df` (principal) | `data/DashboardVacinacao.csv` | `SCHEMA_VACINACAO` |
| `df_aluno_raw` | `data/DashboardVacinacaoAluno.csv` | `SCHEMA_VACINACAO_ALUNO` |
| `df_ano` | `data/DashboardVacinacaoAno.csv` | `SCHEMA_VACINACAO_ANO` |
| `df_home` | `data/DashboardHome.csv` | `SCHEMA_HOME` |

### Schemas (colunas esperadas)

- **`SCHEMA_VACINACAO`:** `Ano, URG, Escola, Vacina, Qtd, Tipo`.
- **`SCHEMA_VACINACAO_ALUNO`:** `Ano, Aluno, DtNasc, Sexo, Vacina, Dose, Lote, IdUrg, URG, Escola, Tipo, Serie, Turma`.
- **`SCHEMA_VACINACAO_ANO`:** `URG, Escola, Vacina, 2022, 2023, 2024, 2025, 2026, Total`.
- **`SCHEMA_HOME`:** usado apenas para os KPIs demográficos (`QtdAlunoEscola`, `QtdAluno`).

### Renomeação de colunas após carga

| CSV original | Nome interno |
|---|---|
| `Qtd` (principal) | `Quantidade` |
| `tipo` (principal) | `Tipo` |
| `DtNasc` (aluno) | `DataNascimento` (convertido para datetime) |

Se `info_aluno["erros"]` ou `info_ano["erros"]` ocorrerem, são exibidos como `st.warning` e o respectivo DataFrame é zerado. Erros em `info` principal abortam a página.

---

## 2. Filtros da Sidebar

Ativados via `sidebar_filters(df, {"ano": True, "urg": True, "escola": True, "tipo": True})`.

| Filtro | Chave session_state | Origem |
|---|---|---|
| Ano(s) | `sidebar_year_filter` | `sidebar_filters` |
| URG(s) | `sidebar_urg_filter` | `sidebar_filters` |
| Escola(s) | `sidebar_escola_filter` | `sidebar_filters` |
| Tipo(s) | `sidebar_tipo_filter` | `sidebar_filters` |
| Vacina(s) | `vacinacao_vacina_multiselect` | `st.sidebar.multiselect` (na página) |

- Título da sidebar: `"Filtros - Vacinação"`.
- O filtro de **Vacina** é renderizado diretamente pela página (não pelo `sidebar_filters`), com `placeholder="Todas"` e callback `sync_local_vacinacao_vacina` (sincroniza `persistent_vacinacao_vacina`).
- `apply_pending_table_filters()` é chamado antes de instanciar a sidebar para aplicar pendências de cross-filter (URG/Escola).
- `sync_sidebar_escola_selection("escola_table_selection_vacinacao")` espelha mudanças da sidebar de escola para a chave da tabela de seleção.

---

## 3. Seletor Temporal Mestre

- `st.segmented_control` (modo `multi`) dentro de `st.container(key="massive_year_selector")`.
- Opções: últimos 5 anos (`current_year - i`).
- Chave: `home_year_buttons`; callback `sync_home_to_sidebar`.
- Variável local: `selected_years_comp = st.session_state["global_years"]`.

---

## 4. Bases Filtradas (Pipeline)

1. `df_base_sem_escola` — copia `df`, aplica Tipo (se subconjunto) e Anos (`global_years`).
2. `df_base_final` — aplica Escola (se subconjunto).
3. `df_master_no_vac` — aplica URG (`global_urgs`) sobre `df_base_final`; **ignora vacina** (usado em cards, tabela ANO, KPI cards toggle).
4. `df_master_filtrado` / `df_filt` — aplica Vacina sobre `df_master_no_vac`. É a base analítica final.
5. `df_filt_no_escola` — `df_base_sem_escola` + URG (sem escola; usado em "Top Escolas por URG").
6. `df_filt_no_vac` = `df_master_no_vac` (alias para cálculos imunes ao filtro de vacina).
7. `df_for_urg_table` — `df_base_sem_escola` + Vacina; **imune a URG** (tabela mestre de URG).

---

## 5. Indicadores e KPIs

### 5.1 Cards demográficos (linha 1)
`render_metric_cards([...])`:
- **TOTAL DE ALUNOS** — `df_home_filt["QtdAlunoEscola"].sum()`.
- **ALUNOS ATENDIDOS** — `df_home_filt["QtdAluno"].sum()`.
- **VACINADOS/APLICAÇÃO** — formato `"{alunos}/{doses}"`:
  - `alunos`: contagem única de `(Aluno, DataNascimento)` em `df_aluno_kpi_global` (respeita Ano/URG/Escola; **ignora Vacina**).
  - `doses`: `df_filt_no_vac["Quantidade"].sum()`.

### 5.2 KPI Cards por Vacina (toggle)
- Base: `vacinas_sum = df_filt_no_vac.groupby("Vacina")["Quantidade"].sum()` (descendente, > 0).
- Renderizados em blocos de 5 via `render_metric_cards(chunk, is_toggle=True, active_labels=..., on_click_callback=toggle_vacinacao)`.
- `toggle_vacinacao(vac_name)` alterna o nome em `vacinacao_vacina_multiselect` e atualiza `persistent_vacinacao_vacina`.
- Se `vacinas_sum` vazio: `st.info("Selecione ao menos um ano para visualizar os indicadores.")`.

### 5.3 Título dinâmico
`filtro_titulo` é construído via `get_filter_display_string_for_title(...)` retornando `"Todos"` quando seleção = universo. Formato: `"Anos: ... / URGs: ... / Escolas: ... / Vacinas: ..."`. Renderizado em `### Indicadores Gerais ({filtro_titulo})`.

Linha "Filtros aplicados" via `format_filters_applied(...)` em `filters_placeholder` (chaves: ano, urg, escola, tipo, vacina).

---

## 6. Tabelas AgGrid

### 6.1 Tabela Comparativa por ANO (Vacina)
- Base: `build_comparativo_anual(df_filt, "Vacina", value_col="Quantidade", pct_label="Total")`.
- `prepare_comparativo_aggrid_data(..., include_selection_column=False)`.
- **Ordenação custom:** mesma ordem dos KPI Cards (`vacinas_sum`); linha `TOTAL` sempre por último.
- `_ajustar_colunas_ano_vacina`: header "Vacina" alinhado à esquerda (`saedas-aggrid-left-header`); colunas de ano com `saedas-aggrid-centered-header`.
- `split_aggrid_footer(...)` separa total → `pinnedBottomRowData`.
- Toolbar: container `vacinacao_ano_actions_toolbar`; arquivo `comparativo_vacinacao_ano.csv`; key `ano_table_vacinacao`.
- Grid key: `ano_table_vacinacao_aggrid`. Wrapper: `.st-table-with-total`. `min_height=140`.
- Caption: percentual de representatividade da Vacina sobre o total do ano.

### 6.2 Tabela Mestre — Performance por URG
- Base: `df_for_urg_table` (imune a URG, sensível a Vacina).
- `build_comparativo_anual(..., "URG", active_row_value=global_urgs)`.
- `rowSelection: "multiple"`, `rowMultiSelectWithClick: True`.
- `onFirstDataRendered`: `JsCode` que marca linhas conforme `global_urgs`.
- Toolbar: container `vacinacao_urg_actions_toolbar`; arquivo `performance_urg_vacinacao.csv`; key `urg_table_vacinacao`.
- Grid key dinâmica: `urg_table_vacinacao_{anos}_{vacinas}_{urgs}` com controle anti-loop via `_prev_urg_table_key_vacinacao`.
- Wrapper: `.selection-master-table`.
- **Cross-filter:** seleções diferentes de `global_urgs` (excluindo "TOTAL") gravam `global_urgs` + `pending_sidebar_urg_filter`, marcam `last_interaction_source = "table"` e chamam `st.rerun()`.
- Caption: "Clique em qualquer linha de URG para filtrar o restante do dashboard."

### 6.3 Top Escolas por URG (via `render_top_por_urg`)
- Base: `df_for_top_escolas` = `df_filt_no_escola` + filtro de vacina + filtro de anos.
- Chamada: `render_top_por_urg(..., "Quantidade", "Principais Escolas por URG", "Escola", table_key="escola_table_selection_vacinacao", active_row_value=sidebar_escola_filter, selection_mode="multiple")`.
- Toolbar derivada: `escola_table_selection_vacinacao_actions_toolbar`.
- **Cross-filter:** `escola_table_selection_vacinacao__selected_values` ≠ `sidebar_escola_filter` → grava `pending_sidebar_escola_filter`, `last_interaction_source = "table_escola"` e `st.rerun()`. Após, `last_interaction_source` é resetado para `""`.

### 6.4 Detalhamento por Aluno (`render_aluno_detalhamento_aggrid`)
- Base: `df_aluno_base = filter_by_sidebar_selections(df_aluno, selections)` + filtro vacina (sidebar).
- Filtros locais adicionais (st.multiselect, default `[]`): **Aluno**, **Série**, **Turma**.
- Caption: `"{n} registros após filtros da sidebar [e de vacina]"`.
- Construção do pivô:
  1. `df_static` — atributos estáticos (`Sexo, URG, Escola, Serie, Turma`) por `(Aluno, DataNascimento)`.
  2. `df_desc` — função `format_vac_list` por `(Aluno, DataNascimento, Ano)`: vacinas em UPPERCASE quando selecionadas (sidebar ou tabela), senão `lower().capitalize()`.
  3. Pivô por Ano: colunas dinâmicas com descrição textual.
  4. `Total` — contagem de registros por aluno.
  5. `Menu/Perfil` — URL via `build_perfil_link` (`?menu=Aluno&aluno=...&nasc=YYYY-MM-DD`).
  6. `DataNascimento` formatada `dd/mm/aaaa`.
- Ordem final de colunas: `Aluno, DataNascimento, Sexo, URG, Escola, Serie, Turma, {anos...}, Total, Perfil`.
- Key tabela: `aluno_table_vacinacao`; toolbar: `vacinacao_aluno_actions_toolbar`; csv: `detalhes_alunos_vacinacao.csv`.

---

## 7. Gráficos

- `render_grouped_bar_anual(df_filt, "Quantidade", "", orientation="h")` — **Comparativo Anual de Vacinação por URG**.
- `render_grouped_bar_anual(df_filt, "Quantidade", "", x_col="Vacina", orientation="h")` — **Distribuição por Tipo de Vacina**.

---

## 8. Estado (session_state)

### Globais
- `global_years`, `global_urgs`.

### Sidebar / sync
- `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`, `sidebar_tipo_filter`.
- `home_year_buttons` (seletor mestre).
- `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`.
- `last_interaction_source` (`"sidebar"`, `"table"`, `"table_escola"` ou `""`).

### Filtros locais
- `vacinacao_vacina_multiselect` (widget).
- `persistent_vacinacao_vacina` (persistência entre páginas via `init_global_state`).

### Tabelas
- `escola_table_selection_vacinacao__selected_values`.
- `escola_table_selection_vacinacao__prev_sidebar_escola_filter`.
- `_prev_urg_table_key_vacinacao` (anti-loop URG).
- `_is_page_first_run`.

### Containers/toolbars (chaves)
- `massive_year_selector`
- `vacinacao_ano_actions_toolbar`
- `vacinacao_urg_actions_toolbar`
- `escola_table_selection_vacinacao_actions_toolbar`
- `vacina_actions_toolbar` (declarada no CSS; reservada)
- `vacinacao_aluno_actions_toolbar`

---

## 9. CSS / Padrões Visuais

- Bloco `<style>` injetado contém:
  - Classes `.home-metric-card`, `.metric-card-static`, `.home-metric-label`, `.home-metric-value`.
  - Botões KPI: `div[class*="st-key-btn_kpi_"] button` (min-height 96px, hover glow `#38bdf8`, estado `primary` com gradiente).
  - Agrupamento e bordas das toolbars listadas acima (botões com `border-radius` 6px nos extremos e remoção de gaps).
- Wrappers obrigatórios:
  - `.selection-master-table` — tabela URG e detalhamento aluno.
  - `.st-table-with-total` — tabela comparativa por ANO.

---

## 10. Integração Redis

- Não há chamadas diretas a Redis em `vacinacao.py`. O cache, quando habilitado, é injetado via `app/utils/data_loader.load_csv` (camada definida em [Redis Cache Spec](redis_cache_spec.md)).
- Estratégia recomendada (alinhada ao padrão das demais telas):
  - Chaves: `saedas:vacinacao:dataset:{principal|aluno|ano|home}`.
  - TTL: 12 horas (ou invalidação por script de ingestão).

---

## 11. Regras de Negócio

- **Imunidade ao filtro de Vacina:** cards demográficos, "Vacinados/Aplicação" (alunos), tabela ANO e KPI cards usam `df_filt_no_vac`.
- **Tabela URG (mestre):** imune ao próprio filtro de URG; sensível a Vacina, Ano, Tipo e Escola.
- **Top Escolas:** imune ao próprio filtro de Escola; sensível aos demais.
- **Detalhamento aluno:** vacinas selecionadas (sidebar ou via destaque cruzado) aparecem em UPPERCASE.
- **Linha TOTAL** nunca é selecionável e permanece sempre como `pinnedBottomRowData`.

---

## 12. Componentes Auxiliares (`app/utils/page_helpers.py`)

`render_section_divider`, `filter_by_sidebar_selections`, `format_filters_applied`, `build_comparativo_anual`, `prepare_comparativo_aggrid_data`, `split_aggrid_footer`, `render_saedas_aggrid`, `render_table_toolbar`, `render_top_por_urg`, `render_grouped_bar_anual`, `render_aluno_detalhamento_aggrid`, `toggle_multiselect_value`.

Callbacks utilizados de `state_manager.py`: `init_global_state`, `apply_pending_table_filters`, `sync_sidebar_escola_selection`, `sync_home_to_sidebar`, `sync_home_urg_to_sidebar`, `sync_local_vacinacao_vacina`.
