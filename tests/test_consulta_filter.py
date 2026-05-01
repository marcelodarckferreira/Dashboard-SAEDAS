import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.utils.page_helpers import (
    get_native_regulacao_button_type,
    should_use_native_regulacao_button,
    toggle_multiselect_value,
)


def test_toggle_multiselect_value_adds_dentista_to_regulacao_selection():
    result = toggle_multiselect_value(["PEDIATRA"], "DENTISTA")

    assert result == ["PEDIATRA", "DENTISTA"]


def test_toggle_multiselect_value_removes_existing_regulacao_selection():
    result = toggle_multiselect_value(["PEDIATRA", "DENTISTA"], "DENTISTA")

    assert result == ["PEDIATRA"]


def test_consulta_regulacao_cards_do_not_use_query_param_toggle_links():
    consulta_source = (
        Path(__file__).resolve().parents[1] / "app" / "app_pages" / "consulta.py"
    ).read_text(encoding="utf-8")

    assert '"toggle_reg"' not in consulta_source
    assert "&toggle_reg=" not in consulta_source
    assert 'href="/?menu=Encaminhamentos' not in consulta_source


def test_consulta_regulacao_overlay_supports_current_streamlit_columns():
    consulta_source = (
        Path(__file__).resolve().parents[1] / "app" / "app_pages" / "consulta.py"
    ).read_text(encoding="utf-8")

    assert '[data-testid="stColumn"]' in consulta_source


def test_consulta_regulacao_multiselect_is_controlled_by_session_state_only():
    consulta_source = (
        Path(__file__).resolve().parents[1] / "app" / "app_pages" / "consulta.py"
    ).read_text(encoding="utf-8")

    widget_start = consulta_source.index("encaminhamentos_selecionados = st.sidebar.multiselect")
    widget_end = consulta_source.index(")", widget_start)
    widget_source = consulta_source[widget_start:widget_end]

    assert "default=" not in widget_source


def test_only_dentista_uses_native_regulacao_button():
    assert should_use_native_regulacao_button("DENTISTA") is True
    assert should_use_native_regulacao_button(" dentista ") is True
    assert should_use_native_regulacao_button("PEDIATRA") is False


def test_dentista_native_button_type_changes_with_selection_state():
    assert get_native_regulacao_button_type("DENTISTA", ["DENTISTA"]) == "primary"
    assert get_native_regulacao_button_type("DENTISTA", []) == "tertiary"


def test_dentista_native_button_matches_metric_card_shape():
    consulta_source = (
        Path(__file__).resolve().parents[1] / "app" / "app_pages" / "consulta.py"
    ).read_text(encoding="utf-8")

    assert "height: 100% !important;" in consulta_source
    assert "padding: 12px 14px !important;" in consulta_source
    assert "background: linear-gradient(135deg, #0f172a, #1f2937) !important;" in consulta_source
    assert "[data-testid=\"stButton\"] button[kind=\"tertiary\"] strong" in consulta_source
    assert 'f"{nome_str.upper()}\\n**{valor_fmt}**"' in consulta_source
