# Design Spec: Toolbar Unificada — Tabela de Detalhamento

**Data:** 2026-05-03  
**Arquivo alvo:** `app/app_pages/home.py`  
**Status:** Aprovado

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
(multiselect — visível somente quando Colunas ativo)
────────────────────────────────────────────────────────────────────────
[ tabela AgGrid                                                        ]
```

Implementado com `st.columns([espaço, toolbar])` para empurrar o grupo à direita.

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

Quando `home_show_column_selector = True`, renderiza `st.multiselect` entre a toolbar e a tabela:

```python
st.multiselect(
    "Colunas a ocultar",
    options=available_columns,
    default=st.session_state["home_hidden_columns"],
    key="home_hidden_columns_selector",
)
```

O estado `home_hidden_columns` é lido em seguida para ocultar colunas via `grid_builder.configure_column(col, hide=True)`.

---

## State Management

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `home_show_column_selector` | `bool` | Controla visibilidade do multiselect |
| `home_hidden_columns` | `list[str]` | Colunas atualmente ocultas na tabela |

Ambas já existem — nenhuma chave nova é necessária.

---

## Remoções

- **Remover** bloco `toolbar_container` atual (linhas ~2461–2480) que contém o botão Colunas à esquerda
- **Remover** bloco `copy_row = st.columns([1.4, 1.2, 4.4])` abaixo da tabela (linhas ~2518–2542) com os botões Copiar e Exportar CSV
- **Remover** CSS `.home-toolbar-row` e estilos associados (linhas ~2303–2334) — substituído por novo bloco CSS

---

## CSS Injection (novo)

A classe `.saedas-toolbar-right` é aplicada envolvendo o `st.columns` com:
```python
st.markdown('<div class="saedas-toolbar-right">', unsafe_allow_html=True)
_, col_toolbar = st.columns([6, 1])
# ... botões dentro de col_toolbar ...
st.markdown('</div>', unsafe_allow_html=True)
```

---

```css
/* Container da nova toolbar */
div[data-testid="stHorizontalBlock"].saedas-toolbar-right {
    justify-content: flex-end !important;
    align-items: center !important;
    gap: 0 !important;
    margin-bottom: 4px;
}

/* Agrupa visualmente os botões */
div.saedas-toolbar-right div[data-testid="column"] {
    flex: 0 0 auto !important;
    padding: 0 !important;
}

/* Remove bordas padrão e aplica estilo unificado */
div.saedas-toolbar-right button {
    background: transparent !important;
    border: 1px solid #334155 !important;
    border-radius: 0 !important;
    border-right: none !important;
    color: #94a3b8 !important;
    height: 34px !important;
    padding: 0 12px !important;
    font-size: 0.78rem !important;
    transition: background 0.15s, color 0.15s !important;
}
div.saedas-toolbar-right button:first-of-type {
    border-radius: 6px 0 0 6px !important;
}
div.saedas-toolbar-right button:last-of-type {
    border-radius: 0 6px 6px 0 !important;
    border-right: 1px solid #334155 !important;
}
div.saedas-toolbar-right button:hover {
    background: #1e293b !important;
    color: #e2e8f0 !important;
}
```

---

## Fora de Escopo

- Persistência de colunas entre sessões (apenas `st.session_state` — sessão atual)
- Aplicar a mesma toolbar nas outras páginas (`aluno.py`, `consulta.py`, etc.)
- Popover flutuante ou painel lateral

---

## Arquivos Afetados

- `app/app_pages/home.py` — único arquivo modificado
