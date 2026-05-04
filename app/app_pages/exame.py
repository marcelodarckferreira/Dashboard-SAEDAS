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
    render_grouped_bar_anual,
    toggle_multiselect_value,
)
from app.utils.state_manager import init_global_state, sync_home_to_sidebar, sync_home_urg_to_sidebar
from app.utils.schemas import SCHEMA_EXAME, SCHEMA_EXAME_ALUNO, SCHEMA_EXAME_ANO
from app.utils.styles import apply_global_css, render_metric_cards, apply_saedas_design, build_row_style_fn, get_table_hover_styles


def carregar_dados_exame():
    csv_file = "data/DashboardExame.csv"
    df, info = load_csv(csv_file, expected_cols=SCHEMA_EXAME)

    csv_file_aluno = "data/DashboardExameAluno.csv"
    df_aluno_raw, info_aluno = load_csv(
        csv_file_aluno, expected_cols=SCHEMA_EXAME_ALUNO
    )

    csv_file_ano = "data/DashboardExameAno.csv"
    df_ano, info_ano = load_csv(csv_file_ano, expected_cols=SCHEMA_EXAME_ANO)

    return {
        "principal": {"df": df, "info": info, "csv": csv_file},
        "aluno": {"df": df_aluno_raw, "info": info_aluno, "csv": csv_file_aluno},
        "ano": {"df": df_ano, "info": info_ano, "csv": csv_file_ano},
    }


def page_exame():
    # Inicializa o estado global sincronizado (Anos e URGs)
    init_global_state()

    # --- LÓGICA DE TOGGLE PARA REGULAÇÕES ---
    def toggle_regulacao(reg_name):
        current = st.session_state.get("exame_regulacao_multiselect", [])
        st.session_state["exame_regulacao_multiselect"] = (
            toggle_multiselect_value(current, reg_name)
        )

    st.title("Visão Geral dos Exames (Regulação)")
    st.markdown(
        "Resumo consolidado das ações realizadas por ano, URG e equipe técnica."
    )
    filters_placeholder = st.empty()
    # apply_global_css() — Já injetado no app.py

    datasets = carregar_dados_exame()

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
            "Exame": "Regulacao",
            "Qtd": "Quantidade",
            "Tipo": "Tipo",
        }
    )

    df_aluno = df_aluno_raw.rename(
        columns={
            "Exame": "Regulacao",
            "DtNasc": "DataNascimento",
        }
    ).copy()
    if not df_aluno.empty and "DataNascimento" in df_aluno.columns:
        df_aluno["DataNascimento"] = pd.to_datetime(
            df_aluno["DataNascimento"], errors="coerce"
        )

    df_ano_exibir = df_ano.copy() if not df_ano.empty else pd.DataFrame()

    st.sidebar.title("Filtros - Exames")

    df_filt_sidebar, selections = sidebar_filters(
        df,
        {"ano": True, "urg": True, "escola": True, "tipo": True},
    )

    regulacao_col = "Regulacao"
    regulacoes_disponiveis = (
        sorted(df_filt_sidebar[regulacao_col].dropna().unique())
        if regulacao_col in df_filt_sidebar.columns
        else []
    )
    regulacoes_selecionadas = st.sidebar.multiselect(
        "Selecione a(s) Regulação(ões):",
        options=regulacoes_disponiveis,
        placeholder="Todas",
        key="exame_regulacao_multiselect"
    )

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
        
    # --- NOVO: Manter base sem filtro de regulação para a tabela comparativa (Show context + Highlight) ---
    current_urgs = st.session_state["global_urgs"]
    if current_urgs:
        df_master_no_reg = df_base_final[df_base_final["URG"].isin(current_urgs)]
    else:
        df_master_no_reg = df_base_final.copy()

    # 4. Filtro de Regulação (Aplicação Final para o restante do dashboard)
    if regulacoes_selecionadas:
        df_master_filtrado = df_master_no_reg[df_master_no_reg[regulacao_col].isin(regulacoes_selecionadas)]
    else:
        df_master_filtrado = df_master_no_reg.copy()

    # Já definido acima na sidebar

    df_filt = (
        df_filt_sidebar[df_filt_sidebar[regulacao_col].isin(regulacoes_selecionadas)]
        if regulacoes_selecionadas and regulacao_col in df_filt_sidebar.columns
        else df_filt_sidebar
    )
    
    # Substitui df_filt pelo filtrado final
    df_filt = df_master_filtrado.copy()
    
    # --- Definições para Gráficos 'Top por URG' ---
    # 1. Sem filtro de escola (para mostrar Top Escolas)
    df_filt_no_escola = df_base_final.copy()
    if current_urgs:
        df_filt_no_escola = df_filt_no_escola[df_filt_no_escola["URG"].isin(current_urgs)]
    
    # 2. Sem filtro de regulação (para mostrar Top Regulações e Tabela Comparativa)
    df_filt_no_reg = df_master_no_reg.copy()
    
    # --- LÓGICA DE SELEÇÃO NAS TABELAS TOP ---
    # Escola
    selected_escola_from_table = None
    if "escola_table_selection_exame" in st.session_state:
        selection = st.session_state["escola_table_selection_exame"]
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

    # Regulação removida da seleção por tabela (Filtro Global via Sidebar agora é o padrão)
    selected_regs_from_table = []

    if regulacoes_selecionadas:
        df_filt = df_filt[df_filt["Regulacao"].isin(regulacoes_selecionadas)]
        selections["regulacao"] = regulacoes_selecionadas

    selections["regulacao"] = list(set(selections.get("regulacao", []) + regulacoes_selecionadas)) or regulacoes_disponiveis

    # --- Geração do filtro_titulo Dinâmico (Data-Driven UI) ---
    def get_filter_display_string_for_title(selected_items_list, all_available_items_list):
        if not selected_items_list or (all_available_items_list and set(map(str, selected_items_list)) == set(map(str, all_available_items_list))):
            return "Todos"
        return ", ".join(map(str, sorted(list(set(selected_items_list)))))

    all_urgs_for_title = sorted(list(df["URG"].dropna().unique()))
    all_years_for_title = sorted(list(df["Ano"].dropna().unique())) if "Ano" in df.columns else []
    all_escolas_for_title = sorted(list(df["Escola"].dropna().unique()))
    all_regs_for_title = sorted(list(df["Regulacao"].dropna().unique()))
    
    current_urgs_for_title = st.session_state["global_urgs"] if st.session_state["global_urgs"] else all_urgs_for_title
    current_escolas_for_title = selections.get("escola", [])
    current_regs_for_title = regulacoes_selecionadas if regulacoes_selecionadas else all_regs_for_title
    
    anos_str = get_filter_display_string_for_title(selected_years_comp, all_years_for_title)
    urgs_str = get_filter_display_string_for_title(current_urgs_for_title, all_urgs_for_title)
    escolas_str = get_filter_display_string_for_title(current_escolas_for_title, all_escolas_for_title)
    regs_str = get_filter_display_string_for_title(current_regs_for_title, all_regs_for_title)
    
    filtro_titulo = f"Anos: {anos_str} / URGs: {urgs_str} / Escolas: {escolas_str} / Regulações: {regs_str}"

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
                ("regulacao", "Regulacao", "Regulação"),
            ],
        )
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Exportar dados")
    csv_export_encoding = "utf-8"
    csv = df_filt.to_csv(index=False, sep=";").encode(csv_export_encoding)
    st.sidebar.download_button(
        label="Exportar CSV (Exame)",
        data=csv,
        file_name="dados_filtrados_exame.csv",
        mime="text/csv",
    )
    
    # 1. Indicador principal (Total Geral)
    total_qtd = df_filt["Quantidade"].sum() if not df_filt.empty else 0
    render_metric_cards([{"label": "TOTAL DE REGULAÇÕES (EXAMES)", "value": total_qtd}])
    
    render_section_divider()
    
    # Sumário por Regulação - IMUNIDADE AO FILTRO DE REGULAÇÃO
    regulacoes_sum = (
        df_filt_no_reg.groupby("Regulacao")["Quantidade"].sum().sort_values(ascending=False)
        if not df_filt_no_reg.empty and "Regulacao" in df_filt_no_reg.columns
        else pd.Series(dtype="float")
    )
    regulacoes_sum = regulacoes_sum[regulacoes_sum > 0]
    
    if not regulacoes_sum.empty:
        # Preparamos os itens para o render_metric_cards em modo toggle
        kpi_metrics = []
        for nome, valor in regulacoes_sum.items():
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
                active_labels=[l.upper() for l in regulacoes_selecionadas],
                on_click_callback=toggle_regulacao
            )
    else:
        st.info("Selecione ao menos um ano para visualizar os indicadores.")
    
    st.markdown("---")

    # --- PRIORIDADE 2 (MEIO): TABELA COMPARATIVA DE PERFORMANCE ---
    st.subheader("Performance por URG")
    st.caption("Nota: Clique em qualquer linha de URG para filtrar o restante do dashboard. Esta tabela é sensível apenas ao filtro de Ano.")

    # Callback para sincronizar seleção da tabela com o estado global
    def sync_urg_table_to_global_exame():
        if "urg_table_selection_exame" in st.session_state:
            selection = st.session_state["urg_table_selection_exame"]
            rows = selection.get("selection", {}).get("rows", [])
            df_table = st.session_state.get("last_df_cmp_urg_exame")
            
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

    # Prepara DF para a tabela (Ignora filtros de URG, Escola e Regulação - Sensível APENAS ao Ano)
    df_for_urg_table = df.copy()
    if selected_years_comp:
        df_for_urg_table = df_for_urg_table[df_for_urg_table["Ano"].isin(selected_years_comp)]
    
    # Nota: Não aplicamos filtro de Escola ou Regulação aqui para garantir que todas as URGs apareçam na lista,
    # permitindo que a tabela funcione como um controlador mestre de navegação.

    current_selected_urgs = st.session_state.get("global_urgs", [])
    df_cmp_urg = build_comparativo_anual(df_for_urg_table, "URG", active_row_value=current_selected_urgs)
    
    # Salva o dataframe para o callback
    st.session_state["last_df_cmp_urg_exame"] = df_cmp_urg

    if df_cmp_urg is not None:
        # Sincronização de Checkboxes (Paridade Sidebar -> Tabela)
        try:
            urg_col_values = df_cmp_urg.data[("URG", "")].tolist()
            target_indices = [i for i, val in enumerate(urg_col_values) if val in current_selected_urgs]
            
            current_table_selection = st.session_state.get("urg_table_selection_exame", {}).get("selection", {}).get("rows", [])
            if set(target_indices) != set(current_table_selection):
                st.session_state["urg_table_selection_exame"] = {"selection": {"rows": target_indices, "columns": []}}
        except Exception: pass

        with st.container():
            st.markdown('<div class="selection-master-table">', unsafe_allow_html=True)
            st.dataframe(
                apply_saedas_design(df_cmp_urg, "URG", current_selected_urgs),
                width="stretch",
                hide_index=True,
                on_select=sync_urg_table_to_global_exame,
                selection_mode="multi-row",
                key="urg_table_selection_exame"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Dados insuficientes para gerar a tabela de performance.")
    
    # --- PRIORIDADE 3: DETALHAMENTO TOP POR URG (ESCOLAS E EXAMES) ---
    render_top_por_urg(
        df_filt_no_escola[df_filt_no_escola["Ano"].isin(selected_years_comp)] if not df_filt_no_escola.empty else pd.DataFrame(), 
        "Quantidade", 
        "Principais Escolas por URG", 
        "Escola", 
        table_key="escola_table_selection_exame",
        active_row_value=selected_escola_from_table
    )
    render_top_por_urg(
        df_filt[df_filt["Ano"].isin(selected_years_comp)] if not df_filt.empty else pd.DataFrame(), 
        "Quantidade", 
        "Principais Exames por URG", 
        "Regulacao"
    )

    st.markdown("---")

    # --- PRIORIDADE 3 (BASE): GRÁFICO DE PERFORMANCE POR URG ---
    st.subheader("Comparativo Anual de Exames por URG")
    render_grouped_bar_anual(df_filt, "Quantidade", "", orientation="h")
    st.markdown("---")

    # --- DISTRIBUIÇÃO POR REGULAÇÃO (GRÁFICO AGRUPADO) ---
    st.subheader("Distribuição por Regulação")
    render_grouped_bar_anual(df_filt, "Quantidade", "", x_col="Regulacao", orientation="h")
    
    st.markdown("### Tabela Comparativa de Exames por Ano")
    df_cmp_regulacao = build_comparativo_anual(df_filt, "Regulacao")
    if df_cmp_regulacao is not None:
        with st.container():
            st.markdown('<div class="st-table-with-total">', unsafe_allow_html=True)
            st.dataframe(df_cmp_regulacao, width="stretch", hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.caption("Nota: As colunas '% Total' representam o percentual de representatividade da Regulação sobre o total realizado no respectivo ano.")



    st.markdown("---")
    st.subheader("Detalhamento por Aluno (ExameAluno)")
    if df_aluno.empty:
        st.info(
            "Dados de alunos não estão disponíveis ou houve erro na leitura do CSV."
        )
    else:
        # ── LÓGICA DE FILTRAGEM CRUZADA PARA O DETALHAMENTO ──
        # Utiliza o contexto filtrado pelo seletor mestre de anos
        df_aluno_base = filter_by_sidebar_selections(df_aluno, selections)
        df_aluno_base = df_aluno_base[df_aluno_base["Ano"].isin(selected_years_comp)] if not df_aluno_base.empty else pd.DataFrame()
        
        # Filtro de regulação da sidebar (se houver)
        if regulacoes_selecionadas and "Regulacao" in df_aluno_base.columns:
            df_aluno_base = df_aluno_base[df_aluno_base["Regulacao"].isin(regulacoes_selecionadas)]

        # Determinar quais alunos exibir: aqueles que possuem registros com as regulações selecionadas na TABELA
        if selected_regs_from_table:
            matching_ids = df_aluno_base[df_aluno_base["Regulacao"].isin(selected_regs_from_table)][["Aluno", "DataNascimento"]].drop_duplicates()
            df_aluno_filtrado = df_aluno_base.merge(matching_ids, on=["Aluno", "DataNascimento"])
        else:
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
            + (" e de regulação" if regulacoes_selecionadas else "")
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
                
                # 2. Criar descrição textual formatada (substituindo Qtd por nomes das regulações)
                def format_reg_list(group):
                    regs = sorted(group["Regulacao"].dropna().unique())
                    formatted_regs = []
                    for r in regs:
                        # Destaque se estiver na seleção da tabela ou da sidebar via UPPERCASE
                        is_selected = (selected_regs_from_table and r in selected_regs_from_table) or \
                                      (regulacoes_selecionadas and r in regulacoes_selecionadas)
                        if is_selected:
                            formatted_regs.append(r.upper())
                        else:
                            formatted_regs.append(r.lower().capitalize())
                    return ", ".join(formatted_regs)

                df_desc = df_aluno_para_exibir.groupby(["Aluno", "DataNascimento", "Ano"]).apply(format_reg_list).reset_index(name="Descricao")
                
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

            styled_aluno = (
                df_aluno_head.style
                .apply(style_fn_aluno, axis=1)
                .set_properties(**{"text-align": "left"})
                .set_table_styles(hover_styles_aluno)
                .hide(axis="index")
            )

            st.dataframe(
                styled_aluno,
                width="stretch",
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
                label="Exportar CSV (Exame por aluno)",
                data=csv_aluno,
                file_name="dados_filtrados_exame_aluno.csv",
                mime="text/csv",
            )

    st.markdown(" ")
    footer_personal()
