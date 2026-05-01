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
    get_native_regulacao_button_type,
    get_selected_comparativo_value,
    render_metric,
    render_top_por_urg,
    format_filters_applied,
    render_grouped_bar_anual,
    should_use_native_regulacao_button,
    toggle_multiselect_value,
)
from app.utils.state_manager import init_global_state, sync_home_to_sidebar, sync_home_urg_to_sidebar
from app.utils.schemas import (
    SCHEMA_CONSULTA,
    SCHEMA_CONSULTA_ALUNO,
    SCHEMA_CONSULTA_ANO,
)
from app.utils.styles import apply_global_css, render_metric_cards, style_urg_performance_table


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
    # --- LÓGICA DE TOGGLE PARA REGULAÇÕES ---
    def toggle_regulacao(reg_name):
        current = st.session_state.get("consulta_encaminhamento_multiselect", [])
        st.session_state["consulta_encaminhamento_multiselect"] = (
            toggle_multiselect_value(current, reg_name)
        )

    st.markdown(
        """
        <style>
            .consulta-metric-card {
                background: linear-gradient(135deg, #0f172a, #1f2937);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                padding: 12px 14px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.18);
                color: #e5e7eb;
                display: flex;
                flex-direction: column;
                gap: 4px;
                height: 100%;
                transition: all 0.3s ease;
                position: relative;
                z-index: 1;
                pointer-events: none !important; /* Permite que o clique passe para o botão */
            }

            .consulta-metric-card-active {
                border: 1px solid #3b82f6 !important;
                background: linear-gradient(135deg, #1e3a8a, #0f172a) !important;
                box-shadow: 0 0 15px rgba(59, 130, 246, 0.3) !important;
            }

            .consulta-metric-label {
                font-size: 0.8rem;
                letter-spacing: 0.02em;
                color: #cbd5e1;
                pointer-events: none !important;
            }

            .consulta-metric-value {
                font-size: 1.6rem;
                font-weight: 700;
                color: #f8fafc;
                line-height: 1.2;
                pointer-events: none !important;
            }

            /* Overlay do botão invisível */
            [data-testid="column"],
            [data-testid="stColumn"] {
                position: relative !important;
            }
            
            [data-testid="stButton"]:has(button[kind="secondary"]) {
                position: absolute !important;
                inset: 0 !important;
                width: 100% !important;
                height: 100% !important;
                z-index: 200 !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            
            [data-testid="stButton"] button[kind="secondary"] {
                position: absolute !important;
                inset: 0 !important;
                width: 100% !important;
                height: 100% !important;
                background-color: transparent !important;
                border: none !important;
                color: transparent !important;
                opacity: 0 !important;
                cursor: pointer !important;
                z-index: 201 !important;
                pointer-events: auto !important;
            }

            /* =========================================================
               Streamlit Native Button as KPI Card
               Ajustado para o desenho enviado: menos espaço interno e texto à esquerda
               ========================================================= */

            /* Botão/Card */
            [data-testid="stButton"] button[kind="primary"],
            [data-testid="stButton"] button[kind="tertiary"] {
                width: 100% !important;
                height: 101px !important;
                min-height: 101px !important;
                border-radius: 13px !important;

                /* Reduz o espaço interno do card */
                padding: 0 !important;

                display: flex !important;
                flex-direction: column !important;
                align-items: flex-start !important;
                justify-content: center !important;

                /* Espaço entre o título e o número */
                gap: 10px !important;

                text-align: left !important;
                line-height: 1 !important;
                overflow: hidden !important;
                color: #f8fafc !important;
                background: #172238 !important;
                box-shadow: 0 4px 18px rgba(0, 0, 0, 0.22) !important;
                transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease, background 0.2s ease !important;
            }

            /* Remove aparência nativa de foco do Streamlit */
            [data-testid="stButton"] button[kind="primary"]:focus,
            [data-testid="stButton"] button[kind="tertiary"]:focus,
            [data-testid="stButton"] button[kind="primary"]:focus-visible,
            [data-testid="stButton"] button[kind="tertiary"]:focus-visible {
                outline: none !important;
            }

            /* Força todos os elementos internos para a esquerda */
            [data-testid="stButton"] button[kind="primary"] *,
            [data-testid="stButton"] button[kind="tertiary"] * {
                text-align: left !important;
                align-self: flex-start !important;
            }

            /* Texto/Título: DENTISTA */
            [data-testid="stButton"] button[kind="primary"] p,
            [data-testid="stButton"] button[kind="tertiary"] p {
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                color: #dbeafe !important;
                font-size: 0.78rem !important;
                font-weight: 600 !important;
                letter-spacing: 0.055em !important;
                line-height: 1.05 !important;
                text-transform: uppercase !important;
                pointer-events: none !important;
            }

            /* Valor: 1.007 */
            [data-testid="stButton"] button[kind="primary"] strong,
            [data-testid="stButton"] button[kind="tertiary"] strong {
                display: block !important;
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                color: #ffffff !important;
                font-size: 1.72rem !important;
                font-weight: 800 !important;
                line-height: 1 !important;
                letter-spacing: -0.04em !important;
                text-align: left !important;
                pointer-events: none !important;
            }

            /* Estado ATIVO */
            [data-testid="stButton"] button[kind="primary"] {
                border: 1px solid #3b82f6 !important;
                background: linear-gradient(135deg, #1e3a8a, #0f172a) !important;
                box-shadow: 0 0 15px rgba(59, 130, 246, 0.4) !important;
            }

            /* Estado INATIVO */
            [data-testid="stButton"] button[kind="tertiary"] {
                border: 1px solid rgba(148, 163, 184, 0.16) !important;
                background: #172238 !important;
                box-shadow: 0 4px 18px rgba(0, 0, 0, 0.22) !important;
            }

            /* Hover discreto */
            [data-testid="stButton"] button[kind="primary"]:hover,
            [data-testid="stButton"] button[kind="tertiary"]:hover {
                transform: translateY(-1px) !important;
                border-color: rgba(96, 165, 250, 0.55) !important;
                background: #1a2942 !important;
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.26) !important;
            }

            /* Clique */
            [data-testid="stButton"] button[kind="primary"]:active,
            [data-testid="stButton"] button[kind="tertiary"]:active {
                transform: translateY(0) !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Inicializa o estado global sincronizado (Anos e URGs)
    init_global_state()

    st.title("Visão Geral do Encaminhamento (Regulação)")
    st.markdown(
        "Resumo consolidado das ações realizadas por ano, URG e equipe técnica."
    )
    filters_placeholder = st.empty()

    apply_global_css()
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
        default=[],
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
    render_metric("TOTAL DE ENCAMINHAMENTOS", total_qtd)
    st.markdown(" ")

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
        # Preparamos os itens de encaminhamento (nome, valor, is_active)
        for start in range(0, len(encaminhamentos_sum), 5):
            slice_enc = encaminhamentos_sum.iloc[start : start + 5]
            cols = st.columns(5)
            for col, (nome, valor) in zip(cols, slice_enc.items()):
                nome_str = str(nome)
                # Verifica se está ativo no filtro da sidebar
                is_active = nome_str in encaminhamentos_selecionados
                card_class = "consulta-metric-card consulta-metric-card-active" if is_active else "consulta-metric-card"
                valor_fmt = f"{int(valor):,}".replace(",", ".")

                with col:
                    if should_use_native_regulacao_button(nome_str):
                        st.button(
                            f"{nome_str.upper()}\n\n**{valor_fmt}**",
                            key=f"btn_reg_{nome_str}",
                            on_click=toggle_regulacao,
                            args=(nome_str,),
                            help=f"Marcar/desmarcar {nome_str.upper()} no filtro de regulação",
                            type=get_native_regulacao_button_type(
                                nome_str, encaminhamentos_selecionados
                            ),
                            use_container_width=True,
                        )
                        continue

                    st.button(
                        f"Alternar regulação {nome_str}",
                        key=f"btn_reg_{nome_str}",
                        on_click=toggle_regulacao,
                        args=(nome_str,),
                        help=f"Marcar/desmarcar {nome_str.upper()} no filtro de regulação",
                    )

                    st.markdown(
                        f'<div class="{card_class}">'
                        f'<div class="consulta-metric-label">{nome_str.upper()}</div>'
                        f'<div class="consulta-metric-value">{valor_fmt}</div>'
                        "</div>",
                        unsafe_allow_html=True
                    )
    else:
        st.info("Selecione ao menos um ano para visualizar os indicadores.")
    
    st.markdown("---")

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
    df_cmp_urg = build_comparativo_anual(df_for_urg_table, "URG", active_row_value=current_selected_urgs)
    
    # Salva o dataframe para o callback
    st.session_state["last_df_cmp_urg_consulta"] = df_cmp_urg

    if df_cmp_urg is not None:
        # Sincronização de Checkboxes (Paridade Sidebar -> Tabela)
        try:
            urg_col_values = df_cmp_urg.data[("URG", "")].tolist()
            target_indices = [i for i, val in enumerate(urg_col_values) if val in current_selected_urgs]
            
            current_table_selection = st.session_state.get("urg_table_selection_consulta", {}).get("selection", {}).get("rows", [])
            if set(target_indices) != set(current_table_selection):
                st.session_state["urg_table_selection_consulta"] = {"selection": {"rows": target_indices, "columns": []}}
        except Exception: pass

        st.dataframe(
            style_urg_performance_table(df_cmp_urg, current_selected_urgs),
            use_container_width=True,
            hide_index=True,
            on_select=sync_urg_table_to_global_consulta,
            selection_mode="multi-row",
            key="urg_table_selection_consulta"
        )
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

    st.markdown("---")

    # --- PRIORIDADE 3 (BASE): GRÁFICO DE DISTRIBUIÇÃO POR URG ---
    st.subheader("Comparativo Anual de Encaminhamentos por URG")
    render_grouped_bar_anual(df_filt, "Quantidade", "", orientation="h")
    st.markdown("---")

    # --- DISTRIBUIÇÃO POR REGULAÇÃO (GRÁFICO AGRUPADO) ---
    st.subheader("Distribuição por Regulação")
    render_grouped_bar_anual(df_filt, "Quantidade", "", x_col="Encaminhamento", orientation="h")
    
    st.markdown("### Tabela Comparativa de Consultas por Ano")
    df_cmp_regulacao = build_comparativo_anual(df_filt, "Encaminhamento")
    if df_cmp_regulacao is not None:
        st.dataframe(df_cmp_regulacao, use_container_width=True, hide_index=True)
        st.caption("Nota: As colunas '% Total' representam o percentual de representatividade do Encaminhamento sobre o total realizado.")

    st.markdown("---")
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
                label="Exportar CSV (Consulta por aluno)",
                data=csv_aluno,
                file_name="dados_filtrados_consulta_aluno.csv",
                mime="text/csv",
            )

    st.markdown(" ")
    footer_personal()
