import pandas as pd
import plotly.express as px
import streamlit as st

from app.utils.styles import render_metric_cards


def get_filter_display_string(key_name, selections, df_original, column_name):
    """Return a compact display string for the current filter selection."""
    selected_items = selections.get(key_name, [])
    if df_original is None or column_name not in df_original.columns:
        return "N/A"

    all_items = sorted(df_original[column_name].dropna().unique())
    if not selected_items or len(selected_items) == len(all_items):
        return "Todos(as)"
    return ", ".join(map(str, sorted(set(selected_items))))


def filter_by_sidebar_selections(df: pd.DataFrame, selections: dict) -> pd.DataFrame:
    """Apply the common sidebar selections (ano, URG, Escola, Tipo) to a DataFrame."""
    if df is None or df.empty:
        return pd.DataFrame(columns=df.columns if df is not None else [])

    filtered = df.copy()

    anos = selections.get("ano") or []
    if "Ano" in filtered.columns and anos:
        filtered = filtered[filtered["Ano"].isin(anos)]

    urgs = selections.get("urg") or []
    if "URG" in filtered.columns and urgs:
        filtered = filtered[filtered["URG"].isin(urgs)]

    escolas = selections.get("escola") or []
    if "Escola" in filtered.columns and escolas:
        filtered = filtered[filtered["Escola"].isin(escolas)]

    tipos = selections.get("tipo") or []
    if "Tipo" in filtered.columns and tipos:
        filtered = filtered[filtered["Tipo"].isin(tipos)]

    return filtered


def render_metric(label: str, value) -> None:
    """Render a single metric card inside a 4-column layout (first column used)."""
    cols_metrics = st.columns(4)
    with cols_metrics[0]:
        render_metric_cards([(label, value)])


def render_grouped_bar(
    df, group_col, value_col, title, percent_label="% do Total", color_col=None
):
    """Render a horizontal bar chart plus table for a grouped summary."""
    group = df.groupby(group_col)[value_col].sum().reset_index()
    if group.empty:
        st.info(f"Nenhum dado de {title.lower()} para exibir.")
        return

    total = group[value_col].sum()
    group[percent_label] = (100 * group[value_col] / total).round(2).astype(str) + "%"
    fig = px.bar(
        group.sort_values(value_col, ascending=False),
        x=value_col,
        y=group_col if isinstance(group_col, str) else group_col[-1],
        orientation="h",
        text=percent_label,
        color=color_col or (group_col if isinstance(group_col, str) else None),
    )
    fig.update_traces(textposition="auto")
    st.subheader(title)
    st.plotly_chart(fig, width="stretch")
    st.dataframe(
        group.sort_values(value_col, ascending=False), width="stretch", hide_index=True
    )
    st.markdown(f"**Total: {total:,.0f}**".replace(",", "."))


def render_evolucao(df, value_col="Quantidade"):
    """Render evolution by Ano and URG line chart and table."""
    evolucao = df.groupby(["Ano", "URG"])[value_col].sum().reset_index()
    st.subheader("Evolução por Ano e URG")
    if evolucao.empty:
        st.info("Nenhum dado de Evolução para exibir.")
        return

    fig = px.line(evolucao, x="Ano", y=value_col, color="URG", markers=True)
    fig.update_layout(
        xaxis=dict(
            tickformat=",d",
            tickmode="array",
            ticktext=[str(int(ano)) for ano in sorted(evolucao["Ano"].unique())],
            tickvals=sorted(evolucao["Ano"].unique()),
        ),
        separators=",.",
        yaxis=dict(tickformat=",.0f"),
    )
    st.plotly_chart(fig, width="stretch")
    st.dataframe(evolucao, width="stretch", hide_index=True)
    st.markdown(f"**Total: {evolucao[value_col].sum():,.0f}**".replace(",", "."))


def render_top_por_urg(df, value_col, titulo, label_col):
    """Render horizontal bar for a single URG selection (one title only)."""
    urgs_aplicadas = df["URG"].unique()
    if len(urgs_aplicadas) != 1:
        st.subheader(titulo)
        st.info("Selecione apenas uma URG na sidebar para detalhar.")
        return

    urg_selecionada = urgs_aplicadas[0]
    st.subheader(f"{titulo} (URG {urg_selecionada})")

    group = df.groupby(label_col)[value_col].sum().reset_index()
    if group.empty:
        st.info(f"Nenhum dado para a URG '{urg_selecionada}' com os filtros atuais.")
        return

    group["% na URG"] = (100 * group[value_col] / group[value_col].sum()).round(
        2
    ).astype(str) + "%"
    fig = px.bar(
        group.sort_values(value_col, ascending=False),
        x=value_col,
        y=label_col,
        orientation="h",
        text="% na URG",
    )
    fig.update_traces(textposition="auto")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(
        group.sort_values(value_col, ascending=False), width="stretch", hide_index=True
    )


def format_filters_applied(
    selections: dict,
    df_original: pd.DataFrame | None,
    mapping: list[tuple[str, str, str | None] | tuple[str, str]],
) -> str:
    """
    Build a compact string describing the sidebar filters.

    mapping: list of tuples with (selection_key, df_column, label_optional)
    """
    parts: list[str] = []
    for entry in mapping:
        if len(entry) == 2:
            key_name, column_name = entry  # type: ignore[misc]
            label = column_name
        else:
            key_name, column_name, label = entry  # type: ignore[misc]
            label = label or column_name
        parts.append(
            f"{label}: "
            f"{get_filter_display_string(key_name, selections, df_original, column_name)}"
        )
    return " | ".join(parts) if parts else "Nenhum filtro aplicado"


def build_comparativo_anual(
    df: pd.DataFrame, categoria_col: str, value_col: str = "Quantidade"
) -> pd.DataFrame | None:
    """
    Gera tabela de comparativo anual com colunas de variação absolutas e percentuais,
    respeitando os filtros aplicados na própria página.
    """
    if (
        df is None
        or df.empty
        or "Ano" not in df.columns
        or categoria_col not in df.columns
        or value_col not in df.columns
    ):
        return None

    temp = df[[categoria_col, "Ano", value_col]].dropna(subset=["Ano", categoria_col])
    temp["Ano"] = pd.to_numeric(temp["Ano"], errors="coerce")
    temp = temp.dropna(subset=["Ano"])
    if temp.empty:
        return None

    temp["Ano"] = temp["Ano"].astype(int)
    pivot = (
        temp.groupby([categoria_col, "Ano"])[value_col]
        .sum(min_count=1)
        .reset_index()
        .pivot(index=categoria_col, columns="Ano", values=value_col)
        .fillna(0)
    )
    if pivot.empty:
        return None

    year_cols = sorted([int(c) for c in pivot.columns if pd.notna(c)])
    pivot["Total"] = pivot[year_cols].sum(axis=1)
    df_cmp = pivot.reset_index()

    # Variações
    for prev, curr in zip(year_cols, year_cols[1:]):
        abs_col = f"Var {curr % 100:02d}-{prev % 100:02d}"
        pct_col = f"Var% {curr % 100:02d}-{prev % 100:02d}"
        df_cmp[abs_col] = df_cmp[curr] - df_cmp[prev]
        df_cmp[pct_col] = df_cmp[abs_col] / df_cmp[prev].replace({0: pd.NA}) * 100

    # Renomeia anos para string
    df_cmp = df_cmp.rename(columns={y: str(y) for y in year_cols})
    year_cols_str = [str(y) for y in year_cols]

    # Ordem fixa: categoria, 2022, Var 23-22, Var% 23-22, 2023, Var 24-23, Var% 24-23, 2024, Var 25-24, Var% 25-24, 2025, Total
    col_order = [categoria_col]

    def add_year_block(prev_year: int, curr_year: int) -> list[str]:
        return [
            f"Var {curr_year % 100:02d}-{prev_year % 100:02d}",
            f"Var% {curr_year % 100:02d}-{prev_year % 100:02d}",
        ]

    if "2022" in year_cols_str:
        col_order.append("2022")
    if "2022" in year_cols_str and "2023" in year_cols_str:
        col_order.extend(add_year_block(2022, 2023))
    if "2023" in year_cols_str:
        col_order.append("2023")
    if "2023" in year_cols_str and "2024" in year_cols_str:
        col_order.extend(add_year_block(2023, 2024))
    if "2024" in year_cols_str:
        col_order.append("2024")
    if "2024" in year_cols_str and "2025" in year_cols_str:
        col_order.extend(add_year_block(2024, 2025))
    if "2025" in year_cols_str:
        col_order.append("2025")
    if "Total" in df_cmp.columns:
        col_order.append("Total")

    # Garante que só mantenha colunas existentes
    col_order = [c for c in col_order if c in df_cmp.columns]
    df_cmp = df_cmp[col_order]

    pct_cols = [c for c in df_cmp.columns if c.startswith("Var% ")]
    abs_cols = [c for c in df_cmp.columns if c not in pct_cols and c != categoria_col]

    df_display = df_cmp.copy()
    for c in abs_cols:
        df_display[c] = df_display[c].map(
            lambda x: f"{x:,.0f}".replace(",", ".") if pd.notna(x) else ""
        )
    for c in pct_cols:
        df_display[c] = df_display[c].map(
            lambda x: f"{x:,.1f}".replace(",", ".") if pd.notna(x) else ""
        )

    return df_display
