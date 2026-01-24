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
