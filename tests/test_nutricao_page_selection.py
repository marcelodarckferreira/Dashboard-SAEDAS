import ast
from pathlib import Path


def test_nutricao_top_table_does_not_enable_row_selection():
    source = Path("app/app_pages/nutricao.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", "") == "render_top_por_urg"
        and any(
            isinstance(arg, ast.Constant)
            and arg.value == "Principais Situações Nutricionais por URG"
            for arg in node.args
        )
    ]

    assert len(calls) == 1

    keyword_names = {keyword.arg for keyword in calls[0].keywords}

    assert "table_key" not in keyword_names
    assert "selection_mode" not in keyword_names


def test_nutricao_top_table_uses_sidebar_filtered_data():
    source = Path("app/app_pages/nutricao.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", "") == "render_top_por_urg"
        and any(
            isinstance(arg, ast.Constant)
            and arg.value == "Principais Situações Nutricionais por URG"
            for arg in node.args
        )
    ]

    assert len(calls) == 1
    assert ast.unparse(calls[0].args[0]).startswith("df_filt[")


def test_non_interactive_comparativo_caption_mentions_sidebar_filters():
    source = Path("app/utils/page_helpers.py").read_text(encoding="utf-8")

    assert "Esta tabela utiliza os filtros da sidebar." in source


def test_final_nutricao_comparativo_uses_filtered_sidebar_data():
    source = Path("app/app_pages/nutricao.py").read_text(encoding="utf-8")

    assert (
        'df_cmp_nutricao = build_comparativo_anual(df_filt, "Nutricao")'
        in source
    )
    assert "nutricao_table_selection" not in source
    assert "sync_nutricao_table_to_sidebar" not in source
