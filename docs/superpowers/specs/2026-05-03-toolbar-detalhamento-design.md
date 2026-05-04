# Design Spec: Toolbar Unificada — Tabela de Detalhamento

**Data:** 2026-05-03  
**Arquivo alvo:** `app/app_pages/home.py`  
**Status:** Implementado (ajustes pós-implementação aplicados)

---

## Contexto

A tabela de detalhamento em `home.py` tem atualmente:
- Botão **Colunas** isolado à esquerda (`st.columns([1, 1])`)
- Botões **Copiar tabela (Detalhamento)** e **Exportar CSV** abaixo da tabela (`st.columns([1.4, 1.2, 4.4])`)

O objetivo é consolidar os controles em uma **toolbar unificada à direita, acima da tabela**, substituindo os três controles existentes.

---

## Design

### Layout

```
[título / controle de linhas]          [⚙️ Colunas | 📋 Copiar | ⬇️ CSV]
────────────────────────────────────────────────────────────────────────
(painel de checkboxes — visível somente quando Colunas ativo)
────────────────────────────────────────────────────────────────────────
[ tabela AgGrid                                                        ]
```

Implementado com `st.container(key="home_detail_toolbar", horizontal=True, horizontal_alignment="right")` para fixar o grupo à direita sem depender de wrappers HTML.

### Grupo de Botões (Visual)

- **Estilo:** grupo unificado — borda externa única (`border: 1px solid #334155; border-radius: 6px`), sem borda nas extremidades internas, separadores verticais internos via `border-right: 1px solid #334155`
- **Background:** transparente (hover: `#1e293b`)
- **Altura:** 34px
- **Implementação:** CSS injection via `st.markdown()` mirando seletores `button[data-testid="baseButton-secondary"]` dentro do container da toolbar

### Botões

| Botão | Ícone | Rótulo | Ação |
|-------|-------|--------|------|
| Colunas | ⚙️ | Colunas | Toggle `home_show_column_selector` em `st.session_state` |
| Copiar | 📋 | Copiar | `df_display_for_copy.to_clipboard(index=False, excel=True)` + `st.toast("Tabela copiada. Cole no Excel com Ctrl+V.")` |
| CSV | ⬇️ | CSV | `st.download_button` com `csv_visible_data` (sep=`;`, UTF-8-BOM) |

**Estado visual do botão Colunas:** quando o painel está aberto, aplica classe CSS de destaque (fundo `#1e3a5f`, texto `#60a5fa`).

### Seletor de Colunas (expansível)

Quando `home_show_column_selector = True`, renderiza um painel com checkboxes entre a toolbar e a tabela:

```python
with st.container(key="home_columns_panel", border=True):
    max_rows_per_column = 10
    column_groups = [
        available_columns[idx : idx + max_rows_per_column]
        for idx in range(0, len(available_columns), max_rows_per_column)
    ]
    with st.container(
        key="home_columns_grid",
        horizontal=True,
        horizontal_alignment="left",
        vertical_alignment="top",
        gap=None,
    ):
        ...
```

Regras do painel:
- Máximo de **10 linhas por coluna**.
- Ao exceder 10 itens, cria uma nova coluna automaticamente.
- Checkboxes: marcado = exibir; desmarcado = ocultar.
- `home_hidden_columns` continua sendo a fonte para `grid_builder.configure_column(col, hide=True)`.

---

## State Management

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `home_show_column_selector` | `bool` | Controla visibilidade do painel de checkboxes |
| `home_hidden_columns` | `list[str]` | Colunas atualmente ocultas na tabela |

Ambas já existem — nenhuma chave nova é necessária.

---

## Remoções

- **Remover** bloco `toolbar_container` atual (linhas ~2461–2480) que contém o botão Colunas à esquerda
- **Remover** bloco `copy_row = st.columns([1.4, 1.2, 4.4])` abaixo da tabela (linhas ~2518–2542) com os botões Copiar e Exportar CSV
- **Remover** CSS `.home-toolbar-row` e estilos associados (linhas ~2303–2334) — substituído por novo bloco CSS

---

## CSS Injection (novo)

---

```css
/* Toolbar (botões) */
.st-key-home_detail_toolbar div[data-testid="stHorizontalBlock"] {
    justify-content: flex-end !important;
    align-items: center !important;
    gap: 0 !important;
    flex-wrap: nowrap !important;
}
.st-key-home_toolbar_column_toggle button,
.st-key-home_toolbar_copy button,
.st-key-download_csv_home_toolbar button {
    background: transparent !important;
    border: 1px solid #334155 !important;
    border-radius: 0 !important;
    border-right: none !important;
    color: #94a3b8 !important;
    height: 34px !important;
    padding: 0 12px !important;
    font-size: 0.78rem !important;
}
.st-key-home_toolbar_column_toggle button {
    border-radius: 6px 0 0 6px !important;
}
.st-key-download_csv_home_toolbar button {
    border-radius: 0 6px 6px 0 !important;
    border-right: 1px solid #334155 !important;
}
.st-key-home_toolbar_column_toggle button:hover,
.st-key-home_toolbar_copy button:hover,
.st-key-download_csv_home_toolbar button:hover {
    background: #1e293b !important;
    color: #e2e8f0 !important;
}

/* Painel de colunas */
.st-key-home_columns_panel div[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
}
.st-key-home_columns_grid div[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
    justify-content: flex-start !important;
    width: fit-content !important;
}
.st-key-home_columns_grid div[data-testid="stElementContainer"] {
    width: fit-content !important;
    min-width: fit-content !important;
    flex: 0 0 auto !important;
}
```

---

## Fora de Escopo

- Persistência de colunas entre sessões (apenas `st.session_state` — sessão atual)
- Aplicar a mesma toolbar nas outras páginas (`aluno.py`, `consulta.py`, etc.)
- Popover flutuante ou painel lateral

---

## Evolução Implementada (Padrão Home)

Após a implementação inicial do detalhamento, o padrão de toolbar agrupada também foi aplicado nas demais tabelas `AgGrid` da Home:

- Tabela comparativa por URG: `📋 Copiar` + `⬇️ CSV` no topo direito.
- Tabela comparativa por Escola: `📋 Copiar` + `⬇️ CSV` no topo direito.
- Comparativo anual geral: `📋 Copiar` + `⬇️ CSV` no topo direito.

Esse padrão foi consolidado no Design System e na documentação de arquitetura como referência para futuras tabelas `AgGrid` da Home.

Estrutura obrigatória do grupo de botões:
- Mesma composição visual do grupo de referência (Detalhamento dos Dados).
- Mesmo comportamento de agrupamento: botões colados, borda contínua e cantos arredondados apenas nas extremidades.
- Não usar variações de design entre tabelas.
- Sem componentes/blocos extras entre toolbar e AgGrid (distância vertical mínima).

Implementação padrão consolidada:
- Toolbar de ações por tabela com `st.container(horizontal=True, horizontal_alignment="right", gap=None)`.
- CSS escopado por `key` fixa do container (`.st-key-home_*_actions_toolbar`).
- Evitar classes dinâmicas (`st-emotion-cache-*`) e wrappers HTML de apoio.

---

## Arquivos Afetados

- `app/app_pages/home.py` — único arquivo modificado
