import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.utils import page_helpers
from app.utils.page_helpers import (
    build_profile_cell_click_navigation_js,
    build_profile_click_return_js,
    build_profile_link_cell_renderer_js,
    get_profile_url_from_aggrid_event,
    get_profile_url_from_aggrid_response,
    get_profile_url_from_aggrid_selection,
    get_selected_comparativo_value,
    prepare_profile_action_column,
    prepare_table_toolbar_exports,
)


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


def test_prepare_profile_action_column_keeps_url_hidden_and_shows_person_button_label():
    df = pd.DataFrame({"Aluno": ["Ana"], "Perfil": ["?menu=Aluno&aluno=Ana"]})

    result = prepare_profile_action_column(df)

    assert result.loc[0, "Perfil"].startswith("👤 Ver Perfil")
    assert "__SAEDAS_PROFILE_URL__?menu=Aluno&aluno=Ana" in result.loc[0, "Perfil"]
    assert result.loc[0, "_PerfilUrl"] == "?menu=Aluno&aluno=Ana"


def test_get_profile_url_from_aggrid_event_returns_hidden_url_for_profile_click():
    event_data = {
        "colDef": {"field": "Perfil"},
        "data": {"_PerfilUrl": "?menu=Aluno&aluno=Ana&nasc=2010-01-01"},
    }

    assert (
        get_profile_url_from_aggrid_event(event_data)
        == "?menu=Aluno&aluno=Ana&nasc=2010-01-01"
    )


def test_get_profile_url_from_aggrid_event_ignores_other_columns():
    event_data = {
        "colDef": {"field": "Aluno"},
        "data": {"_PerfilUrl": "?menu=Aluno&aluno=Ana"},
    }

    assert get_profile_url_from_aggrid_event(event_data) is None


def test_get_profile_url_from_aggrid_event_accepts_column_col_id_payload():
    event_data = {
        "column": {"colId": "Perfil"},
        "data": {"_PerfilUrl": "?menu=Aluno&aluno=Ana"},
    }

    assert get_profile_url_from_aggrid_event(event_data) == "?menu=Aluno&aluno=Ana"


def test_profile_click_custom_return_js_returns_profile_url_payload():
    collector_js = build_profile_click_return_js()

    assert "streamlitRerunEventTriggerName !== 'cellClicked'" in collector_js
    assert "column.getColId ? column.getColId() : null" in collector_js
    assert "return {profileUrl: profileUrl};" in collector_js
    assert "_PerfilUrl" in collector_js


def test_profile_link_cell_renderer_builds_native_parent_target_link_html():
    renderer_js = build_profile_link_cell_renderer_js()

    assert "function(params)" in renderer_js
    assert "params.eGridCell || params.eParentOfValue" in renderer_js
    assert "window.parent.location.href = profileUrl" in renderer_js
    assert "params.data._PerfilUrl" in renderer_js
    assert "👤 Ver Perfil" in renderer_js


def test_profile_cell_click_navigation_js_routes_parent_window():
    click_js = build_profile_cell_click_navigation_js()

    assert "function(params)" in click_js
    assert "params.colDef.field !== 'Perfil'" in click_js
    assert "params.data._PerfilUrl" in click_js
    assert "window.parent.location.href = profileUrl" in click_js


def test_get_profile_url_from_aggrid_response_reads_custom_response():
    class ResponseStub:
        def get(self, key, default=None):
            return {"profileUrl": "?menu=Aluno&aluno=Ana"}.get(key, default)

    assert (
        get_profile_url_from_aggrid_response(ResponseStub())
        == "?menu=Aluno&aluno=Ana"
    )


def test_get_profile_url_from_aggrid_selection_reads_hidden_url_from_selected_row():
    class ResponseStub:
        selected_rows = pd.DataFrame({"_PerfilUrl": ["?menu=Aluno&aluno=Ana"]})

    assert (
        get_profile_url_from_aggrid_selection(ResponseStub())
        == "?menu=Aluno&aluno=Ana"
    )


def test_route_to_profile_url_updates_main_menu_widget_state(monkeypatch):
    rerun_called = {"value": False}

    class StreamlitStub:
        session_state = {}

        @staticmethod
        def rerun():
            rerun_called["value"] = True

    monkeypatch.setattr(page_helpers, "st", StreamlitStub)

    page_helpers.route_to_profile_url("?menu=Aluno&aluno=Ana&nasc=2010-01-01")

    assert StreamlitStub.session_state["menu_escolhido"] == "Aluno"
    assert StreamlitStub.session_state["sidebar_main_menu"] == "Aluno"
    assert StreamlitStub.session_state["aluno_preselect"] == {
        "nome": "Ana",
        "nasc": "2010-01-01",
    }
    assert rerun_called["value"] is True


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
