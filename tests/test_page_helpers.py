import pandas as pd

from app.utils import page_helpers
from app.utils.page_helpers import get_selected_comparativo_value


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
