# Spec: Página de Atendimentos de Professor

**Arquivo:** `app/app_pages/professor.py`
**Função de entrada:** `page_professor()`
**Título:** Visão Geral dos Atendimentos de Professor

---

## 1. Fontes de Dados

| Variável | Arquivo CSV | Schema |
|---|---|---|
| `df` (principal) | `data/DashboardProfessor.csv` | `SCHEMA_PROFESSOR` |
| `df_aluno_raw` | `data/DashboardProfessorAluno.csv` | `SCHEMA_PROFESSOR_ALUNO` |
| `df_ano` | `data/DashboardProfessorAno.csv` | `SCHEMA_PROFESSOR_ANO` |
| `df_home` | `data/DashboardHome.csv` | `SCHEMA_HOME` |

Carga centralizada em `carregar_dados_professor()`, retornando dicionário com chaves
`principal`, `aluno`, `ano`, `home`.

### Renomeação de colunas após carga

| CSV original (principal) | Nome interno |
|---|---|
| `Descricao` | `Atendimento` |
| `Qtd` | `Quantidade` |

| CSV original (aluno) | Nome interno |
|---|---|
| `DtNasc` | `DataNascimento` |
| `Profissional` | `Profissional` |

`DataNascimento` em `df_aluno` é convertida via `pd.to_datetime(..., errors="coerce")`.

---

## 2. Filtros da Sidebar

Ativados via `sidebar_filters(df, {"ano": True, "urg": True, "escola": True, "tipo": True})`.

| Filtro | Chave session_state |
|---|---|
| Ano(s) | `sidebar_year_filter` |
| URG(s) | `sidebar_urg_filter` |
| Escola(s) | `sidebar_escola_filter` |
| Tipo(s) | `sidebar_tipo_filter` |

Observação: o filtro de Atendimento foi removido conforme comentário no código
(`# Filtro de Atendimento removido conforme solicitação`). A variável
`atendimentos_selecionados` permanece como `[]`.

A função `toggle_atendimento(label)` existe no código mas não é referenciada por
nenhum card (mantida para reuso futuro).

---

## 3. Seletor Temporal Mestre

- Componente `st.segmented_control` em `st.container(key="massive_year_selector")`.
- Opções: últimos 5 anos a partir de `datetime.datetime.now().year`, ordem decrescente.
- `selection_mode="multi"`, key `home_year_buttons`, callback `sync_home_to_sidebar`.
- Estado de verdade: `st.session_state["global_years"]`.

---

## 4. Hierarquia de Bases de Dados

```
df (bruto, renomeado)
 └─► df_base_sem_escola  [filtros: Tipo, Ano]
      └─► df_base_final  [filtros: + Escola]
           └─► df_master_no_atend  [filtros: + URG]
                └─► df_master_filtrado = df_filt  [filtros: + Atendimento (atualmente vazio)]

df_base_sem_escola
 └─► df_filt_no_escola  [filtros: + URG  (sem Escola)]

df_master_no_atend
 └─► df_filt_no_atend  [= df_master_no_atend]
```

### Matriz de imunidade por base

| Base | Tipo | Ano | URG | Escola | Atendimento |
|---|---|---|---|---|---|
| `df_base_sem_escola` | ✓ | ✓ | — | — | — |
| `df_base_final` | ✓ | ✓ | — | ✓ | — |
| `df_master_no_atend` | ✓ | ✓ | ✓ | ✓ | — |
| `df_filt` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `df_filt_no_atend` | ✓ | ✓ | ✓ | ✓ | **IMUNE** |
| `df_filt_no_escola` | ✓ | ✓ | ✓ | **IMUNE** | — |

Regra: se nenhum ano estiver selecionado, `df_base_sem_escola` é zerado
(`pd.DataFrame()`).

---

## 5. Componentes e Regras de Filtro

### 5.1 Filtros Aplicados (placeholder)

- `st.empty()` criado antes do divisor.
- Preenchido com `format_filters_applied(selections, df, [...])` cobrindo
  Ano, URG, Escola e Tipo.

### 5.2 Indicadores Gerais (Cards Estáticos)

Renderizado por `render_metric_cards([...])`:

| Card | Origem |
|---|---|
| TOTAL DE ALUNOS | `df_home_filt["QtdAlunoEscola"].sum()` |
| ALUNOS ATENDIDOS | `df_home_filt["QtdAluno"].sum()` |
| ATEND. PROFESSOR | `df_filt["Quantidade"].sum()` |

`df_home_filt` aplica Ano (do `selected_years_comp`), URG (`urgs_aplicadas`) e
Escola sobre `df_home`.

Se `df_filt` estiver vazio, exibe info: "Selecione ao menos um ano para
visualizar os indicadores."

### 5.3 Tabela Comparativa de Performance por URG (Mestre)

**Base:** `df_for_urg_table` = `df` filtrado apenas por Ano (`selected_years_comp`).

- Gerada com `build_comparativo_anual(df_for_urg_table, "URG", active_row_value=current_selected_urgs)`.
- `rowSelection: "multiple"`, `rowMultiSelectWithClick: True`.
- Rodapé fixo via `pinnedBottomRowData` (linha TOTAL).
- Sync via JS `onFirstDataRendered` (`sync_selection_js`) — marca linhas pelas URGs ativas.
- Key dinâmico: `urg_table_professor_{urgs_selecionadas|none}` — anti-stale.
- Toolbar: container `professor_urg_actions_toolbar`, CSV `performance_urg_professor.csv`.
- Caption: "Esta tabela é sensível apenas ao filtro de Ano."

**Sync URG (bidirecional):**

| Origem | Ação |
|---|---|
| Sidebar → Tabela | `apply_pending_table_filters()` + JS `onFirstDataRendered` |
| Tabela → Sidebar | Se `set(new_urgs) != set(current_urgs)` → seta `global_urgs`, `pending_sidebar_urg_filter`, `last_interaction_source="table"` → `st.rerun()` |

### 5.4 Tabela Top Escolas por URG (Mestre)

**Base:** `df_filt_no_escola` filtrada por `selected_years_comp`.

- Renderizada via `render_top_por_urg(..., "Quantidade", "Principais Escolas por URG", "Escola", table_key="escola_table_selection_professor", active_row_value=st.session_state.get("sidebar_escola_filter", []), selection_mode="multiple")`.
- Toolbar gerada automaticamente: `escola_table_selection_professor_actions_toolbar`.

**Sync Escola (bidirecional):**

| Origem | Ação |
|---|---|
| Sidebar → Tabela | `sync_sidebar_escola_selection("escola_table_selection_professor")` |
| Tabela → Sidebar | Se `escolas_tabela_atual` difere de `sidebar_escola_filter` → `pending_sidebar_escola_filter`, `last_interaction_source="table_escola"` → `st.rerun()` |

Ao final do bloco: `last_interaction_source` é zerado (`""`).

### 5.5 Gráfico Distribuição por URG

**Base:** `df_filt` agregado por `groupby(["URG", "Ano"])["Quantidade"].sum()`.

- Ordenação por numeral romano via `_urg_sort_key` (depois por Ano).
- `px.bar` com `barmode="group"`, color por Ano (string categórica).
- Texto formatado em milhares com separador `.` (ex.: `3.235`).
- `hovertemplate` customizado; `hovermode="x unified"`.

### 5.6 Detalhamento por Aluno

**Base:**
1. `filter_by_sidebar_selections(df_aluno, selections)` → aplica Ano, URG, Escola, Tipo.
2. Filtra por `selected_years_comp`.

**Filtros locais adicionais (widgets inline):**

| Widget | Coluna | Key |
|---|---|---|
| Multiselect Aluno | `Aluno` | `professor_aluno_multiselect` |
| Multiselect Série | `Serie` | `professor_serie_multiselect` |
| Multiselect Turma | `Turma` | `professor_turma_multiselect` |

Caption exibe `{n} registros após filtros da sidebar`.

**Estrutura da tabela resultante:**

- `df_static`: por `["ID", "Aluno"]`, último valor de `DataNascimento`, `Sexo`,
  `Profissional`, `URG`, `Escola`, `Serie`, `Turma`.
- `df_counts`: `groupby(["ID","Ano"]).size()` → coluna `Qtd`.
- `df_pivot_ano`: pivot por Ano, valor `Qtd`, NaN → 0.
- `df_aluno_final = df_static.merge(df_pivot_ano, on="ID")`.
- Coluna `Total`: soma das colunas de ano.
- Zeros são substituídos por string vazia; inteiros formatados sem decimais.
- Coluna `Menu` = `build_perfil_link(row)` (query string `?menu=Aluno&aluno=Nome&nasc=YYYY-MM-DD`).
- `DataNascimento` formatado como `%d/%m/%Y`.
- Ordem das colunas: `ID, Aluno, DataNascimento, Sexo, Profissional, URG, Escola, Serie, Turma, [Anos...], Total, Menu`.
- Coluna `Menu` renomeada para `Perfil`.
- Limite de exibição: `preview_limit = 500`. Exibe aviso se exceder.
- Renderização: `render_aluno_detalhamento_aggrid(df_aluno_head, key="aluno_table_professor", csv_name="detalhes_alunos_professor.csv", toolbar_key="professor_aluno_actions_toolbar")`.

---

## 6. Título Dinâmico dos Indicadores

```
### Indicadores Gerais (Anos: X / URGs: X / Escolas: X)
```

Construído por `get_filter_display_string_for_title(...)`:
- `"Todos"` quando lista vazia ou igual ao conjunto total disponível.
- Caso contrário, itens ordenados separados por `, `.

---

## 7. Estado Global e Chaves de Session State

### Chaves globais (compartilhadas entre páginas)

| Chave | Tipo | Descrição |
|---|---|---|
| `global_years` | `list[int]` | Anos selecionados (fonte de verdade) |
| `global_urgs` | `list[str]` | URGs selecionadas (fonte de verdade) |
| `sidebar_year_filter` | `list[int]` | Espelho do widget de ano |
| `sidebar_urg_filter` | `list[str]` | Espelho do widget de URG |
| `sidebar_escola_filter` | `list[str]` | Espelho do widget de escola |
| `home_year_buttons` | `list[int]` | Estado do seletor temporal mestre |
| `last_interaction_source` | `str` | `""`, `"sidebar"`, `"table"`, `"table_escola"` |
| `pending_sidebar_urg_filter` | `list[str]` | Pendência de URG da tabela para a sidebar |
| `pending_sidebar_escola_filter` | `list[str]` | Pendência de Escola da tabela para a sidebar |

### Chaves locais da página

| Chave | Descrição |
|---|---|
| `professor_atendimento_multiselect` | Reservado para `toggle_atendimento` (atualmente não usado por UI) |
| `professor_aluno_multiselect` | Filtro local por Aluno |
| `professor_serie_multiselect` | Filtro local por Série |
| `professor_turma_multiselect` | Filtro local por Turma |
| `escola_table_selection_professor__selected_values` | Escolas selecionadas na tabela |
| `_prev_urg_table_key_professor` | Key anterior da AgGrid de URG (anti-stale) |
| `aluno_table_professor` | Key da AgGrid de detalhamento por aluno |

---

## 8. Regras de Sincronismo — Fluxo Completo

```
RENDER
  │
  ├─ init_global_state()
  ├─ apply_pending_table_filters()
  │    ├─ pending_sidebar_urg_filter → sidebar_urg_filter + global_urgs
  │    └─ pending_sidebar_escola_filter → sidebar_escola_filter
  │
  ├─ sidebar_filters()  [renderiza widgets]
  ├─ sync_sidebar_escola_selection("escola_table_selection_professor")
  │
  ├─ Seletor Temporal Mestre → global_years
  │
  ├─ [renderiza cards, tabela URG, tabela Escola, gráfico, detalhamento aluno]
  │
  ├─ URG table response
  │    └─ se seleção mudou → global_urgs + pending_sidebar_urg_filter
  │                       + last_interaction_source="table" → rerun()
  │
  └─ Escola sync check
       ├─ seleções diferem → pending_sidebar_escola_filter
       │    + last_interaction_source="table_escola" → rerun()
       └─ always: last_interaction_source = ""
```

---

## 9. Estilos Críticos (Injetados na Página)

Bloco `<style>` em `st.markdown(..., unsafe_allow_html=True)`:

- `.home-metric-label`, `.home-metric-value`, `.home-metric-card`, `.metric-card-static`.
- `div[class*="st-key-btn_kpi_"] button` (KPIs clicáveis — reservado).
- Toolbars agrupadas (gap zero, alinhamento e bordas):
  - `.st-key-professor_urg_actions_toolbar`
  - `.st-key-escola_table_selection_professor_actions_toolbar`
  - `.st-key-professor_cobertura_actions_toolbar`
  - `.st-key-professor_aluno_actions_toolbar`

---

## 10. Exportação de Dados

- Toolbar URG: `performance_urg_professor.csv`.
- Toolbar Escola: arquivo padrão de `render_top_por_urg`.
- Toolbar Aluno: `detalhes_alunos_professor.csv`.
- Implementação via `render_table_toolbar` (CSV com `;` e BOM UTF-8; cópia em TSV).

---

## 11. Cache e Performance

- **Redis Integration:** segue a camada de cache definida em [Redis Cache Spec](redis_cache_spec.md).
- **Estratégia em Professor:**
  - **Datasets:** cachear os 4 DataFrames base (`Principal`, `Aluno`, `Ano`, `Home`).
  - **Chaves sugeridas:**
    - `saedas:professor:dataset:main`
    - `saedas:professor:dataset:aluno`
    - `saedas:professor:dataset:ano`
    - `saedas:home:dataset:main` (reaproveitado)
  - **Invalidação:** TTL de 12 horas ou via scripts de integração.
