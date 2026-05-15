import json
import re
from st_aggrid import GridOptionsBuilder, GridUpdateMode, JsCode
import pandas as pd
import plotly.express as px
import streamlit as st
import datetime
from urllib.parse import urlencode

from components.footer_personal import footer_personal
from components.sidebar_filters import sidebar_filters
from app.utils.data_loader import load_csv
from app.utils.page_helpers import (
    filter_by_sidebar_selections,
    build_comparativo_anual,
    get_selected_comparativo_value,
    render_metric,
    render_top_por_urg,
    format_filters_applied,
    prepare_nutricao_aluno_table,
    render_grouped_bar_anual,
    toggle_multiselect_value,
    render_section_divider,
    prepare_comparativo_aggrid_data,
    split_aggrid_footer,
    render_table_toolbar,
    render_saedas_aggrid,
)
from app.utils.state_manager import (
    apply_pending_table_filters,
    init_global_state,
    sync_sidebar_escola_selection,
    sync_home_to_sidebar,
    sync_home_urg_to_sidebar,
)
from app.utils.schemas import (
    SCHEMA_NUTRICAO,
    SCHEMA_NUTRICAO_ALUNO,
    SCHEMA_NUTRICAO_ANO,
    SCHEMA_HOME,
)
from app.utils.styles import apply_global_css, render_metric_cards, apply_saedas_design, build_row_style_fn, get_table_hover_styles


def carregar_dados_nutricao():
    csv_file = "data/DashboardNutricao.csv"
    df, info = load_csv(csv_file, expected_cols=SCHEMA_NUTRICAO)

    csv_file_aluno = "data/DashboardNutricaoAluno.csv"
    df_aluno_raw, info_aluno = load_csv(
        csv_file_aluno, expected_cols=SCHEMA_NUTRICAO_ALUNO
    )

    csv_file_ano = "data/DashboardNutricaoAno.csv"
    df_ano, info_ano = load_csv(csv_file_ano, expected_cols=SCHEMA_NUTRICAO_ANO)

    csv_file_home = "data/DashboardHome.csv"
    df_home, info_home = load_csv(csv_file_home, expected_cols=SCHEMA_HOME)

    return {
        "principal": {"df": df, "info": info, "csv": csv_file},
        "aluno": {"df": df_aluno_raw, "info": info_aluno, "csv": csv_file_aluno},
        "ano": {"df": df_ano, "info": info_ano, "csv": csv_file_ano},
        "home": {"df": df_home, "info": info_home, "csv": csv_file_home},
    }


def page_nutricao():
    # Inicializa o estado global sincronizado (Anos e URGs)
    init_global_state()

    # --- LÓGICA DE TOGGLE PARA NUTRIÇÃO ---
    def toggle_nutricao(nut_name):
        current = st.session_state.get("nutricao_situacao_multiselect", [])
        st.session_state["nutricao_situacao_multiselect"] = (
            toggle_multiselect_value(current, nut_name)
        )

    st.title("Visão Geral da Nutrição")
    st.markdown(
        "Resumo consolidado das ações realizadas por ano, URG e equipe técnica."
    )
    st.markdown(
        """
        <style>
/* Rótulos e valores dos cards */
            .home-metric-label {
                font-size: 0.78rem !important;
                font-weight: 700 !important;
                color: #94a3b8 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.05em !important;
                margin-bottom: 4px !important;
            }
            .home-metric-value {
                font-size: 1.85rem !important;
                font-weight: 800 !important;
                color: #f1f5f9 !important;
                line-height: 1.1 !important;
            }
            .home-metric-card {
                border-radius: 12px !important;
                padding: 20px !important;
                height: 100% !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: center !important;
                border: 1.5px solid transparent !important;
                background-origin: border-box !important;
                background-clip: padding-box, border-box !important;
                transition: all 0.25s ease !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
            }
            .metric-card-static {
                background-image: linear-gradient(#0f172a, #0f172a), linear-gradient(135deg, #94a3b8 0%, #334155 100%) !important;
            }
            /* KPIs toggle com o mesmo look-and-feel dos cards da Home */
            div[class*="st-key-btn_kpi_"] button {
                min-height: 96px !important;
                border-radius: 12px !important;
                padding: 12px 14px !important;
                border: 1.5px solid #334155 !important;
                background: #0f172a !important;
                color: #f1f5f9 !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
                transition: all 0.25s ease !important;
                white-space: pre-line !important;
                text-align: left !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: stretch !important;
                justify-content: flex-start !important;
                line-height: 1.2 !important;
                font-size: 0.78rem !important;
                font-weight: 700 !important;
                letter-spacing: 0.05em !important;
                text-transform: uppercase !important;
            }
            div[class*="st-key-btn_kpi_"] [data-testid^="stBaseButton-"] {
                justify-content: flex-start !important;
                text-align: left !important;
            }
            div[class*="st-key-btn_kpi_"] button p {
                margin: 0 !important;
                white-space: pre-line !important;
                color: #94a3b8 !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: flex-start !important;
                align-items: flex-start !important;
                min-height: 100% !important;
                text-align: left !important;
                width: 100% !important;
            }
            div[class*="st-key-btn_kpi_"] button p strong {
                display: block !important;
                margin-top: 6px !important;
                color: #f1f5f9 !important;
                font-size: 2rem !important;
                line-height: 1.05 !important;
                letter-spacing: 0 !important;
                text-transform: none !important;
            }
            div[class*="st-key-btn_kpi_"] button:hover {
                transform: translateY(-3px) !important;
                border-color: #38bdf8 !important;
                box-shadow: 0 0 20px rgba(56, 189, 248, 0.3), 0 10px 25px rgba(0, 0, 0, 0.5) !important;
            }
            div[class*="st-key-btn_kpi_"] button[kind="primary"] {
                border-color: #38bdf8 !important;
                background: linear-gradient(135deg, rgba(56, 189, 248, 0.18) 0%, rgba(30, 64, 175, 0.22) 100%) !important;
            }
            
            /* Estilos para Agrupamento de Botões na Toolbar das Tabelas */
            .st-key-nutricao_urg_actions_toolbar div[data-testid="stHorizontalBlock"],
            .st-key-nutricao_ano_actions_toolbar div[data-testid="stHorizontalBlock"],
            .st-key-escola_table_selection_nutricao_actions_toolbar div[data-testid="stHorizontalBlock"],
            .st-key-nutricao_aluno_actions_toolbar div[data-testid="stHorizontalBlock"],
            .st-key-nutricao_simple_actions_toolbar div[data-testid="stHorizontalBlock"] {
                gap: 0 !important;
                --st-horizontal-block-gap: 0px !important;
                justify-content: flex-end !important;
                align-items: center !important;
                padding-right: 6px !important;
                overflow: visible !important;
            }
            .st-key-nutricao_urg_actions_toolbar div[data-testid="stColumn"],
            .st-key-nutricao_ano_actions_toolbar div[data-testid="stColumn"],
            .st-key-escola_table_selection_nutricao_actions_toolbar div[data-testid="stColumn"],
            .st-key-nutricao_aluno_actions_toolbar div[data-testid="stColumn"],
            .st-key-nutricao_simple_actions_toolbar div[data-testid="stColumn"] {
                padding: 0 !important;
                margin: 0 !important;
                width: auto !important;
                flex: 0 1 auto !important;
                overflow: visible !important;
            }
            .st-key-nutricao_urg_actions_toolbar button,
            .st-key-nutricao_ano_actions_toolbar button,
            .st-key-escola_table_selection_nutricao_actions_toolbar button,
            .st-key-nutricao_aluno_actions_toolbar button,
            .st-key-nutricao_simple_actions_toolbar button {
                background: transparent !important;
                border: 1px solid #334155 !important;
                border-right: none !important;
                border-radius: 0 !important;
                color: #94a3b8 !important;
                height: 34px !important;
                padding: 0 12px !important;
                margin: 0 !important;
                white-space: nowrap !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }
            .st-key-nutricao_urg_actions_toolbar div[class*="st-key-copy_"] button,
            .st-key-nutricao_ano_actions_toolbar div[class*="st-key-copy_"] button,
            .st-key-escola_table_selection_nutricao_actions_toolbar div[class*="st-key-copy_"] button,
            .st-key-nutricao_aluno_actions_toolbar div[class*="st-key-copy_"] button,
            .st-key-nutricao_simple_actions_toolbar div[class*="st-key-copy_"] button {
                border-radius: 6px 0 0 6px !important;
            }
            .st-key-nutricao_urg_actions_toolbar div[class*="st-key-download_"] button,
            .st-key-nutricao_ano_actions_toolbar div[class*="st-key-download_"] button,
            .st-key-escola_table_selection_nutricao_actions_toolbar div[class*="st-key-download_"] button,
            .st-key-nutricao_aluno_actions_toolbar div[class*="st-key-download_"] button,
            .st-key-nutricao_simple_actions_toolbar div[class*="st-key-download_"] button {
                border-right: 1px solid #334155 !important;
                border-radius: 0 6px 6px 0 !important;
            }
            .st-key-nutricao_urg_actions_toolbar button:hover,
            .st-key-nutricao_ano_actions_toolbar button:hover,
            .st-key-escola_table_selection_nutricao_actions_toolbar button:hover,
            .st-key-nutricao_aluno_actions_toolbar button:hover,
            .st-key-nutricao_simple_actions_toolbar button:hover {
                border-color: #38bdf8 !important;
                color: #38bdf8 !important;
                z-index: 2 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    filters_placeholder = st.empty()
    # apply_global_css() — Já injetado no main.py
    datasets = carregar_dados_nutricao()

    df, info = datasets["principal"]["df"], datasets["principal"]["info"]
    csv_file_aluno = datasets["aluno"]["csv"]
    df_aluno_raw, info_aluno = datasets["aluno"]["df"], datasets["aluno"]["info"]
    csv_file_ano = datasets["ano"]["csv"]
    df_ano, info_ano = datasets["ano"]["df"], datasets["ano"]["info"]
    df_home, info_home = datasets["home"]["df"], datasets["home"]["info"]

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

    if info_home["erros"]:
        st.error(f"Erro ao carregar dados demográficos: {'; '.join(info_home['erros'])}")
        df_home = pd.DataFrame()

    df = df.rename(
        columns={
            "Ano": "Ano",
            "URG": "URG",
            "Escola": "Escola",
            "Nutricao": "Nutricao",
            "Qtd": "Quantidade",
            "Tipo": "Tipo",
        }
    )

    df_aluno = df_aluno_raw.rename(
        columns={
            "Nutricao": "Nutricao",
            "DtNasc": "DataNascimento",
        }
    ).copy()
    if not df_aluno.empty and "DataNascimento" in df_aluno.columns:
        df_aluno["DataNascimento"] = pd.to_datetime(
            df_aluno["DataNascimento"], errors="coerce"
        )

    df_ano_exibir = df_ano.copy() if not df_ano.empty else pd.DataFrame()

    st.sidebar.title("Filtros - Nutrição")

    apply_pending_table_filters()

    df_filt_sidebar, selections = sidebar_filters(
        df,
        {"ano": True, "urg": True, "escola": True, "tipo": True},
    )

    sync_sidebar_escola_selection("escola_table_selection_nutricao")

    render_section_divider()
    st.markdown(" ")

    # --- SELETOR TEMPORAL MESTRE (INDICADORES E PÁGINA) ---
    current_year = datetime.datetime.now().year
    years_options = sorted([current_year - i for i in range(5)], reverse=True)
    
    with st.container(key="massive_year_selector"):
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
    # Partimos do DF bruto — sem escola — para preservar a tabela de escolas imune ao próprio filtro
    df_base_sem_escola = df.copy()
    
    # 1. Filtro de Tipo (Instituição) — Sem escola ainda
    if selections.get("tipo"):
        all_types = set(df["Tipo"].dropna().unique())
        selected_types = set(selections["tipo"])
        if selected_types != all_types:
            df_base_sem_escola = df_base_sem_escola[df_base_sem_escola["Tipo"].isin(selections["tipo"])]

    # 2. Filtro de Anos (Global) — Sem escola ainda
    if selected_years_comp:
        df_base_sem_escola = df_base_sem_escola[df_base_sem_escola["Ano"].isin(selected_years_comp)]
    else:
        df_base_sem_escola = pd.DataFrame()

    df_base_final = df_base_sem_escola.copy()

    # 3. Filtro de Escola (Cascata da Sidebar) — Aplicado após salvar a base sem escola
    if selections.get("escola"):
        all_schools = set(df["Escola"].dropna().unique())
        selected_schools = set(selections["escola"])
        if selected_schools != all_schools:
            df_base_final = df_base_final[df_base_final["Escola"].isin(selections["escola"])]

    # 4. Filtro de URGs (Global - Vinculação Bidirecional)
    current_urgs = st.session_state["global_urgs"]
    # Manter base sem filtro de nutrição para a tabela comparativa (Show context + Highlight)
    if current_urgs:
        df_master_no_nut = df_base_final[df_base_final["URG"].isin(current_urgs)]
    else:
        df_master_no_nut = df_base_final.copy()

    # 5. Filtro de URGs (Aplicação Final para o restante do dashboard)
    if current_urgs:
        df_master_filtrado = df_base_final[df_base_final["URG"].isin(current_urgs)]
    else:
        df_master_filtrado = df_base_final.copy()

    nutricao_col = "Nutricao"
    nutricoes_disponiveis = (
        sorted(df[nutricao_col].dropna().unique())
        if nutricao_col in df.columns
        else []
    )
    
    # Filtro de Situação Nutricional (Sincronizado entre Sidebar e Botões KPI)
    nutricoes_selecionadas = st.sidebar.multiselect(
        "Selecione a(s) Situação(ões) Nutricional(ais):",
        options=nutricoes_disponiveis,
        placeholder="Todas",
        key="nutricao_situacao_multiselect"
    )

    # 6. Filtro de Nutrição (Aplicação Final para o restante do dashboard)
    if nutricoes_selecionadas:
        df_master_filtrado = df_master_no_nut[df_master_no_nut["Nutricao"].isin(nutricoes_selecionadas)]
    else:
        df_master_filtrado = df_master_no_nut.copy()

    # Substitui df_filt pelo filtrado final
    df_filt = df_master_filtrado.copy()
    
    # --- Definições para Gráficos 'Top por URG' ---
    # 1. Sem filtro de escola (para mostrar Top Escolas) — usa df_base_sem_escola
    df_filt_no_escola = df_base_sem_escola.copy()
    if current_urgs:
        df_filt_no_escola = df_filt_no_escola[df_filt_no_escola["URG"].isin(current_urgs)]
    
    # 2. Sem filtro de nutrição (para mostrar Top Situações e Tabela Comparativa)
    df_filt_no_nut = df_master_no_nut.copy()
    
    # --- LÓGICA DE SELEÇÃO NAS TABELAS TOP ---
    # Escola
    selected_escola_from_table = None
    if "escola_table_selection_nutricao" in st.session_state:
        selection = st.session_state["escola_table_selection_nutricao"]
        rows = selection.get("selection", {}).get("rows", [])
        if rows:
            df_cmp_escola = build_comparativo_anual(df_filt_no_escola, "Escola")
            if df_cmp_escola is not None:
                selected_escola_from_table = get_selected_comparativo_value(
                    df_cmp_escola, rows, "Escola"
                )
    
    if selected_escola_from_table:
        df_filt = df_filt[df_filt["Escola"] == selected_escola_from_table]
        selections["escola"] = [selected_escola_from_table]

    # Nutricao is controlled only by the sidebar/KPI filters on this page.
    selected_nuts_from_table = []

    if nutricoes_selecionadas:
        df_filt = df_filt[df_filt["Nutricao"].isin(nutricoes_selecionadas)]
        selections["nutricao"] = nutricoes_selecionadas

    selections["nutricao"] = list(set(selections.get("nutricao", []) + nutricoes_selecionadas)) or nutricoes_disponiveis

    # --- Geração do filtro_titulo Dinâmico (Data-Driven UI) ---
    def get_filter_display_string_for_title(selected_items_list, all_available_items_list):
        if not selected_items_list or (all_available_items_list and set(map(str, selected_items_list)) == set(map(str, all_available_items_list))):
            return "Todos"
        return ", ".join(map(str, sorted(list(set(selected_items_list)))))


    all_urgs_for_title = sorted(list(df["URG"].dropna().unique()))
    all_years_for_title = sorted(list(df["Ano"].dropna().unique())) if "Ano" in df.columns else []
    all_escolas_for_title = sorted(list(df["Escola"].dropna().unique()))
    all_nuts_for_title = sorted(list(df["Nutricao"].dropna().unique()))
    
    current_urgs_for_title = st.session_state["global_urgs"] if st.session_state["global_urgs"] else all_urgs_for_title
    current_escolas_for_title = selections.get("escola", [])
    current_nuts_for_title = nutricoes_selecionadas if nutricoes_selecionadas else all_nuts_for_title
    
    anos_str = get_filter_display_string_for_title(selected_years_comp, all_years_for_title)
    urgs_str = get_filter_display_string_for_title(current_urgs_for_title, all_urgs_for_title)
    escolas_str = get_filter_display_string_for_title(current_escolas_for_title, all_escolas_for_title)
    nuts_str = get_filter_display_string_for_title(current_nuts_for_title, all_nuts_for_title)
    
    filtro_titulo = f"Anos: {anos_str} / URGs: {urgs_str} / Escolas: {escolas_str} / Nutrição: {nuts_str}"

    st.markdown(f"### Indicadores Gerais ({filtro_titulo})")
    
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
                ("nutricao", "Nutricao", "Situação Nutricional"),
            ],
        )
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Exportar dados")

    csv_export_encoding = "utf-8"
    csv = df_filt.to_csv(index=False, sep=";").encode(csv_export_encoding)
    st.sidebar.download_button(
        label="Exportar CSV (Nutrição)",
        data=csv,
        file_name="dados_filtrados_nutricao.csv",
        mime="text/csv",
    )
    
    # 1. Indicador principal (Total Geral)
    # --- Cálculo de Métricas Demográficas (Vindas da Home) ---
    df_home_filt = filter_by_sidebar_selections(df_home, selections)
    if not df_home_filt.empty:
        total_alunos_escola = df_home_filt["QtdAlunoEscola"].sum()
        total_alunos_atendidos = df_home_filt["QtdAluno"].sum()
    else:
        total_alunos_escola = 0
        total_alunos_atendidos = 0

    # Total de registros deve ignorar o filtro de Situação Nutricional para ser um indicador geral
    total_qtd = df_master_no_nut["Quantidade"].sum() if not df_master_no_nut.empty else 0
    render_metric_cards([
        {"label": "TOTAL DE ALUNOS", "value": total_alunos_escola},
        {"label": "ALUNOS ATENDIDOS", "value": total_alunos_atendidos},
        {"label": "TOTAL DE REGISTROS DE NUTRIÇÃO", "value": total_qtd}
    ])

    # Sumário por Situação Nutricional - IMUNIDADE AO FILTRO DE NUTRIÇÃO
    nutricao_sum = (
        df_filt_no_nut.groupby("Nutricao")["Quantidade"].sum().sort_values(ascending=False)
        if not df_filt_no_nut.empty and "Nutricao" in df_filt_no_nut.columns
        else pd.Series(dtype="float")
    )
    nutricao_sum = nutricao_sum[nutricao_sum > 0]
    
    if not nutricao_sum.empty:
        # Preparamos os itens para o render_metric_cards em modo toggle
        kpi_metrics = []
        for nome, valor in nutricao_sum.items():
            kpi_metrics.append({
                "label": str(nome).upper(),
                "value": valor
            })
        
        # Renderiza em blocos de 5 para manter o grid elegante
        for i in range(0, len(kpi_metrics), 5):
            chunk = kpi_metrics[i : i + 5]
            render_metric_cards(
                chunk, 
                is_toggle=True, 
                active_labels=[l.upper() for l in nutricoes_selecionadas],
                on_click_callback=toggle_nutricao
            )
    else:
        st.info("Selecione ao menos um ano para visualizar os indicadores.")

    st.markdown("---")

    # --- PRIORIDADE 2 (MEIO): TABELA COMPARATIVA DE PERFORMANCE ---
    st.subheader("Performance por URG")
    st.caption("Nota: Clique em qualquer linha de URG para filtrar o restante do dashboard. Esta tabela é sensível apenas ao filtro de Ano.")

    # Tabela mestre de URG: imune aos filtros de URG e Escola que ela coordena.
    df_for_urg_table = df_base_sem_escola.copy()
    if nutricoes_selecionadas:
        df_for_urg_table = df_for_urg_table[df_for_urg_table["Nutricao"].isin(nutricoes_selecionadas)]
    
    current_selected_urgs = st.session_state.get("global_urgs", [])
    df_cmp_urg = build_comparativo_anual(df_for_urg_table, "URG", active_row_value=current_selected_urgs)

    if df_cmp_urg is not None:
        df_cmp_urg_aggrid, column_defs, column_map = prepare_comparativo_aggrid_data(df_cmp_urg)
        df_cmp_urg_body, footer_rows = split_aggrid_footer(df_cmp_urg_aggrid)
        urg_field = next((f for f, col in column_map.items() if col == "URG" or col == ("URG", "")), None)

        selected_urgs_js = json.dumps(list(map(str, current_selected_urgs)))
        urg_field_js = json.dumps(urg_field)
        sync_selection_js = JsCode(f"""
            function(params) {{
                const selectedUrgs = new Set({selected_urgs_js});
                const urgField = {urg_field_js};
                if (!params.api || !urgField) return;
                params.api.forEachNode(function(node) {{
                    const rowUrg = node.data ? String(node.data[urgField] || '') : '';
                    node.setSelected(selectedUrgs.has(rowUrg));
                }});
            }}
        """)

        grid_options_urg = {
            "columnDefs": column_defs,
            "defaultColDef": {"resizable": True, "sortable": True, "filter": False, "suppressMenu": True},
            "rowSelection": "multiple",
            "rowMultiSelectWithClick": True,
            "pinnedBottomRowData": footer_rows,
            "onFirstDataRendered": sync_selection_js,
        }

        df_cmp_urg_export = pd.concat([df_cmp_urg_body, pd.DataFrame(footer_rows)], ignore_index=True) if footer_rows else df_cmp_urg_body.copy()
        with st.container(key="nutricao_urg_actions_toolbar"):
            render_table_toolbar(df_cmp_urg_export, "performance_urg_nutricao.csv", "urg_table_nutricao")

        _urg_key_sel = "_".join(sorted(map(str, current_selected_urgs))) if current_selected_urgs else "none"
        urg_table_key = f"urg_table_nutricao_{_urg_key_sel}"
        _urg_key_changed = st.session_state.get("_prev_urg_table_key_nutricao") != urg_table_key
        st.session_state["_prev_urg_table_key_nutricao"] = urg_table_key
        st.markdown('<div class="selection-master-table">', unsafe_allow_html=True)
        aggrid_response = render_saedas_aggrid(
            df_cmp_urg_body,
            grid_options=grid_options_urg,
            key=urg_table_key,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            incluir_total=bool(footer_rows),
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # AgGrid pode retornar None quando não há seleção, tratamos como lista vazia []
        selected_rows_raw = aggrid_response.get("selected_rows")
        selected_rows = []
        if selected_rows_raw is not None:
            if isinstance(selected_rows_raw, pd.DataFrame):
                selected_rows = selected_rows_raw.to_dict(orient="records")
            elif isinstance(selected_rows_raw, dict):
                selected_rows = [selected_rows_raw]
            else:
                selected_rows = list(selected_rows_raw)

        if not _urg_key_changed and urg_field:
            new_selected_urgs = [
                row.get(urg_field) 
                for row in selected_rows 
                if row.get(urg_field) and str(row.get(urg_field)) != "TOTAL"
            ]
            
            # Sincronização Granular: Se houver mudança (inclusive para lista vazia), propaga para a sidebar
            if set(map(str, new_selected_urgs)) != set(map(str, current_selected_urgs)):
                st.session_state["global_urgs"] = new_selected_urgs
                st.session_state["pending_sidebar_urg_filter"] = new_selected_urgs
                st.session_state["last_interaction_source"] = "table"
                st.rerun()
    else:
        st.info("Dados insuficientes para gerar a tabela de performance.")
    
    # --- PRIORIDADE 3: DETALHAMENTO TOP POR URG (ESCOLAS E NUTRIÇÃO) ---
    # Escolas por URG: Deve respeitar o filtro de Situação Nutricional
    df_for_top_escolas = df_filt_no_escola.copy()
    if nutricoes_selecionadas:
        df_for_top_escolas = df_for_top_escolas[df_for_top_escolas["Nutricao"].isin(nutricoes_selecionadas)]

    render_top_por_urg(
        df_for_top_escolas[df_for_top_escolas["Ano"].isin(selected_years_comp)] if not df_for_top_escolas.empty else pd.DataFrame(), 
        "Quantidade", 
        "Principais Escolas por URG", 
        "Escola", 
        table_key="escola_table_selection_nutricao",
        active_row_value=st.session_state.get("sidebar_escola_filter", []),
        selection_mode="multiple"
    )

    escolas_tabela_atual = st.session_state.get("escola_table_selection_nutricao__selected_values", [])
    current_sidebar_escolas = st.session_state.get("sidebar_escola_filter", [])
    
    # Sincronismo tabela -> sidebar: removida restrição rígida de last_source para permitir limpeza total
    if set(map(str, escolas_tabela_atual)) != set(map(str, current_sidebar_escolas)):
        st.session_state["pending_sidebar_escola_filter"] = escolas_tabela_atual
        st.session_state["last_interaction_source"] = "table_escola"
        st.rerun()
    st.session_state["last_interaction_source"] = ""


    st.markdown("---")

    # --- PRIORIDADE 3 (BASE): GRÁFICO DE PERFORMANCE POR URG ---
    st.subheader("Comparativo Anual de Nutrição por URG")
    render_grouped_bar_anual(df_filt, "Quantidade", "", orientation="h")
    st.markdown("---")

    # --- DISTRIBUIÇÃO POR SITUAÇÃO NUTRICIONAL (GRÁFICO AGRUPADO) ---
    st.subheader("Distribuição por Situação Nutricional")
    render_grouped_bar_anual(df_filt_no_nut, "Quantidade", "", x_col="Nutricao", orientation="h")
    




    st.markdown("---")
    st.subheader("Detalhamento por Aluno")
    if df_aluno.empty:
        st.info(
            "Dados de alunos não estão disponíveis ou houve erro na leitura do CSV."
        )
    else:
        # ── LÓGICA DE FILTRAGEM CRUZADA PARA O DETALHAMENTO ──
        # Utiliza o contexto filtrado pelo seletor mestre de anos
        df_aluno_base = filter_by_sidebar_selections(df_aluno, selections)
        df_aluno_base = df_aluno_base[df_aluno_base["Ano"].isin(selected_years_comp)] if not df_aluno_base.empty else pd.DataFrame()
        
        # Filtro de nutrição da sidebar (se houver)
        if nutricoes_selecionadas and "Nutricao" in df_aluno_base.columns:
            df_aluno_base = df_aluno_base[df_aluno_base["Nutricao"].isin(nutricoes_selecionadas)]

        df_aluno_filtrado = df_aluno_base.copy()

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
            )
            if turmas_selecionadas:
                df_aluno_filtrado = df_aluno_filtrado[
                    df_aluno_filtrado[turma_col].astype(str).isin(turmas_selecionadas)
                ]

        total_registros_aluno = len(df_aluno_filtrado)
        st.caption(
            f"{total_registros_aluno} registros após filtros da sidebar"
            + (" e de nutrição" if nutricoes_selecionadas else "")
        )

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

            df_aluno_final = prepare_nutricao_aluno_table(
                df_aluno_filtrado, build_perfil_link, selected_nuts=selected_nuts_from_table
            )

            # Renomear coluna Menu para Perfil para exibição
            df_aluno_final = df_aluno_final.rename(columns={"Menu": "Perfil"})
            preview_limit = 500
            df_aluno_head = df_aluno_final.head(preview_limit).reset_index(drop=True)

            if not df_aluno_head.empty:
                # Aplicar design padrão (Zebra, Hover, etc)
                styled_aluno = (
                    df_aluno_head.style.pipe(apply_saedas_design, categoria_col="Aluno")
                    .set_properties(**{"text-align": "left"})
                    .hide(axis="index")
                )

                with st.container(key="nutricao_aluno_actions_toolbar"):
                    render_table_toolbar(df_aluno_head, "detalhes_alunos_nutricao.csv", "aluno_table_nutricao")

                st.markdown('<div class="st-table-with-total">', unsafe_allow_html=True)
                st.dataframe(
                    styled_aluno,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Perfil": st.column_config.LinkColumn(
                            "Perfil", display_text="📄 Ver Perfil"
                        )
                    },
                )
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Nenhum registro detalhado para exibir.")

            if total_registros_aluno > preview_limit:
                st.info(
                    f"Exibindo apenas as primeiras {preview_limit} linhas de {total_registros_aluno}."
                )

    st.markdown(" ")
    footer_personal()
