# Spec: Página de Assistência Social

**Arquivo:** `app/app_pages/assistencia_social.py`
**Função de entrada:** `page_assistencia_social()`
**Título:** Visão Geral dos Atendimentos de Assistente Social

---

## 1. Fontes de Dados

| Variável | Arquivo CSV | Schema |
|---|---|---|
| `df` (principal) | `data/DashboardAssistenciaSocial.csv` | `SCHEMA_ASSISTENCIA_SOCIAL` |
| `df_aluno_raw` | `data/DashboardAssistenciaSocialAluno.csv` | `SCHEMA_ASSISTENCIA_SOCIAL_ALUNO` |
| `df_ano` | `data/DashboardAssistenciaSocialAno.csv` | `SCHEMA_ASSISTENCIA_SOCIAL_ANO` |
| `df_home` | `data/DashboardHome.csv` | `SCHEMA_HOME` |

### Renomeação de colunas após carga

| CSV original | Nome interno |
|---|---|
| `Descricao` | `Atendimento` |
| `Qtd` | `Quantidade` |
| `DtNasc` | `DataNascimento` |

---

## 2. Filtros da Sidebar

Título da sidebar: **"Filtros - Assistente Social"**.

Ativados via `sidebar_filters(df, {"ano": True, "urg": True, "escola": True, "tipo": True})`.

| Filtro | Chave session_state |
|---|---|
| Ano(s) | `sidebar_year_filter` |
| URG(s) | `sidebar_urg_filter` |
| Escola(s) | `sidebar_escola_filter` |
| Tipo(s) | `sidebar_tipo_filter` |

> Observação: o filtro de Atendimento foi **removido conforme solicitação**. A variável `atendimentos_selecionados` é mantida como lista vazia no código.

---

## 3. Seletor Temporal Mestre

- Container `massive_year_selector` com `st.segmented_control` em modo `multi`.
- Anos: ano atual e os 4 anteriores (5 anos no total).
- Callback: `sync_home_to_sidebar`.
- Fonte de verdade: `st.session_state["global_years"]`.

---

## 4. Hierarquia de Bases de Dados

```
df (bruto)
 └─► df_base_sem_escola  [filtros: Tipo, Ano]
      └─► df_base_final  [filtros: + Escola]
           └─► df_master_no_atend  [filtros: + URG]
                └─► df_master_filtrado / df_filt  [+ Atendimento (sempre vazio)]

df_base_sem_escola
 └─► df_filt_no_escola  [filtros: + URG  (sem Escola)]

df_master_no_atend
 └─► df_filt_no_atend  [= df_master_no_atend]
```

### Matriz de imunidade por base

| Base | Tipo | Ano | URG | Escola |
|---|---|---|---|---|
| `df_base_sem_escola` | ✓ | ✓ | — | — |
| `df_base_final` | ✓ | ✓ | — | ✓ |
| `df_master_no_atend` | ✓ | ✓ | ✓ | ✓ |
| `df_filt` | ✓ | ✓ | ✓ | ✓ |
| `df_filt_no_escola` | ✓ | ✓ | ✓ | **IMUNE** |

---

## 5. Componentes e Regras de Filtro

### 5.1 Filtros Aplicados (placeholder)

- Renderizado com `st.empty()` no topo, preenchido após cálculo das seleções.
- `format_filters_applied(selections, df, [Ano, URG, Escola, Tipo])`.

### 5.2 Indicadores Gerais (Cards Estáticos)

`render_metric_cards(...)` com três cards:

| Card | Origem |
|---|---|
| TOTAL DE ALUNOS | `df_home["QtdAlunoEscola"].sum()` filtrado por Ano/URG/Escola |
| ALUNOS ATENDIDOS | `df_home["QtdAluno"].sum()` filtrado por Ano/URG/Escola |
| ATEND. ASSIST. SOCIAL | `df_filt["Quantidade"].sum()` |

Quando `df_filt` está vazio, exibe `st.info("Selecione ao menos um ano para visualizar os indicadores.")`.

### 5.3 Tabela Performance por URG (Mestre de Seleção)

**Base:** `df_for_urg_table` = `df` filtrado apenas por Ano.

- `build_comparativo_anual(df_for_urg_table, "URG", active_row_value=current_selected_urgs)`.
- `prepare_comparativo_aggrid_data` + `split_aggrid_footer`.
- Seleção múltipla com `rowMultiSelectWithClick`.
- Sincronização via JS `onFirstDataRendered` (`sync_selection_js`).
- Key dinâmico: `urg_table_assistencia_social_{urgs_selecionadas}`.
- Stale-guard: `_prev_urg_table_key_assistencia_social`.
- Wrapper CSS: `.selection-master-table`.
- Toolbar: `assistencia_social_urg_actions_toolbar`.
- Caption: "Clique em qualquer linha de URG para filtrar o restante do dashboard. Esta tabela é sensível apenas ao filtro de Ano."

**Sync URG (bidirecional):**

| Origem | Ação |
|---|---|
| Sidebar → Tabela | `apply_pending_table_filters()` + `onFirstDataRendered` JS |
| Tabela → Sidebar | Detecta mudança em `new_selected_urgs` → seta `global_urgs`, `pending_sidebar_urg_filter`, `last_interaction_source="table"` → `rerun()` |

### 5.4 Top Escolas por URG (Mestre de Seleção)

**Base:** `df_filt_no_escola` adicionalmente filtrado por `selected_years_comp`.

- `render_top_por_urg(..., table_key="escola_table_selection_assistencia_social", selection_mode="multiple")`.
- `active_row_value = st.session_state.get("sidebar_escola_filter", [])`.
- Pré-renderização: `sync_sidebar_escola_selection("escola_table_selection_assistencia_social")`.

**Sync Escola (bidirecional):**

| Origem | Ação |
|---|---|
| Sidebar → Tabela | `sync_sidebar_escola_selection(...)` |
| Tabela → Sidebar | Se seleções diferem de `sidebar_escola_filter` → seta `pending_sidebar_escola_filter`, `last_interaction_source="table_escola"` → `rerun()` |

Após o bloco de sync, `last_interaction_source` é zerado (`""`).

### 5.5 Gráfico Distribuição por URG

**Base:** `df_filt` agregado por `URG` × `Ano` (soma de `Quantidade`).

- `px.bar` (barras agrupadas), `barmode="group"`, `color="Ano"`.
- Ordenação por numeral romano da URG (`_urg_sort_key` / `_roman_to_int`).
- Texto na barra formatado como `"3.235"` (separador de milhar pt-BR).
- Hover unificado por X.
- Quando vazio: `st.info("Nenhum dado de URG para exibir.")`.

### 5.6 Detalhamento por Aluno

**Base de construção:**
1. `filter_by_sidebar_selections(df_aluno, selections)`.
2. Filtra por `selected_years_comp`.

**Filtros locais inline:**
- `assistencia_social_aluno_multiselect`
- `assistencia_social_serie_multiselect`
- `assistencia_social_turma_multiselect`

Exibe caption `"{N} registros após filtros da sidebar"`.

**Estrutura da tabela (colunas):**
`ID | Aluno | DataNascimento | Sexo | Profissional | URG | Escola | Serie | Turma | [Ano1] | [Ano2] | ... | Total | Perfil`

- Atributos estáticos via `groupby(["ID","Aluno"]).last()`.
- Contagem de atendimentos por Ano via `pivot` (`size`).
- Coluna `Total` = soma das colunas de Ano.
- Zeros substituídos por string vazia (UI limpa).
- `DataNascimento` formatada `dd/mm/YYYY`.
- Coluna `Menu` renomeada para `Perfil`; gerada por `build_perfil_link` → `?menu=Aluno&aluno=Nome&nasc=YYYY-MM-DD`.
- `preview_limit = 500` linhas; aviso se exceder.
- Renderização: `render_aluno_detalhamento_aggrid(..., key="aluno_table_assistencia_social", csv_name="detalhes_alunos_assistencia_social.csv", toolbar_key="assistencia_social_aluno_actions_toolbar")`.

---

## 6. Título Dinâmico dos Indicadores

```
### Indicadores Gerais (Anos: X / URGs: X / Escolas: X)
```

- Helper local `get_filter_display_string_for_title(...)` retorna `"Todos"` quando todos disponíveis ou nenhum selecionado; caso contrário lista os itens ordenados separados por `, `.

---

## 7. Estado Global e Chaves de Session State

### Chaves globais

| Chave | Tipo | Descrição |
|---|---|---|
| `global_years` | `list[int]` | Anos selecionados |
| `global_urgs` | `list[str]` | URGs selecionadas |
| `sidebar_year_filter` | `list[int]` | Espelho do widget de ano |
| `sidebar_urg_filter` | `list[str]` | Espelho do widget de URG |
| `sidebar_escola_filter` | `list[str]` | Espelho do widget de escola |
| `last_interaction_source` | `str` | `""`, `"sidebar"`, `"table"`, `"table_escola"` |
| `pending_sidebar_urg_filter` | `list[str]` | Pendência de URG da tabela |
| `pending_sidebar_escola_filter` | `list[str]` | Pendência de Escola da tabela |

### Chaves locais

| Chave | Descrição |
|---|---|
| `assistencia_social_atendimento_multiselect` | (resíduo) usado por `toggle_atendimento`; UI removida |
| `assistencia_social_aluno_multiselect` | Filtro inline de aluno |
| `assistencia_social_serie_multiselect` | Filtro inline de série |
| `assistencia_social_turma_multiselect` | Filtro inline de turma |
| `escola_table_selection_assistencia_social__selected_values` | Escolas selecionadas na tabela |
| `_prev_urg_table_key_assistencia_social` | Stale-guard da AgGrid de URG |

---

## 8. Exportação de Dados

- Toolbar URG: `assistencia_social_urg_actions_toolbar` → CSV `performance_urg_assistencia_social.csv`.
- Toolbar Top Escolas: `escola_table_selection_assistencia_social_actions_toolbar` (via `render_top_por_urg`).
- Toolbar Detalhamento por Aluno: `assistencia_social_aluno_actions_toolbar` → CSV `detalhes_alunos_assistencia_social.csv`.
- Outras toolbars CSS escopadas no bloco `<style>`: `assistencia_social_cobertura_actions_toolbar` (declarada mas não instanciada).

---

## 9. Cache e Performance
- **Redis Integration:** Utiliza a camada de cache definida em [Redis Cache Spec](redis_cache_spec.md).
- **Estratégia em Assistência Social:**
    - **Datasets:** Cachear os 4 DataFrames base (`Principal`, `Aluno`, `Ano`, `Home`).
    - **Chaves:**
        - `saedas:assistencia_social:dataset:main`
        - `saedas:assistencia_social:dataset:aluno`
        - `saedas:assistencia_social:dataset:ano`
        - `saedas:home:dataset:main` (Reaproveitado)
    - **Invalidação:** TTL de 12 horas ou via scripts de integração.
