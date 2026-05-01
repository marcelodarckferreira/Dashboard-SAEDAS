import re
import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from urllib.parse import urlencode

from components.footer_personal import footer_personal
from components.sidebar_filters import sidebar_filters
from app.utils.data_loader import load_csv
from app.utils.page_helpers import (
    filter_by_sidebar_selections,
    build_comparativo_anual,
    render_metric,
    render_top_por_urg,
    format_filters_applied,
)
from app.utils.state_manager import init_global_state, sync_home_to_sidebar, sync_home_urg_to_sidebar
from app.utils.schemas import SCHEMA_MEDICO, SCHEMA_MEDICO_ALUNO, SCHEMA_MEDICO_ANO
from app.utils.styles import apply_global_css, render_metric_cards


# ── Utilitários de ordenação por numeral romano ───────────────────────────────
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
    """Extrai o numeral romano do nome da URG e retorna seu valor inteiro.

    Exemplos:
        'URG I-CENTRO'          → 1
        'URG VIII-MIGUEL COUTO' → 8
        'URG IX-TINGUA'         → 9
    """
    m = re.search(r"URG\s+([IVXLCDM]+)", str(urg_name), re.IGNORECASE)
    return _roman_to_int(m.group(1)) if m else 999


def carregar_dados_medico():
    csv_file = "data/DashboardMedico.csv"
    df, info = load_csv(csv_file, expected_cols=SCHEMA_MEDICO)

    csv_file_aluno = "data/DashboardMedicoAluno.csv"
    df_aluno_raw, info_aluno = load_csv(
        csv_file_aluno, expected_cols=SCHEMA_MEDICO_ALUNO
    )

    csv_file_ano = "data/DashboardMedicoAno.csv"
    df_ano, info_ano = load_csv(csv_file_ano, expected_cols=SCHEMA_MEDICO_ANO)

    from app.utils.schemas import SCHEMA_HOME
    df_home, _ = load_csv("data/DashboardHome.csv", expected_cols=SCHEMA_HOME)

    return {
        "principal": {"df": df, "info": info, "csv": csv_file},
        "aluno": {"df": df_aluno_raw, "info": info_aluno, "csv": csv_file_aluno},
        "ano": {"df": df_ano, "info": info_ano, "csv": csv_file_ano},
        "home": {"df": df_home},
    }


def page_medico():
    # Inicializa o estado global sincronizado (Anos e URGs)
    init_global_state()

    st.title("Visão Geral dos Atendimentos Médicos")
    st.markdown(
        "Resumo consolidado dos atendimentos médicos realizados por ano, URG e escola."
    )
    filters_placeholder = st.empty()
    st.markdown("---")
    apply_global_css()

    datasets = carregar_dados_medico()

    df, info = datasets["principal"]["df"], datasets["principal"]["info"]
    csv_file_aluno = datasets["aluno"]["csv"]
    df_aluno_raw, info_aluno = datasets["aluno"]["df"], datasets["aluno"]["info"]
    csv_file_ano = datasets["ano"]["csv"]
    df_ano, info_ano = datasets["ano"]["df"], datasets["ano"]["info"]

    if info_aluno["erros"]:
        st.warning(
            f"Falha ao ler '{csv_file_aluno}': " + "; ".join(info_aluno["erros"])
        )
        df_aluno_raw = pd.DataFrame()
    elif info_aluno["alertas"]:
        st.info("; ".join(info_aluno["alertas"]))

    if info_ano["erros"]:
        st.warning(f"Falha ao ler '{csv_file_ano}': " + "; ".join(info_ano["erros"]))
        df_ano = pd.DataFrame()
    elif info_ano["alertas"]:
        st.info("; ".join(info_ano["alertas"]))

    if info["erros"]:
        st.error("; ".join(info["erros"]))
        footer_personal()
        return
    if info["alertas"]:
        st.warning("; ".join(info["alertas"]))

    df = df.rename(
        columns={
            "Ano": "Ano",
            "URG": "URG",
            "Escola": "Escola",
            "Descricao": "Atendimento",
            "Qtd": "Quantidade",
            "Tipo": "Tipo",
        }
    )

    df_aluno = df_aluno_raw.rename(
        columns={
            "DtNasc": "DataNascimento",
            "Profissional": "Profissional",
        }
    ).copy()
    if not df_aluno.empty and "DataNascimento" in df_aluno.columns:
        df_aluno["DataNascimento"] = pd.to_datetime(
            df_aluno["DataNascimento"], errors="coerce"
        )

    df_ano_exibir = df_ano.copy() if not df_ano.empty else pd.DataFrame()

    st.sidebar.title("Filtros - Médico")

    df_filt_sidebar, selections = sidebar_filters(
        df,
        {"ano": True, "urg": True, "escola": True, "tipo": True},
    )

    atendimento_col = "Atendimento"
    atendimentos_disponiveis = (
        sorted(df_filt_sidebar[atendimento_col].dropna().unique())
        if atendimento_col in df_filt_sidebar.columns
        else []
    )
    # Filtro de Atendimento removido conforme solicitação
    atendimentos_selecionados = []

    # --- SELETOR TEMPORAL MESTRE (INDICADORES E PÁGINA) ---
    current_year = datetime.datetime.now().year
    years_options = sorted([current_year - i for i in range(5)], reverse=True)
    
    st.segmented_control(
        label="Ano(s) de Referência:",
        options=years_options,
        selection_mode="multi",
        key="home_year_buttons",
        on_change=sync_home_to_sidebar,
        label_visibility="collapsed"
    )
    # Sincroniza a variável local com o estado global
    selected_years_comp = st.session_state["global_years"]

    # --- Aplicação Final dos Filtros (Fontes de Verdade Globais) ---
    df_base_final = df.copy()
    
    # 1. Filtro de Escola (Cascata da Sidebar)
    if selections.get("escola"):
        all_schools = set(df["Escola"].dropna().unique())
        selected_schools = set(selections["escola"])
        if selected_schools != all_schools:
            df_base_final = df_base_final[df_base_final["Escola"].isin(selections["escola"])]
            
    # 2. Filtro de Tipo (Instituição)
    if selections.get("tipo"):
        all_types = set(df["Tipo"].dropna().unique())
        selected_types = set(selections["tipo"])
        if selected_types != all_types:
            df_base_final = df_base_final[df_base_final["Tipo"].isin(selections["tipo"])]

    # 3. Filtro de Anos (Global)
    if selected_years_comp:
        df_base_final = df_base_final[df_base_final["Ano"].isin(selected_years_comp)]
    else:
        df_base_final = pd.DataFrame()
        
    # 4. Filtro de Atendimento (Sidebar)
    if atendimentos_selecionados:
        df_base_final = df_base_final[df_base_final[atendimento_col].isin(atendimentos_selecionados)]

    # 5. Filtro de URGs (Global - Vinculação Bidirecional)
    current_urgs = st.session_state["global_urgs"]
    if current_urgs:
        df_master_filtrado = df_base_final[df_base_final["URG"].isin(current_urgs)]
    else:
        df_master_filtrado = df_base_final.copy()

    # Substitui df_filt pelo filtrado final
    df_filt = df_master_filtrado.copy()

    # --- Definições para Gráficos 'Top por URG' ---
    # 1. Sem filtro de escola e tipo (para mostrar todas as Escolas da URG/Ano)
    df_filt_no_escola = df.copy()
    if selected_years_comp:
        df_filt_no_escola = df_filt_no_escola[df_filt_no_escola["Ano"].isin(selected_years_comp)]
    if current_urgs:
        df_filt_no_escola = df_filt_no_escola[df_filt_no_escola["URG"].isin(current_urgs)]
        
    # 2. Com filtro de escola (para mostrar Top Atendimentos)
    df_filt_no_atend = df_filt.copy()

    filters_placeholder.markdown(
        "**Filtros aplicados:** "
        + format_filters_applied(
            selections,
            df,
            [
                ("ano", "Ano", "Ano"),
                ("urg", "URG", "URG"),
                ("escola", "Escola", "Escola"),
                ("tipo", "Tipo", "Tipo"),
            ],
        )
    )
    urgs_aplicadas = selections.get("urg", [])

    st.sidebar.markdown("---")
    st.sidebar.subheader("Exportar dados")
    csv_export_encoding = "utf-8"
    csv = df_filt.to_csv(index=False, sep=";").encode(csv_export_encoding)
    st.sidebar.download_button(
        label="Exportar CSV (Médico)",
        data=csv,
        file_name="dados_filtrados_medico.csv",
        mime="text/csv",
    )

    # --- PRIORIDADE 1 (TOPO): MÉTRICAS ---
    
    # Calcula total de alunos (QtdAluno) do Home filtrado pelos anos do componente e seleções da sidebar
    df_home = datasets["home"]["df"].copy()
    total_alunos = 0
    if not df_home.empty:
        escolas_selecionadas = selections.get("escola", [])
        if selected_years_comp and "Ano" in df_home.columns:
            df_home = df_home[df_home["Ano"].isin(selected_years_comp)]
        if urgs_aplicadas and "URG" in df_home.columns:
            df_home = df_home[df_home["URG"].isin(urgs_aplicadas)]
        if escolas_selecionadas and "Escola" in df_home.columns:
            df_home = df_home[df_home["Escola"].isin(escolas_selecionadas)]
        if "QtdAlunoEscola" in df_home.columns:
            df_home["QtdAlunoEscola"] = pd.to_numeric(df_home["QtdAlunoEscola"], errors="coerce").fillna(0)
            total_alunos = int(df_home["QtdAlunoEscola"].sum())

    col_atend, col_alunos = st.columns(2)
    with col_atend:
        render_metric_cards([("TOTAL DE ATENDIMENTOS MÉDICOS", df_filt["Quantidade"].sum() if not df_filt.empty else 0)])
    with col_alunos:
        render_metric_cards([("TOTAL GERAL DE ALUNOS", total_alunos)])

    # ── Cards: Top URGs por atendimentos (ordenados por numeral romano) - CAIXA ALTA ──────
    urg_sum = (
        df_filt.groupby("URG")["Quantidade"].sum()
        if not df_filt.empty and "URG" in df_filt.columns
        else pd.Series(dtype="float")
    )
    urg_sum = urg_sum[urg_sum > 0]
    if not urg_sum.empty:
        urg_sum = urg_sum.reset_index()
        urg_sum["_order"] = urg_sum["URG"].map(_urg_sort_key)
        urg_sum = urg_sum.sort_values("_order").drop(columns="_order")
        urg_sum = urg_sum.set_index("URG")["Quantidade"]
        for start in range(0, min(len(urg_sum), 10), 5):
            slice_urg = urg_sum.iloc[start : start + 5]
            cols = st.columns(5)
            for col, (nome, valor) in zip(cols, slice_urg.items()):
                with col:
                    # Rótulo da URG em CAIXA ALTA e sem comportamento de clique
                    render_metric_cards([(f"{str(nome).upper()}", valor)])
    else:
        st.info("Selecione ao menos um ano para visualizar os indicadores.")
    
    st.markdown("---")

    # ── Tabela Comparativa de Performance por URG ─────────────────────
    st.subheader("Performance por URG")
    st.caption("Nota: Clique em qualquer linha de URG para filtrar o restante do dashboard. Esta tabela é sensível apenas ao filtro de Ano.")

    # Callback para sincronizar seleção da tabela com o estado global
    def sync_urg_table_to_global_medico():
        if "urg_table_selection_medico" in st.session_state:
            selection = st.session_state["urg_table_selection_medico"]
            rows = selection.get("selection", {}).get("rows", [])
            df_table = st.session_state.get("last_df_pivot_medico")
            
            if df_table is not None:
                selected_urgs = []
                for r in rows:
                    try:
                        urg_val = df_table.iloc[r]["URG"]
                        if urg_val and urg_val != "TOTAL":
                            selected_urgs.append(urg_val)
                    except: continue
                
                st.session_state["global_urgs"] = selected_urgs
                st.session_state["sidebar_urg_filter"] = selected_urgs
                st.session_state["last_interaction_source"] = "table"

    if df_ano_exibir.empty:
        st.info("Dados agregados de Médico por ano não estão disponíveis.")
    else:
        import numpy as np
        # Prepara DF para a tabela (Ignora filtros de URG e Escola - Sensível APENAS ao Ano)
        # Nota: Não aplicamos filtro de Escola aqui para garantir que todas as URGs apareçam na lista,
        # permitindo que a tabela funcione como um controlador mestre de navegação.
        df_ano_urg = df_ano_exibir.copy()

        year_cols_ano = [str(yc) for yc in selected_years_comp if str(yc) in df_ano_urg.columns]

        if not df_ano_urg.empty and year_cols_ano and "URG" in df_ano_urg.columns:
            for yc in year_cols_ano:
                df_ano_urg[yc] = pd.to_numeric(df_ano_urg[yc], errors="coerce").fillna(0)
            df_pivot = df_ano_urg.groupby("URG")[year_cols_ano].sum().reset_index()

            # Cálculos anuais: % Total para todos os anos
            for year in year_cols_ano:
                total_ano = df_pivot[year].sum()
                df_pivot[f"% Total {year[-2:]}"] = (
                    (df_pivot[year] / total_ano * 100) if total_ano > 0 else 0
                ).round(1)

            # Cálculos interanuais: Var% em relação ao ano anterior
            for prev, curr in zip(year_cols_ano, year_cols_ano[1:]):
                var_pct_col = f"Var% {curr[-2:]}-{prev[-2:]}"
                diff = df_pivot[curr] - df_pivot[prev]
                df_pivot[var_pct_col] = (diff / df_pivot[prev].replace(0, float("nan")) * 100).round(1)

            # Ordenação obrigatória: Ano, % Total, Var%
            ordered_cols = ["URG"]
            for i, year in enumerate(year_cols_ano):
                ordered_cols.append(year)
                ordered_cols.append(f"% Total {year[-2:]}")
                if i > 0:
                    prev = year_cols_ano[i - 1]
                    ordered_cols.append(f"Var% {year[-2:]}-{prev[-2:]}")
            
            df_pivot["Total"] = df_pivot[year_cols_ano].sum(axis=1)
            ordered_cols.append("Total")

            df_pivot = df_pivot[[c for c in ordered_cols if c in df_pivot.columns]]
            
            # Identifica colunas % Total e Var% dinamicamente
            var_pct_cols = [c for c in df_pivot.columns if c.startswith("% Total") or c.startswith("Var%")]

            # --- Nova Linha de Total ---
            total_row = {"URG": "TOTAL"}
            for c in df_pivot.columns:
                if c != "URG" and c not in var_pct_cols:
                    total_row[c] = df_pivot[c].sum()
                elif c in var_pct_cols:
                    total_row[c] = pd.NA
                    
            df_pivot = pd.concat([df_pivot, pd.DataFrame([total_row])], ignore_index=True)

            # Ordena por numeral romano da URG (I → II → III → ...)
            df_pivot["_order"] = df_pivot["URG"].map(lambda x: 9999 if x == "TOTAL" else _urg_sort_key(x))
            df_pivot = df_pivot.sort_values("_order").drop(columns="_order").reset_index(drop=True)

            # Salva o dataframe para o callback
            st.session_state["last_df_pivot_medico"] = df_pivot

            # Conversão das colunas para MultiIndex (Super-Header por Ano)
            new_cols = []
            for c in df_pivot.columns:
                if c == "URG":
                    new_cols.append(("URG", ""))
                elif c == "Total":
                    new_cols.append(("Total Geral", ""))
                elif c in year_cols_ano:
                    new_cols.append((c, "Qtd"))
                elif str(c).startswith("% Total"):
                    y_str = str(c).split(" ")[-1]
                    new_cols.append((f"20{y_str}", c))
                elif str(c).startswith("Var%"):
                    y_str = str(c).split(" ")[1].split("-")[0]
                    new_cols.append((f"20{y_str}", c.replace("-", "/")))
                else:
                    new_cols.append(("", c))
            df_pivot_display = df_pivot.copy()
            df_pivot_display.columns = pd.MultiIndex.from_tuples(new_cols)

            # Zebra-striping e Bordas via Styler
            def _zebra(row):
                active_urgs = st.session_state.get("global_urgs", [])
                is_active = row[("URG", "")] in active_urgs
                
                if row[("URG", "")] == "TOTAL":
                    style = "background-color: #2b3b4e; font-weight: bold; border-top: 2px solid #ffffff; color: #ffffff; border-bottom: 1px solid rgba(255, 255, 255, 0.1); border-left: 1px solid rgba(255, 255, 255, 0.1); border-right: 1px solid rgba(255, 255, 255, 0.1);"
                elif is_active:
                    style = "background-color: rgba(96, 165, 250, 0.3) !important; border: 2px solid #60a5fa !important; font-weight: bold;"
                else:
                    bg = "#1e2530" if row.name % 2 == 0 else "#161c26"
                    style = f"background-color: {bg}; border: 1px solid rgba(255, 255, 255, 0.1);"
                return [style] * len(row)

            # Sincronização de Checkboxes (Paridade Sidebar -> Tabela)
            # Só atualiza se a mudança vier da SIDEBAR ou se for a carga inicial
            current_urgs = st.session_state.get("global_urgs", [])
            try:
                urg_col_values = df_pivot["URG"].tolist()
                target_indices = [i for i, val in enumerate(urg_col_values) if val in current_urgs]
                
                # Obtém a seleção atual da tabela
                current_sel_obj = st.session_state.get("urg_table_selection_medico", {})
                current_table_selection = current_sel_obj.get("selection", {}).get("rows", [])
                
                # Só sobrescreve se houver divergência real e a última interação NÃO foi na própria tabela
                if set(target_indices) != set(current_table_selection):
                    if st.session_state.get("last_interaction_source") != "table":
                        st.session_state["urg_table_selection_medico"] = {"selection": {"rows": target_indices, "columns": []}}
            except Exception: pass

            def _fmt_br(v):
                """Formata número com separador de milhar brasileiro (ponto)."""
                try:
                    f = float(v)
                    if pd.isna(f) or f == 0:
                        return ""
                    return f"{int(f):,}".replace(",", ".")
                except (ValueError, TypeError):
                    return ""

            def _fmt_pct(v):
                """Formata valor percentual com 2 casas decimais e sufixo %."""
                try:
                    f = float(v)
                    if pd.isna(f) or f == 0:
                        return ""
                    return f"{f:.2f}%"
                except (ValueError, TypeError):
                    return ""

            # Efeito Hover e bordas do thead
            hover_styles = [
                {"selector": "thead th", "props": [("text-align", "center"), ("background-color", "#161c26")]},
                {"selector": "thead tr:first-child th", "props": [("border-bottom", "2px solid rgba(255, 255, 255, 0.2)"), ("background-color", "#12171f")]},
                {"selector": "tbody tr:hover td", "props": [("background-color", "#374151 !important")]},
                {"selector": "tbody tr:hover th", "props": [("background-color", "#374151 !important")]},
            ]

            fmt_br_dict = {c: _fmt_br for c in new_cols if c[1] == "Qtd" or c[0] == "Total Geral"}
            fmt_pct_dict = {c: _fmt_pct for c in new_cols if c[1].startswith("% Total") or c[1].startswith("Var%")}

            styled_pivot = (
                df_pivot_display.style
                .apply(_zebra, axis=1)
                .set_properties(**{"text-align": "right"}, subset=[c for c in new_cols if c[0] != "URG"])
                .set_properties(**{"text-align": "left", "font-weight": "600"}, subset=[("URG", "")])
                .set_table_styles(hover_styles)
                .format(fmt_br_dict, na_rep="")
                .format(fmt_pct_dict, na_rep="")
                .hide(axis="index")
            )
            
            # Renderização da Tabela com Múltipla Seleção (Usando Styler para visual premium)
            st.dataframe(
                styled_pivot, 
                use_container_width=True, 
                hide_index=True,
                on_select=sync_urg_table_to_global_medico,
                selection_mode="multi-row",
                key="urg_table_selection_medico"
            )
        else:
            st.info("Não há dados suficientes para montar o comparativo por URG.")

    st.markdown("---")
    # --- PRIORIDADE 3: DETALHAMENTO TOP POR URG (ESCOLAS E ATENDIMENTOS) ---
    
    # Callback para sincronizar seleção da tabela de escolas com a sidebar
    def sync_escola_table_to_sidebar_medico():
        if "escola_table_selection_medico" in st.session_state:
            selection = st.session_state["escola_table_selection_medico"]
            rows = selection.get("selection", {}).get("rows", [])
            df_table = st.session_state.get("last_df_cmp_escola_medico")
            
            if df_table is not None:
                selected_escolas = []
                for r in rows:
                    try:
                        # O DataFrame retornado por build_comparativo_anual tem MultiIndex
                        # A primeira coluna é a categoria (Escola)
                        val = df_table.data.iloc[r][("Escola", "")]
                        if val and val != "TOTAL":
                            selected_escolas.append(val)
                    except: continue
                
                st.session_state["sidebar_escola_filter"] = selected_escolas

    current_selected_escolas = selections.get("escola", [])
    df_cmp_escola = render_top_por_urg(
        df_filt_no_escola, 
        "Quantidade", 
        "Principais Escolas por URG", 
        "Escola", 
        table_key="escola_table_selection_medico",
        active_row_value=current_selected_escolas,
        on_select=sync_escola_table_to_sidebar_medico,
        selection_mode="multi-row"
    )
    st.session_state["last_df_cmp_escola_medico"] = df_cmp_escola

    # Sincronização de Checkboxes (Paridade Sidebar -> Tabela)
    if df_cmp_escola is not None:
        try:
            escola_col_values = df_cmp_escola.data[("Escola", "")].tolist()
            target_indices = [i for i, val in enumerate(escola_col_values) if val in current_selected_escolas]
            
            current_table_selection = st.session_state.get("escola_table_selection_medico", {}).get("selection", {}).get("rows", [])
            if set(target_indices) != set(current_table_selection):
                st.session_state["escola_table_selection_medico"] = {"selection": {"rows": target_indices, "columns": []}}
        except Exception: pass
    render_top_por_urg(
        df_filt_no_atend, 
        "Quantidade", 
        "Principais Atendimentos por URG", 
        "Atendimento"
    )

    st.markdown("---")
    # ── Distribuição por URG ──────────────────────────────────────────────────
    st.subheader("Distribuição por URG")
    urg_ano_group = (
        df_filt.groupby(["URG", "Ano"])["Quantidade"].sum().reset_index()
        if not df_filt.empty and "URG" in df_filt.columns and "Ano" in df_filt.columns
        else pd.DataFrame()
    )
    if urg_ano_group.empty:
        st.info("Nenhum dado de URG para exibir.")
    else:
        # Ordena gráfico por numeral romano da URG e por Ano
        urg_ano_group["_order"] = urg_ano_group["URG"].map(_urg_sort_key)
        urg_ano_group_sorted = urg_ano_group.sort_values(["_order", "Ano"]).drop(columns="_order")
        
        # Converte o Ano para string categórica
        urg_ano_group_sorted["Ano"] = urg_ano_group_sorted["Ano"].astype(str)
        
        # Formata os valores absolutos para as labels e hover (ex: "3.235")
        urg_ano_group_sorted["_text_fmt"] = urg_ano_group_sorted["Quantidade"].apply(
            lambda x: f"{int(x):,}".replace(",", ".") if pd.notna(x) else ""
        )
        
        fig_urg = px.bar(
            urg_ano_group_sorted,
            x="URG",
            y="Quantidade",
            color="Ano",
            barmode="group",
            text="_text_fmt",
            category_orders={"URG": urg_ano_group_sorted["URG"].unique().tolist()}
        )
        
        fig_urg.update_traces(
            textposition="auto",
            hovertemplate="<b>URG:</b> %{x}<br><b>Quantidade:</b> %{text}<extra></extra>"
        )
        fig_urg.update_layout(
            showlegend=True,
            legend_title_text="Ano",
            xaxis_title="URG",
            yaxis_title="Total de Atendimentos",
            hovermode="x unified"
        )
        st.plotly_chart(fig_urg, use_container_width=True)

    # ── Painel de Cobertura e Atendimento por URG ───────────────────────────────────────────────────
    st.subheader("Painel de Cobertura e Atendimento por URG")
    df_home_perf = datasets["home"]["df"].copy()
    if not df_home_perf.empty and "QtdAlunoEscola" in df_home_perf.columns:
        if selected_years_comp and "Ano" in df_home_perf.columns:
            df_home_perf = df_home_perf[df_home_perf["Ano"].astype(str).isin(map(str, selected_years_comp))]
        if urgs_aplicadas and "URG" in df_home_perf.columns:
            df_home_perf = df_home_perf[df_home_perf["URG"].isin(urgs_aplicadas)]
        
        _escolas_sel = selections.get("escola", [])
        if _escolas_sel and "Escola" in df_home_perf.columns:
            df_home_perf = df_home_perf[df_home_perf["Escola"].isin(_escolas_sel)]
            
        df_home_perf["QtdAlunoEscola"] = pd.to_numeric(df_home_perf["QtdAlunoEscola"], errors="coerce").fillna(0)
        
        if "Ano" in df_home_perf.columns:
            alunos_ano = df_home_perf.groupby(["URG", "Ano"])["QtdAlunoEscola"].sum().reset_index()
        else:
            alunos_ano = df_home_perf.groupby("URG")["QtdAlunoEscola"].sum().reset_index()
            alunos_ano["Ano"] = "Geral"
    else:
        alunos_ano = pd.DataFrame(columns=["URG", "Ano", "QtdAlunoEscola"])

    if not df_filt.empty and "URG" in df_filt.columns and "Ano" in df_filt.columns:
        atendimentos_ano = df_filt.groupby(["URG", "Ano"])["Quantidade"].sum().reset_index()
        
        # Merge atendimentos and alunos
        df_perf_ano = atendimentos_ano.merge(alunos_ano, on=["URG", "Ano"], how="left").fillna(0)
        
        anos_presentes = sorted(df_perf_ano["Ano"].astype(str).unique())
        df_pivot_perf = pd.DataFrame({"URG": df_perf_ano["URG"].unique()})
        
        for y in anos_presentes:
            df_y = df_perf_ano[df_perf_ano["Ano"].astype(str) == y]
            df_pivot_perf = df_pivot_perf.merge(df_y[["URG", "Quantidade", "QtdAlunoEscola"]], on="URG", how="left").fillna(0)
            
            df_pivot_perf = df_pivot_perf.rename(columns={
                "Quantidade": f"Atend_Abs_{y}",
                "QtdAlunoEscola": f"Alunos_Abs_{y}"
            })
            
            soma_atend = df_pivot_perf[f"Atend_Abs_{y}"].sum()
            df_pivot_perf[f"%_Total_Geral_{y}"] = (df_pivot_perf[f"Atend_Abs_{y}"] / soma_atend * 100) if soma_atend > 0 else 0
            df_pivot_perf[f"%_Cobertura_{y}"] = (df_pivot_perf[f"Atend_Abs_{y}"] / df_pivot_perf[f"Alunos_Abs_{y}"].replace(0, float("nan")) * 100)
            
        ordered_cols = ["URG"]
        for y in anos_presentes:
            ordered_cols.extend([f"Atend_Abs_{y}", f"%_Total_Geral_{y}", f"Alunos_Abs_{y}", f"%_Cobertura_{y}"])
            
        df_pivot_perf = df_pivot_perf[ordered_cols]
        
        # Linha TOTAL
        total_row = {"URG": "TOTAL"}
        for y in anos_presentes:
            total_row[f"Atend_Abs_{y}"] = df_pivot_perf[f"Atend_Abs_{y}"].sum()
            total_row[f"Alunos_Abs_{y}"] = df_pivot_perf[f"Alunos_Abs_{y}"].sum()
            total_row[f"%_Total_Geral_{y}"] = pd.NA
            total_row[f"%_Cobertura_{y}"] = pd.NA
            
        df_pivot_perf = pd.concat([df_pivot_perf, pd.DataFrame([total_row])], ignore_index=True)
        
        df_pivot_perf["_order"] = df_pivot_perf["URG"].map(lambda x: 9999 if x == "TOTAL" else _urg_sort_key(x))
        df_pivot_perf = df_pivot_perf.sort_values("_order").drop(columns="_order").reset_index(drop=True)
        
        new_cols_perf = []
        for c in df_pivot_perf.columns:
            if c == "URG":
                new_cols_perf.append(("URG", ""))
            else:
                parts = c.split("_")
                y = parts[-1]
                metric = "_".join(parts[:-1])
                if metric == "Atend_Abs":
                    new_cols_perf.append((y, "Total de Atendimentos"))
                elif metric == "%_Total_Geral":
                    new_cols_perf.append((y, "% do Total Geral"))
                elif metric == "Alunos_Abs":
                    new_cols_perf.append((y, "Total de Alunos"))
                elif metric == "%_Cobertura":
                    new_cols_perf.append((y, "% Cobertura"))
                    
        def _fmt_br_perf(v):
            try:
                f = float(v)
                if pd.isna(f) or f == 0:
                    return ""
                return f"{int(f):,}".replace(",", ".")
            except (ValueError, TypeError):
                return ""

        def _fmt_pct_perf(v):
            try:
                f = float(v)
                if pd.isna(f) or f == 0:
                    return ""
                return f"{f:.2f}%"
            except (ValueError, TypeError):
                return ""

        # Mapeia diretamente no DataFrame para impedir que o Streamlit sobrescreva com floats
        for c in df_pivot_perf.columns:
            if c == "URG" or c == "_order":
                continue
            if "Atend_Abs_" in c or "Alunos_Abs_" in c:
                df_pivot_perf[c] = df_pivot_perf[c].map(_fmt_br_perf)
            elif "%_Total_Geral_" in c or "%_Cobertura_" in c:
                df_pivot_perf[c] = df_pivot_perf[c].map(_fmt_pct_perf)

        df_pivot_perf.columns = pd.MultiIndex.from_tuples(new_cols_perf)

        hover_styles_perf = [
            {"selector": "thead th", "props": [("text-align", "center"), ("background-color", "#161c26")]},
            {"selector": "thead tr:first-child th", "props": [("border-bottom", "2px solid rgba(255, 255, 255, 0.2)"), ("background-color", "#12171f")]},
            {"selector": "tbody tr:hover td", "props": [("background-color", "#374151 !important")]},
            {"selector": "tbody tr:hover th", "props": [("background-color", "#374151 !important")]},
        ]

        def _zebra_perf(row):
            if row[("URG", "")] == "TOTAL":
                style = "background-color: #2b3b4e; font-weight: bold; border-top: 2px solid #ffffff; color: #ffffff; border-bottom: 1px solid rgba(255, 255, 255, 0.1); border-left: 1px solid rgba(255, 255, 255, 0.1); border-right: 1px solid rgba(255, 255, 255, 0.1);"
            else:
                bg = "#1e2530" if row.name % 2 == 0 else "#161c26"
                style = f"background-color: {bg}; border: 1px solid rgba(255, 255, 255, 0.1);"
            return [style] * len(row)

        styled_perf = (
            df_pivot_perf.style
            .apply(_zebra_perf, axis=1)
            .set_properties(**{"text-align": "right"}, subset=[c for c in new_cols_perf if c[0] != "URG"])
            .set_properties(**{"text-align": "left", "font-weight": "600"}, subset=[("URG", "")])
            .set_table_styles(hover_styles_perf)
            .hide(axis="index")
        )
        # Callback para sincronizar seleção do Painel de Cobertura
        def sync_perf_table_to_global_medico():
            if "perf_table_selection_medico" in st.session_state:
                selection = st.session_state["perf_table_selection_medico"]
                rows = selection.get("selection", {}).get("rows", [])
                df_table = st.session_state.get("last_df_pivot_perf_medico")
                
                if df_table is not None:
                    selected_urgs = []
                    for r in rows:
                        try:
                            urg_val = df_table.iloc[r]["URG"]
                            if urg_val and urg_val != "TOTAL":
                                selected_urgs.append(urg_val)
                        except: continue
                    
                    st.session_state["global_urgs"] = selected_urgs
                    st.session_state["sidebar_urg_filter"] = selected_urgs
                    st.session_state["last_interaction_source"] = "table_perf"

        # Sincroniza a seleção inicial (Paridade Sidebar -> Tabela)
        current_urgs_perf = st.session_state.get("global_urgs", [])
        try:
            urg_col_perf = df_pivot_perf["URG"].tolist()
            target_indices_perf = [i for i, val in enumerate(urg_col_perf) if val in current_urgs_perf]
            
            current_sel_perf_obj = st.session_state.get("perf_table_selection_medico", {})
            current_perf_table_selection = current_sel_perf_obj.get("selection", {}).get("rows", [])
            
            if set(target_indices_perf) != set(current_perf_table_selection):
                if st.session_state.get("last_interaction_source") != "table_perf":
                    st.session_state["perf_table_selection_medico"] = {"selection": {"rows": target_indices_perf, "columns": []}}
        except: pass

        st.session_state["last_df_pivot_perf_medico"] = df_pivot_perf

        st.dataframe(
            df_pivot_perf, 
            use_container_width=True, 
            hide_index=True,
            on_select=sync_perf_table_to_global_medico,
            selection_mode="multi-row",
            key="perf_table_selection_medico"
        )
    else:
        st.info("Nenhum dado de URG disponível para o cálculo de performance anual.")


    st.markdown("---")
    st.subheader("Detalhamento por Aluno (MédicoAluno)")
    if df_aluno.empty:
        st.info(
            "Dados de alunos não estão disponíveis ou houve erro na leitura do CSV."
        )
    else:
        df_aluno_base = filter_by_sidebar_selections(df_aluno, selections)
        df_aluno_filtrado = df_aluno_base[df_aluno_base["Ano"].isin(selected_years_comp)] if not df_aluno_base.empty else pd.DataFrame()

        aluno_col = "Aluno"
        serie_col = "Serie"
        turma_col = "Turma"

        if aluno_col in df_aluno_filtrado.columns:
            alunos_disponiveis = sorted(
                list(df_aluno_filtrado[aluno_col].dropna().astype(str).unique())
            )
            alunos_selecionados = st.multiselect(
                "Filtrar por Aluno",
                options=alunos_disponiveis,
                default=[],
                placeholder="Todos",
                key="medico_aluno_multiselect",
            )
            if alunos_selecionados:
                df_aluno_filtrado = df_aluno_filtrado[
                    df_aluno_filtrado[aluno_col].astype(str).isin(alunos_selecionados)
                ]

        if serie_col in df_aluno_filtrado.columns:
            series_disponiveis = sorted(
                list(df_aluno_filtrado[serie_col].dropna().astype(str).unique())
            )
            series_selecionadas = st.multiselect(
                "Filtrar por Série",
                options=series_disponiveis,
                default=[],
                placeholder="Todas",
                key="medico_serie_multiselect",
            )
            if series_selecionadas:
                df_aluno_filtrado = df_aluno_filtrado[
                    df_aluno_filtrado[serie_col].astype(str).isin(series_selecionadas)
                ]

        if turma_col in df_aluno_filtrado.columns:
            turmas_disponiveis = sorted(
                list(df_aluno_filtrado[turma_col].dropna().astype(str).unique())
            )
            turmas_selecionadas = st.multiselect(
                "Filtrar por Turma",
                options=turmas_disponiveis,
                default=[],
                placeholder="Todas",
                key="medico_turma_multiselect",
            )
            if turmas_selecionadas:
                df_aluno_filtrado = df_aluno_filtrado[
                    df_aluno_filtrado[turma_col].astype(str).isin(turmas_selecionadas)
                ]

        total_registros_aluno = len(df_aluno_filtrado)
        st.caption(f"{total_registros_aluno} registros após filtros da sidebar")

        if df_aluno_filtrado.empty:
            st.warning("Nenhum registro de aluno para os filtros selecionados.")
        else:
            def build_perfil_link(row: pd.Series) -> str:
                nome = str(row.get("Aluno", "")).strip()
                if not nome:
                    return ""
                nasc_val = row.get("DataNascimento")
                nasc_str = ""
                if pd.notna(nasc_val):
                    nasc_dt = pd.to_datetime(nasc_val, errors="coerce")
                    if pd.notna(nasc_dt):
                        nasc_str = nasc_dt.date().isoformat()
                params = {"menu": "Aluno", "aluno": nome}
                if nasc_str:
                    params["nasc"] = nasc_str
                return f"?{urlencode(params)}"

            df_aluno_para_exibir = df_aluno_filtrado.copy()
            
            if not df_aluno_para_exibir.empty:
                # 1. Obter os atributos estáticos mais recentes do aluno
                static_cols = ["DataNascimento", "Sexo", "Profissional", "URG", "Escola", "Serie", "Turma"]
                static_cols = [c for c in static_cols if c in df_aluno_para_exibir.columns]
                
                df_static = df_aluno_para_exibir.groupby(["ID", "Aluno"], as_index=False)[static_cols].last()
                
                # 2. Contar consultas por aluno e por Ano
                df_counts = df_aluno_para_exibir.groupby(["ID", "Ano"]).size().reset_index(name="Qtd")
                
                # 3. Pivotar os anos para colunas
                df_pivot_ano = df_counts.pivot(index="ID", columns="Ano", values="Qtd").fillna(0)
                anos_cols = list(df_pivot_ano.columns)
                
                # 4. Mesclar dados estáticos com as colunas de ano
                df_aluno_final = df_static.merge(df_pivot_ano, on="ID", how="left")
                
                # 5. Calcular o Total de consultas do aluno
                df_aluno_final["Total"] = df_aluno_final[anos_cols].sum(axis=1)
                
                # 6. Limpar zeros (UI Limpa) e formatar como inteiro
                for c in anos_cols + ["Total"]:
                    df_aluno_final[c] = df_aluno_final[c].apply(lambda x: f"{int(x)}" if pd.notna(x) and x > 0 else "")
                
                # Link do Menu
                df_aluno_final["Menu"] = df_aluno_final.apply(build_perfil_link, axis=1)
                
                # Formatar Data de Nascimento
                if "DataNascimento" in df_aluno_final.columns:
                    df_aluno_final["DataNascimento"] = pd.to_datetime(
                        df_aluno_final["DataNascimento"], errors="coerce"
                    ).dt.strftime("%d/%m/%Y")
                    
                # Reordenar colunas
                col_order = ["ID", "Aluno", "DataNascimento", "Sexo", "Profissional", "URG", "Escola", "Serie", "Turma"]
                col_order = [c for c in col_order if c in df_aluno_final.columns] + anos_cols + ["Total", "Menu"]
                df_aluno_final = df_aluno_final[col_order]
                
                # Substituir NaN nos campos de texto por string vazia
                df_aluno_final = df_aluno_final.fillna("")
                
            else:
                df_aluno_final = pd.DataFrame()

            preview_limit = 500
            df_aluno_head = df_aluno_final.head(preview_limit).reset_index(drop=True)

            hover_styles_aluno = [
                {"selector": "thead th", "props": [("text-align", "center"), ("background-color", "#161c26"), ("font-weight", "bold")]},
                {"selector": "thead tr:first-child th", "props": [("border-bottom", "2px solid rgba(255, 255, 255, 0.2)"), ("background-color", "#12171f")]},
                {"selector": "tbody tr:hover td", "props": [("background-color", "#374151 !important")]},
                {"selector": "tbody tr:hover th", "props": [("background-color", "#374151 !important")]},
            ]

            def _zebra_aluno(row):
                bg = "#1e2530" if row.name % 2 == 0 else "#161c26"
                style = f"background-color: {bg}; border: 1px solid rgba(255, 255, 255, 0.05);"
                return [style] * len(row)

            styled_aluno = (
                df_aluno_head.style
                .apply(_zebra_aluno, axis=1)
                .set_properties(**{"text-align": "left"})
                .set_table_styles(hover_styles_aluno)
                .hide(axis="index")
            )

            st.dataframe(
                styled_aluno,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Menu": st.column_config.LinkColumn(
                        "Menu", display_text="Perfil"
                    )
                },
            )
            if total_registros_aluno > preview_limit:
                st.info(
                    f"Exibindo apenas as primeiras {preview_limit} linhas de {total_registros_aluno}."
                )

            csv_aluno = df_aluno_filtrado.to_csv(index=False, sep=";").encode("utf-8")
            st.download_button(
                label="Exportar CSV (Médico por aluno)",
                data=csv_aluno,
                file_name="dados_filtrados_medico_aluno.csv",
                mime="text/csv",
            )

    st.markdown(" ")
    footer_personal()
