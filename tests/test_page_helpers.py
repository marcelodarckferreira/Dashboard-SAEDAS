import pandas as pd
from pathlib import Path

from app.utils import page_helpers
from app.utils.page_helpers import get_selected_comparativo_value, prepare_table_toolbar_exports


class StreamlitStub:
    def __init__(self):
        self.subheaders = []
        self.infos = []

    def subheader(self, value):
        self.subheaders.append(value)

    def info(self, value):
        self.infos.append(value)


def test_render_top_por_urg_handles_empty_dataframe_without_urg(monkeypatch):
    st_stub = StreamlitStub()
    monkeypatch.setattr(page_helpers, "st", st_stub)

    result = page_helpers.render_top_por_urg(
        pd.DataFrame(), "Quantidade", "Principais Exames por URG", "Regulacao"
    )

    assert result is None
    assert st_stub.subheaders == ["Principais Exames por URG"]
    assert st_stub.infos == ["Nenhum dado para exibir com os filtros atuais."]


def test_get_selected_comparativo_value_ignores_stale_row_index():
    df = pd.DataFrame({("Escola", ""): ["EMEF 1"]})

    result = get_selected_comparativo_value(df, [3], "Escola")

    assert result is None


def test_get_selected_comparativo_value_returns_valid_multiindex_value():
    df = pd.DataFrame({("Escola", ""): ["EMEF 1", "TOTAL"]})

    assert get_selected_comparativo_value(df, [0], "Escola") == "EMEF 1"
    assert get_selected_comparativo_value(df, [1], "Escola") is None


def test_prepare_table_toolbar_exports_uses_csv_and_tsv_formats():
    df = pd.DataFrame({"URG": ["URG I-CENTRO"], "Qtd": [160]})

    csv_data, copy_text = prepare_table_toolbar_exports(df)

    assert csv_data == "URG;Qtd\nURG I-CENTRO;160\n".encode("utf-8-sig")
    assert copy_text == "URG\tQtd\nURG I-CENTRO\t160\n"


def test_home_detail_toolbar_uses_shared_table_toolbar_component():
    source = Path("app/app_pages/home.py").read_text(encoding="utf-8")

    assert 'with st.container(key="home_detail_toolbar")' in source
    assert "render_table_toolbar(" in source
    assert 'leading_action_label="⚙️ Colunas"' in source
    assert ".to_clipboard(" not in source


def test_massive_year_selector_targets_streamlit_button_group_dom():
    css = Path("app/assets/styles.css").read_text(encoding="utf-8")

    assert '.st-key-massive_year_selector [data-testid="stButtonGroup"]' in css
    assert '.st-key-massive_year_selector [data-baseweb="button-group"]' in css
    assert "grid-template-columns: repeat(5, minmax(0, 1fr)) !important;" in css
    assert "height: 100% !important;" in css
    assert "place-items: center !important;" in css
    assert "position: absolute !important;" in css
    assert "inset: 0 !important;" in css
