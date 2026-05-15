# Spec: Página de Encaminhamentos (Consulta)

**Arquivo:** `app/app_pages/consulta.py`
**Função de entrada:** `page_consulta()`
**Título:** Visão Geral do Encaminhamento (Regulação)

---

## 1. Fontes de Dados

| Variável | Arquivo CSV | Schema |
|---|---|---|
| `df` (principal) | `data/DashboardConsulta.csv` | `SCHEMA_CONSULTA` |
| `df_aluno_raw` | `data/DashboardConsultaAluno.csv` | `SCHEMA_CONSULTA_ALUNO` |
| `df_ano` | `data/DashboardConsultaAno.csv` | `SCHEMA_CONSULTA_ANO` |
| `df_home` | `data/DashboardHome.csv` | `SCHEMA_HOME` |

### Renomeação de colunas após carga

| CSV original | Nome interno |
|---|---|
| `Consulta` | `Encaminhamento` |
| `tipo` | `Tipo` |
| `DtNasc` | `DataNascimento` |
| `Qtd` | `Quantidade` |

---

## 2. Filtros da Sidebar

Ativados via `sidebar_filters(df, {"ano": True, "urg": True, "escola": True, "tipo": True})`.

| Filtro | Chave session_state | Callback |
|---|---|---|
| Ano(s) | `sidebar_year_filter` | `sync_sidebar_to_home` |
| URG(s) | `sidebar_urg_filter` | `sync_sidebar_urg_to_home` |
| Escola(s) | `sidebar_escola_filter` | `sync_sidebar_escola_to_global` |
| Tipo(s) | `sidebar_tipo_filter` | — |
| Encaminhamento(s) | `consulta_encaminhamento_multiselect` | toggle via `toggle_regulacao` |

O filtro de Encaminhamento é renderizado diretamente na sidebar da página (não via `sidebar_filters`).

---

## 3. Seletor Temporal Mestre

- Ver especificações em [Shared Components Spec](shared_components_spec.md#2-seletor-temporal-mestre-botoes-de-ano).

---

## 4. Hierarquia de Bases de Dados

O fluxo de dados é reativo, baseado em filtros da sidebar e seleções em tabelas "mestras" que propagam filtros para os demais componentes. Os componentes reutilizáveis (como a Toolbar de Ações) seguem a [Especificação de Componentes Compartilhados](shared_components_spec.md).

```
df (bruto)
 └─► df_base_sem_escola  [filtros: Tipo, Ano]
      └─► df_base_final  [filtros: + Escola]
           └─► df_master_no_enc  [filtros: + URG]
                └─► df_filt  [filtros: + Encaminhamento]
                └─► df_filt_no_enc  [= df_master_no_enc, sem filtro de Encaminhamento]

df_base_sem_escola
 └─► df_filt_no_escola  [filtros: + URG, + Encaminhamento  (sem Escola)]
```

### Matriz de imunidade por base

| Base | Tipo | Ano | URG | Escola | Encaminhamento |
|---|---|---|---|---|---|
| `df_base_sem_escola` | ✓ | ✓ | — | — | — |
| `df_base_final` | ✓ | ✓ | — | ✓ | — |
| `df_master_no_enc` | ✓ | ✓ | ✓ | ✓ | — |
| `df_filt` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `df_filt_no_enc` | ✓ | ✓ | ✓ | ✓ | **IMUNE** |
| `df_filt_no_escola` | ✓ | ✓ | ✓ | **IMUNE** | ✓ |

---

## 5. Componentes e Regras de Filtro

### 5.1 Filtros Aplicados (placeholder)

- Renderizado com `st.empty()` antes de qualquer componente.
- Preenchido com `format_filters_applied(selections, df, [...])` após calcular todas as seleções.
- Exibe: Ano, URG, Escola, Tipo, Regulação (Encaminhamento).

### 5.2 Indicadores Gerais (Cards Estáticos)

**Base:** `df_home_filt` (para alunos), `df_master_no_enc` (para total de encaminhamentos).

| Card | Origem | Imune a Encaminhamento |
|---|---|---|
| TOTAL DE ALUNOS | `df_home_filt["QtdAlunoEscola"].sum()` | ✓ |
| ALUNOS ATENDIDOS | `df_home_filt["QtdAluno"].sum()` | ✓ |
| ENCAMINHAMENTOS | `df_master_no_enc["Quantidade"].sum()` | ✓ |

`df_home_filt` aplica filtros de Ano, URG, Escola e Tipo sobre `df_home`.

**Regra:** esses três cards são **sempre imunes ao filtro de Encaminhamento**. São indicadores de contexto geral, não de categoria específica.

### 5.3 KPI Cards de Encaminhamento (Toggle)

**Base:** `df_filt_no_enc` → `encaminhamentos_sum = groupby("Encaminhamento")["Quantidade"].sum()`

- Apenas encaminhamentos com `Quantidade > 0` são exibidos.
- Ordenados por valor decrescente.
- Renderizados em blocos de 5 por linha via `render_metric_cards(..., is_toggle=True)`.
- Clique em um card chama `toggle_regulacao(reg_name)`, que alterna o encaminhamento em `consulta_encaminhamento_multiselect`.
- Card ativo (selecionado) recebe estilo `primary`.

**Regra:** os KPI cards de categoria são **imunes ao filtro de Encaminhamento** para exibir todas as opções disponíveis como controles de seleção.

### 5.4 Tabela Comparativa de Performance por ANO

**Base:** `df_filt` (respeita todos os filtros, incluindo Encaminhamento).

- Gerada com `build_comparativo_anual(df_filt, "Encaminhamento", value_col="Quantidade", pct_label="Total")`.
- Linhas representam cada tipo de encaminhamento presente no filtro ativo.
- Colunas: Qtd por ano, % Total por ano, Var% entre anos consecutivos, Total Geral.
- Rodapé fixo com linha TOTAL via `pinnedBottomRowData`.
- Ordenação das linhas: segue a ordem dos KPI cards (`encaminhamentos_sum`), TOTAL sempre ao final.
- Sem coluna de seleção (`include_selection_column=False`).
- Toolbar: key `consulta_ano_actions_toolbar`.
- Nota de rodapé explica `% Total` e `Var%`.

### 5.5 Tabela Performance por URG (Mestre de Seleção)

**Base:** `df_for_urg_table` = `df` filtrado por Tipo + Ano + Encaminhamento (sem filtro de URG e sem filtro de Escola).

- Gerada com `build_comparativo_anual(..., "URG", pct_label="Cobertura")`.
- Seleção múltipla com checkbox; clique em linha filtra `global_urgs`.
- Sincronização de seleção via JS `onFirstDataRendered` — destaca URGs ativas.
- Key dinâmico: `urg_table_consulta_{urgs_selecionadas}` — protege contra resposta stale.
- Toolbar: key `consulta_urg_actions_toolbar`.
- Caption: "Sensível aos filtros de Ano, Tipo e Encaminhamento."

**Regra de sync URG (bidirecional):**

| Origem | Ação |
|---|---|
| Sidebar → Tabela | `apply_pending_table_filters()` + `onFirstDataRendered` JS |
| Tabela → Sidebar | Detecta `set(new_urgs) != set(current_urgs)` → seta `pending_sidebar_urg_filter` + `rerun()` |

### 5.6 Tabela Top Escolas por URG (Mestre de Seleção)

**Base:** `df_filt_no_escola` filtrado por Ano (sem filtro de Escola, com filtro de Encaminhamento e URG).

- Renderizada via `render_top_por_urg(..., table_key="escola_table_selection_consulta", selection_mode="multiple")`.
- `active_row_value = st.session_state.get("sidebar_escola_filter", [])`.
- Sincronização via JS `onFirstDataRendered` e `onRowDataUpdated`.
- Key AgGrid inclui as escolas ativas como sufixo — protege contra resposta stale.
- Toolbar gerada automaticamente dentro de `render_top_por_urg` com key `escola_table_selection_consulta_actions_toolbar`.

**Regra de sync Escola (bidirecional):**

| Origem | Ação |
|---|---|
| Sidebar → Tabela | `sync_sidebar_escola_selection("escola_table_selection_consulta")` detecta mudança e atualiza `{table_key}__selected_values` |
| Tabela → Sidebar | Bloco pós-renderização: se `last_source not in ("sidebar", "table")` e seleções diferem → seta `pending_sidebar_escola_filter` + `rerun()` |

**Regra crítica de anti-loop:** O sync tabela→sidebar só dispara quando `last_interaction_source` for `""` ou `"table_escola"`. Quando `"table"` (mudança de URG) ou `"sidebar"` (mudança via sidebar), o sync de escola é suprimido para evitar rerun em cascata. O `last_interaction_source` é sempre zerado (`""`) ao final do bloco de sync de escola.

### 5.7 Gráfico Comparativo Anual por URG

**Base:** `df_filt` (todos os filtros aplicados).

- `render_grouped_bar_anual(df_filt, "Quantidade", "", orientation="h")`
- Barras horizontais agrupadas por ano, eixo Y = URG.
- Cor por ano (mapa fixo 2022–2026).

### 5.8 Gráfico Distribuição por Encaminhamento

**Base:** `df_filt` (todos os filtros aplicados, incluindo Encaminhamento).

- `render_grouped_bar_anual(df_filt, "Quantidade", "", x_col="Encaminhamento", orientation="h")`
- Barras horizontais agrupadas por ano, eixo Y = Encaminhamento.
- Quando filtro de Encaminhamento ativo, exibe apenas os tipos selecionados.

### 5.9 Detalhamento por Aluno

**Base de construção:**
1. `filter_by_sidebar_selections(df_aluno, selections)` → aplica Ano, URG, Tipo da sidebar.
2. Filtra por `selected_years_comp`.
3. Filtra por `selections["escola"]` (escolas efetivas da sidebar).
4. Filtra por `encaminhamentos_selecionados` (se houver).

**Filtros locais adicionais (widgets inline):**
- Multiselect de Aluno
- Multiselect de Série
- Multiselect de Turma

**Estrutura da tabela resultante (colunas):**
`Aluno | DataNascimento | Sexo | URG | Escola | Serie | Turma | [Ano1] | [Ano2] | ... | Total | Perfil`

- Colunas de ano contêm os encaminhamentos daquele ano (texto, ex: `"Médico, Psicólogo"`).
- Encaminhamentos na seleção ativa são destacados em UPPERCASE; demais em capitalize.
- Coluna `Perfil` renderizada como `LinkColumn` com label `"📄 Ver Perfil"`.
- Link gerado por `build_perfil_link` → query params `?menu=Aluno&aluno=Nome&nasc=YYYY-MM-DD`.
- Limite de exibição: 500 linhas (`preview_limit`). Exibe aviso se exceder.
- Toolbar: key `consulta_aluno_actions_toolbar`.

---

## 6. Título Dinâmico dos Indicadores

```
### Indicadores Gerais (Anos: X / URGs: X / Escolas: X / Regulações: X)
```

- `"Todos"` quando todos os itens disponíveis estão selecionados ou nenhum está selecionado.
- Lista dos selecionados separada por `, ` quando há seleção parcial.

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
| `last_interaction_source` | `str` | `""`, `"sidebar"`, `"table"`, `"table_escola"` |
| `pending_sidebar_urg_filter` | `list[str]` | Pendência de URG da tabela para a sidebar |
| `pending_sidebar_escola_filter` | `list[str]` | Pendência de Escola da tabela para a sidebar |

### Chaves locais da página

| Chave | Descrição |
|---|---|
| `consulta_encaminhamento_multiselect` | Encaminhamentos selecionados via sidebar/toggle |
| `escola_table_selection_consulta__selected_values` | Escolas selecionadas na tabela |
| `escola_table_selection_consulta__aggrid_key` | Key atual da AgGrid de escolas (stale-guard) |
| `escola_table_selection_consulta__prev_sidebar_escola_filter` | Prev value para detecção de mudança da sidebar |
| `_prev_urg_table_key_consulta` | Key anterior da AgGrid de URG (stale-guard) |
| `last_df_cmp_urg_consulta` | DataFrame do comparativo URG (para debug/callback) |

---

## 8. Regras de Sincronismo — Fluxo Completo

```
RENDER
  │
  ├─ apply_pending_table_filters()
  │    ├─ pending_sidebar_urg_filter → sidebar_urg_filter + global_urgs
  │    └─ pending_sidebar_escola_filter → sidebar_escola_filter
  │
  ├─ sidebar_filters()  [renderiza widgets]
  │
  ├─ sync_sidebar_escola_selection()
  │    └─ se sidebar_escola_filter mudou → atualiza {table_key}__selected_values
  │                                      → last_interaction_source = "sidebar"
  │
  ├─ [renderiza todos os componentes]
  │
  ├─ URG table response
  │    └─ se seleção mudou → pending_sidebar_urg_filter + last = "table" → rerun()
  │
  └─ Escola sync check
       ├─ last_source not in ("sidebar","table") AND seleções diferem
       │    → pending_sidebar_escola_filter + last = "table" → rerun()
       └─ always: last_interaction_source = ""
```

---

## 9. Exportação de Dados

- Sidebar: botão "Exportar CSV (Consulta)" com `df_filt` (todos os filtros aplicados).
- Toolbars de tabela: implementadas via `render_table_toolbar`, exportam o DataFrame da respectiva tabela (corpo + rodapé).
- Botão "📋 Copiar": funcionalidade via `st.components.v1.html` (JS) para contornar restrições de permissão de iframe.
- Download CSV (Toolbar): realizado via JavaScript (Blob) para evitar rerun do Streamlit.
- Ver detalhes técnicos em [Especificação de Componentes Compartilhados](shared_components_spec.md).

---

## 10. Observações de Implementação

- A variável `df_ano_exibir` é construída mas não usada — pode ser removida futuramente.
- `selected_encs_from_table = []` é mantido fixo (feature de seleção via tabela de encaminhamento foi removida; sidebar é a única fonte).
- `render_top_por_urg` retorna `df_cmp` que não é capturado na chamada de escola — o retorno é ignorado intencionalmente.
- Toolbars de tabela: o CSS global em `styles.css` (`_actions_toolbar`) garante o alinhamento e visibilidade dos componentes HTML.
