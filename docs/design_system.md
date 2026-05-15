# SAEDAS Design System

Fonte única de verdade para padrões visuais, tokens de cores e componentes de interface.

---

## Relação com PRD/SPEC

- Este arquivo contém padrões visuais globais e reutilizáveis do produto.
- PRDs (`docs/superpowers/prd/`) definem a necessidade de UX/UI por iniciativa.
- SPECs (`docs/specs/`) descrevem a solução técnica de UI daquela iniciativa. Refira-se a [Componentes Compartilhados](specs/shared_components_spec.md) para detalhes de baixo nível.
- Regra de governança: ajuste visual local começa no PRD/SPEC; quando estabilizar como padrão, entra neste Design System.

---

## 1. Arquitetura do Tema

O sistema de cores funciona em **quatro camadas em cascata**, da menor para a maior prioridade:

| Camada | Contexto | Mecanismo |
| :--- | :--- | :--- |
| `:root` | Padrão global (dark) | Valores base, sem mídia query |
| `@media (prefers-color-scheme: light)` | Sistema do usuário em modo claro | Sobrescreve `:root` |
| `[data-theme="light/dark"]` | Toggle manual do Streamlit | Sobrescreve tudo com `!important` |
| Pandas Styler (`apply()`) | Linhas interativas em dataframes | Inline style Python-side |

> **Por que quatro camadas?** O Streamlit permite que o usuário alterne o tema via UI independentemente da preferência do sistema operacional. Os dois primeiros blocos cobrem a detecção automática; os dois últimos garantem que o toggle manual sempre vença.

---

## 2. Tokens de Cores

Cada token está definido explicitamente nos quatro contextos. Altere sempre os quatro ao modificar um token.

### 2.1 Superfícies

| Token | Finalidade | Light | Dark |
| :--- | :--- | :--- | :--- |
| `--surface-primary` | Fundo principal da página | `#ffffff` | `#0f172a` |
| `--surface-secondary` | Fundo secundário / alternado | `#f8fafc` | `#1e293b` |
| `--surface-elevated` | Superfícies elevadas (rodapé fixo, modais) | `#f1f5f9` | `#1e293b` |
| `--surface-active` | Fundo de linha selecionada/ativa em tabelas | `rgba(37,99,235,0.08)` | `rgba(56,189,248,0.15)` |
| `--surface-hover` | Fundo ao passar o mouse em linhas | `#f1f5f9` | `#334155` |

### 2.2 Header (Cabeçalho de Tabela)

| Token | Finalidade | Light | Dark |
| :--- | :--- | :--- | :--- |
| `--header-bg` | Fundo do cabeçalho (`thead th`) | `#f8fafc` | `#1e293b` |
| `--header-text` | Texto do cabeçalho | `#475569` | `#cbd5e1` |

### 2.3 Footer — Pro Footer (linha de TOTAL)

O `st.dataframe` não possui footer nativo. O padrão SAEDAS usa a **última linha** (`tr:last-child`) como Pro Footer, espelhando visualmente o header (**bookend**).

| Token | Finalidade | Light | Dark |
| :--- | :--- | :--- | :--- |
| `--footer-bg` | Fundo da linha TOTAL | `#f8fafc` | `#1e293b` |
| `--footer-text` | Texto da linha TOTAL | `#475569` | `#cbd5e1` |

Os valores de `--footer-*` são **idênticos** a `--header-*` intencionalmente. Se precisar diferenciar, altere apenas os tokens de footer.

### 2.4 Texto

| Token | Finalidade | Light | Dark |
| :--- | :--- | :--- | :--- |
| `--text-main` | Texto principal da página | `#1e293b` | `#f1f5f9` |
| `--text-muted` | Texto discreto / secundário | `#64748b` | `#94a3b8` |
| `--text-active` | Texto de linha ativa em tabelas | `#2563eb` | `#38bdf8` |

### 2.5 Bordas e Destaque

| Token | Finalidade | Light | Dark |
| :--- | :--- | :--- | :--- |
| `--border-ui` | Bordas de componentes e divisores | `#e2e8f0` | `#334155` |
| `--accent-color` | Cor primária de destaque (bordas, toggles) | `#2563eb` | `#38bdf8` |
| `--accent-color-alpha` | Destaque com transparência (glow, sombras) | `rgba(37,99,235,0.15)` | `rgba(56,189,248,0.3)` |

---

## 3. Pro Footer — Padrão de Linha de Total

### Por que existe

O `st.dataframe` do Streamlit não implementa um `tfoot` HTML real. O padrão SAEDAS resolve isso com uma convenção: **toda tabela com totalizadores deve ter "TOTAL" como último registro do DataFrame**. O CSS aplica o estilo de footer automaticamente via `tr:last-child`.

### Definição CSS

```css
/* app/assets/styles.css */
[data-testid="stDataFrame"] tr:last-child td,
[data-testid="stDataFrame"] [role="row"]:last-child [role="gridcell"] {
    background-color: var(--footer-bg) !important;
    color: var(--footer-text) !important;
    font-weight: 700 !important;
    border-top: 2px solid var(--border-ui) !important;
}
```

### Definição Python (Pandas Styler)

O `set_table_styles` no `apply_saedas_design` reforça o footer via bloco `<style>` processado pelo browser:

```python
# app/utils/styles.py — dentro de apply_saedas_design()
{
    "selector": "tbody tr:last-child td",
    "props": [
        ("background-color", "var(--footer-bg)"),
        ("color",            "var(--footer-text)"),
        ("font-weight",      "700"),
        ("border-top",       "2px solid var(--border-ui)"),
    ],
}
```

### Regras obrigatórias

- A linha `"TOTAL"` **deve ser sempre a última** do DataFrame. A função `build_comparativo_anual` garante isso automaticamente.
- O checkbox de seleção da última linha é ocultado via CSS (`visibility: hidden`) — não requer código Python.
- Não use `font-weight: 800` ou itálico — o footer usa as mesmas tipografias do header.
- Nunca estilize o TOTAL via filtro de dados no Python — deixe o CSS e o `set_table_styles` resolverem.

---

## 4. Tabelas — Regras Visuais

### 4.1 Header padrão

Aplicado automaticamente pelo CSS global e reforçado pelo `set_table_styles`:

```css
[data-testid="stDataFrame"] thead th {
    background-color: var(--header-bg);
    color: var(--header-text);
    font-weight: 600;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 2px solid var(--border-ui);
}
```

### 4.2 Linha ativa (seleção)

Controlada pelo `SAEDAS_PALETTE` no Python (não por CSS variáveis) porque o `apply()` inline não resolve `var()` de forma confiável no Streamlit:

```python
# Linha selecionada — cores vindas de SAEDAS_PALETTE[tema]
background-color: {colors['surface_active']}
color:            {colors['text_active']}
font-weight: bold
```

### 4.3 Ocultar controles nativos

Busca interna e menus de coluna são ocultados globalmente para foco analítico:

```css
[data-testid="stDataFrame"] [data-testid="stDataFrameSearch"],
[data-testid="stDataFrame"] [data-testid="stDataFrameColumnHeaderMenu"] {
    display: none !important;
}
```

---

## 5. SAEDAS_PALETTE — Paleta Python

### Motivação

O renderizador do `st.dataframe` processa os estilos inline do Pandas Styler antes de entregá-los ao browser. Nesse estágio, `var(--token)` **não é resolvido** — o valor fica indefinido ou invertido. A `SAEDAS_PALETTE` resolve esse problema fornecendo valores hex diretos para os estilos que precisam de Python-side (linha ativa).

> **Nota:** Header e Footer usam `var()` via `set_table_styles` (bloco `<style>` no HTML), que o browser resolve corretamente. Apenas a **linha ativa** usa `SAEDAS_PALETTE`.

### Estrutura

```python
# app/utils/styles.py
SAEDAS_PALETTE = {
    "dark": {
        "header_bg":   "#1e293b",   # = --header-bg dark
        "header_text": "#cbd5e1",   # = --header-text dark
        "border_ui":   "#334155",   # = --border-ui dark
    },
    "light": {
        "header_bg":   "#f8fafc",   # = --header-bg light
        "header_text": "#475569",   # = --header-text light
        "border_ui":   "#e2e8f0",   # = --border-ui light
    },
}

# Cores do Pro Footer — hardcoded a nível de módulo (independentes de tema)
_FOOTER_BG     = "#1e293b"   # Slate 800
_FOOTER_TEXT   = "#cbd5e1"   # Slate 300
_FOOTER_BORDER = "#334155"   # Slate 700
```

> **Por que o footer é hardcoded?** O `st.dataframe` usa o renderizador `glide-data-grid` e `st.context.theme` não reflete o toggle manual da UI a tempo de aplicar os estilos. Valores fixos garantem contraste adequado em ambos os temas.

### Regra de manutenção

Ao alterar qualquer cor de tabela, atualize **os três lugares** em sincronia:

| O quê | Onde |
| :--- | :--- |
| Tokens CSS de header/border | `app/assets/styles.css` — todos os 4 blocos de tema |
| Equivalentes Python de header | `SAEDAS_PALETTE` em `app/utils/styles.py` |
| Cores de footer fixas | `_FOOTER_BG`, `_FOOTER_TEXT`, `_FOOTER_BORDER` em `app/utils/styles.py` |

---

## 6. apply_saedas_design — API

Função central de estilização. Aplica header, footer e linha ativa a qualquer Styler do Pandas.

```python
# Assinatura
apply_saedas_design(styler, categoria_col, active_items=None)
```

| Parâmetro | Tipo | Descrição |
| :--- | :--- | :--- |
| `styler` | `pd.Styler` ou `pd.DataFrame` | Dados a estilizar. DataFrame é convertido automaticamente. |
| `categoria_col` | `str` | Nome da coluna que identifica a categoria (ex: `"URG"`, `"Escola"`). |
| `active_items` | `list`, `set` ou valor escalar | Aceito por compatibilidade de assinatura, mas **intencionalmente ignorado**. O destaque de linha ativa não é mais aplicado via Python-side nesta função. |

> **Linha ativa:** O realce de linha ativa foi removido do `apply_saedas_design` para eliminar a dependência de `SAEDAS_PALETTE` nos estilos inline do Pandas Styler (que não resolvem `var()` CSS). O comportamento visual de seleção ativa é gerenciado diretamente pelo CSS do AgGrid via `rowSelection` e `onFirstDataRendered`.

```python
# Uso correto (via build_comparativo_anual — já chama apply_saedas_design internamente)
df_cmp = build_comparativo_anual(df, "URG", active_row_value=current_urgs)

# Uso direto (quando build_comparativo_anual não é usado)
df.style.pipe(apply_saedas_design, categoria_col="URG")
```

> **Evite** chamar `apply_saedas_design` sobre um Styler que já passou por `build_comparativo_anual` — o design já foi aplicado.

---

## 7. KPI Cards

### 7.1 Card Estático (`.metric-card-static`)

Exibição pura de valor, sem interação. Utilizado para totais gerais.

- **Borda:** Gradiente Prateado (Silver) — `linear-gradient(135deg, #94a3b8 0%, #334155 100%)`.
- **Fundo:** Sólido Profundo (`#0f172a`).
- **Cursor:** Padrão | Sem hover de elevação.

### 7.2 Card Interativo/Link (`.home-metric-link`)

Elemento clicável que funciona como atalho de navegação ou filtro (Toggle).

- **Borda:** Gradiente Azul (Blue) — `linear-gradient(135deg, #38bdf8 0%, #1e40af 100%)`.
- **Brilho (Glow):** Shadow azulada persistente e intensificada no hover.
- **Ícone:** Inclusão automática do ícone `↗` (External Link) ao lado do rótulo.
- **Interatividade (Hover):**
  - Elevação visual: `transform: translateY(-3px)`.
  - Transição: `0.25s cubic-bezier(0.4, 0, 0.2, 1)`.
- **Estado Ativo (Toggle):** Borda dupla (glow + gap) e fundo `--header-bg`.

### 7.3 Grid dos Indicadores (Regra Obrigatória)

- Todos os indicadores gerais (cards estáticos e cards toggle) devem usar **grid fixo de 5 colunas por linha** (padrão).
- A última linha deve manter a mesma largura de card das linhas anteriores (sem card esticado em largura total).
- Quando houver mais de 5 indicadores, a renderização deve quebrar automaticamente em novas linhas de 5.
- O parâmetro `fixed_columns` de `render_metric_cards` permite sobrescrever o número de colunas quando necessário (ex.: `fixed_columns=4` para páginas com 4 categorias fixas).
- Implementação padrão centralizada em `app/utils/styles.py` na função `render_metric_cards(...)`.

### 7.4 Ordem em Tabelas Comparativas por ANO (Regra Obrigatória)

- Nas telas com indicadores gerais por categoria (ex.: Encaminhamento, Regulação), a **Tabela Comparativa de Performance por ANO** deve seguir a **mesma ordem visual dos indicadores gerais**.
- A regra vale para a renderização da grade (AgGrid) e para exportação CSV da mesma tabela.
- A linha `TOTAL` deve permanecer como última linha, independentemente da ordenação das categorias.
- Implementação atual aplicada em:
  - `app/app_pages/consulta.py` (Encaminhamentos)
  - `app/app_pages/exame.py` (Regulações)

---

## 8. Rodapé de Página (footer_personal)

O componente `footer_personal()` em `app/components/footer_personal.py` exibe um rodapé fixo usando `position: fixed; bottom: 0`. Usa o token `--surface-elevated` para o fundo.

```python
# Chamada obrigatória no final de cada page_*()
from components.footer_personal import footer_personal
footer_personal()
```

---

## 9. CSS de Componentes Streamlit (Regra de Estabilidade)

Para customizações de layout em componentes Streamlit:

- **Não usar** classes dinâmicas do Emotion (`.st-emotion-cache-*`), pois mudam entre reruns/builds.
- Preferir seletores estáveis por `key` (`.st-key-...`) e `data-testid`.
- Escopar CSS no menor container possível (ex.: `.st-key-home_columns_panel ...`) para evitar efeito colateral em outras páginas.

Exemplo recomendado:

```css
.st-key-home_columns_panel div[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
}
```

---

## 10. Padrão de Toolbar Unificada (Clipboard + CSV)

Para tabelas do dashboard (AgGrid e Pandas), o uso da `render_table_toolbar()` é **obrigatório**. Este componente supera as restrições de segurança do navegador que impedem o acesso ao clipboard em iframes padrão do Streamlit.

### 10.1 Arquitetura Híbrida
A toolbar não usa botões nativos do Streamlit para Cópia e CSV. Ela é renderizada via `st.components.v1.html`, o que garante:
- **Gesto do Usuário:** O clique ocorre dentro do iframe do componente, permitindo o uso da `navigator.clipboard API`.
- **Zero Rerun:** O download do CSV e a cópia são processados inteiramente no lado do cliente (JavaScript), tornando a interface instantânea e evitando recargas desnecessárias do servidor.

### 10.2 Regras de Posicionamento e Alinhamento
- **Localização:** Sempre no topo direito da tabela/gráfico correspondente.
- **Estrutura de Colunas:**
  - Com botão de ação extra: `st.columns([0.70, 0.12, 0.18], gap="small")`
  - Sem botão de ação extra: `st.columns([0.82, 0.18], gap="small")`
- **Container:** O container pai deve ter `overflow: visible !important` para não cortar os botões ou o feedback de "Copiado".

### 10.3 Estética e Feedback
- **Agrupamento:** Botões colados com borda única entre eles.
- **Feedback:** O botão de cópia deve exibir "✅ Copiado!" por 2 segundos após o sucesso.
- **Destaque:** O botão CSV possui fundo azul translúcido (`--surface-active`) para diferenciação visual.

---

## 11. Governança e Regras de Implementação

Para evitar regressões e manter a integridade visual (WOW factor), as seguintes regras de negócio devem ser seguidas rigorosamente:

### 11.1 Isolamento de CSS
- **Nunca** injete CSS global diretamente nas páginas se ele puder ser resolvido via `app/assets/styles.css`.
- Use seletores por `key` para evitar que estilos de uma aba "vazem" para outra.

### 11.2 Hierarquia de Mudanças
1. **Tokens (Cores/Bordas):** Alterar apenas em `styles.css`.
2. **Componentes (Estrutura):** Alterar apenas em `app/utils/page_helpers.py`.
3. **Páginas (Layout):** Organização via `st.columns` e containers.

### 11.3 Restrições de Browser (Permissions Policy)
Ao implementar novas funcionalidades que exijam APIs do navegador (Clipboard, Geolocalização, Notificações):
- **Sempre** utilize componentes HTML customizados.
- O Streamlit isola cada elemento em um iframe com políticas restritivas; componentes unificados são a única forma de garantir que o "user gesture" seja capturado corretamente.

---

## 12. Checklist de Validação Visual
Antes de considerar uma tarefa de UI como concluída, verifique:
- [ ] Os botões da toolbar estão perfeitamente alinhados à direita da tabela?
- [ ] O arredondamento das bordas está correto (externas redondas, internas retas)?
- [ ] O clipboard funciona em ambiente de produção (Docker/HTTPS)?
- [ ] O tema Light e Dark estão legíveis e respeitando os tokens?
- [ ] Não há "layout shift" (pulos na tela) ao carregar os componentes?
 
 ---
 
 ## 12. Checklist de Validação Visual
