import pandas as pd
import plotly.express as px
import streamlit as st
import re
import numpy as np
import json
from st_aggrid import JsCode, AgGrid, GridUpdateMode

from app.utils.styles import render_metric_cards, apply_saedas_design


def toggle_multiselect_value(current_selection: list | None, value) -> list:
    """Return a new multiselect list with value toggled on or off."""
    current = list(current_selection or [])
    if value in current:
        current.remove(value)
    else:
        current.append(value)
    return current


def render_section_divider():
    """Renderiza um divisor visual padrão com espaçamento otimizado."""
    st.markdown(" ")
    st.markdown("---")


def prepare_nutricao_aluno_table(
    df_aluno: pd.DataFrame, build_perfil_link, selected_nuts: list = None
) -> pd.DataFrame:
    """Prepare the Nutrição por aluno table with flat string columns for Streamlit."""
    if df_aluno is None or df_aluno.empty:
        return pd.DataFrame()

    df_aluno_para_exibir = df_aluno.copy()

    static_cols = ["Sexo", "URG", "Escola", "Serie", "Turma"]
    static_cols = [c for c in static_cols if c in df_aluno_para_exibir.columns]

    df_static = df_aluno_para_exibir.groupby(
        ["Aluno", "DataNascimento"], as_index=False
    )[static_cols].last()
    df_static["Menu"] = df_static.apply(build_perfil_link, axis=1)

    if "DataNascimento" in df_aluno_para_exibir.columns:
        df_aluno_para_exibir["Idade"] = (
            pd.to_numeric(df_aluno_para_exibir["Ano"], errors="coerce")
            - pd.to_datetime(
                df_aluno_para_exibir["DataNascimento"], errors="coerce"
            ).dt.year
        )
    else:
        df_aluno_para_exibir["Idade"] = pd.NA

    metrics_cols = ["Peso (kg)", "Altura (m)", "IMC", "Idade", "Nutricao"]
    df_aluno_para_exibir = df_aluno_para_exibir.rename(
        columns={"Peso": "Peso (kg)", "Altura": "Altura (m)"}
    )

    df_metrics = (
        df_aluno_para_exibir.groupby(["Aluno", "DataNascimento", "Ano"])[metrics_cols]
        .last()
        .reset_index()
    )

    df_pivot = df_metrics.pivot(
        index=["Aluno", "DataNascimento"], columns="Ano", values=metrics_cols
    )
    df_pivot = df_pivot.swaplevel(axis=1).sort_index(axis=1, level=0)
    df_pivot = df_pivot.reindex(columns=metrics_cols, level=1)

    def _to_float(value):
        if pd.isna(value) or str(value).strip() == "":
            return None
        try:
            return float(str(value).replace(",", "."))
        except ValueError:
            return None

    def _fmt_peso(value):
        parsed = _to_float(value)
        return f"{parsed:.2f}".replace(".", ",") if parsed is not None else ""

    def _fmt_altura(value):
        parsed = _to_float(value)
        return f"{parsed:.2f}".replace(".", ",") if parsed is not None else ""

    def _fmt_imc(value):
        parsed = _to_float(value)
        return f"{parsed:.2f}".replace(".", ",") if parsed is not None else ""

    def _fmt_idade(value):
        parsed = _to_float(value)
        return f"{int(parsed)}" if parsed is not None else ""

    def _fmt_nutricao(value):
        if pd.isna(value):
            return ""
        val = str(value).replace("**", "").strip()
        if selected_nuts and val in selected_nuts:
            return val.upper()
        return val.lower().capitalize()

    for ano in df_pivot.columns.levels[0]:
        if "Peso (kg)" in df_pivot[ano]:
            df_pivot[(ano, "Peso (kg)")] = df_pivot[(ano, "Peso (kg)")].apply(
                _fmt_peso
            )
        if "Altura (m)" in df_pivot[ano]:
            df_pivot[(ano, "Altura (m)")] = df_pivot[(ano, "Altura (m)")].apply(
                _fmt_altura
            )
        if "IMC" in df_pivot[ano]:
            df_pivot[(ano, "IMC")] = df_pivot[(ano, "IMC")].apply(_fmt_imc)
        if "Idade" in df_pivot[ano]:
            df_pivot[(ano, "Idade")] = df_pivot[(ano, "Idade")].apply(_fmt_idade)
        if "Nutricao" in df_pivot[ano]:
            df_pivot[(ano, "Nutricao")] = df_pivot[(ano, "Nutricao")].apply(_fmt_nutricao)

    df_pivot = df_pivot.reset_index()
    
    # 5. Achatar o MultiIndex para strings (Streamlit não suporta column_config com MultiIndex)
    new_columns = []
    for col in df_pivot.columns:
        if isinstance(col, tuple) and col[1] != "":
            new_columns.append(f"{col[0]} | {col[1]}")
        elif isinstance(col, tuple):
            new_columns.append(col[0])
        else:
            new_columns.append(col)
    df_pivot.columns = new_columns

    df_aluno_final = df_static.merge(
        df_pivot, on=["Aluno", "DataNascimento"], how="left"
    ).fillna("")
    
    # Reordenar colunas
    static_cols_needed = ["Aluno", "DataNascimento", "Sexo", "URG", "Escola", "Serie", "Turma", "Menu"]
    col_order_static = [c for c in static_cols_needed if c in df_aluno_final.columns]
    col_order_anos = [c for c in df_aluno_final.columns if c not in col_order_static]
    df_aluno_final = df_aluno_final[col_order_static + sorted(col_order_anos)]
    
    return df_aluno_final


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


def get_selected_comparativo_value(df_cmp, rows, categoria_col: str):
    """Return a selected comparativo category safely, ignoring stale row indexes."""
    if df_cmp is None or not rows:
        return None

    data = getattr(df_cmp, "data", df_cmp)
    if data is None or data.empty:
        return None

    row_index = rows[0]
    if not isinstance(row_index, int) or row_index < 0 or row_index >= len(data):
        return None

    column_key = (categoria_col, "")
    if column_key not in data.columns:
        column_key = categoria_col
    if column_key not in data.columns:
        return None

    selected_value = data.iloc[row_index][column_key]
    if selected_value == "TOTAL":
        return None
    return selected_value


def render_metric(label: str, value) -> None:
    """Render a single metric card inside a 4-column layout (first column used)."""
    cols_metrics = st.columns(4)
    with cols_metrics[0]:
        render_metric_cards([(label, value)])





def _roman_to_int(s: str) -> int:
    """Converte numeral romano (string) para inteiro."""
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    result, prev = 0, 0
    for ch in reversed(s.upper()):
        v = vals.get(ch, 0)
        result += v if v >= prev else -v
        prev = v
    return result

def _urg_sort_key(urg_name: str) -> int:
    """Extrai o numeral romano do nome da URG e retorna seu valor inteiro."""
    m = re.search(r"URG\s+([IVXLCDM]+)", str(urg_name), re.IGNORECASE)
    return _roman_to_int(m.group(1)) if m else 999


def render_grouped_bar_anual(df, value_col, titulo, x_col="URG", orientation="v"):
    """Render bar chart for a single category grouped by year, vertical or horizontal."""
    if df is None or df.empty or x_col not in df.columns or "Ano" not in df.columns or value_col not in df.columns:
        st.info("Nenhum dado disponível para exibir o gráfico.")
        return

    evolucao = df.groupby([x_col, "Ano"])[value_col].sum().reset_index()

    # Escala cromática: Paleta categórica
    color_map = {
        2022: "#60a5fa",  # Azul Claro
        2023: "#1e3a8a",  # Azul Escuro
        2024: "#fb7185",  # Rosa/Salmão
        2025: "#ef4444",  # Vermelho
        2026: "#2dd4bf",  # Verde Água
    }
    
    # Calcular % do Total para exibir no texto
    total_geral = evolucao[value_col].sum()
    evolucao["% Total"] = (100 * evolucao[value_col] / total_geral).round(2).astype(str) + "%"

    x_axis = x_col if orientation == "v" else value_col
    y_axis = value_col if orientation == "v" else x_col
    
    cat_orders = {}
    if x_col == "URG":
        evolucao["_urg_order"] = evolucao["URG"].apply(_urg_sort_key)
        # Sempre ordena ascendente (URG I, II, III...)
        evolucao = evolucao.sort_values(by=["_urg_order", "Ano"], ascending=[True, True])
        urg_ordered = evolucao["URG"].unique().tolist()
        cat_orders[x_col] = urg_ordered
    else:
        # Ordenação padrão decrescente por quantidade se não for URG
        evolucao_totals = evolucao.groupby(x_col)[value_col].sum().reset_index()
        evolucao_totals = evolucao_totals.sort_values(by=value_col, ascending=(orientation == "v"))
        cat_orders[x_col] = evolucao_totals[x_col].tolist()

    fig = px.bar(
        evolucao,
        x=x_axis,
        y=y_axis,
        color="Ano",
        barmode="group",
        orientation=orientation,
        text="% Total" if orientation == "h" else value_col,
        title=titulo,
        color_discrete_map=color_map,
        category_orders=cat_orders,
        hover_data={x_col: True, "Ano": True, value_col: True, "% Total": True}
    )

    fig.update_traces(textposition="outside", textfont_size=12)
    
    layout_args = {
        "uniformtext_minsize": 8,
        "uniformtext_mode": "hide",
        "legend_title_text": "Ano",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "font_color": "white",
    }
    if orientation == "v":
        layout_args["xaxis_title"] = x_col
        layout_args["yaxis_title"] = "Total"
    else:
        layout_args["xaxis_title"] = "Total"
        layout_args["yaxis_title"] = x_col
        
    fig.update_layout(**layout_args)
    
    if orientation == "v":
        fig.update_xaxes(tickangle=-45, showgrid=False)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(255, 255, 255, 0.1)")
    else:
        fig.update_yaxes(showgrid=False, autorange="reversed")
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(255, 255, 255, 0.1)")

    st.plotly_chart(fig, use_container_width=True)


def render_top_por_urg(df, value_col, titulo, label_col, table_key=None, active_row_value=None, selection_mode="single-row", on_select="rerun"):
    """Render horizontal bar for a single URG selection (one title only)."""
    if (
        df is None
        or df.empty
        or "URG" not in df.columns
        or value_col not in df.columns
        or label_col not in df.columns
    ):
        st.subheader(titulo)
        st.info("Nenhum dado para exibir com os filtros atuais.")
        return

    urgs_aplicadas = df["URG"].dropna().unique()
    if len(urgs_aplicadas) == 0:
        st.subheader(titulo)
        st.info("Selecione ao menos uma URG na sidebar para detalhar.")
        return
    if len(urgs_aplicadas) == 1:
        urg_selecionada = urgs_aplicadas[0]
        st.subheader(f"{titulo} (URG {urg_selecionada})")
    else:
        st.subheader(f"{titulo} ({len(urgs_aplicadas)} URGs selecionadas)")
        urg_selecionada = "múltiplas URGs"

    has_ano = "Ano" in df.columns
    groupby_cols = ["Ano", label_col] if has_ano else [label_col]

    group = df.groupby(groupby_cols)[value_col].sum().reset_index()
    if group.empty:
        st.info(f"Nenhum dado para a URG '{urg_selecionada}' com os filtros atuais.")
        return

    # Ajusta o ano para string para ser usado como categoria de cor
    if has_ano:
        group["Ano"] = group["Ano"].astype(int).astype(str)

    group["% na URG"] = (100 * group[value_col] / group[value_col].sum()).round(
        2
    ).astype(str) + "%"
    
    fig_args = {
        "data_frame": group.sort_values(value_col, ascending=False),
        "x": value_col,
        "y": label_col,
        "orientation": "h",
        "text": "% na URG",
    }
    
    if has_ano:
        fig_args["color"] = "Ano"
        fig_args["barmode"] = "group"
        # Mantém as cores categóricas dos anos
        fig_args["color_discrete_map"] = {
            "2022": "#60a5fa",  # Azul Claro
            "2023": "#1e3a8a",  # Azul Escuro
            "2024": "#fb7185",  # Rosa/Salmão
            "2025": "#ef4444",  # Vermelho
            "2026": "#2dd4bf",  # Verde Água
        }

    fig = px.bar(**fig_args)
    fig.update_traces(textposition="auto")
    st.plotly_chart(fig, use_container_width=True)
    
    if has_ano:
        st.markdown(f"### Tabela Comparativa de {label_col} por Ano")
        df_cmp = build_comparativo_anual(df, label_col, value_col, active_row_value=active_row_value)
        if df_cmp is not None:
            df_cmp_aggrid, column_defs, column_map = prepare_comparativo_aggrid_data(
                df_cmp, include_selection_column=bool(table_key)
            )
            df_body, footer_rows = split_aggrid_footer(df_cmp_aggrid)
            label_field = next(
                (f for f, col in column_map.items() if col == label_col or col == (label_col, "")),
                None
            )

            grid_options = {
                "columnDefs": column_defs,
                "defaultColDef": {
                    "resizable": True,
                    "sortable": True,
                    "filter": False,
                    "suppressMenu": True,
                },
                "pinnedBottomRowData": footer_rows,
            }
            if table_key:
                grid_options["rowSelection"] = "single" if selection_mode == "single-row" else "multiple"
                grid_options["rowMultiSelectWithClick"] = selection_mode != "single-row"
                active_values = active_row_value if isinstance(active_row_value, list) else ([active_row_value] if active_row_value else [])
                active_values = [str(v) for v in active_values if v not in (None, "")]
                pre_selected_rows = []
                if label_field and active_values:
                    pre_selected_rows = [
                        idx
                        for idx, val in enumerate(df_body[label_field].tolist())
                        if str(val) in active_values
                    ]
                selected_values_js = json.dumps(active_values)
                label_field_js = json.dumps(label_field) if label_field else "null"
                sync_selection_js = JsCode(
                    f"""
                    function(params) {{
                        const selectedValues = new Set({selected_values_js});
                        const labelField = {label_field_js};
                        if (!params.api || !labelField) return;
                        params.api.forEachNode(function(node) {{
                            const rowLabel = node.data ? String(node.data[labelField] || '') : '';
                            node.setSelected(selectedValues.has(rowLabel));
                        }});
                    }}
                    """
                )
                grid_options["onFirstDataRendered"] = sync_selection_js
                grid_options["onRowDataUpdated"] = sync_selection_js
                if pre_selected_rows:
                    grid_options["initialState"] = {"rowSelection": pre_selected_rows}

            df_export = (
                pd.concat([df_body, pd.DataFrame(footer_rows)], ignore_index=True)
                if footer_rows
                else df_body.copy()
            )
            toolbar_container_key = f"{table_key}_actions_toolbar" if table_key else f"{label_col.lower()}_actions_toolbar"
            with st.container(key=toolbar_container_key):
                render_table_toolbar(
                    df_export,
                    f"top_{label_col.lower()}_por_urg.csv",
                    f"{table_key or label_col}_toolbar",
                )

            wrapper_class = "selection-master-table" if table_key else "st-table-with-total"
            st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
            active_values_for_key = active_row_value if isinstance(active_row_value, list) else ([active_row_value] if active_row_value else [])
            active_values_for_key = [str(v) for v in active_values_for_key if v not in (None, "")]
            table_state_suffix = "|".join(sorted(active_values_for_key)) if active_values_for_key else "all"
            aggrid_response = render_saedas_aggrid(
                df_body,
                grid_options=grid_options,
                key=f"{table_key or label_col}_aggrid_top_urg_{table_state_suffix}",
                update_mode=GridUpdateMode.SELECTION_CHANGED if table_key else GridUpdateMode.NO_UPDATE,
                incluir_total=bool(footer_rows),
            )
            st.markdown("</div>", unsafe_allow_html=True)

            if table_key and label_field:
                selected_rows = aggrid_response.get("selected_rows", None)
                has_grid_selection_payload = selected_rows is not None
                if isinstance(selected_rows, pd.DataFrame):
                    selected_rows = selected_rows.to_dict(orient="records")
                elif isinstance(selected_rows, dict):
                    selected_rows = [selected_rows]
                if has_grid_selection_payload:
                    selected_rows = selected_rows or []
                    selected_values = [
                        row.get(label_field)
                        for row in selected_rows
                        if row.get(label_field) not in (None, "", "TOTAL")
                    ]
                    # Guard: if grid returned empty but sidebar already has active values,
                    # the grid just re-rendered (new key) and JS hasn't fired yet — skip overwrite.
                    if selected_values or not active_values:
                        st.session_state[f"{table_key}__selected_values"] = selected_values
                    selected_indexes = [
                        idx
                        for idx, value in enumerate(df_cmp_aggrid[label_field].tolist())
                        if value in selected_values
                    ]
                    st.session_state[table_key] = {"selection": {"rows": selected_indexes}}

            urg_scope_text = (
                f"da URG {urg_selecionada}"
                if len(urgs_aplicadas) == 1
                else "das URGs selecionadas"
            )
            if table_key:
                st.caption(
                    f"Nota: Clique em qualquer linha de {label_col} para filtrar todo o restante do dashboard. "
                    f"As colunas '% Total' representam o percentual sobre o total {urg_scope_text} no respectivo ano."
                )
            else:
                st.caption(
                    f"Nota: Esta tabela utiliza os filtros da sidebar. "
                    f"As colunas '% Total' representam o percentual sobre o total {urg_scope_text} no respectivo ano."
                )
            return df_cmp
    else:
        group_sorted = group.sort_values(value_col, ascending=False).reset_index(drop=True)
        gb = {
            "defaultColDef": {
                "resizable": True,
                "sortable": True,
                "filter": False,
                "suppressMenu": True,
            }
        }
        with st.container(key=f"{label_col.lower()}_simple_actions_toolbar"):
            render_table_toolbar(
                group_sorted,
                f"top_{label_col.lower()}_por_urg.csv",
                f"{label_col}_simple_top_urg",
            )
        st.markdown('<div class="st-table-with-total">', unsafe_allow_html=True)
        render_saedas_aggrid(
            group_sorted,
            grid_options=gb,
            key=f"{label_col}_top_urg_simple_aggrid",
            update_mode=GridUpdateMode.NO_UPDATE,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    return None


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
    df: pd.DataFrame, 
    categoria_col: str, 
    value_col: str = "Quantidade", 
    active_row_value: str = None,
    denominator_row_label: str = None,
    pct_label: str = "Total"
) -> pd.DataFrame | None:
    """
    Gera tabela de comparativo anual com colunas de variação absolutas e percentuais.
    Suporta Taxa de Cobertura se denominator_row_label for fornecido.
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
    
    # Ordenação especial para URGs
    if categoria_col == "URG":
        pivot["_order"] = pivot.index.map(_urg_sort_key)
        pivot = pivot.sort_values("_order").drop(columns="_order")
    else:
        pivot = pivot.sort_index()

    if pivot.empty:
        return None

    year_cols = sorted([int(c) for c in pivot.columns if pd.notna(c)])
    pivot["Total"] = pivot[year_cols].sum(axis=1)
    df_cmp = pivot.reset_index()

    # Cálculos anuais: % Cobertura ou % Total
    for year in year_cols:
        pct_col_name = f"% {pct_label} {year % 100:02d}"
        
        if denominator_row_label:
            # Padrão Cobertura: denominador é uma linha específica (ex: TOTAL DE ALUNOS)
            valor_base = df_cmp.loc[df_cmp[categoria_col] == denominator_row_label, year].values
            total_ref = valor_base[0] if len(valor_base) > 0 else 0
        else:
            # Padrão Total: denominador é a soma da coluna
            total_ref = df_cmp[year].sum()
            
        df_cmp[pct_col_name] = (df_cmp[year] / total_ref * 100) if total_ref > 0 else 0

    # Cálculos interanuais: Var% em relação ao ano anterior
    for prev, curr in zip(year_cols, year_cols[1:]):
        var_pct_col = f"Var% {curr % 100:02d}-{prev % 100:02d}"
        diff = df_cmp[curr] - df_cmp[prev]
        df_cmp[var_pct_col] = (diff / df_cmp[prev].replace({0: pd.NA}) * 100)

    # Renomeia anos para string
    df_cmp = df_cmp.rename(columns={y: str(y) for y in year_cols})
    year_cols_str = [str(y) for y in year_cols]

    # Ordenação das colunas
    col_order = [categoria_col]
    for i, curr_year in enumerate(year_cols):
        col_order.append(str(curr_year))
        col_order.append(f"% {pct_label} {curr_year % 100:02d}")
        
        if i > 0:
            prev_year = year_cols[i - 1]
            col_order.append(f"Var% {curr_year % 100:02d}-{prev_year % 100:02d}")

    if "Total" in df_cmp.columns:
        col_order.append("Total")

    df_cmp = df_cmp[[c for c in col_order if c in df_cmp.columns]]

    # Formatação
    pct_cols = [c for c in df_cmp.columns if c.startswith("%") or c.startswith("Var%")]
    abs_cols = [c for c in df_cmp.columns if c not in pct_cols and c != categoria_col]

    # --- Adiciona Linha de TOTAL ---
    total_row = {categoria_col: "TOTAL"}
    for c in df_cmp.columns:
        if c in abs_cols:
            total_row[c] = df_cmp[c].sum()
        elif c in pct_cols:
            total_row[c] = pd.NA

    df_cmp = pd.concat([df_cmp, pd.DataFrame([total_row])], ignore_index=True)

    df_display = df_cmp.copy()
    for c in abs_cols:
        df_display[c] = df_display[c].map(
            lambda x: f"{x:,.0f}".replace(",", ".") if pd.notna(x) and float(x) != 0 else ""
        )
    for c in pct_cols:
        df_display[c] = df_display[c].map(
            lambda x: f"{x:,.1f}%".replace(",", ".") if pd.notna(x) and float(x) != 0 else "-"
        )

    # MultiIndex Header
    new_cols = []
    for c in df_display.columns:
        if c == categoria_col:
            new_cols.append((categoria_col, ""))
        elif c == "Total":
            new_cols.append(("Total Geral", ""))
        elif c in year_cols_str:
            new_cols.append((c, "Qtd"))
        elif str(c).startswith(f"% {pct_label}"):
            y_str = str(c).split(" ")[-1]
            new_cols.append((f"20{y_str}", c))
        elif str(c).startswith("Var%"):
            parts = str(c).split(" ")
            y_str = parts[1].split("-")[0] if len(parts) > 1 else ""
            new_cols.append((f"20{y_str}", c.replace("-", "/")))
        else:
            new_cols.append(("", c))
            
    df_display.columns = pd.MultiIndex.from_tuples(new_cols)

    return df_display.style.pipe(
        apply_saedas_design, categoria_col=categoria_col, active_items=active_row_value
    ).hide(axis="index")


def calcular_altura_aggrid(
    df: pd.DataFrame, limite_linhas: int | str | None = "Todas as linhas", incluir_total: bool = False, max_rows: int = 20
) -> int:
    """
    Calcula a altura ideal para uma tabela AgGrid, adaptando-se ao conteúdo 
    até um teto máximo para manter a ergonomia da página.
    """
    APPROX_ROW_HEIGHT = 34
    APPROX_HEADER_HEIGHT = 36
    SAFETY_PADDING = 6

    if not isinstance(df, pd.DataFrame):
        return APPROX_HEADER_HEIGHT + SAFETY_PADDING

    num_data_rows = len(df)
    
    # Lógica Inteligente:
    # 1. Se o usuário definiu um limite (ex: paginação), respeitamos.
    # 2. Se for "Todas", adaptamos ao conteúdo, mas limitamos ao max_rows (teto de 20 por padrão).
    if isinstance(limite_linhas, int) and limite_linhas > 0:
        num_rows_to_display = min(num_data_rows, limite_linhas)
    else:
        num_rows_to_display = min(num_data_rows, max_rows)

    data_height = num_rows_to_display * APPROX_ROW_HEIGHT
    total_row_height = APPROX_ROW_HEIGHT if incluir_total and num_data_rows > 0 else 0
    grid_height = APPROX_HEADER_HEIGHT + data_height + total_row_height + SAFETY_PADDING
    
    min_height = APPROX_HEADER_HEIGHT + (APPROX_ROW_HEIGHT if incluir_total else 0) + SAFETY_PADDING
    return max(grid_height, min_height)


def prepare_comparativo_aggrid_data(
    df_styler, include_selection_column: bool = True
) -> tuple[pd.DataFrame, list[dict], dict]:
    """Converte o Styler do comparativo anual em dados/colunas compatíveis com AgGrid."""
    df_data = getattr(df_styler, "data", df_styler)
    if df_data is None or df_data.empty:
        return pd.DataFrame(), [], {}

    df_grid = df_data.copy().reset_index(drop=True)
    column_map = {}
    grouped_columns = {}
    flat_columns = []

    # Colunas que devem ser alinhadas à esquerda (labels)
    LABEL_COLUMNS = {
        "URG", "Escola", "Descricao", "Encaminhamento", "Aluno", "Ação", "Profissional", "Exame", "Vacina"
    }

    for idx, col in enumerate(df_grid.columns):
        if isinstance(col, tuple):
            group_label = str(col[0] or "")
            child_label = str(col[1] or "")
            header_label = child_label or group_label
        else:
            group_label = ""
            header_label = str(col)

        field_name = f"col_{idx}"
        column_map[field_name] = col
        flat_columns.append(field_name)

        col_def = {
            "field": field_name,
            "headerName": header_label,
            "sortable": True,
            "filter": False,
            "resizable": True,
        }
        
        # Lógica de alinhamento
        is_label = False
        if isinstance(col, tuple):
            is_label = any(lbl in LABEL_COLUMNS for lbl in col if lbl)
        else:
            is_label = col in LABEL_COLUMNS

        if not is_label:
            col_def["cellStyle"] = {"textAlign": "center"}

        if group_label and child_label:
            grouped_columns.setdefault(group_label, []).append(col_def)
        else:
            grouped_columns.setdefault(field_name, []).append(
                {
                    **col_def,
                    "headerName": header_label,
                    "headerClass": "saedas-aggrid-header",
                }
            )

    df_grid.columns = flat_columns
    
    column_defs = []
    if include_selection_column:
        column_defs.append(
            {
                "headerName": "",
                "valueGetter": JsCode(
                    "function(p){return p.node.rowPinned?'':p.node.rowIndex+1;}"
                ),
                "checkboxSelection": True,
                "headerCheckboxSelection": False,
                "width": 60,
                "maxWidth": 60,
                "pinned": "left",
                "sortable": False,
                "filter": False,
                "resizable": False,
                "suppressMenu": True,
            }
        )

    for group_name, children in grouped_columns.items():
        if group_name in flat_columns:
            column_defs.extend(children)
        else:
            column_defs.append(
                {
                    "headerName": group_name,
                    "headerClass": "saedas-aggrid-centered-header",
                    "children": children,
                }
            )

    return df_grid, column_defs, column_map


def split_aggrid_footer(df_grid: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Usa a última linha do DataFrame como rodapé fixo do AgGrid."""
    if df_grid.empty:
        return df_grid, []

    footer_row = df_grid.tail(1).replace({np.nan: None}).to_dict(orient="records")
    body_df = df_grid.iloc[:-1].copy().reset_index(drop=True)
    return body_df, footer_row


def render_saedas_aggrid(
    df_data: pd.DataFrame, 
    grid_options: dict, 
    key: str, 
    update_mode=GridUpdateMode.NO_UPDATE, 
    incluir_total: bool = False,
    max_rows: int = 20,
    min_height: int | None = None,
    **kwargs
):
    """
    Função Mestra para renderização de AgGrid no SAEDAS.
    Encapsula:
    1. Cálculo de altura dinâmica (adaptativa ou teto de 20 linhas).
    2. Estilização padrão do Design System (Headers e Footers).
    3. Configurações otimizadas de performance e layout.
    """
    # 1. Cálculo Automático da Altura
    grid_height = calcular_altura_aggrid(
        df_data, 
        limite_linhas="Todas as linhas", 
        incluir_total=incluir_total, 
        max_rows=max_rows
    )
    if min_height is not None:
        grid_height = max(grid_height, min_height)

    # 2. Definição de Estilo Padrão (Design System)
    default_custom_css = {
        ".ag-header": {
            "background-color": "var(--header-bg) !important",
            "color": "var(--header-text) !important",
        },
        ".ag-header-cell, .ag-header-group-cell": {
            "background-color": "var(--header-bg) !important",
            "color": "var(--header-text) !important",
            "font-weight": "700 !important",
        },
        ".ag-header-cell-label, .ag-header-group-cell-label": {
            "justify-content": "center !important",
            "text-align": "center !important",
        },
        ".ag-header-cell-text, .ag-header-group-text": {
            "text-align": "center !important",
            "width": "100% !important",
        },
        ".ag-pinned-bottom-container .ag-row": {
            "background-color": "var(--footer-bg) !important",
            "color": "var(--footer-text) !important",
            "font-weight": "700 !important",
            "border-top": "2px solid var(--border-ui) !important",
        },
    }
    
    # Mescla CSS customizado se fornecido
    custom_css = dict(default_custom_css)
    extra_custom_css = kwargs.get("custom_css")
    if isinstance(extra_custom_css, dict):
        custom_css.update(extra_custom_css)

    # 3. Renderização
    return AgGrid(
        df_data,
        gridOptions=grid_options,
        height=grid_height,
        update_mode=update_mode,
        allow_unsafe_jscode=kwargs.get("allow_unsafe_jscode", True),
        fit_columns_on_grid_load=kwargs.get("fit_columns_on_grid_load", True),
        theme=kwargs.get("theme", "streamlit"),
        key=key,
        custom_css=custom_css,
        **{k: v for k, v in kwargs.items() if k not in ["custom_css", "allow_unsafe_jscode", "fit_columns_on_grid_load", "theme"]}
    )


def render_table_toolbar(df_export: pd.DataFrame, file_name: str, key_prefix: str):
    """Renderiza a barra de ferramentas (Copiar e CSV) para tabelas alinhada à direita."""
    csv_data = df_export.to_csv(index=False, sep=";").encode("utf-8-sig")
    
    # Criamos colunas para forçar o agrupamento horizontal e alinhamento à direita
    # O primeiro espaço é vazio para empurrar os botões para a direita
    _, col_copy, col_csv = st.columns([0.85, 0.08, 0.07], gap="small")
    
    with col_copy:
        if st.button("📋 Copiar", key=f"copy_{key_prefix}", help="Copiar tabela para a área de transferência"):
            try:
                # Geramos o texto em formato TSV (Tab-Separated Values) que é o padrão esperado pelo Excel
                table_text = df_export.to_csv(index=False, sep="\t")
                
                # Injeção de JavaScript para realizar a cópia no lado do cliente (navegador)
                st.components.v1.html(
                    f"""
                    <script>
                    async function copyToClipboard() {{
                        const text = {json.dumps(table_text)};
                        try {{
                            if (navigator.clipboard && navigator.clipboard.writeText) {{
                                await navigator.clipboard.writeText(text);
                            }} else {{
                                throw new Error('Clipboard API not available');
                            }}
                        }} catch (err) {{
                            const textArea = document.createElement("textarea");
                            textArea.value = text;
                            textArea.style.position = "fixed";
                            textArea.style.left = "-9999px";
                            textArea.style.top = "0";
                            document.body.appendChild(textArea);
                            textArea.focus();
                            textArea.select();
                            try {{
                                document.execCommand('copy');
                            }} catch (copyErr) {{
                                console.error('Erro no fallback de cópia:', copyErr);
                            }}
                            document.body.removeChild(textArea);
                        }}
                    }}
                    copyToClipboard();
                    </script>
                    """,
                    height=0
                )
                st.toast("Tabela copiada com sucesso!", icon="✅")
            except Exception as exc:
                st.toast(f"Erro ao processar cópia: {exc}", icon="❌")
                
    with col_csv:
        st.download_button(
            label="⬇️ CSV",
            data=csv_data,
            file_name=file_name,
            mime="text/csv",
            key=f"download_{key_prefix}",
            help="Baixar tabela em formato CSV"
        )
