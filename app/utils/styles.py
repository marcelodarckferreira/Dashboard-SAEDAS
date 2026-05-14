import pathlib
import streamlit as st
import pandas as pd

# ──────────────────────────────────────────────────────────────────
# Paleta de Design (fonte única de verdade para estilos de dataframe)
# Espelha os tokens CSS de styles.css para uso no Pandas Styler,
# já que o renderizador nativo do st.dataframe não resolve var() CSS.
# ──────────────────────────────────────────────────────────────────
# Cores fixas do Pro Footer — independentes de tema.
# st.dataframe usa glide-data-grid e st.context.theme não reflete o toggle da UI,
# portanto usamos valores hardcoded que funcionam em light e dark.
_FOOTER_BG     = "#1e293b"   # Slate 800 — cor de marca do header
_FOOTER_TEXT   = "#cbd5e1"   # Slate 300 — texto legível sobre fundo escuro
_FOOTER_BORDER = "#334155"   # Slate 700

SAEDAS_PALETTE = {
    "dark": {
        "header_bg":   "#1e293b",
        "header_text": "#cbd5e1",
        "border_ui":   "#334155",
    },
    "light": {
        "header_bg":   "#f8fafc",
        "header_text": "#475569",
        "border_ui":   "#e2e8f0",
    },
}


def _current_theme_colors() -> dict:
    """Retorna a paleta do tema ativo (light ou dark)."""
    try:
        base = st.context.theme.base  # "light" | "dark"
    except Exception:
        base = "dark"
    return SAEDAS_PALETTE.get(base, SAEDAS_PALETTE["dark"])


# ──────────────────────────────────────────────────────────────────
# Injeção do CSS global
# ──────────────────────────────────────────────────────────────────
def apply_global_css(css_path: str = "app/assets/styles.css") -> None:
    """Injeta CSS global a partir do arquivo de design system."""
    path = pathlib.Path(css_path)
    if not path.exists():
        return
    css = path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# Lógica Interna de Estilo de Linha (Reutilizável)
# ──────────────────────────────────────────────────────────────────
def _saedas_row_style_logic(row, categoria_col):
    """Lógica central de decisão de estilo por linha."""
    try:
        try:
            val_cat = row[(categoria_col, "")]
        except (KeyError, IndexError):
            val_cat = row.get(categoria_col, row.iloc[0])

        # TOTAL: distinção via font-weight e border-top.
        if str(val_cat).strip().upper() == "TOTAL":
            return [
                "font-weight: 700 !important; "
                f"border-top: 2px solid {_FOOTER_BORDER} !important; "
            ] * len(row)

        return [""] * len(row)
    except Exception:
        return [""] * len(row)


# ──────────────────────────────────────────────────────────────────
# Função Global de Estilização (SAEDAS Design)
# ──────────────────────────────────────────────────────────────────
def apply_saedas_design(styler, categoria_col, active_items=None):  # noqa: ARG001
    """
    Aplica o design system (header + Pro Footer) às tabelas do projeto.
    """
    del active_items  # intencionalmente não utilizado
    if styler is None:
        return None

    if not hasattr(styler, "apply"):
        styler = styler.style

    # set_table_styles gera um bloco <style> processado pelo browser,
    # onde var() CSS é resolvido corretamente pelo tema ativo (toggle incluso).
    return styler.apply(_saedas_row_style_logic, axis=1, categoria_col=categoria_col).set_table_styles([
        {
            "selector": "thead th",
            "props": [
                ("background-color", "var(--header-bg)"),
                ("color", "var(--header-text)"),
                ("font-weight", "700"),
                ("border-bottom", "2px solid var(--border-ui)"),
            ],
        },
        {
            "selector": "tbody tr:last-child td",
            "props": [
                ("font-weight", "700"),
                ("border-top", f"2px solid {_FOOTER_BORDER}"),
            ],
        },
    ])


# ──────────────────────────────────────────────────────────────────
# Wrappers de Compatibilidade
# ──────────────────────────────────────────────────────────────────
def style_urg_performance_table(df, active_urgs, categoria_col: str = "URG"):
    return apply_saedas_design(df, categoria_col, active_urgs)

def build_row_style_fn(categoria_col: str, active_row_value=None):
    """Retorna uma função de estilo compatível com df.style.apply."""
    del active_row_value # Mantido para compatibilidade de assinatura
    return lambda row: _saedas_row_style_logic(row, categoria_col)

def render_metric_cards(
    metrics: list, 
    is_toggle: bool = False, 
    active_labels: list[str] = None,
    on_click_callback=None,
    fixed_columns: int | None = None,
) -> None:
    """
    Renderiza cards de métricas premium com suporte a links e interatividade.
    
    metrics: Lista de dicts [{"label": "...", "value": 123, "link": "/?menu=..."}] ou tuplas [("LABEL", 123)]
    is_toggle: Se True, renderiza como botões clicáveis do Streamlit para disparar reruns.
    active_labels: Labels ativos no modo toggle.
    on_click_callback: Função a ser chamada quando um card (botão) é clicado.
    """
    if active_labels is None: active_labels = []
    
    # Normalização de dados: converte tuplas em dicionários
    normalized_metrics = []
    for m in metrics:
        if isinstance(m, tuple) and len(m) >= 2:
            normalized_metrics.append({"label": m[0], "value": m[1]})
        elif isinstance(m, dict):
            normalized_metrics.append(m)
        else:
            continue

    # Injeta CSS de reset de link localmente para garantir paridade com a Home
    st.markdown("""
        <style>
            .metric-card-link-wrapper {
                text-decoration: none !important;
                color: inherit !important;
                display: block;
                height: 100%;
            }
            .metric-card-link-wrapper:hover {
                text-decoration: none !important;
            }
            div[data-testid="stMarkdownContainer"] a.metric-card-link-wrapper {
                text-decoration: none !important;
                border-bottom: none !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Padrão global dos indicadores gerais: grid fixo de 5 colunas.
    num_cols = fixed_columns if fixed_columns is not None else 5
    num_cols = max(1, int(num_cols))

    for row_start in range(0, len(normalized_metrics), num_cols):
        row_metrics = normalized_metrics[row_start: row_start + num_cols]
        cols = st.columns(num_cols)

        for i, metric in enumerate(row_metrics):
            col = cols[i]

            label = str(metric.get("label", "")).upper()
            value = metric.get("value", 0)
            link = metric.get("link")

            try:
                if isinstance(value, (int, float)):
                    value_fmt = f"{float(value):,.0f}".replace(",", ".")
                else:
                    value_fmt = str(value)
            except:
                value_fmt = str(value)

            with col:
                if is_toggle:
                    is_active = label in [l.upper() for l in active_labels]
                    button_type = "primary" if is_active else "secondary"
                    st.button(
                        f"{label}\n**{value_fmt}**",
                        key=f"btn_kpi_{label}_{value_fmt}_{row_start}_{i}",
                        on_click=on_click_callback,
                        args=(label,) if on_click_callback else None,
                        type=button_type,
                        use_container_width=True
                    )
                else:
                    base_class = "home-metric-card"
                    state_class = "metric-card-static"
                    link_class = "home-metric-link" if link else ""

                    card_content = f"""
                    <div class="{base_class} {state_class} {link_class}">
                        <div class="home-metric-label">{label}</div>
                        <div class="home-metric-value">{value_fmt}</div>
                    </div>
                    """

                    if link:
                        # target="_self" é crucial para navegação SPA no Streamlit
                        st.markdown(
                            f'<a href="{link}" target="_self" class="home-metric-link-wrapper">{card_content}</a>', 
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(card_content, unsafe_allow_html=True)

def get_table_hover_styles():
    """Retorna estilos de hover (Legacy wrapper)."""
    colors = _current_theme_colors()
    return [{"selector": "thead th", "props": [("font-weight", "700"), ("border-bottom", f"2px solid {colors['border_ui']}")]}]
