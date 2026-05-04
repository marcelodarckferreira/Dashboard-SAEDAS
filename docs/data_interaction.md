# Interação e Fluxo de Dados

Descreve como o sistema gerencia estado global, sincronização bidirecional e regras de filtragem.

---

## Relação com PRD/SPEC

- Este arquivo descreve regras globais de estado e fluxo de dados (cross-page).
- PRDs (`docs/superpowers/prd/`) definem o comportamento esperado por feature.
- SPECs (`docs/superpowers/specs/`) detalham como a feature implementa esse comportamento.
- Regra de governança: decisão de feature fica no PRD/SPEC; regra reutilizável e transversal sobe para este documento.

---

## 1. Estado Global (session_state)

Todas as chaves são inicializadas por `init_global_state()` em `app/utils/state_manager.py`. Esta função é **idempotente** — pode ser chamada várias vezes sem efeito colateral.

| Chave | Tipo | Finalidade |
| :--- | :--- | :--- |
| `global_years` | `list[int]` | Anos selecionados ativos em todo o dashboard |
| `global_urgs` | `list[str]` | URGs selecionadas ativas em todo o dashboard |
| `sidebar_year_filter` | `list[int]` | Estado do widget multiselect de anos na sidebar |
| `sidebar_urg_filter` | `list[str]` | Estado do widget multiselect de URGs na sidebar |
| `sidebar_escola_filter` | `list[str]` | Estado do widget multiselect de escolas na sidebar |
| `home_year_buttons` | `list[int]` | Estado do `st.segmented_control` de anos na Home |
| `last_interaction_source` | `str` | `"sidebar"` ou `"table"` — origem da última mudança de URG |

> **Regra:** Nunca leia filtros diretamente do widget. Leia sempre de `global_years` e `global_urgs` — eles são a única fonte de verdade cross-page.

---

## 2. Sincronização Bidirecional (Two-Way Binding)

O sistema mantém paridade entre **Sidebar** e **Tabelas de seleção**. Qualquer mudança em um lado propaga para o outro via callbacks do Streamlit.

### Fluxo de Anos

```text
Sidebar (multiselect)  ──on_change──►  sync_sidebar_to_home()
                                            ├─ global_years  ← sidebar_year_filter
                                            └─ home_year_buttons ← sidebar_year_filter

Home (segmented_control) ──on_change──►  sync_home_to_sidebar()
                                            ├─ global_years  ← home_year_buttons
                                            └─ sidebar_year_filter ← home_year_buttons
```

### Fluxo de URGs

```text
Sidebar (multiselect)  ──on_change──►  sync_sidebar_urg_to_home()
                                            ├─ global_urgs ← sidebar_urg_filter
                                            └─ last_interaction_source = "sidebar"

Tabela Home (on_select) ──callback──►  sync_urg_table_to_global()  [definida em home.py]
                                            ├─ global_urgs ← linhas selecionadas
                                            ├─ sidebar_urg_filter ← global_urgs
                                            └─ last_interaction_source = "table"
```

### Anti-loop: `last_interaction_source`

Sem esse controle, a atualização da sidebar dispararia o callback da tabela e vice-versa, criando um loop infinito de reruns. A lógica é:

- Quando a origem é `"sidebar"` → a tabela lê `global_urgs` para atualizar sua seleção visual, mas **não dispara callback**.
- Quando a origem é `"table"` → a sidebar recebe o novo valor via `sidebar_urg_filter`, mas **não reprocessa o filtro da tabela**.

---

## 3. Leis de Filtragem

## Regra Geral de Implementação

Quando houver solicitação de nova tabela de seleção, aplicar automaticamente o padrão estabelecido na Home:

- usar estado global como fonte de verdade;
- sincronizar seleção da tabela com filtros da sidebar (two-way binding);
- evitar auto-filtragem da tabela pela própria seleção;
- propagar filtros para todos os componentes dependentes.

---

### Lei 1 — Independência da Tabela Mestre

Tabelas que servem como **controles de seleção** (ex: Tabela de URGs na Home) **não podem** ser filtradas pela própria seleção que geram.

- **Correto:** A tabela de URGs exibe todas as URGs do ano selecionado, independente de quais estão marcadas.
- **Errado:** Filtrar a tabela de URGs por `global_urgs` faria as linhas não selecionadas desaparecerem, impossibilitando a re-seleção.

```python
# home.py — imunidade ao filtro de URG na tabela mestre
df_for_performance_table = df.copy()
if selected_years_comp:
    df_for_performance_table = df_for_performance_table[
        df_for_performance_table["Ano"].isin(selected_years_comp)
    ]
# ← sem filtro de URG aqui
```

### Lei 1.1 — Tabela de Seleção exige sincronismo com Sidebar

Toda tabela usada como controle de seleção (ex.: URG/Escola na Home) deve ter sincronismo bidirecional com os filtros da sidebar.

Regras obrigatórias:
- Seleção na tabela atualiza estado global e parâmetro correspondente da sidebar.
- Alteração na sidebar reaplica seleção visual na tabela.
- A fonte de verdade continua sendo o estado global (`session_state`), nunca o widget isolado.
- Usar proteção anti-loop por `last_interaction_source` para evitar reruns infinitos.

Fluxo padrão:

```text
Sidebar -> sync_sidebar_* -> estado global -> seleção visual na tabela
Tabela  -> callback tabela -> estado global -> sidebar_*_filter
```

### Lei 2 — Cascata de Filtros

A ordem de precedência é obrigatória. Cada nível restringe o universo para o próximo:

```text
1. Ano     (filtro temporal mestre — sem exceção)
     ↓
2. URG     (filtro regional nível 1)
     ↓
3. Escola  (filtro regional nível 2 — opções dependem da URG selecionada)
```

O componente `sidebar_filters` implementa essa cascata: as escolas disponíveis no multiselect são pré-filtradas pela URG selecionada.

### Lei 3 — Linha TOTAL nunca é selecionável

A linha `"TOTAL"` ao final das tabelas é detectada pelo callback e ignorada:

```python
# home.py — sync_urg_table_to_global()
for r in rows:
    urg_val = df_table.data.iloc[r][("URG", "")]
    if urg_val and urg_val != "TOTAL":
        selected_urgs.append(urg_val)
```

O CSS também oculta o checkbox da última linha (`tr:last-child`) via `visibility: hidden`.

---

## 4. Funções de Sincronização (state_manager.py)

| Função | Disparada por | O que faz |
| :--- | :--- | :--- |
| `init_global_state()` | `app.py` e cada `page_*()` | Cria chaves ausentes no `session_state` |
| `sync_sidebar_to_home()` | `on_change` do multiselect de anos | `global_years` e `home_year_buttons` ← `sidebar_year_filter` |
| `sync_home_to_sidebar()` | `on_change` do segmented_control | `global_years` e `sidebar_year_filter` ← `home_year_buttons` |
| `sync_sidebar_urg_to_home()` | `on_change` do multiselect de URGs | `global_urgs` ← `sidebar_urg_filter`; source = `"sidebar"` |
| `sync_home_urg_to_sidebar()` | Callback interno de paridade | `sidebar_urg_filter` ← `global_urgs`; source = `"table"` |
| `sync_sidebar_escola_to_global()` | `on_change` do multiselect de escolas | Registra source = `"sidebar"` |

---

## 5. sidebar_filters — API

```python
df_filtrado, selections = sidebar_filters(df, filter_config)
```

### `filter_config`

```python
filter_config = {
    "ano":    True,   # exibe multiselect de anos
    "urg":    True,   # exibe multiselect de URGs
    "escola": True,   # exibe multiselect de escolas (cascata com URG)
    "tipo":   False,  # exibe multiselect de tipo (ex: municipal/estadual)
}
```

### `selections` retornado

```python
{
    "ano":    [2024, 2025],   # anos efetivamente aplicados (todos se vazio)
    "urg":    ["URG III-COMENDADOR SOARES"],
    "escola": ["Escola X", "Escola Y"],
    "tipo":   [],
}
```

> Quando nenhum item está selecionado num filtro, `selections[chave]` contém **todos os valores disponíveis** — nunca uma lista vazia que zeraria os dados.

---

## 6. Carregamento de Dados (data_loader.py)

```python
df, info = load_csv("data/DashboardHome.csv", expected_cols=SCHEMA_HOME)
```

### Retorno `info`

```python
{
    "erros":   [],       # lista de strings — problemas fatais (arquivo ausente, schema inválido)
    "alertas": [],       # lista de strings — avisos não-fatais (colunas extras, tipos divergentes)
}
```

### Padrão de uso obrigatório

```python
df, info = load_csv(csv_path, expected_cols=SCHEMA_XXX)

if info["erros"]:
    st.error("; ".join(info["erros"]))
    footer_personal()
    return

if info["alertas"]:
    st.warning("; ".join(info["alertas"]))
```

Nunca ignore `info["erros"]` — uma página renderizada com DataFrame inválido gera erros silenciosos difíceis de depurar.

---

## 7. Padrão AgGrid SAEDAS

Todas as tabelas interativas do sistema devem seguir o padrão arquitetural definido via `render_saedas_aggrid` (em `app/utils/page_helpers.py`).

### 7.1. Renderização Unificada

O uso direto de `st.dataframe` ou `AgGrid` puro é desencorajado. Deve-se utilizar o wrapper mestre:

```python
from app.utils.page_helpers import render_saedas_aggrid

render_saedas_aggrid(
    df_data=df_body,
    grid_options=options,
    key="minha_tabela_key",
    incluir_total=True  # se houver linha de total fixada
)
```

### 7.2. Governança de Altura (Regra das 20 Linhas)

O sistema implementa uma lógica de **Altura Inteligente** via `calcular_altura_aggrid`:

1.  **Adaptabilidade:** Para volumes pequenos (ex: 5 linhas), a tabela ajusta seu contêiner exatamente ao tamanho dos dados, evitando espaços vazios.
2.  **Teto de Ergonomia (Cap):** Para volumes grandes, a altura é limitada ao equivalente a **20 linhas**. Acima disso, o scroll interno do AgGrid é ativado. Isso garante que gráficos situados abaixo da tabela permaneçam acessíveis.

### 7.3. Toolbar de Exportação

Toda tabela AgGrid deve ser precedida pela barra de ferramentas unificada:

```python
from app.utils.page_helpers import render_table_toolbar

render_table_toolbar(df_export, "nome_arquivo.csv", "prefixo_key")
```

- **📋 Copiar:** Copia os dados formatados para a área de transferência (excel-friendly).
- **⬇️ CSV:** Exporta o conteúdo completo, incluindo a linha de TOTAL se houver.

### 7.4. Estilização (Design System)

O wrapper `render_saedas_aggrid` injeta automaticamente as seguintes regras de estilo:
- **Headers:** Fundo e texto contrastantes, fonte negrito (fontWeight 700).
- **Footers (Total):** Linha de total fixada no fundo (`pinnedBottomRowData`), com fundo diferenciado e borda superior reforçada.
- **Índice:** Adição automática de coluna de índice numerada (1 a N) fixada à esquerda.
