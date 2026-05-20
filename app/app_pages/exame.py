import json
import re
import pandas as pd
import streamlit as st
import datetime
from urllib.parse import urlencode

from components.footer_personal import footer_personal
from components.sidebar_filters import sidebar_filters
from app.utils.data_loader import load_csv
from st_aggrid import GridUpdateMode, JsCode
from app.utils.page_helpers import (
    filter_by_sidebar_selections,
    build_comparativo_anual,
    render_top_por_urg,
    format_filters_applied,
    render_grouped_bar_anual,
    toggle_multiselect_value,
    render_section_divider,
    prepare_comparativo_aggrid_data,
    split_aggrid_footer,
    render_table_toolbar,
    render_saedas_aggrid,
    render_aluno_detalhamento_aggrid
)
from app.utils.state_manager import (
    apply_pending_table_filters,
    init_global_state,
    sync_sidebar_escola_selection,
    sync_home_to_sidebar,
    sync_local_exame_regulacao
)
from app.utils.schemas import SCHEMA_EXAME, SCHEMA_EXAME_ALUNO, SCHEMA_EXAME_ANO, SCHEMA_HOME
from app.utils.styles import render_metric_cards, apply_saedas_design


from app.utils.redis_client import redis_cache

def carregar_dados_exame():
    """Carrega os datasets da página Exame com suporte a Smart Cache Redis."""
    keys = {
        "principal": ("saedas:exame:dataset:main", "data/DashboardExame.csv", SCHEMA_EXAME),
        "aluno": ("saedas:exame:dataset:aluno", "data/DashboardExameAluno.csv", SCHEMA_EXAME_ALUNO),
        "ano": ("saedas:exame:dataset:ano", "data/DashboardExameAno.csv", SCHEMA_EXAME_ANO),
        "home": ("saedas:home:dataset:main", "data/DashboardHome.csv", SCHEMA_HOME),
    }

    results = {}
    for key_id, (redis_key, csv_path, schema) in keys.items():
        # Tenta recuperar do Redis verificando timestamp
        df = redis_cache.get_dataframe_with_timestamp(redis_key, csv_path)
        
        if df is not None:
            results[key_id] = {
                "df": df,
                "info": {"encoding_usado": "Redis (Cache)", "erros": [], "alertas": [], "alertas_ano": []},
                "csv": csv_path
            }
        else:
            # Fallback para o disco
            df, info = load_csv(csv_path, expected_cols=schema)
            results[key_id] = {"df": df, "info": info, "csv": csv_path}
            if not df.empty:
                redis_cache.set_dataframe_with_timestamp(redis_key, df, csv_path)
    return results


def page_exame():
    def toggle_regulacao(reg_name):
        current = st.session_state.get("exame_regulacao_multiselect", [])
        st.session_state["exame_regulacao_multiselect"] = (
            toggle_multiselect_value(current, reg_name)
        )
        # Sincroniza com a chave persistente
        st.session_state["persistent_exame_regulacao"] = st.session_state["exame_regulacao_multiselect"]

    init_global_state()

    st.title("Visão Geral dos Exames (Regulação)")
    st.markdown("Resumo consolidado das ações realizadas por ano, URG e equipe técnica.")
    st.markdown(
        """
        <style>
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
                align-items: flex-start !important;
                justify-content: center !important;
                line-height: 1.2 !important;
                font-size: 0.78rem !important;
                font-weight: 700 !important;
                letter-spacing: 0.05em !important;
                text-transform: uppercase !important;
            }
            div[class*="st-key-btn_kpi_"] button p {
                margin: 0 !important;
                white-space: pre-line !important;
                color: #94a3b8 !important;
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
            .st-key-exame_urg_actions_toolbar div[data-testid="stHorizontalBlock"],
            .st-key-exame_ano_actions_toolbar div[data-testid="stHorizontalBlock"],
            .st-key-exame_aluno_actions_toolbar div[data-testid="stHorizontalBlock"],
            .st-key-escola_table_selection_exame_actions_toolbar div[data-testid="stHorizontalBlock"] {
                gap: 0 !important;
                --st-horizontal-block-gap: 0px !important;
                justify-content: flex-end !important;
                align-items: center !important;
                padding-right: 6px !important;
                overflow: visible !important;
            }
            .st-key-exame_urg_actions_toolbar div[data-testid="stColumn"],
            .st-key-exame_ano_actions_toolbar div[data-testid="stColumn"],
            .st-key-exame_aluno_actions_toolbar div[data-testid="stColumn"],
            .st-key-escola_table_selection_exame_actions_toolbar div[data-testid="stColumn"] {
                padding: 0 !important;
                margin: 0 !important;
                width: auto !important;
                flex: 0 1 auto !important;
                overflow: visible !important;
            }
            .st-key-exame_urg_actions_toolbar button,
            .st-key-exame_ano_actions_toolbar button,
            .st-key-exame_aluno_actions_toolbar button,
            .st-key-escola_table_selection_exame_actions_toolbar button {
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
            .st-key-exame_urg_actions_toolbar div[class*="st-key-copy_"] button,
            .st-key-exame_ano_actions_toolbar div[class*="st-key-copy_"] button,
            .st-key-exame_aluno_actions_toolbar div[class*="st-key-copy_"] button,
            .st-key-escola_table_selection_exame_actions_toolbar div[class*="st-key-copy_"] button {
                border-radius: 6px 0 0 6px !important;
            }
            .st-key-exame_urg_actions_toolbar div[class*="st-key-download_"] button,
            .st-key-exame_ano_actions_toolbar div[class*="st-key-download_"] button,
            .st-key-exame_aluno_actions_toolbar div[class*="st-key-download_"] button,
            .st-key-escola_table_selection_exame_actions_toolbar div[class*="st-key-download_"] button {
                border-right: 1px solid #334155 !important;
                border-radius: 0 6px 6px 0 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    filters_placeholder = st.empty()
    render_section_divider()
    st.markdown(" ")

    datasets = carregar_dados_exame()
    df, info = datasets["principal"]["df"], datasets["principal"]["info"]
    csv_file_aluno = datasets["aluno"]["csv"]
    df_aluno_raw, info_aluno = datasets["aluno"]["df"], datasets["aluno"]["info"]
    csv_file_ano = datasets["ano"]["csv"]
    df_ano, info_ano = datasets["ano"]["df"], datasets["ano"]["info"]
    df_home, info_home = datasets["home"]["df"], datasets["home"]["info"]

    if info_aluno["erros"]:
        st.warning(f"Falha ao ler '{csv_file_aluno}': " + "; ".join(info_aluno["erros"]))
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
            "Exame": "Regulacao",
            "Qtd": "Quantidade",
            "Tipo": "Tipo",
        }
    )

    df_aluno = df_aluno_raw.rename(columns={"Exame": "Regulacao", "DtNasc": "DataNascimento"}).copy()
    if not df_aluno.empty and "DataNascimento" in df_aluno.columns:
        df_aluno["DataNascimento"] = pd.to_datetime(df_aluno["DataNascimento"], errors="coerce")

    st.sidebar.title("Filtros - Exames")
    apply_pending_table_filters()

    df_filt_sidebar, selections = sidebar_filters(df, {"ano": True, "urg": True, "escola": True, "tipo": True})

    sync_sidebar_escola_selection("escola_table_selection_exame")

    current_year = datetime.datetime.now().year
    years_options = sorted([current_year - i for i in range(5)], reverse=True)
    with st.container(key="massive_year_selector"):
        st.segmented_control(
            label="Ano(s) de Referência:",
            options=years_options,
            selection_mode="multi",
            key="home_year_buttons",
            on_change=sync_home_to_sidebar,
            label_visibility="collapsed",
        )
    selected_years_comp = st.session_state["global_years"]

    regulacao_col = "Regulacao"
    regulacoes_disponiveis = sorted(df[regulacao_col].dropna().unique()) if regulacao_col in df.columns else []

    # Restaura o estado persistente caso o Streamlit tenha podado a chave do widget na navegação
    if "exame_regulacao_multiselect" not in st.session_state:
        st.session_state["exame_regulacao_multiselect"] = st.session_state.get("persistent_exame_regulacao", [])

    # Filtro de Regulação (Sincronizado entre Sidebar e Botões KPI)
    regulacoes_selecionadas = st.sidebar.multiselect(
        "Selecione a(s) Regulação(ões):",
        options=regulacoes_disponiveis,
        placeholder="Todas",
        key="exame_regulacao_multiselect",
        on_change=sync_local_exame_regulacao
    )

    df_base_sem_escola = df.copy()
    if selections.get("tipo"):
        all_types = set(df["Tipo"].dropna().unique())
        if set(selections["tipo"]) != all_types:
            df_base_sem_escola = df_base_sem_escola[df_base_sem_escola["Tipo"].isin(selections["tipo"])]
    if selected_years_comp:
        df_base_sem_escola = df_base_sem_escola[df_base_sem_escola["Ano"].isin(selected_years_comp)]
    else:
        df_base_sem_escola = pd.DataFrame()

    df_base_final = df_base_sem_escola.copy()
    if selections.get("escola"):
        all_schools = set(df["Escola"].dropna().unique())
        if set(selections["escola"]) != all_schools:
            df_base_final = df_base_final[df_base_final["Escola"].isin(selections["escola"])]

    current_urgs = st.session_state["global_urgs"]
    if current_urgs:
        df_master_no_reg = df_base_final[df_base_final["URG"].isin(current_urgs)]
    else:
        df_master_no_reg = df_base_final.copy()

    if regulacoes_selecionadas:
        df_master_filtrado = df_master_no_reg[df_master_no_reg["Regulacao"].isin(regulacoes_selecionadas)]
    else:
        df_master_filtrado = df_master_no_reg.copy()

    df_filt = df_master_filtrado.copy()
    
    # df_filt_no_escola: Ignora filtro de ESCOLA, mas mantém Ano, URG e Tipo (Sidebar)
    df_filt_no_escola = df_base_sem_escola.copy()
    if current_urgs:
        df_filt_no_escola = df_filt_no_escola[df_filt_no_escola["URG"].isin(current_urgs)]
    
    # df_filt_no_urg_no_escola: Ignora URG e ESCOLA (usado para a tabela mestra de URG)
    df_filt_no_urg_no_escola = df_base_sem_escola.copy()

    df_filt_no_reg = df_master_no_reg.copy()

    if regulacoes_selecionadas:
        selections["regulacao"] = regulacoes_selecionadas
    else:
        selections["regulacao"] = regulacoes_disponiveis

    def get_filter_display_string_for_title(selected_items_list, all_available_items_list):
        if not selected_items_list or (all_available_items_list and set(map(str, selected_items_list)) == set(map(str, all_available_items_list))):
            return "Todos"
        return ", ".join(map(str, sorted(list(set(selected_items_list)))))

    all_urgs_for_title = sorted(list(df["URG"].dropna().unique()))
    all_years_for_title = sorted(list(df["Ano"].dropna().unique())) if "Ano" in df.columns else []
    all_escolas_for_title = sorted(list(df["Escola"].dropna().unique()))
    all_regs_for_title = sorted(list(df["Regulacao"].dropna().unique()))

    current_urgs_for_title = st.session_state["global_urgs"] if st.session_state["global_urgs"] else all_urgs_for_title
    anos_str = get_filter_display_string_for_title(selected_years_comp, all_years_for_title)
    urgs_str = get_filter_display_string_for_title(current_urgs_for_title, all_urgs_for_title)
    escolas_str = get_filter_display_string_for_title(selections.get("escola", []), all_escolas_for_title)
    regs_str = get_filter_display_string_for_title(regulacoes_selecionadas if regulacoes_selecionadas else all_regs_for_title, all_regs_for_title)

    st.markdown(f"### Indicadores Gerais (Anos: {anos_str} / URGs: {urgs_str} / Escolas: {escolas_str} / Regulações: {regs_str})")

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
                ("regulacao", "Regulacao", "Regulação"),
            ],
        )
    )

    st.sidebar.markdown("---")
    

    # --- Cálculo de Métricas Demográficas (Vindas da Home) ---
    df_home_filt = filter_by_sidebar_selections(df_home, selections)
    if not df_home_filt.empty:
        total_alunos_escola = df_home_filt["QtdAlunoEscola"].sum()
        total_alunos_atendidos = df_home_filt["QtdAluno"].sum()
    else:
        total_alunos_escola = 0
        total_alunos_atendidos = 0

    # TOTAL DE EXAMES deve ignorar o filtro de Regulação (conforme solicitado: indicadores gerais não filtram por tipo)
    total_qtd = df_filt_no_reg["Quantidade"].sum() if not df_filt_no_reg.empty else 0
    render_metric_cards([
        {"label": "TOTAL DE ALUNOS", "value": total_alunos_escola},
        {"label": "ALUNOS ATENDIDOS", "value": total_alunos_atendidos},
        {"label": "TOTAL DE EXAMES", "value": total_qtd}
    ])
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    regulacoes_sum = (
        df_filt_no_reg.groupby("Regulacao")["Quantidade"].sum().sort_values(ascending=False)
        if not df_filt_no_reg.empty and "Regulacao" in df_filt_no_reg.columns
        else pd.Series(dtype="float")
    )
    regulacoes_sum = regulacoes_sum[regulacoes_sum > 0]

    if not regulacoes_sum.empty:
        kpi_metrics = [{"label": str(nome).upper(), "value": valor} for nome, valor in regulacoes_sum.items()]
        for i in range(0, len(kpi_metrics), 5):
            chunk = kpi_metrics[i : i + 5]
            render_metric_cards(
                chunk,
                is_toggle=True,
                active_labels=[l.upper() for l in regulacoes_selecionadas],
                on_click_callback=toggle_regulacao,
            )
            if i + 5 < len(kpi_metrics):
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    else:
        st.info("Selecione ao menos um ano para visualizar os indicadores.")

    render_section_divider()

    # --- NOVO: Tabela Comparativa de Performance por ANO (Exames) ---
    st.subheader("Tabela Comparativa de Performance por ANO (Exames)")
    df_cmp_ano_perf = build_comparativo_anual(
        df_filt,
        "Regulacao",
        value_col="Quantidade",
        pct_label="Total",
    )
    if df_cmp_ano_perf is not None:
        df_ano_perf_aggrid, ano_perf_column_defs, _ = prepare_comparativo_aggrid_data(
            df_cmp_ano_perf, include_selection_column=False
        )

        # Mantém a mesma ordem dos indicadores gerais (cards), preservando TOTAL no final.
        if not df_ano_perf_aggrid.empty and not regulacoes_sum.empty:
            first_col = df_ano_perf_aggrid.columns[0]
            ordem_indicadores = {
                str(nome).strip().upper(): idx
                for idx, nome in enumerate(regulacoes_sum.index.tolist())
            }
            df_ano_perf_aggrid["_ordem_kpi"] = df_ano_perf_aggrid[first_col].map(
                lambda x: ordem_indicadores.get(str(x).strip().upper(), 10**6)
            )
            df_ano_perf_aggrid["_is_total"] = (
                df_ano_perf_aggrid[first_col].astype(str).str.strip().str.upper().eq("TOTAL")
            )
            df_ano_perf_aggrid = (
                df_ano_perf_aggrid
                .sort_values(by=["_is_total", "_ordem_kpi"], ascending=[True, True], kind="stable")
                .drop(columns=["_ordem_kpi", "_is_total"])
                .reset_index(drop=True)
            )

        df_ano_perf_body, ano_perf_footer = split_aggrid_footer(df_ano_perf_aggrid)

        def _ajustar_colunas_ano_exames(column_defs: list[dict]) -> None:
            for col_def in column_defs:
                header_name = str(col_def.get("headerName", "")).strip()

                if header_name == "Regulacao":
                    col_def["headerName"] = "Regulação"
                    col_def["cellStyle"] = {"textAlign": "left"}
                    col_def["headerClass"] = "saedas-aggrid-left-header"

                if re.fullmatch(r"20\d{2}", header_name):
                    col_def["headerClass"] = "saedas-aggrid-centered-header"

                children = col_def.get("children")
                if isinstance(children, list) and children:
                    _ajustar_colunas_ano_exames(children)

        _ajustar_colunas_ano_exames(ano_perf_column_defs)

        ano_perf_grid_options = {
            "columnDefs": ano_perf_column_defs,
            "defaultColDef": {
                "resizable": True,
                "sortable": True,
                "filter": False,
                "suppressMenu": True,
            },
            "pinnedBottomRowData": ano_perf_footer,
        }

        df_ano_perf_export = (
            pd.concat([df_ano_perf_body, pd.DataFrame(ano_perf_footer)], ignore_index=True)
            if ano_perf_footer
            else df_ano_perf_body.copy()
        )
        with st.container(key="exame_ano_actions_toolbar"):
            render_table_toolbar(
                df_ano_perf_export,
                "comparativo_performance_ano_exames.csv",
                "ano_perf_table_exame",
            )

        st.markdown('<div class="st-table-with-total">', unsafe_allow_html=True)
        render_saedas_aggrid(
            df_ano_perf_body,
            grid_options=ano_perf_grid_options,
            key="ano_perf_table_exame_aggrid",
            incluir_total=bool(ano_perf_footer),
            min_height=140,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption(
            "Nota: As colunas '% Total' representam o percentual da Regulação no respectivo ano. "
            "As colunas 'Var%' mostram a variação em relação ao ano anterior."
        )
    else:
        st.info("Dados insuficientes para gerar a tabela comparativa de performance por ano.")

    render_section_divider()

    st.subheader("Performance por URG")
    st.caption("Nota: Clique em qualquer linha de URG para filtrar o restante do dashboard. Esta tabela é sensível apenas ao filtro de Ano.")

    # Tabela de Performance por URG: IMUNE ao filtro de URG (mostra tudo para permitir seleção)
    df_for_urg_table = df_filt_no_urg_no_escola.copy()
    
    # Mas respeita o filtro de Regulação
    if regulacoes_selecionadas:
        df_for_urg_table = df_for_urg_table[df_for_urg_table["Regulacao"].isin(regulacoes_selecionadas)]

    df_cmp_urg = build_comparativo_anual(df_for_urg_table, "URG", active_row_value=current_urgs)

    if df_cmp_urg is not None:
        df_cmp_urg_aggrid, column_defs, column_map = prepare_comparativo_aggrid_data(df_cmp_urg)
        df_cmp_urg_body, footer_rows = split_aggrid_footer(df_cmp_urg_aggrid)
        urg_field = next((f for f, col in column_map.items() if col == "URG" or col == ("URG", "")), None)

        selected_urgs_js = json.dumps(list(map(str, current_urgs)))
        urg_field_js = json.dumps(urg_field) if urg_field else "null"
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

        grid_options = {
            "columnDefs": column_defs,
            "defaultColDef": {"resizable": True, "sortable": True, "filter": False, "suppressMenu": True},
            "rowSelection": "multiple",
            "rowMultiSelectWithClick": True,
            "pinnedBottomRowData": footer_rows,
            "onFirstDataRendered": sync_selection_js,
        }

        df_cmp_urg_export = pd.concat([df_cmp_urg_body, pd.DataFrame(footer_rows)], ignore_index=True) if footer_rows else df_cmp_urg_body.copy()
        with st.container(key="exame_urg_actions_toolbar"):
            render_table_toolbar(df_cmp_urg_export, "performance_urg_exame.csv", "urg_table_exame")

        _years_key = "_".join(sorted(map(str, selected_years_comp))) if selected_years_comp else "all"
        _reg_key_sel = "_".join(sorted(map(str, regulacoes_selecionadas))) if regulacoes_selecionadas else "all"
        _urg_key_sel = "_".join(sorted(map(str, current_urgs))) if current_urgs else "none"
        urg_table_key = f"urg_table_exame_{_years_key}_{_reg_key_sel}_{_urg_key_sel}"
        _urg_key_changed = st.session_state.get("_is_page_first_run") or (st.session_state.get("_prev_urg_table_key_exame") != urg_table_key)
        st.session_state["_prev_urg_table_key_exame"] = urg_table_key
        st.markdown('<div class="selection-master-table">', unsafe_allow_html=True)
        aggrid_response = render_saedas_aggrid(
            df_cmp_urg_body,
            grid_options=grid_options,
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
            if set(map(str, new_selected_urgs)) != set(map(str, current_urgs)):
                st.session_state["global_urgs"] = new_selected_urgs
                st.session_state["pending_sidebar_urg_filter"] = new_selected_urgs
                st.session_state["last_interaction_source"] = "table"
                st.rerun()
    else:
        st.info("Dados insuficientes para gerar a tabela de performance.")

    # Top Escolas: deve respeitar o filtro de Regulação
    df_for_top_escolas = df_filt_no_escola.copy()
    if regulacoes_selecionadas:
        df_for_top_escolas = df_for_top_escolas[df_for_top_escolas["Regulacao"].isin(regulacoes_selecionadas)]

    render_top_por_urg(
        df_for_top_escolas[df_for_top_escolas["Ano"].isin(selected_years_comp)] if not df_for_top_escolas.empty else pd.DataFrame(),
        "Quantidade",
        "Principais Escolas por URG",
        "Escola",
        table_key="escola_table_selection_exame",
        active_row_value=st.session_state.get("sidebar_escola_filter", []),
        selection_mode="multiple",
    )

    escolas_tabela_atual = st.session_state.get("escola_table_selection_exame__selected_values", [])
    current_sidebar_escolas = st.session_state.get("sidebar_escola_filter", [])
    
    # Sincronismo tabela -> sidebar: removida restrição rígida de last_source para permitir limpeza total
    if set(map(str, escolas_tabela_atual)) != set(map(str, current_sidebar_escolas)):
        st.session_state["pending_sidebar_escola_filter"] = escolas_tabela_atual
        st.session_state["last_interaction_source"] = "table_escola"
        st.rerun()
    st.session_state["last_interaction_source"] = ""

    render_section_divider()

    st.subheader("Comparativo Anual de Exames por URG")
    render_grouped_bar_anual(df_filt, "Quantidade", "", orientation="h")
    render_section_divider()

    st.subheader("Distribuição por Regulação")
    render_grouped_bar_anual(df_filt, "Quantidade", "", x_col="Regulacao", orientation="h")

    render_section_divider()
    st.subheader("Detalhamento por Aluno")
    if df_aluno.empty:
        st.info("Dados de alunos não estão disponíveis ou houve erro na leitura do CSV.")
    else:
        df_aluno_base = filter_by_sidebar_selections(df_aluno, selections)
        df_aluno_base = df_aluno_base[df_aluno_base["Ano"].isin(selected_years_comp)] if not df_aluno_base.empty else pd.DataFrame()

        selected_escolas_effective = selections.get("escola", [])
        if selected_escolas_effective:
            df_aluno_filtrado = df_aluno_base[df_aluno_base["Escola"].isin(selected_escolas_effective)]
        else:
            df_aluno_filtrado = df_aluno_base.copy()

        if regulacoes_selecionadas and "Regulacao" in df_aluno_filtrado.columns:
            df_aluno_filtrado = df_aluno_filtrado[df_aluno_filtrado["Regulacao"].isin(regulacoes_selecionadas)]

        aluno_col, serie_col, turma_col = "Aluno", "Serie", "Turma"
        if aluno_col in df_aluno_filtrado.columns:
            alunos_disponiveis = sorted(list(df_aluno_filtrado[aluno_col].dropna().astype(str).unique()))
            alunos_selecionados = st.multiselect("Filtrar por Aluno", options=alunos_disponiveis, default=[], placeholder="Todos")
            if alunos_selecionados:
                df_aluno_filtrado = df_aluno_filtrado[df_aluno_filtrado[aluno_col].astype(str).isin(alunos_selecionados)]

        if serie_col in df_aluno_filtrado.columns:
            series_disponiveis = sorted(list(df_aluno_filtrado[serie_col].dropna().astype(str).unique()))
            series_selecionadas = st.multiselect("Filtrar por Série", options=series_disponiveis, default=[], placeholder="Todas")
            if series_selecionadas:
                df_aluno_filtrado = df_aluno_filtrado[df_aluno_filtrado[serie_col].astype(str).isin(series_selecionadas)]

        if turma_col in df_aluno_filtrado.columns:
            turmas_disponiveis = sorted(list(df_aluno_filtrado[turma_col].dropna().astype(str).unique()))
            turmas_selecionadas = st.multiselect("Filtrar por Turma", options=turmas_disponiveis, default=[], placeholder="Todas")
            if turmas_selecionadas:
                df_aluno_filtrado = df_aluno_filtrado[df_aluno_filtrado[turma_col].astype(str).isin(turmas_selecionadas)]

        total_registros_aluno = len(df_aluno_filtrado)
        st.caption(f"{total_registros_aluno} registros após filtros da sidebar" + (" e de regulação" if regulacoes_selecionadas else ""))

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
            static_cols = [c for c in ["Sexo", "URG", "Escola", "Serie", "Turma"] if c in df_aluno_para_exibir.columns]
            df_static = df_aluno_para_exibir.groupby(["Aluno", "DataNascimento"], as_index=False)[static_cols].last()

            def format_reg_list(group):
                regs = sorted(group["Regulacao"].dropna().unique())
                return ", ".join([r.lower().capitalize() for r in regs])

            df_desc = df_aluno_para_exibir.groupby(["Aluno", "DataNascimento", "Ano"]).apply(format_reg_list).reset_index(name="Descricao")
            df_pivot_ano = df_desc.pivot(index=["Aluno", "DataNascimento"], columns="Ano", values="Descricao").fillna("").reset_index()
            anos_cols = [c for c in df_pivot_ano.columns if c not in ["Aluno", "DataNascimento"]]

            df_aluno_final = df_static.merge(df_pivot_ano, on=["Aluno", "DataNascimento"], how="left")
            df_counts_total = df_aluno_para_exibir.groupby(["Aluno", "DataNascimento"]).size().reset_index(name="Total")
            df_aluno_final = df_aluno_final.merge(df_counts_total, on=["Aluno", "DataNascimento"], how="left")
            for c in anos_cols:
                df_aluno_final[c] = df_aluno_final[c].fillna("")
            if "Total" in df_aluno_final.columns:
                df_aluno_final["Total"] = df_aluno_final["Total"].apply(lambda x: f"{int(x)}" if pd.notna(x) and x > 0 else "")
            df_aluno_final["Menu"] = df_aluno_final.apply(build_perfil_link, axis=1)
            if "DataNascimento" in df_aluno_final.columns:
                df_aluno_final["DataNascimento"] = pd.to_datetime(df_aluno_final["DataNascimento"], errors="coerce").dt.strftime("%d/%m/%Y")

            col_order = [c for c in ["Aluno", "DataNascimento", "Sexo", "URG", "Escola", "Serie", "Turma"] if c in df_aluno_final.columns] + anos_cols + ["Total", "Menu"]
            df_aluno_final = df_aluno_final[col_order].fillna("")

            # Renomear coluna Menu para Perfil para exibição
            df_aluno_final = df_aluno_final.rename(columns={"Menu": "Perfil"})

            if not df_aluno_final.empty:
                # Renderização da tabela de alunos usando AgGrid padronizado com Toolbar integrada
                render_aluno_detalhamento_aggrid(
                    df_aluno_final, 
                    key="aluno_table_exame",
                    csv_name="detalhes_alunos_exame.csv",
                    toolbar_key="exame_aluno_actions_toolbar"
                )
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Nenhum registro detalhado para exibir.")

    st.markdown(" ")
    footer_personal()
