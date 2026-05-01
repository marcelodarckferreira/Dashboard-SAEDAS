import pandas as pd
import plotly.express as px
import streamlit as st
import re

from app.utils.styles import render_metric_cards


def toggle_multiselect_value(current_selection: list | None, value) -> list:
    """Return a new multiselect list with value toggled on or off."""
    current = list(current_selection or [])
    if value in current:
        current.remove(value)
    else:
        current.append(value)
    return current


def should_use_native_regulacao_button(value) -> bool:
    """Return True when a regulacao card should be rendered as a native button."""
    return True


def get_native_regulacao_button_type(value, selected_values: list | None) -> str:
    """Return the Streamlit button type that matches the regulacao selection state."""
    return "primary" if value in (selected_values or []) else "tertiary"


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
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        group.sort_values(value_col, ascending=False), use_container_width=True, hide_index=True
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
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(evolucao, use_container_width=True, hide_index=True)
    st.markdown(f"**Total: {evolucao[value_col].sum():,.0f}**".replace(",", "."))


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
    evolucao = df.groupby([x_col, "Ano"])[value_col].sum().reset_index()
    if evolucao.empty:
        st.info("Nenhum dado para exibir no gráfico.")
        return

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

    urgs_aplicadas = df["URG"].unique()
    if len(urgs_aplicadas) != 1:
        st.subheader(titulo)
        st.info("Selecione apenas uma URG na sidebar para detalhar.")
        return

    urg_selecionada = urgs_aplicadas[0]
    st.subheader(f"{titulo} (URG {urg_selecionada})")

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
            kwargs = {
                "use_container_width": True,
                "hide_index": True
            }
            if table_key:
                kwargs["on_select"] = on_select
                kwargs["selection_mode"] = selection_mode
                kwargs["key"] = table_key
                
            st.dataframe(df_cmp, **kwargs)
            if table_key:
                st.caption(f"Nota: Clique em qualquer linha de {label_col} para filtrar todo o restante do dashboard. As colunas '% Total' representam o percentual sobre o total da URG {urg_selecionada} no respectivo ano.")
            else:
                st.caption(f"Nota: Esta tabela utiliza os filtros da sidebar. As colunas '% Total' representam o percentual sobre o total da URG {urg_selecionada} no respectivo ano.")
            return df_cmp
    else:
        st.dataframe(
            group.sort_values(value_col, ascending=False), use_container_width=True, hide_index=True
        )
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
    df: pd.DataFrame, categoria_col: str, value_col: str = "Quantidade", active_row_value: str = None
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
    
    # Ordenação especial para URGs (numeral romano)
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

    # Cálculos anuais: % Total para todos os anos
    for year in year_cols:
        pct_col = f"% Total {year % 100:02d}"
        total_ano = df_cmp[year].sum()
        df_cmp[pct_col] = (df_cmp[year] / total_ano * 100) if total_ano > 0 else 0

    # Cálculos interanuais: Var% em relação ao ano anterior
    for prev, curr in zip(year_cols, year_cols[1:]):
        var_pct_col = f"Var% {curr % 100:02d}-{prev % 100:02d}"
        diff = df_cmp[curr] - df_cmp[prev]
        df_cmp[var_pct_col] = (diff / df_cmp[prev].replace({0: pd.NA}) * 100)

    # Renomeia anos para string
    df_cmp = df_cmp.rename(columns={y: str(y) for y in year_cols})
    year_cols_str = [str(y) for y in year_cols]

    # Ordenação obrigatória: Ano, % Total, Var%
    col_order = [categoria_col]
    for i, curr_year in enumerate(year_cols):
        col_order.append(str(curr_year))
        col_order.append(f"% Total {curr_year % 100:02d}")
        
        if i > 0:
            prev_year = year_cols[i - 1]
            col_order.append(f"Var% {curr_year % 100:02d}-{prev_year % 100:02d}")

    if "Total" in df_cmp.columns:
        col_order.append("Total")

    # Garante que só mantenha colunas existentes
    col_order = [c for c in col_order if c in df_cmp.columns]
    df_cmp = df_cmp[col_order]

    # Formatação condicional
    pct_cols = [c for c in df_cmp.columns if c.startswith("% Total") or c.startswith("Var%")]
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

    # Conversão das colunas para MultiIndex (Super-Header por Ano)
    new_cols = []
    for c in df_display.columns:
        if c == categoria_col:
            new_cols.append((categoria_col, ""))
        elif c == "Total":
            new_cols.append(("Total Geral", ""))
        elif c in year_cols_str:
            new_cols.append((c, "Qtd"))
        elif str(c).startswith("% Total"):
            y_str = str(c).split(" ")[-1]
            new_cols.append((f"20{y_str}", c))
        elif str(c).startswith("Var%"):
            y_str = str(c).split(" ")[1].split("-")[0]
            new_cols.append((f"20{y_str}", c.replace("-", "/")))
        else:
            new_cols.append(("", c))
            
    df_display.columns = pd.MultiIndex.from_tuples(new_cols)

    # Estilização (UI): Zebra, Bordas e Destaque do TOTAL
    def style_table_rows(row):
        try:
            # Tenta obter o valor da categoria (Escola/Atendimento)
            # O MultiIndex do build_comparativo_anual tem a categoria no nível (col, '')
            try:
                val_cat = row[(categoria_col, "")]
            except (KeyError, IndexError):
                val_cat = row.iloc[0] # Fallback para a primeira coluna
                
            is_total = (val_cat == "TOTAL")
            
            # Se for uma lista/conjunto de valores, verifica se o valor da linha está nela
            if isinstance(active_row_value, (list, set, tuple)):
                is_active = val_cat in active_row_value
            else:
                is_active = (active_row_value and val_cat == active_row_value)
            
            if is_total:
                # Destaque do Rodapé
                style = "background-color: #2b3b4e; font-weight: bold; border-top: 2px solid #ffffff; color: #ffffff; border-bottom: 1px solid rgba(255, 255, 255, 0.1); border-left: 1px solid rgba(255, 255, 255, 0.1); border-right: 1px solid rgba(255, 255, 255, 0.1);"
            elif is_active:
                # Active State (Igual ao da Performance por URG)
                style = "background-color: rgba(96, 165, 250, 0.3) !important; border: 2px solid #60a5fa !important; font-weight: bold; color: #ffffff;"
            else:
                # Zebra Effect e Reforço da Grid
                # Usa o índice numérico da linha para o zebra
                row_idx = row.name if isinstance(row.name, (int, float)) else 0
                bg = "#1e2530" if row_idx % 2 == 0 else "#161c26"
                style = f"background-color: {bg}; border: 1px solid rgba(255, 255, 255, 0.1); color: #ffffff;"
            
            # Adiciona cursor pointer para feedback visual de interatividade
            style += " cursor: pointer;"
            return [style] * len(row)
            
        except Exception:
            # Fallback seguro para evitar tela branca
            return ["background-color: #161c26; color: #ffffff;"] * len(row)

    # Efeito Hover e bordas globais da tabela via CSS injection
    hover_styles = [
        {"selector": "thead th", "props": [("text-align", "center"), ("background-color", "#161c26")]},
        {"selector": "thead tr:first-child th", "props": [("border-bottom", "2px solid rgba(255, 255, 255, 0.2)"), ("background-color", "#12171f")]},
        {"selector": "tbody tr:hover td", "props": [("background-color", "#374151 !important")]},
        {"selector": "tbody tr:hover th", "props": [("background-color", "#374151 !important")]},
    ]

    styled_df = (
        df_display.style
        .apply(style_table_rows, axis=1)
        .set_table_styles(hover_styles)
        .hide(axis="index")
    )
    
    return styled_df
