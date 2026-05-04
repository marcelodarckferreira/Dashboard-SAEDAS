import json
import pandas as pd
import plotly.express as px
import streamlit as st
import datetime
from urllib.parse import urlencode

from components.footer_personal import footer_personal
from components.sidebar_filters import sidebar_filters
from app.utils.data_loader import load_csv
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from app.utils.page_helpers import (
    filter_by_sidebar_selections,
    build_comparativo_anual,
    get_selected_comparativo_value,
    render_top_por_urg,
    format_filters_applied,
    render_grouped_bar_anual,
    toggle_multiselect_value,
    render_section_divider,
    calcular_altura_aggrid,
    prepare_comparativo_aggrid_data,
    split_aggrid_footer,
    render_table_toolbar,
    render_saedas_aggrid
)
from app.utils.state_manager import init_global_state, sync_home_to_sidebar, sync_home_urg_to_sidebar
from app.utils.schemas import (
    SCHEMA_CONSULTA,
    SCHEMA_CONSULTA_ALUNO,
    SCHEMA_CONSULTA_ANO,
)
from app.utils.styles import apply_global_css, render_metric_cards, build_row_style_fn, get_table_hover_styles, apply_saedas_design


def carregar_dados_consulta():
    csv_file = "data/DashboardConsulta.csv"
    df, info = load_csv(csv_file, expected_cols=SCHEMA_CONSULTA)

    csv_file_aluno = "data/DashboardConsultaAluno.csv"
    df_aluno_raw, info_aluno = load_csv(
        csv_file_aluno, expected_cols=SCHEMA_CONSULTA_ALUNO
    )

    csv_file_ano = "data/DashboardConsultaAno.csv"
    df_ano, info_ano = load_csv(csv_file_ano, expected_cols=SCHEMA_CONSULTA_ANO)

    return {
        "principal": {"df": df, "info": info, "csv": csv_file},
        "aluno": {"df": df_aluno_raw, "info": info_aluno, "csv": csv_file_aluno},
        "ano": {"df": df_ano, "info": info_ano, "csv": csv_file_ano},
    }


def page_consulta():
    def toggle_regulacao(reg_name):
        current = st.session_state.get("consulta_encaminhamento_multiselect", [])
        st.session_state["consulta_encaminhamento_multiselect"] = (
            toggle_multiselect_value(current, reg_name)
        )

    # Inicializa o estado global sincronizado (Anos e URGs)
    init_global_state()

    st.title("Visão Geral do Encaminhamento (Regulação)")
    st.markdown(
        "Resumo consolidado das ações realizadas por ano, URG e equipe técnica."
    )
    filters_placeholder = st.empty()

    # apply_global_css() — Já injetado no app.py
    datasets = carregar_dados_consulta()

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
            "Consulta": "Encaminhamento",
            "Qtd": "Quantidade",
            "tipo": "Tipo",
        }
    )

    df_aluno = df_aluno_raw.rename(
        columns={
            "Consulta": "Encaminhamento",
            "tipo": "Tipo",
            "DtNasc": "DataNascimento",
        }
    ).copy()
    if not df_aluno.empty and "DataNascimento" in df_aluno.columns:
        df_aluno["DataNascimento"] = pd.to_datetime(
            df_aluno["DataNascimento"], errors="coerce"
        )

    df_ano_exibir = df_ano.copy() if not df_ano.empty else pd.DataFrame()

    st.sidebar.title("Filtros - Encaminhamentos")

    df_filt_sidebar, selections = sidebar_filters(
        df,
        {"ano": True, "urg": True, "escola": True, "tipo": True},
    )

    # --- SELETOR TEMPORAL MESTRE (INDICADORES E PÁGINA) ---
    current_year = datetime.datetime.now().year
    years_options = sorted([current_year - i for i in range(5)], reverse=True)
    
    st.segmented_control(
        label="Ano(s) de Referência:",
        options=years_options,
        selection_mode="multi",
        key="massive_year_selector",
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
        
    # 3. Filtro de URGs (Global - Vinculação Bidirecional)
    current_urgs = st.session_state["global_urgs"]
    # --- NOVO: Manter base sem filtro de encaminhamento para a tabela comparativa (Show context + Highlight) ---
    current_urgs = st.session_state["global_urgs"]
    if current_urgs:
        df_master_no_enc = df_base_final[df_base_final["URG"].isin(current_urgs)]
    else:
        df_master_no_enc = df_base_final.copy()

    encaminhamento_col = "Encaminhamento"
    encaminhamentos_disponiveis = (
        sorted(df_filt_sidebar[encaminhamento_col].dropna().unique())
        if encaminhamento_col in df_filt_sidebar.columns
        else []
    )
    
    # Filtro de Encaminhamento (Sincronizado entre Sidebar e Botões KPI)
    encaminhamentos_selecionados = st.sidebar.multiselect(
        "Selecione o(s) Encaminhamento(s):",
        options=encaminhamentos_disponiveis,
        placeholder="Todos",
        key="consulta_encaminhamento_multiselect"
    )

    # 4. Filtro de Encaminhamento (Aplicação Final para o restante do dashboard)
    if encaminhamentos_selecionados:
        df_master_filtrado = df_master_no_enc[df_master_no_enc["Encaminhamento"].isin(encaminhamentos_selecionados)]
    else:
        df_master_filtrado = df_master_no_enc.copy()

    # Substitui df_filt pelo filtrado final
    df_filt = df_master_filtrado.copy()
    
    # --- Definições para Gráficos 'Top por URG' ---
    # 1. Sem filtro de escola (para mostrar Top Escolas)
    df_filt_no_escola = df_base_final.copy()
    if current_urgs:
        df_filt_no_escola = df_filt_no_escola[df_filt_no_escola["URG"].isin(current_urgs)]
    
    # 2. Sem filtro de encaminhamento (para mostrar Top Encaminhamentos e Tabela Comparativa)
    df_filt_no_enc = df_master_no_enc.copy()
    
    # --- LÓGICA DE SELEÇÃO NAS TABELAS TOP ---
    # Escola
    selected_escola_from_table = None
    if "escola_table_selection_consulta" in st.session_state:
        selection = st.session_state["escola_table_selection_consulta"]
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

    # Encaminhamento removido da seleção por tabela (Filtro Global via Sidebar agora é o padrão)
    selected_encs_from_table = []

    if encaminhamentos_selecionados:
        df_filt = df_filt[df_filt["Encaminhamento"].isin(encaminhamentos_selecionados)]
        selections["encaminhamento"] = encaminhamentos_selecionados

    selections["encaminhamento"] = list(set(selections.get("encaminhamento", []) + encaminhamentos_selecionados)) or encaminhamentos_disponiveis

    # --- Geração do filtro_titulo Dinâmico (Data-Driven UI) ---
    def get_filter_display_string_for_title(selected_items_list, all_available_items_list):
        if not selected_items_list or (all_available_items_list and set(map(str, selected_items_list)) == set(map(str, all_available_items_list))):
            return "Todos"
        return ", ".join(map(str, sorted(list(set(selected_items_list)))))

    all_urgs_for_title = sorted(list(df["URG"].dropna().unique()))
    all_years_for_title = sorted(list(df["Ano"].dropna().unique())) if "Ano" in df.columns else []
    all_escolas_for_title = sorted(list(df["Escola"].dropna().unique()))
    all_encs_for_title = sorted(list(df["Encaminhamento"].dropna().unique()))
    
    current_urgs_for_title = st.session_state["global_urgs"] if st.session_state["global_urgs"] else all_urgs_for_title
    current_escolas_for_title = selections.get("escola", [])
    current_encs_for_title = encaminhamentos_selecionados if encaminhamentos_selecionados else all_encs_for_title
    
    anos_str = get_filter_display_string_for_title(selected_years_comp, all_years_for_title)
    urgs_str = get_filter_display_string_for_title(current_urgs_for_title, all_urgs_for_title)
    escolas_str = get_filter_display_string_for_title(current_escolas_for_title, all_escolas_for_title)
    encs_str = get_filter_display_string_for_title(current_encs_for_title, all_encs_for_title)
    
    filtro_titulo = f"Anos: {anos_str} / URGs: {urgs_str} / Escolas: {escolas_str} / Regulações: {encs_str}"

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
                ("encaminhamento", "Encaminhamento", "Regulação"),
            ],
        )
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Exportar dados")
    csv_export_encoding = "utf-8"
    csv = df_filt.to_csv(index=False, sep=";").encode(csv_export_encoding)
    st.sidebar.download_button(
        label="Exportar CSV (Consulta)",
        data=csv,
        file_name="dados_filtrados_consulta.csv",
        mime="text/csv",
    )
    
    # 1. Indicador principal (Total Geral)
    total_qtd = df_filt["Quantidade"].sum() if not df_filt.empty else 0
    render_metric_cards([{"label": "TOTAL DE ENCAMINHAMENTOS", "value": total_qtd}])
    
    render_section_divider()

    # Sumário por tipo de consulta (Encaminhamento) - IMUNIDADE AO FILTRO DE REGULAÇÃO
    # Usamos df_filt_no_enc para que todos os rótulos apareçam mesmo com filtros ativos
    encaminhamentos_sum = (
        df_filt_no_enc.groupby("Encaminhamento")["Quantidade"]
        .sum()
        .sort_values(ascending=False)
        if not df_filt_no_enc.empty and "Encaminhamento" in df_filt_no_enc.columns
        else pd.Series(dtype="float")
    )
    encaminhamentos_sum = encaminhamentos_sum[encaminhamentos_sum > 0]
    
    if not encaminhamentos_sum.empty:
        # Preparamos os itens para o novo render_metric_cards em modo toggle
        kpi_metrics = []
        for nome, valor in encaminhamentos_sum.items():
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
                active_labels=[l.upper() for l in encaminhamentos_selecionados],
                on_click_callback=toggle_regulacao
            )
            
        # NOTA: O render_metric_cards agora dispara o callback toggle_regulacao.
        # Isso restaura a interatividade premium com o design unificado.
    else:
        st.info("Selecione ao menos um ano para visualizar os indicadores.")
    
    render_section_divider()

    # --- PRIORIDADE 2 (MEIO): TABELA COMPARATIVA DE PERFORMANCE ---
    st.subheader("Performance por URG")
    st.caption("Nota: Clique em qualquer linha de URG para filtrar o restante do dashboard. Esta tabela é sensível apenas ao filtro de Ano.")

    # Callback para sincronizar seleção da tabela com o estado global
    def sync_urg_table_to_global_consulta():
        if "urg_table_selection_consulta" in st.session_state:
            selection = st.session_state["urg_table_selection_consulta"]
            rows = selection.get("selection", {}).get("rows", [])
            df_table = st.session_state.get("last_df_cmp_urg_consulta")
            
            if df_table is not None:
                selected_urgs = []
                for r in rows:
                    try:
                        urg_val = df_table.data.iloc[r][("URG", "")]
                        if urg_val and urg_val != "TOTAL":
                            selected_urgs.append(urg_val)
                    except: continue
                
                st.session_state["global_urgs"] = selected_urgs
                st.session_state["sidebar_urg_filter"] = selected_urgs
                st.session_state["last_interaction_source"] = "table"

    # Prepara DF para a tabela (Ignora filtros de URG, Escola e Encaminhamento - Sensível APENAS ao Ano)
    df_for_urg_table = df.copy()
    if selected_years_comp:
        df_for_urg_table = df_for_urg_table[df_for_urg_table["Ano"].isin(selected_years_comp)]
    
    # Nota: Não aplicamos filtro de Escola ou Encaminhamento aqui para garantir que todas as URGs apareçam na lista,
    # permitindo que a tabela funcione como um controlador mestre de navegação.

    current_selected_urgs = st.session_state.get("global_urgs", [])
    df_cmp_urg = build_comparativo_anual(
        df_for_urg_table, 
        "URG", 
        active_row_value=current_selected_urgs,
        pct_label="Cobertura"
    )
    
    # Salva o dataframe para o callback
    st.session_state["last_df_cmp_urg_consulta"] = df_cmp_urg

    if df_cmp_urg is not None:
        df_cmp_urg_aggrid, column_defs, column_map = prepare_comparativo_aggrid_data(df_cmp_urg)
        df_cmp_urg_body, footer_rows = split_aggrid_footer(df_cmp_urg_aggrid)

        urg_field = next((f for f, col in column_map.items() if col == "URG" or col == ("URG", "")), None)

        pre_selected_rows = []
        if urg_field and current_selected_urgs:
            pre_selected_rows = [idx for idx, val in enumerate(df_cmp_urg_body[urg_field].tolist()) if val in current_selected_urgs]

        # Sincronização JS para seleção mestre
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

        grid_height = calcular_altura_aggrid(df_cmp_urg_body, incluir_total=bool(footer_rows))

        # Barra de ferramentas
        df_cmp_urg_export = pd.concat([df_cmp_urg_body, pd.DataFrame(footer_rows)], ignore_index=True) if footer_rows else df_cmp_urg_body.copy()
        render_table_toolbar(df_cmp_urg_export, "performance_urg_consulta.csv", "urg_table_consulta")

        st.markdown('<div class="selection-master-table">', unsafe_allow_html=True)
        aggrid_response = render_saedas_aggrid(
            df_cmp_urg_body,
            grid_options=grid_options,
            key=f"urg_table_consulta_{hash(str(current_selected_urgs))}",
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            incluir_total=bool(footer_rows)
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Atualizar estado global com a seleção da tabela
        selected_rows = aggrid_response.get("selected_rows", None)
        if selected_rows is not None and urg_field:
            if isinstance(selected_rows, pd.DataFrame):
                selected_rows = selected_rows.to_dict(orient="records")
            elif isinstance(selected_rows, dict):
                selected_rows = [selected_rows]
            
            new_selected_urgs = [row.get(urg_field) for row in selected_rows if row.get(urg_field) and row.get(urg_field) != "TOTAL"]
            if set(new_selected_urgs) != set(current_selected_urgs):
                st.session_state["global_urgs"] = new_selected_urgs
                st.rerun()
    else:
        st.info("Dados insuficientes para gerar a tabela de performance.")
    
    # --- PRIORIDADE 3: DETALHAMENTO TOP POR URG (ESCOLAS E ENCAMINHAMENTOS) ---
    render_top_por_urg(
        df_filt[df_filt["Ano"].isin(selected_years_comp)] if not df_filt.empty else pd.DataFrame(), 
        "Quantidade", 
        "Principais Escolas por URG", 
        "Escola", 
        table_key="escola_table_selection_consulta",
        active_row_value=selected_escola_from_table
    )
    render_top_por_urg(
        df_filt[df_filt["Ano"].isin(selected_years_comp)] if not df_filt.empty else pd.DataFrame(), 
        "Quantidade", 
        "Principais Encaminhamentos por URG", 
        "Encaminhamento"
    )

    render_section_divider()

    # --- PRIORIDADE 3 (BASE): GRÁFICO DE DISTRIBUIÇÃO POR URG ---
    st.subheader("Comparativo Anual de Encaminhamentos por URG")
    render_grouped_bar_anual(df_filt, "Quantidade", "", orientation="h")
    render_section_divider()

    # --- DISTRIBUIÇÃO POR REGULAÇÃO (GRÁFICO AGRUPADO) ---
    st.subheader("Distribuição por Regulação")
    render_grouped_bar_anual(df_filt, "Quantidade", "", x_col="Encaminhamento", orientation="h")
    
    st.markdown("### Tabela Comparativa de Consultas por Ano")
    df_cmp_regulacao = build_comparativo_anual(df_filt, "Encaminhamento", pct_label="Cobertura")
    if df_cmp_regulacao is not None:
        df_reg_aggrid, reg_column_defs, _ = prepare_comparativo_aggrid_data(df_cmp_regulacao, include_selection_column=False)
        df_reg_body, reg_footer = split_aggrid_footer(df_reg_aggrid)
        
        reg_grid_options = {
            "columnDefs": reg_column_defs,
            "defaultColDef": {"resizable": True, "sortable": True, "filter": False, "suppressMenu": True},
            "pinnedBottomRowData": reg_footer,
        }
        reg_grid_height = calcular_altura_aggrid(df_reg_body, incluir_total=bool(reg_footer))

        # Barra de ferramentas
        df_reg_export = pd.concat([df_reg_body, pd.DataFrame(reg_footer)], ignore_index=True) if reg_footer else df_reg_body.copy()
        render_table_toolbar(df_reg_export, "comparativo_regulacao_consulta.csv", "reg_table_consulta")

        st.markdown('<div class="st-table-with-total">', unsafe_allow_html=True)
        render_saedas_aggrid(
            df_reg_body,
            grid_options=reg_grid_options,
            key="reg_table_consulta_aggrid",
            incluir_total=bool(reg_footer)
        )
        st.markdown('</div>', unsafe_allow_html=True)
        st.caption("Nota: As colunas '% Cobertura' representam o percentual de representatividade do Encaminhamento sobre o total realizado.")

    render_section_divider()
    st.subheader("Detalhamento por Aluno (ConsultaAluno)")
    if df_aluno.empty:
        st.info(
            "Dados de alunos não estão disponíveis ou houve erro na leitura do CSV."
        )
    else:
        # ── LÓGICA DE FILTRAGEM CRUZADA PARA O DETALHAMENTO ──
        # Utiliza o df_master_filtrado para respeitar os anos selecionados no seletor mestre
        df_aluno_base = filter_by_sidebar_selections(df_aluno, selections)
        df_aluno_base = df_aluno_base[df_aluno_base["Ano"].isin(selected_years_comp)] if not df_aluno_base.empty else pd.DataFrame()
        
        # Sincronizar com a seleção da tabela de escolas (se houver)
        if selected_escola_from_table:
            df_aluno_filtrado = df_aluno_base[df_aluno_base["Escola"] == selected_escola_from_table]
        else:
            df_aluno_filtrado = df_aluno_base.copy()

        # Filtro de encaminhamentos da sidebar (se houver)
        if encaminhamentos_selecionados and "Encaminhamento" in df_aluno_filtrado.columns:
            df_aluno_filtrado = df_aluno_filtrado[df_aluno_filtrado["Encaminhamento"].isin(encaminhamentos_selecionados)]

        # Determinar quais alunos exibir: aqueles que possuem registros com os encaminhamentos selecionados na TABELA
        if selected_encs_from_table:
            matching_ids = df_aluno_base[df_aluno_base["Encaminhamento"].isin(selected_encs_from_table)][["Aluno", "DataNascimento"]].drop_duplicates()
            df_aluno_filtrado = df_aluno_base.merge(matching_ids, on=["Aluno", "DataNascimento"])
        else:
            df_aluno_filtrado = df_aluno_filtrado # Mantém o que já foi filtrado por escola/sidebar

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
            + (" e de encaminhamento" if encaminhamentos_selecionados else "")
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

            df_aluno_para_exibir = df_aluno_filtrado.copy()
            if not df_aluno_para_exibir.empty:
                # 1. Obter atributos estáticos
                static_cols = ["Sexo", "URG", "Escola", "Serie", "Turma"]
                static_cols = [c for c in static_cols if c in df_aluno_para_exibir.columns]
                
                df_static = df_aluno_para_exibir.groupby(["Aluno", "DataNascimento"], as_index=False)[static_cols].last()
                
                # 2. Criar descrição textual formatada (substituindo Qtd por nomes das especialidades)
                def format_enc_list(group):
                    encs = sorted(group["Encaminhamento"].dropna().unique())
                    formatted_encs = []
                    for e in encs:
                        # Destaque se estiver na seleção da tabela ou da sidebar via UPPERCASE
                        is_selected = (selected_encs_from_table and e in selected_encs_from_table) or \
                                      (encaminhamentos_selecionados and e in encaminhamentos_selecionados)
                        if is_selected:
                            formatted_encs.append(e.upper())
                        else:
                            formatted_encs.append(e.lower().capitalize())
                    return ", ".join(formatted_encs)

                df_desc = df_aluno_para_exibir.groupby(["Aluno", "DataNascimento", "Ano"]).apply(format_enc_list).reset_index(name="Descricao")
                
                # 3. Pivotar os anos para colunas com a descrição textual
                df_pivot_ano = df_desc.pivot(index=["Aluno", "DataNascimento"], columns="Ano", values="Descricao").fillna("").reset_index()
                anos_cols = [c for c in df_pivot_ano.columns if c not in ["Aluno", "DataNascimento"]]
                
                # 4. Mesclar dados estáticos
                df_aluno_final = df_static.merge(df_pivot_ano, on=["Aluno", "DataNascimento"], how="left")
                
                # 5. Calcular Total (Qtd total de registros para o aluno)
                df_counts_total = df_aluno_para_exibir.groupby(["Aluno", "DataNascimento"]).size().reset_index(name="Total")
                df_aluno_final = df_aluno_final.merge(df_counts_total, on=["Aluno", "DataNascimento"], how="left")
                
                # 6. Formatação final
                for c in anos_cols:
                    df_aluno_final[c] = df_aluno_final[c].fillna("")
                
                if "Total" in df_aluno_final.columns:
                    df_aluno_final["Total"] = df_aluno_final["Total"].apply(lambda x: f"{int(x)}" if pd.notna(x) and x > 0 else "")
                
                # Link do Menu
                df_aluno_final["Menu"] = df_aluno_final.apply(build_perfil_link, axis=1)
                
                # Formatar Data de Nascimento
                if "DataNascimento" in df_aluno_final.columns:
                    df_aluno_final["DataNascimento"] = pd.to_datetime(
                        df_aluno_final["DataNascimento"], errors="coerce"
                    ).dt.strftime("%d/%m/%Y")
                    
                # Reordenar colunas
                col_order = ["Aluno", "DataNascimento", "Sexo", "URG", "Escola", "Serie", "Turma"]
                col_order = [c for c in col_order if c in df_aluno_final.columns] + anos_cols + ["Total", "Menu"]
                df_aluno_final = df_aluno_final[col_order].fillna("")
            else:
                df_aluno_final = pd.DataFrame()

            preview_limit = 500
            df_aluno_head = df_aluno_final.head(preview_limit).reset_index(drop=True)

            style_fn_aluno = build_row_style_fn("Aluno")
            hover_styles_aluno = get_table_hover_styles()

            if not df_aluno_head.empty:
                gb = GridOptionsBuilder.from_dataframe(df_aluno_head)
                gb.configure_default_column(resizable=True, sortable=True, filter=False, suppressMenu=True)
                gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=15)
                
                # Configura link de perfil via JsCode
                gb.configure_column(
                    "Menu",
                    headerName="Perfil",
                    cellRenderer=JsCode("""
                        function(params) {
                            if (!params.value) return '';
                            return '<a href="' + params.value + '" target="_self" style="text-decoration:none; color:#2e7d32; font-weight:bold;">📄 Ver Perfil</a>';
                        }
                    """),
                    width=100,
                    pinned="right"
                )

                # Adiciona índice numerado de 1 a N
                gb.configure_column(
                    "",
                    headerName="",
                    valueGetter="node.rowIndex + 1",
                    pinned="left",
                    width=60,
                    maxWidth=60,
                    lockPinned=True,
                    cellStyle={"textAlign": "center", "fontWeight": "bold"}
                )
                
                grid_options = gb.build()
                grid_height = calcular_altura_aggrid(df_aluno_head, limite_linhas=15)

                # Barra de ferramentas
                render_table_toolbar(df_aluno_head, "detalhes_alunos_consulta.csv", "aluno_table_consulta")

                st.markdown('<div class="st-table-with-total">', unsafe_allow_html=True)
                render_saedas_aggrid(
                    df_aluno_head,
                    grid_options=grid_options,
                    key="aluno_table_consulta_aggrid",
                    max_rows=15
                )
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Nenhum registro detalhado para exibir.")
            
            # Remover o download_button manual que existia no final
            if total_registros_aluno > preview_limit:
                st.info(
                    f"Exibindo apenas as primeiras {preview_limit} linhas de {total_registros_aluno}."
                )

    st.markdown(" ")
    footer_personal()
