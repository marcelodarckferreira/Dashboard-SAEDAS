from app.utils.page_helpers import render_section_divider
import re
import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from urllib.parse import urlencode

import json
from st_aggrid import GridUpdateMode, JsCode
from components.footer_personal import footer_personal
from components.sidebar_filters import sidebar_filters
from app.utils.data_loader import load_csv
from app.utils.page_helpers import (
    filter_by_sidebar_selections,
    build_comparativo_anual,
    render_metric,
    render_top_por_urg,
    format_filters_applied,
    prepare_comparativo_aggrid_data,
    render_saedas_aggrid,
    split_aggrid_footer,
    render_table_toolbar,
)
from app.utils.state_manager import init_global_state, sync_home_to_sidebar, sync_home_urg_to_sidebar
from app.utils.schemas import SCHEMA_MEDICO, SCHEMA_MEDICO_ALUNO, SCHEMA_MEDICO_ANO
from app.utils.styles import apply_global_css, render_metric_cards, apply_saedas_design, build_row_style_fn, get_table_hover_styles


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
    init_global_state()
    apply_global_css()

    st.title("Visão Geral dos Atendimentos Médicos")
    st.markdown(
        "Resumo consolidado dos atendimentos médicos realizados por ano, URG e escola."
    )
    st.markdown(
        """
        <style>
            /* Container Principal - Ajuste de Espaçamento Vertical */
            .st-key-massive_year_selector {
                margin-top: -1.5rem !important;
                margin-bottom: 1rem !important;
            }

            /* Alvo em QUALQUER botão dentro do container do seletor */
            .st-key-massive_year_selector button {
                height: 56px !important;
                min-width: 120px !important;
                border-radius: 0 !important;
                background-color: #1e293b !important;
                border: 1px solid #334155 !important;
                border-right: none !important;
                transition: all 0.3s ease !important;
                margin: 0 !important;
            }

            /* Arredondamento apenas nas extremidades do GRUPO */
            .st-key-massive_year_selector div[data-testid="stSegmentedControlItem"]:first-of-type button,
            .st-key-massive_year_selector button:first-of-type {
                border-radius: 10px 0 0 10px !important;
            }

            .st-key-massive_year_selector div[data-testid="stSegmentedControlItem"]:last-of-type button,
            .st-key-massive_year_selector button:last-of-type {
                border-radius: 0 10px 10px 0 !important;
                border-right: 1px solid #334155 !important;
            }

            /* Alvo em QUALQUER parágrafo ou texto dentro dos botões */
            .st-key-massive_year_selector button p,
            .st-key-massive_year_selector button span {
                font-size: 1.85rem !important;
                font-weight: 700 !important;
                color: #f8fafc !important;
                line-height: 1 !important;
                margin: 0 !important;
                padding: 0 !important;
            }

            /* Estado Ativo */
            .st-key-massive_year_selector button[data-testid*="Active"],
            .st-key-massive_year_selector button[aria-pressed="true"] {
                background-color: #3b82f6 !important;
                border-color: #60a5fa !important;
                box-shadow: none !important;
            }

            .st-key-massive_year_selector button[data-testid*="Active"] p,
            .st-key-massive_year_selector button[aria-pressed="true"] p {
                color: #ffffff !important;
            }
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
            .st-key-medico_urg_actions_toolbar div[data-testid="stHorizontalBlock"],
            .st-key-escola_table_selection_medico_actions_toolbar div[data-testid="stHorizontalBlock"],
            .st-key-medico_cobertura_actions_toolbar div[data-testid="stHorizontalBlock"],
            .st-key-medico_aluno_actions_toolbar div[data-testid="stHorizontalBlock"] {
                gap: 0 !important;
                --st-horizontal-block-gap: 0px !important;
                justify-content: flex-end !important;
                align-items: center !important;
                padding-right: 6px !important;
                overflow: visible !important;
            }
            .st-key-medico_urg_actions_toolbar div[data-testid="stColumn"],
            .st-key-escola_table_selection_medico_actions_toolbar div[data-testid="stColumn"],
            .st-key-medico_cobertura_actions_toolbar div[data-testid="stColumn"],
            .st-key-medico_aluno_actions_toolbar div[data-testid="stColumn"] {
                padding: 0 !important;
                margin: 0 !important;
                width: auto !important;
                flex: 0 1 auto !important;
                overflow: visible !important;
            }
            .st-key-medico_urg_actions_toolbar button,
            .st-key-escola_table_selection_medico_actions_toolbar button,
            .st-key-medico_cobertura_actions_toolbar button,
            .st-key-medico_aluno_actions_toolbar button {
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
            .st-key-medico_urg_actions_toolbar div[class*="st-key-copy_"] button,
            .st-key-escola_table_selection_medico_actions_toolbar div[class*="st-key-copy_"] button,
            .st-key-medico_cobertura_actions_toolbar div[class*="st-key-copy_"] button,
            .st-key-medico_aluno_actions_toolbar div[class*="st-key-copy_"] button {
                border-radius: 6px 0 0 6px !important;
            }
            .st-key-medico_urg_actions_toolbar div[class*="st-key-download_"] button,
            .st-key-escola_table_selection_medico_actions_toolbar div[class*="st-key-download_"] button,
            .st-key-medico_cobertura_actions_toolbar div[class*="st-key-download_"] button,
            .st-key-medico_aluno_actions_toolbar div[class*="st-key-download_"] button {
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
    
    # apply_global_css() — Já injetado no main.py

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

    # Sincronização de Filtros Pendentes (Vindos de Interação com Tabelas)
    pending_table_urgs = st.session_state.pop("pending_sidebar_urg_filter", None)
    if pending_table_urgs is not None:
        st.session_state["sidebar_urg_filter"] = pending_table_urgs
        st.session_state["global_urgs"] = pending_table_urgs
        st.session_state["last_interaction_source"] = "table"

    pending_table_escolas = st.session_state.pop("pending_sidebar_escola_filter", None)
    if pending_table_escolas is not None:
        st.session_state["sidebar_escola_filter"] = pending_table_escolas
        st.session_state["last_interaction_source"] = "table_escola"

    df_filt_sidebar, selections = sidebar_filters(
        df,
        {"ano": True, "urg": True, "escola": True, "tipo": True},
    )

    # Rastreamento de Mudança na Sidebar vs Tabela para Escola
    current_sidebar_escolas = list(st.session_state.get("sidebar_escola_filter", []))
    prev_sidebar_escolas = list(st.session_state.get("_prev_sidebar_escola_filter", []))
    if set(map(str, current_sidebar_escolas)) != set(map(str, prev_sidebar_escolas)):
        st.session_state["last_interaction_source"] = "sidebar"
        st.session_state["escola_table_selection_medico__selected_values"] = current_sidebar_escolas
    st.session_state["_prev_sidebar_escola_filter"] = current_sidebar_escolas

    atendimento_col = "Atendimento"
    atendimentos_disponiveis = (
        sorted(df_filt_sidebar[atendimento_col].dropna().unique())
        if atendimento_col in df_filt_sidebar.columns
        else []
    )
    # Filtro de Atendimento removido conforme solicitação
    atendimentos_selecionados = []

    def toggle_atendimento(label: str) -> None:
        """Alterna a seleção de um tipo de atendimento médico via KPI card."""
        current = list(st.session_state.get("medico_atendimento_multiselect", []))
        if label in current:
            current.remove(label)
        else:
            current.append(label)
        st.session_state["medico_atendimento_multiselect"] = current

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
    df_base_sem_escola = df.copy()
    
    # 1. Filtro de Tipo (Instituição)
    if selections.get("tipo"):
        all_types = set(df["Tipo"].dropna().unique())
        if set(selections["tipo"]) != all_types:
            df_base_sem_escola = df_base_sem_escola[df_base_sem_escola["Tipo"].isin(selections["tipo"])]
            
    # 2. Filtro de Anos (Global)
    if selected_years_comp:
        df_base_sem_escola = df_base_sem_escola[df_base_sem_escola["Ano"].isin(selected_years_comp)]
    else:
        df_base_sem_escola = pd.DataFrame()

    df_base_final = df_base_sem_escola.copy()
    # 3. Filtro de Escola (Cascata da Sidebar)
    if selections.get("escola"):
        all_schools = set(df["Escola"].dropna().unique())
        if set(selections["escola"]) != all_schools:
            df_base_final = df_base_final[df_base_final["Escola"].isin(selections["escola"])]

    # 4. Filtro de URGs (Global - Vinculação Bidirecional)
    current_urgs = st.session_state["global_urgs"]
    if current_urgs:
        df_master_no_atend = df_base_final[df_base_final["URG"].isin(current_urgs)]
    else:
        df_master_no_atend = df_base_final.copy()

    # 5. Filtro de Atendimento (Sidebar)
    if atendimentos_selecionados:
        df_master_filtrado = df_master_no_atend[df_master_no_atend[atendimento_col].isin(atendimentos_selecionados)]
    else:
        df_master_filtrado = df_master_no_atend.copy()

    # Substitui df_filt pelo filtrado final
    df_filt = df_master_filtrado.copy()

    # --- Definições para Gráficos 'Top por URG' ---
    # 1. Sem filtro de escola (mas com Tipo, Ano e URG)
    df_filt_no_escola = df_base_sem_escola.copy()
    if current_urgs:
        df_filt_no_escola = df_filt_no_escola[df_filt_no_escola["URG"].isin(current_urgs)]
        
    # 2. Sem filtro de Atendimento (mas com Tipo, Ano, Escola e URG)
    df_filt_no_atend = df_master_no_atend.copy()

    # --- Geração do filtro_titulo Dinâmico (Data-Driven UI) ---
    def get_filter_display_string_for_title(selected_items_list, all_available_items_list):
        if not selected_items_list or (all_available_items_list and set(map(str, selected_items_list)) == set(map(str, all_available_items_list))):
            return "Todos"
        return ", ".join(map(str, sorted(list(set(selected_items_list)))))

    all_urgs_for_title = sorted(list(df["URG"].dropna().unique()))
    all_years_for_title = sorted(list(df["Ano"].dropna().unique())) if "Ano" in df.columns else []
    all_escolas_for_title = sorted(list(df["Escola"].dropna().unique()))
    
    current_urgs_for_title = st.session_state["global_urgs"] if st.session_state["global_urgs"] else all_urgs_for_title
    current_escolas_for_title = selections.get("escola", [])
    
    anos_str = get_filter_display_string_for_title(selected_years_comp, all_years_for_title)
    urgs_str = get_filter_display_string_for_title(current_urgs_for_title, all_urgs_for_title)
    escolas_str = get_filter_display_string_for_title(current_escolas_for_title, all_escolas_for_title)
    
    filtro_titulo = f"Anos: {anos_str} / URGs: {urgs_str} / Escolas: {escolas_str}"

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
            ],
        )
    )
    urgs_aplicadas = selections.get("urg", [])



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

    total_atend = df_filt["Quantidade"].sum() if not df_filt.empty else 0

    render_metric_cards([
        {"label": "TOTAL DE ATENDIMENTOS MÉDICOS", "value": total_atend},
        {"label": "TOTAL GERAL DE ALUNOS", "value": total_alunos}
    ])
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if df_filt.empty:
        st.info("Selecione ao menos um ano para visualizar os indicadores.")
    
    st.markdown("---")

    # ── Tabela Comparativa de Performance por URG ─────────────────────
    st.subheader("Performance por URG")
    st.caption("Nota: Clique em qualquer linha de URG para filtrar o restante do dashboard. Esta tabela é sensível apenas ao filtro de Ano.")

    df_for_urg_table = df.copy()
    if selected_years_comp:
        df_for_urg_table = df_for_urg_table[df_for_urg_table["Ano"].isin(selected_years_comp)]

    current_selected_urgs = st.session_state.get("global_urgs", [])
    df_cmp_urg = build_comparativo_anual(df_for_urg_table, "URG", active_row_value=current_selected_urgs)

    if df_cmp_urg is not None:
        df_cmp_urg_aggrid, column_defs, column_map = prepare_comparativo_aggrid_data(df_cmp_urg)
        df_cmp_urg_body, footer_rows = split_aggrid_footer(df_cmp_urg_aggrid)
        urg_field = next((f for f, col in column_map.items() if col == "URG" or col == ("URG", "")), None)

        pre_selected_rows = []
        if urg_field and current_selected_urgs:
            pre_selected_rows = [idx for idx, val in enumerate(df_cmp_urg_body[urg_field].tolist()) if val in current_selected_urgs]

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

        grid_options = {
            "columnDefs": column_defs,
            "defaultColDef": {"resizable": True, "sortable": True, "filter": False, "suppressMenu": True},
            "rowSelection": "multiple",
            "rowMultiSelectWithClick": True,
            "pinnedBottomRowData": footer_rows,
            "onFirstDataRendered": sync_selection_js,
            "onRowDataUpdated": sync_selection_js,
        }
        if pre_selected_rows:
            grid_options["initialState"] = {"rowSelection": pre_selected_rows}

        df_cmp_urg_export = pd.concat([df_cmp_urg_body, pd.DataFrame(footer_rows)], ignore_index=True) if footer_rows else df_cmp_urg_body.copy()
        with st.container(key="medico_urg_actions_toolbar"):
            render_table_toolbar(df_cmp_urg_export, "performance_urg_medico.csv", "urg_table_medico")

        st.markdown('<div class="selection-master-table">', unsafe_allow_html=True)
        aggrid_response = render_saedas_aggrid(
            df_cmp_urg_body,
            grid_options=grid_options,
            key=f"urg_table_medico_{hash(str(current_selected_urgs))}",
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            incluir_total=bool(footer_rows),
        )
        st.markdown("</div>", unsafe_allow_html=True)

        selected_rows = aggrid_response.get("selected_rows", None)
        if selected_rows is not None and urg_field:
            if isinstance(selected_rows, pd.DataFrame):
                selected_rows = selected_rows.to_dict(orient="records")
            elif isinstance(selected_rows, dict):
                selected_rows = [selected_rows]
            new_selected_urgs = [row.get(urg_field) for row in selected_rows if row.get(urg_field) and row.get(urg_field) != "TOTAL"]
            
            # Proteção contra reset indesejado durante o remount do componente (key change)
            is_empty_on_remount = (not new_selected_urgs and current_selected_urgs and st.session_state.get("last_interaction_source") != "table")
            
            if not is_empty_on_remount and set(new_selected_urgs) != set(current_selected_urgs):
                st.session_state["global_urgs"] = new_selected_urgs
                st.session_state["pending_sidebar_urg_filter"] = new_selected_urgs
                st.session_state["last_interaction_source"] = "table"
                st.rerun()
    else:
        st.info("Dados insuficientes para gerar a tabela de performance por URG.")

    st.markdown("---")
    # --- PRIORIDADE 3: DETALHAMENTO TOP POR URG (ESCOLAS E ATENDIMENTOS) ---
    
    df_cmp_escola = render_top_por_urg(
        df_filt_no_escola[df_filt_no_escola["Ano"].isin(selected_years_comp)] if not df_filt_no_escola.empty else pd.DataFrame(),
        "Quantidade", 
        "Principais Escolas por URG", 
        "Escola", 
        table_key="escola_table_selection_medico",
        active_row_value=st.session_state.get("sidebar_escola_filter", []),
        selection_mode="multiple"
    )

    escolas_tabela_atual = st.session_state.get("escola_table_selection_medico__selected_values", [])
    current_sidebar_escolas = st.session_state.get("sidebar_escola_filter", [])
    last_source = st.session_state.get("last_interaction_source", "")
    if last_source != "sidebar" and set(map(str, escolas_tabela_atual)) != set(map(str, current_sidebar_escolas)):
        st.session_state["pending_sidebar_escola_filter"] = escolas_tabela_atual
        st.session_state["last_interaction_source"] = "table"
        st.rerun()
    elif last_source == "sidebar":
        st.session_state["last_interaction_source"] = ""


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




    st.markdown("---")
    st.subheader("Detalhamento por Aluno")
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
                
                # Renomear coluna Menu para Perfil para exibição
                df_aluno_final = df_aluno_final.rename(columns={"Menu": "Perfil"})
                preview_limit = 500
                df_aluno_head = df_aluno_final.head(preview_limit).reset_index(drop=True)

                # Aplicar design padrão (Zebra, Hover, etc)
                styled_aluno = (
                    df_aluno_head.style.pipe(apply_saedas_design, categoria_col="Aluno")
                    .set_properties(**{"text-align": "left"})
                    .hide(axis="index")
                )

                with st.container(key="medico_aluno_actions_toolbar"):
                    render_table_toolbar(df_aluno_head, "detalhes_alunos_medico.csv", "aluno_table_medico")

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
