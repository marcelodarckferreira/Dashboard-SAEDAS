# Especificação de Componentes Compartilhados — Dashboard SAEDAS

Este documento detalha os componentes de interface reutilizáveis do sistema SAEDAS, especificando seu comportamento, design e implementação técnica. Todas as funções públicas relevantes estão implementadas em `app/utils/page_helpers.py`.

---

## 1. API Pública de `app/utils/page_helpers.py`

A seguir, o catálogo das funções públicas atualmente expostas pelo módulo `page_helpers.py` (refletindo a implementação real do código).

### 1.1 Helpers Gerais
- `toggle_multiselect_value(current_selection: list | None, value) -> list`
  Retorna uma nova lista de seleção múltipla com o valor alternado (toggle on/off). Utilizado por botões/KPIs de toggle.
- `render_section_divider() -> None`
  Renderiza um divisor visual padrão (`st.markdown("---")`) com espaçamento otimizado.
- `render_metric(label: str, value) -> None`
  Renderiza um único cartão de métrica isolado dentro de um layout de 4 colunas (usando apenas a primeira). Internamente chama `render_metric_cards` (importada de `app.utils.styles`).

### 1.2 Filtros e Display de Seleção
- `get_filter_display_string(key_name, selections, df_original, column_name) -> str`
  Retorna string compacta descrevendo a seleção atual (`"Todos(as)"` quando vazia ou completa).
- `filter_by_sidebar_selections(df: pd.DataFrame, selections: dict) -> pd.DataFrame`
  Aplica as seleções padrão da sidebar (chaves `ano`, `urg`, `escola`, `tipo`) a um DataFrame, retornando o subconjunto filtrado.
- `format_filters_applied(selections, df_original, mapping) -> str`
  Constrói um breadcrumb textual dos filtros aplicados a partir de um mapping `(selection_key, df_column, label?)`.

### 1.3 Tabelas Comparativas Anuais
- `build_comparativo_anual(df, categoria_col, value_col="Quantidade", active_row_value=None, denominator_row_label=None, pct_label="Total") -> pd.DataFrame | None`
  Gera tabela comparativa anual com colunas absolutas, `% Total` (ou `% Cobertura` quando `denominator_row_label` é fornecido), variação interanual `Var% YY-YY` e linha `TOTAL` ao final. Retorna um `Styler` com MultiIndex de cabeçalho e estilização SAEDAS (`apply_saedas_design`).
- `get_selected_comparativo_value(df_cmp, rows, categoria_col) -> Any`
  Extrai com segurança o valor selecionado de uma tabela comparativa (ignora índices obsoletos e o rótulo `TOTAL`).
- `prepare_comparativo_aggrid_data(df_styler, include_selection_column=True) -> tuple[pd.DataFrame, list[dict], dict]`
  Converte o `Styler` comparativo em dataframe simples + `columnDefs` + mapa de campos para uso no AgGrid (com cabeçalhos agrupados e alinhamento por tipo de coluna).
- `split_aggrid_footer(df_grid) -> tuple[pd.DataFrame, list[dict]]`
  Separa a última linha do dataframe (linha `TOTAL`) como `pinnedBottomRowData` do AgGrid.

### 1.4 Gráficos Plotly Padronizados
- `render_grouped_bar_anual(df, value_col, titulo, x_col="URG", orientation="v") -> None`
  Renderiza barras agrupadas por ano com paleta categórica fixa (2022–2026), ordenação especial de URG por numeral romano (`_urg_sort_key`) e rótulos de `% Total`.
- `render_top_por_urg(df, value_col, titulo, label_col, table_key=None, active_row_value=None, selection_mode="single-row", on_select="rerun") -> pd.DataFrame | None`
  Renderiza gráfico horizontal por URG + tabela comparativa anual associada. Quando `table_key` é fornecido, habilita seleção de linha sincronizada com `st.session_state[f"{table_key}__selected_values"]` e `st.session_state[table_key]`.

### 1.5 Toolbar Unificada de Tabela
- `prepare_table_toolbar_exports(df_export) -> tuple[bytes, str]`
  Prepara os formatos padrão da toolbar: CSV (separador `;`, BOM UTF-8) e TSV para clipboard.
- `render_table_toolbar(df_export, file_name, key_prefix, *, df_download=None, leading_action_label=None, leading_action_key=None, leading_action_help=None, copy_key=None, download_key=None) -> bool`
  Renderiza barra de ações HTML (Copiar + CSV, opcionalmente com botão de ação leading). Retorna `True` quando o botão leading é clicado.

### 1.6 AgGrid Padronizado (Design System)
- `calcular_altura_aggrid(df, limite_linhas="Todas as linhas", incluir_total=False, max_rows=20) -> int`
  Calcula altura ideal: piso de 5 linhas, teto configurável (default 20), com altura adicional para linha de total quando aplicável.
- `render_saedas_aggrid(df_data, grid_options, key, update_mode=NO_UPDATE, incluir_total=False, max_rows=20, min_height=None, **kwargs)`
  Função mestra: calcula altura dinâmica, aplica CSS do Design System (headers, footer fixo) e delega para `st_aggrid.AgGrid`.
- `render_aluno_detalhamento_aggrid(df, key, max_rows=20, csv_name=None, toolbar_key=None) -> None`
  Renderização padronizada da tabela de detalhamento de alunos: toolbar automática, coluna `Perfil` com link visual e bridge JS para navegação.

### 1.7 Perfil do Aluno (Deep-linking via AgGrid)
- `prepare_profile_action_column(df) -> pd.DataFrame`
  Prepara a coluna `Perfil` com marcador `__SAEDAS_PROFILE_URL__` e mantém a URL original em `_PerfilUrl` (coluna oculta).
- `get_profile_url_from_aggrid_event(event_data) -> str | None`
  Extrai a URL de perfil de um evento `cellClicked` do AgGrid.
- `build_profile_click_return_js() -> str`
  Retorna JS de coletor customizado que extrai `profileUrl` de cliques de célula.
- `build_profile_link_cell_renderer_js() -> str`
  Cell renderer do AgGrid que transforma a célula `Perfil` em link nativo.
- `build_profile_cell_click_navigation_js() -> str`
  Click handler do AgGrid que roteia clique em `Perfil` para `window.parent.location`.
- `get_profile_url_from_aggrid_response(aggrid_response) -> str | None`
  Lê `profileUrl` do retorno customizado do AgGrid.
- `get_profile_url_from_aggrid_selection(aggrid_response) -> str | None`
  Extrai URL de perfil da linha selecionada (via `_PerfilUrl`).
- `render_profile_click_bridge() -> None`
  Injeta script (via `components.html`) que substitui células `Perfil` por âncoras `<a target="_top">` no documento pai.
- `route_to_profile_url(perfil_url: str) -> None`
  Faz parse da URL (`?aluno=...&nasc=...`), define `aluno_preselect` em `session_state`, navega para o menu "Aluno" e dispara `st.rerun()`.

### 1.8 Preparação de Dados Específicos
- `prepare_nutricao_aluno_table(df_aluno, build_perfil_link, selected_nuts=None) -> pd.DataFrame`
  Pivota a tabela de Nutrição por aluno em colunas `Ano | Métrica` (Peso, Altura, IMC, Idade, Nutrição), formata valores e adiciona coluna `Menu` com link de perfil.

### 1.9 Constantes e Internos Notáveis
- `PROFILE_URL_MARKER = "__SAEDAS_PROFILE_URL__"` — marcador embutido na célula `Perfil` para permitir extração via DOM no bridge JS.
- Funções auxiliares internas: `_roman_to_int`, `_urg_sort_key` (ordenação canônica de URGs).

---

## 2. Toolbar Unificada (Copiar + CSV)

### 2.1 Motivação Técnica
Devido às restrições de Permissions Policy do navegador em iframes do Streamlit, a `navigator.clipboard` não funciona via `st.button`. A solução unifica todos os botões em um único componente HTML (`st.components.v1.html`), garantindo que o gesto do usuário ocorra no contexto onde a API é permitida.

### 2.2 Modo Triple Group (com ação leading)
Quando `leading_action_label` é informado:
- O componente cria um `st.checkbox` oculto como trigger.
- O JS dentro do iframe localiza o checkbox no parent e simula um clique.
- A função retorna `True` no rerun seguinte.

### 2.3 Layout
- Triple Group: `st.columns([0.65, 0.35])`.
- Dual Group: `st.columns([0.82, 0.18])`.
- O `st.container` pai deve usar a chave `{prefix}_actions_toolbar` para isolamento visual.

### 2.4 Comportamento dos Botões
| Botão | Ação | Feedback |
| :--- | :--- | :--- |
| Coluna (opcional) | Trigger Streamlit | rerun |
| Copiar | `navigator.clipboard.writeText` (TSV) | "✅ Copiado!" 2s |
| CSV | Blob + link virtual (`;` UTF-8 BOM) | Download instantâneo |

---

## 3. Seletor Temporal Mestre (Botões de Ano)

### 3.1 Estrutura Técnica
- **Container:** `st.container(key="massive_year_selector")`
- **Widget:** `st.segmented_control` com `selection_mode="multi"`
- **Estado Global:** `st.session_state["global_years"]`

### 3.2 Sincronização
Usa o callback `sync_home_to_sidebar` (de `state_manager.py`):
1. Atualiza `global_years` e `sidebar_year_filter`.
2. Dispara `st.rerun()`.
3. Todas as tabelas e gráficos via `filter_by_sidebar_selections` reagem.

### 3.3 Regras Visuais
- Bloco sólido conectado (`gap: 0`), container com `overflow: hidden`.
- Altura `80px`, fonte `2.4rem (800)`.
- Item ativo: gradiente `135deg, #38bdf8 → #1e40af`.

---

## 4. Tabela de Detalhamento de Alunos (AgGrid)

### 4.1 Função
`render_aluno_detalhamento_aggrid(df, key, max_rows=20, csv_name=None, toolbar_key=None)`

### 4.2 Regras de Altura (via `calcular_altura_aggrid`)
| Regra | Condição | Comportamento |
| :--- | :--- | :--- |
| Altura Mínima | Tabela vazia ou < 5 registros | 5 linhas |
| Teto de Scroll | Qualquer estado | 20 linhas (configurável via `max_rows`) |

### 4.3 Funcionalidades Integradas
1. Toolbar automática (via `render_table_toolbar`).
2. Coluna `Perfil` (visual) + `_PerfilUrl` (técnica, 1px).
3. Bridge JS (`render_profile_click_bridge`) que substitui a célula por âncora nativa com `target="_top"`.

### 4.4 Alinhamento
- "Aluno", "Escola" → esquerda (`saedas-aggrid-left-header`).
- Demais → centralizadas (`saedas-aggrid-header`).

---

## 5. Próximos Componentes (Backlog)
- [ ] Metric Cards Customizados (extensão de `render_metric_cards`)
- [ ] Breadcrumb de Filtros Aplicados (extensão de `format_filters_applied`)
- [ ] Footer Personalizado
