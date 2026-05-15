import ast
from pathlib import Path


def test_consulta_top_table_uses_sidebar_filtered_data():
    source = Path("app/app_pages/consulta.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", "") == "render_top_por_urg"
        and any(
            isinstance(arg, ast.Constant)
            and arg.value == "Principais Encaminhamentos por URG"
            for arg in node.args
        )
    ]

    assert len(calls) == 1
    assert ast.unparse(calls[0].args[0]).startswith("df_filt[")


def test_consulta_top_table_does_not_enable_row_selection():
    source = Path("app/app_pages/consulta.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", "") == "render_top_por_urg"
        and any(
            isinstance(arg, ast.Constant)
            and arg.value == "Principais Encaminhamentos por URG"
            for arg in node.args
        )
    ]

    assert len(calls) == 1

    keyword_names = {keyword.arg for keyword in calls[0].keywords}

    assert "table_key" not in keyword_names
    assert "selection_mode" not in keyword_names


def test_consulta_encaminhamento_year_performance_ignores_own_filter():
    source = Path("app/app_pages/consulta.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    assignments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "df_cmp_ano_perf"
            for target in node.targets
        )
    ]

    assert len(assignments) == 1
    call = assignments[0].value

    assert isinstance(call, ast.Call)
    assert getattr(call.func, "id", "") == "build_comparativo_anual"
    assert ast.unparse(call.args[0]) == "df_filt_no_enc"


def test_consulta_encaminhamento_distribution_ignores_own_filter():
    source = Path("app/app_pages/consulta.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", "") == "render_grouped_bar_anual"
        and any(
            keyword.arg == "x_col"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == "Encaminhamento"
            for keyword in node.keywords
        )
    ]

    assert len(calls) == 1
    assert ast.unparse(calls[0].args[0]) == "df_filt_no_enc"


def test_consulta_encaminhamento_options_are_global_not_sidebar_filtered():
    source = Path("app/app_pages/consulta.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    assignments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "encaminhamentos_disponiveis"
            for target in node.targets
        )
    ]

    assert len(assignments) == 1
    assignment_source = ast.unparse(assignments[0].value)

    assert "df_filt_sidebar" not in assignment_source
    assert "df[" in assignment_source
