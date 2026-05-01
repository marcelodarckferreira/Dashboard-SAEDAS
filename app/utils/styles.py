import pathlib
import streamlit as st


def apply_global_css(css_path: str = "app/assets/styles.css") -> None:
    """Injeta CSS global a partir do arquivo fornecido."""
    path = pathlib.Path(css_path)
    if not path.exists():
        return
    css = path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_metric_cards(metrics: list[tuple[str, float | int | str]]) -> None:
    """
    Renderiza uma linha de cards de métricas com o estilo usado na Home.
    Cada item da lista é uma tupla (rótulo, valor).
    """
    metric_css = """
    <style>
        .home-metric-card {
            background: linear-gradient(135deg, #0f172a, #1f2937);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 14px 16px;
            box-shadow: 0 4px 18px rgba(0,0,0,0.18);
            color: #e5e7eb;
            display: flex;
            flex-direction: column;
            gap: 6px;
            height: 100%;
        }
        .home-metric-label {
            font-size: 0.9rem;
            letter-spacing: 0.01em;
            color: #cbd5e1;
        }
        .home-metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #f8fafc;
            line-height: 1.2;
        }
    </style>
    """
    st.markdown(metric_css, unsafe_allow_html=True)

    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        try:
            value_fmt = f"{float(value):,.0f}".replace(",", ".")
        except Exception:
            value_fmt = str(value)
        card_html = (
            f'<div class="home-metric-card">'
            f'<div class="home-metric-label">{label}</div>'
            f'<div class="home-metric-value">{value_fmt}</div>'
            "</div>"
        )
        with col:
            st.markdown(card_html, unsafe_allow_html=True)


def style_urg_performance_table(df, active_urgs, categoria_col="URG"):
    """
    Aplica o estilo de destaque (Highlight) e zebra às tabelas de performance.
    Garante que as unidades ativas fiquem visivelmente realçadas.
    """
    if df is None:
        return None

    # Se já for um Styler (ex: vindo de build_comparativo_anual), usa-o diretamente.
    # Caso contrário, cria um Styler a partir do DataFrame.
    styler = df if hasattr(df, "apply") else df.style

    def _zebra_highlight(row):
        # O MultiIndex do build_comparativo_anual tem a categoria no nível (col, '')
        try:
            val_cat = row[(categoria_col, "")]
        except (KeyError, IndexError):
            try:
                val_cat = row[categoria_col]
            except:
                val_cat = None

        is_active = val_cat in active_urgs

        if val_cat == "TOTAL":
            style = "background-color: #2b3b4e; font-weight: bold; border-top: 2px solid #ffffff; color: #ffffff;"
        elif is_active:
            # Vibrant Highlight Pattern
            style = "background-color: rgba(96, 165, 250, 0.3) !important; border: 2px solid #60a5fa !important; font-weight: bold;"
        else:
            # Alternância de cores para zebra
            bg = "#1e2530" if row.name % 2 == 0 else "#161c26"
            style = f"background-color: {bg}; border: 1px solid rgba(255, 255, 255, 0.05);"
        return [style] * len(row)

    hover_styles = [
        {
            "selector": "thead th",
            "props": [("text-align", "center"), ("background-color", "#161c26")],
        },
        {
            "selector": "tbody tr:hover td",
            "props": [("background-color", "#374151 !important")],
        },
    ]

    return styler.apply(_zebra_highlight, axis=1).set_table_styles(hover_styles, overwrite=False)
