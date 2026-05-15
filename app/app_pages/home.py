import json
import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
from components.footer_personal import footer_personal
from components.sidebar_filters import sidebar_filters
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from app.utils.page_helpers import (
    format_filters_applied, 
    build_comparativo_anual,
    calcular_altura_aggrid,
    prepare_comparativo_aggrid_data,
    split_aggrid_footer,
    render_table_toolbar,
    render_saedas_aggrid
)
from app.utils.state_manager import (
    apply_pending_table_filters,
    init_global_state,
    sync_home_to_sidebar,
)
from app.utils.data_loader import load_csv
from app.utils.schemas import (
    SCHEMA_HOME,
    SCHEMA_HOME_ANO,
    SCHEMA_HOME_ESCOLA_ANO,
    SCHEMA_HOME_URG_ANO,
)
from app.utils.styles import apply_global_css, apply_saedas_design, render_metric_cards

AUTO_ID_COLUMN = "::auto_unique_id::"

EXCLUDED_EXPORT_COLUMNS = [AUTO_ID_COLUMN]


def carregar_dados_home():
    """Carrega todos os 4 datasets da Home com tratamento de erros."""
    csv_file = "data/DashboardHome.csv"
    df, info = load_csv(csv_file, expected_cols=SCHEMA_HOME)

    csv_file_escola_ano = "data/DashboardHomeEscolaAno.csv"
    df_escola_ano, info_escola_ano = load_csv(
        csv_file_escola_ano, expected_cols=SCHEMA_HOME_ESCOLA_ANO
    )

    csv_file_home_ano = "data/DashboardHomeAno.csv"
    df_home_ano, info_home_ano = load_csv(
        csv_file_home_ano, expected_cols=SCHEMA_HOME_ANO
    )

    csv_file_urg_ano = "data/DashboardHomeURGAno.csv"
    df_urg_ano, info_urg_ano = load_csv(
        csv_file_urg_ano, expected_cols=SCHEMA_HOME_URG_ANO
    )

    return {
        "home": {"df": df, "info": info, "csv": csv_file},
        "escola_ano": {
            "df": df_escola_ano,
            "info": info_escola_ano,
            "csv": csv_file_escola_ano,
        },
        "home_ano": {
            "df": df_home_ano,
            "info": info_home_ano,
            "csv": csv_file_home_ano,
        },
        "urg_ano": {"df": df_urg_ano, "info": info_urg_ano, "csv": csv_file_urg_ano},
    }


def page_home():
    # Inicializa o estado global sincronizado (Anos e URGs)
    init_global_state()

    st.title("Visão Geral do SAEDAS")
    
    # Injeta CSS Global
    apply_global_css()

    # --- UNIFICAÇÃO DE ESTILOS (Design System Centralizado) ---
    st.markdown(
        """
        <style>
            /* 1. Cabeçalhos e Tipografia Global */
            h3 {
                color: #f1f5f9 !important;
                font-weight: 800 !important;
                margin-bottom: 1.5rem !important;
                letter-spacing: -0.02em !important;
            }


            /* 3. KPI Cards (Design Premium com Borda Iluminada) */
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
            .home-metric-link {
                background-image: linear-gradient(#0f172a, #0f172a), linear-gradient(135deg, #38bdf8 0%, #1e40af 100%) !important;
                cursor: pointer !important;
            }
            .home-metric-link:hover {
                transform: translateY(-3px) !important;
                background-image: linear-gradient(#0f172a, #0f172a), linear-gradient(135deg, #7dd3fc 0%, #3b82f6 100%) !important;
                box-shadow: 0 0 20px rgba(56, 189, 248, 0.3), 0 10px 25px rgba(0, 0, 0, 0.5) !important;
            }
            .home-metric-label {
                position: relative !important; z-index: 5 !important;
                font-size: 0.78rem !important;
                font-weight: 700 !important;
                color: #94a3b8 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.05em !important;
                margin-bottom: 4px !important;
            }
            .home-metric-value {
                position: relative !important; z-index: 5 !important;
                font-size: 1.85rem !important;
                font-weight: 800 !important;
                color: #f1f5f9 !important;
                line-height: 1.1 !important;
            }

            /* 5. Painel de Configuração de Colunas */
            .home-columns-panel-title { font-size: 0.72rem; font-weight: 700; color: #cbd5e1; text-transform: uppercase; }
            .home-columns-panel-subtitle { font-size: 0.7rem; color: #94a3b8; }
            .st-key-home_columns_panel div[data-testid="stVerticalBlockBorderWrapper"] { padding: 4px 6px !important; border-radius: 6px !important; }
            
            /* 6. Legendas das Tabelas */
            .home-legend-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(280px, 1fr));
                column-gap: 24px; row-gap: 6px; margin-top: 8px;
            }
            .home-legend-item { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: #94a3b8; }

            /* 7. Estado Ativo do Toggle de Colunas */
            .column-toggle-active button {
                background: #1e3a5f !important;
                color: #60a5fa !important;
                border-color: #38bdf8 !important;
            }

            /* 8. Resets de Link e Remoção de Sublinhados (KPI Cards) */
            div[data-testid="stMarkdownContainer"] a.home-metric-link-wrapper,
            div[data-testid="stMarkdownContainer"] a.home-metric-link-wrapper * {
                text-decoration: none !important;
                border-bottom: none !important;
                display: block !important;
                height: 100%;
            }
            a.home-metric-link-wrapper:hover, 
            a.home-metric-link-wrapper:hover * {
                text-decoration: none !important;
                border-bottom: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "Resumo consolidado das ações realizadas por ano, URG e equipe técnica."
    )
    filters_placeholder = st.empty()

    st.markdown("---")

    datasets = carregar_dados_home()

    home_data = datasets["home"]
    csv_file = home_data["csv"]
    df, info = home_data["df"], home_data["info"]

    escola_ano_data = datasets["escola_ano"]
    csv_file_escola_ano = escola_ano_data["csv"]
    df_escola_ano, info_escola_ano = (
        escola_ano_data["df"],
        escola_ano_data["info"],
    )

    home_ano_data = datasets["home_ano"]
    csv_file_home_ano = home_ano_data["csv"]
    df_home_ano, info_home_ano = (
        home_ano_data["df"],
        home_ano_data["info"],
    )

    urg_ano_data = datasets["urg_ano"]
    csv_file_urg_ano = urg_ano_data["csv"]
    df_urg_ano, info_urg_ano = (
        urg_ano_data["df"],
        urg_ano_data["info"],
    )

    if info["erros"]:
        st.error("; ".join(info["erros"]))

        footer_personal()

        return

    if info["alertas"]:
        st.warning("; ".join(info["alertas"]))

    if info_escola_ano["erros"]:
        st.warning(
            f"Falha ao ler '{csv_file_escola_ano}': "
            + "; ".join(info_escola_ano["erros"])
        )

        df_escola_ano = pd.DataFrame()

    elif info_escola_ano["alertas"]:
        st.info("; ".join(info_escola_ano["alertas"]))

    if info_home_ano["erros"]:
        st.warning(
            f"Falha ao ler '{csv_file_home_ano}': " + "; ".join(info_home_ano["erros"])
        )

        df_home_ano = pd.DataFrame()

    elif info_home_ano["alertas"]:
        st.info("; ".join(info_home_ano["alertas"]))

    if info_urg_ano["erros"]:
        st.warning(
            f"Falha ao ler '{csv_file_urg_ano}': " + "; ".join(info_urg_ano["erros"])
        )

        df_urg_ano = pd.DataFrame()

    elif info_urg_ano["alertas"]:
        st.info("; ".join(info_urg_ano["alertas"]))

    if df.empty:
        st.warning(f"O arquivo '{csv_file}' está vazio ou não contém dados.")

        footer_personal()

        return


    # --- Filtros na Sidebar ---
    home_filter_config = {"ano": True, "urg": True, "escola": True, "tipo": False}

    apply_pending_table_filters()

    df_filtrado, selections = sidebar_filters(df, home_filter_config)
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
    # Usamos o DF base para garantir que as seleções cross-page/cross-component sejam respeitadas integralmente
    df_base_final = df.copy()
    
    # 1. Filtro de Escola (Cascata da Sidebar)
    # Nota: selections['escola'] já reflete o filtro de escola aplicado.
    if selections.get("escola"):
        # Se 'Todas as Escolas' não for o estado (sidebar_filters lida com isso retornando todas)
        # Verificamos se a lista retornada é diferente da lista total de escolas no df original
        all_schools = set(df["Escola"].dropna().unique())
        selected_schools = set(selections["escola"])
        if selected_schools != all_schools:
            df_base_final = df_base_final[df_base_final["Escola"].isin(selections["escola"])]
            
    # 2. Filtro de Anos (Global - Centralizado no State Manager)
    if selected_years_comp:
        df_base_final = df_base_final[df_base_final["Ano"].isin(selected_years_comp)]
    else:
        # Se nenhum ano selecionado, o dashboard fica vazio por padrão
        df_base_final = df_base_final.iloc[0:0]
        
    # 3. Filtro de URGs (Global - Vinculação Bidirecional Tabela/Sidebar)
    current_urgs = st.session_state["global_urgs"]
    if current_urgs:
        df_master_filtrado = df_base_final[df_base_final["URG"].isin(current_urgs)]
        if len(current_urgs) == 1:
            st.info(f"📍 Filtrando por URG selecionada: **{current_urgs[0]}**")
        else:
            st.info(f"📍 Filtrando por conjunto de URGs: **{', '.join(current_urgs)}**")
    else:
        # Se vazio (Todos), mantém o df base (já filtrado por escola e ano)
        df_master_filtrado = df_base_final.copy()

    # --- Geração do filtro_titulo Dinâmico (Data-Driven UI) ---
    def get_filter_display_string_for_title(selected_items_list, all_available_items_list):
        if not selected_items_list or (all_available_items_list and set(map(str, selected_items_list)) == set(map(str, all_available_items_list))):
            return "Todos"
        return ", ".join(map(str, sorted(list(set(selected_items_list)))))

    all_urgs_for_title = sorted(list(df["URG"].dropna().unique()))
    all_years_for_title = sorted(list(df["Ano"].dropna().unique())) if "Ano" in df.columns else []
    all_escolas_for_title = sorted(list(df["Escola"].dropna().unique()))
    
    # Se global_urgs for vazio, significa 'Todas'
    current_urgs_for_title = st.session_state["global_urgs"] if st.session_state["global_urgs"] else all_urgs_for_title
    current_escolas_for_title = selections.get("escola", [])
    
    anos_str = get_filter_display_string_for_title(selected_years_comp, all_years_for_title)
    urgs_str = get_filter_display_string_for_title(current_urgs_for_title, all_urgs_for_title)
    escolas_str = get_filter_display_string_for_title(current_escolas_for_title, all_escolas_for_title)
    
    filtro_titulo = f"Anos: {anos_str} / URGs: {urgs_str} / Escolas: {escolas_str}"

    st.markdown(f"### Indicadores Gerais ({filtro_titulo})")


    # --- Filtros aplicados Breadcrumb ---
    filters_placeholder.markdown(
        "**Filtros aplicados:** "
        + format_filters_applied(
            selections,
            df,
            [
                ("ano", "Ano", "Ano"),
                ("urg", "URG", "URG"),
                ("escola", "Escola", "Escola"),
            ],
        )
    )


    # Preparamos o df para a Tabela de Performance (IMUNIDADE AO FILTRO DE UNIDADE)
    # Ignora filtros de URG e Escola para que todas as linhas apareçam, reagindo APENAS ao Ano.
    df_for_performance_table = df.copy()
    if selected_years_comp:
        df_for_performance_table = df_for_performance_table[df_for_performance_table["Ano"].isin(selected_years_comp)]

    st.caption("Nota: Clique em qualquer linha de URG (na tabela de Performance por URG abaixo) para filtrar o restante do dashboard. Clique novamente para remover o filtro.")

    # --- PRIORIDADE 1 (TOPO): MÉTRICAS (Sempre Visíveis na Home) ---
    if not df_master_filtrado.empty:
        total_alunos_escola = df_master_filtrado["QtdAlunoEscola"].sum()
        total_alunos = df_master_filtrado["QtdAluno"].sum()
        
        # Especialidades individuais
        total_professor = df_master_filtrado["QtdProfessor"].sum()
        total_psicologo = df_master_filtrado["QtdPsicologo"].sum()
        total_assist_social = df_master_filtrado["QtdAssistSocial"].sum()
        total_enfermagem = df_master_filtrado["QtdEnfermagem"].sum()
        total_medico = df_master_filtrado["QtdMedico"].sum()
        
        # Atendimentos Profissionais
        total_atendimentos_profissionais = (total_professor + total_psicologo + total_assist_social + total_enfermagem + total_medico)
        
        total_vacinacao_alunos = df_master_filtrado["QtdVacinacao"].sum()
        total_doses_vacina = df_master_filtrado["QtdVacina"].sum()
        total_exames = df_master_filtrado["QtdExame"].sum()
        total_encaminhamentos = df_master_filtrado["QtdEncaminhamento"].sum()
    else:
        total_alunos_escola = 0
        total_alunos = 0
        total_professor = 0
        total_psicologo = 0
        total_assist_social = 0
        total_enfermagem = 0
        total_medico = 0
        total_atendimentos_profissionais = 0
        total_vacinacao_alunos = 0
        total_doses_vacina = 0
        total_exames = 0
        total_encaminhamentos = 0


    primary_metrics = [
        ("TOTAL DE ALUNOS", total_alunos_escola),
        ("ALUNOS ATENDIDOS", total_alunos),
        ("ATENDIMENTOS", total_atendimentos_profissionais),
    ]
    professional_metrics = [
        ("ATEND. PROFESSOR", total_professor),
        ("ATEND. PSICÓLOGO", total_psicologo),
        ("ATEND. ASSIST. SOCIAL", total_assist_social),
        ("ATEND. ENFERMAGEM", total_enfermagem),
        ("ATEND. MÉDICO", total_medico),
    ]
    service_metrics = [
        ("ENCAMINHAMENTOS", total_encaminhamentos),
        ("EXAMES", total_exames),
        ("VACINADOS/APLICAÇÃO", f"{total_vacinacao_alunos}/{total_doses_vacina}"),
    ]

    # Mapeamento de labels para nomes de menu
    label_to_menu = {
        "ENCAMINHAMENTOS": "Encaminhamentos",
        "EXAMES": "Exames",
        "VACINADOS/APLICAÇÃO": "Vacinação",
        "ATEND. MÉDICO": "Médico",
        "ATEND. PROFESSOR": "Professor",
        "ATEND. PSICÓLOGO": "Psicólogo",
        "ATEND. ASSIST. SOCIAL": "Assistente Social",
        "ATEND. ENFERMAGEM": "Enfermagem",
    }

    def prepare_metrics(raw_metrics):
        return [
            {
                "label": label,
                "value": value,
                "link": f"/?menu={label_to_menu[label]}" if label in label_to_menu else None
            }
            for label, value in raw_metrics
        ]

    render_metric_cards(prepare_metrics(primary_metrics))
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    render_metric_cards(prepare_metrics(professional_metrics))
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    render_metric_cards(prepare_metrics(service_metrics))
    
    st.markdown(" ")
    st.markdown("---")

    # --- NOVO: Tabela Comparativa de Performance por ANO ---
    st.subheader(f"Tabela Comparativa de Performance por ANO ({filtro_titulo})")
    st.caption("Nota: As colunas '% Cobertura' representam o percentual de cada indicador sobre o TOTAL DE ALUNOS no respectivo ano.")

    # Definição das métricas na ordem exata dos cards (rótulos)
    metric_definitions = [
        {"key": "QtdAlunoEscola", "label": "TOTAL DE ALUNOS"},
        {"key": "QtdAluno", "label": "ALUNOS ATENDIDOS"},
        {"key": "total_profissionais", "label": "ATENDIMENTOS"},
        {"key": "QtdProfessor", "label": "ATEND. PROFESSOR"},
        {"key": "QtdPsicologo", "label": "ATEND. PSICÓLOGO"},
        {"key": "QtdAssistSocial", "label": "ATEND. ASSIST. SOCIAL"},
        {"key": "QtdEnfermagem", "label": "ATEND. ENFERMAGEM"},
        {"key": "QtdMedico", "label": "ATEND. MÉDICO"},
        {"key": "QtdEncaminhamento", "label": "ENCAMINHAMENTOS"},
        {"key": "QtdExame", "label": "EXAMES"},
        {"key": "QtdVacina", "label": "DOSES DE VACINA APLICADAS"},
        {"key": "QtdVacinacao", "label": "ALUNOS VACINADOS"},
    ]

    comparison_years = sorted([int(y) for y in (selected_years_comp or [])])

    # --- Filtros para a Tabela por ANO (Respeita URG, Escola e Tipo) ---
    df_home_ano_source = df.copy()
    
    # Garante que 'Ano' seja numérico para comparação
    df_home_ano_source["Ano"] = pd.to_numeric(df_home_ano_source["Ano"], errors="coerce")
    
    # 1. Filtro de URG
    if current_urgs:
        df_home_ano_source = df_home_ano_source[df_home_ano_source["URG"].isin(current_urgs)]
    
    # 2. Filtro de Escola (Cascata)
    current_escolas_sel = selections.get("escola", [])
    if current_escolas_sel:
        all_schools_all = set(df["Escola"].dropna().unique())
        if set(current_escolas_sel) != all_schools_all:
            df_home_ano_source = df_home_ano_source[df_home_ano_source["Escola"].isin(current_escolas_sel)]

    # 3. Filtro de Tipo (se configurado)
    current_tipos_sel = selections.get("tipo", [])
    if current_tipos_sel and "Tipo" in df_home_ano_source.columns:
        all_tipos_all = set(df["Tipo"].dropna().unique())
        if set(current_tipos_sel) != all_tipos_all:
            df_home_ano_source = df_home_ano_source[df_home_ano_source["Tipo"].isin(current_tipos_sel)]

    # 4. Filtro de Anos (Anos selecionados + Anos de comparação)
    if comparison_years:
        df_home_ano_source = df_home_ano_source[df_home_ano_source["Ano"].isin(comparison_years)]

    annual_metric_rows = []
    for metric in metric_definitions:
        key = metric["key"]
        description = metric["label"]
        
        row = {"Descricao": description}
        
        if key == "total_profissionais":
            # Atendimentos Profissionais é a soma de 5 especialidades
            prof_cols = ["QtdProfessor", "QtdPsicologo", "QtdAssistSocial", "QtdEnfermagem", "QtdMedico"]
            # Filtra apenas colunas existentes
            actual_prof_cols = [c for c in prof_cols if c in df_home_ano_source.columns]
            if not actual_prof_cols:
                continue
            
            metric_by_year = (
                df_home_ano_source.groupby("Ano")[actual_prof_cols]
                .sum(min_count=1)
                .sum(axis=1)
                .reindex(comparison_years, fill_value=0)
            )
        else:
            if key not in df_home_ano_source.columns:
                continue
            
            metric_by_year = (
                df_home_ano_source.groupby("Ano")[key]
                .sum(min_count=1)
                .reindex(comparison_years, fill_value=0)
            )

        for year, value in metric_by_year.items():
            row[str(int(year))] = value

        row["Total"] = metric_by_year.sum()
        annual_metric_rows.append(row)

    df_home_ano_exibir = pd.DataFrame(annual_metric_rows)

    if df_home_ano_exibir.empty:
        st.info("Dados insuficientes para gerar o comparativo anual geral.")

    else:
        # Filtrar o comparativo pelos anos selecionados no seletor mestre
        all_years_possible = ["2022", "2023", "2024", "2025", "2026"]
        year_cols_selected = [str(y) for y in comparison_years]
        year_cols_to_drop = [c for c in all_years_possible if c in df_home_ano_exibir.columns and c not in year_cols_selected]
        
        if year_cols_to_drop:
            df_home_ano_exibir = df_home_ano_exibir.drop(columns=year_cols_to_drop)

        year_cols_existentes = [c for c in year_cols_selected if c in df_home_ano_exibir.columns]
        
        numeric_cols_to_process = [
            col for col in year_cols_existentes + ["Total"] if col in df_home_ano_exibir.columns
        ]

        if numeric_cols_to_process:
            df_home_ano_exibir[numeric_cols_to_process] = df_home_ano_exibir[numeric_cols_to_process].apply(
                pd.to_numeric, errors="coerce"
            ).fillna(0)

        # Recalcula o Total usando apenas colunas selecionadas
        df_home_ano_exibir["Total"] = df_home_ano_exibir[year_cols_existentes].sum(axis=1) if year_cols_existentes else 0

        # Cálculos anuais: % Cobertura (Percentual sobre o Total de Alunos da Escola)
        for year in year_cols_existentes:
            # Localiza o valor de "TOTAL DE ALUNOS (ESCOLA)" para o ano atual para usar como denominador
            valor_base_cobertura = df_home_ano_exibir.loc[
                df_home_ano_exibir["Descricao"] == "TOTAL DE ALUNOS", year
            ].values
            
            total_alunos_ano = valor_base_cobertura[0] if len(valor_base_cobertura) > 0 else 0
            
            pct_col = f"% Cobertura {year[-2:]}"
            df_home_ano_exibir[pct_col] = (df_home_ano_exibir[year] / total_alunos_ano * 100) if total_alunos_ano > 0 else 0

        # Cálculos interanuais: Var% em relação ao ano anterior
        for prev, curr in zip(year_cols_existentes, year_cols_existentes[1:]):
            var_pct_col = f"Var% {curr[-2:]}-{prev[-2:]}"
            diff = df_home_ano_exibir[curr] - df_home_ano_exibir[prev]
            df_home_ano_exibir[var_pct_col] = (diff / df_home_ano_exibir[prev].replace(0, float("nan")) * 100)

        col_order = []
        if "URG" in df_home_ano_exibir.columns:
            col_order.append("URG")

        if "Descricao" in df_home_ano_exibir.columns:
            col_order.append("Descricao")

        for i, year in enumerate(year_cols_existentes):
            col_order.append(year)
            col_order.append(f"% Cobertura {year[-2:]}")
            if i > 0:
                prev = year_cols_existentes[i - 1]
                col_order.append(f"Var% {year[-2:]}-{prev[-2:]}")

        if "Total" in df_home_ano_exibir.columns:
            col_order.append("Total")

        df_home_ano_exibir = df_home_ano_exibir[col_order]

        pct_cols = [c for c in df_home_ano_exibir.columns if c.startswith("% Cobertura") or c.startswith("Var%")]

        # Cria uma versão apenas para exibição formatada (mantém df_home_ano_exibir numérico para o gráfico)

        categoria_col_home = "Descricao" if "Descricao" in df_home_ano_exibir.columns else "URG" if "URG" in df_home_ano_exibir.columns else None
        
        if categoria_col_home:
            total_row = {categoria_col_home: "TOTAL"}
            for c in df_home_ano_exibir.columns:
                if c in year_cols_existentes or c == "Total" or c.startswith("Var "):
                    total_row[c] = df_home_ano_exibir[c].sum()
                elif c.startswith("Var% ") or c.startswith("% Cobertura"):
                    total_row[c] = np.nan
            
            # Cria o DF da linha de total. O Pandas agora lida melhor com np.nan para tipos float.
            total_row_df = pd.DataFrame([total_row])
            df_home_ano_display = pd.concat([df_home_ano_exibir, total_row_df], ignore_index=True)
        else:
            df_home_ano_display = df_home_ano_exibir.copy()

        abs_cols = [
            c
            for c in df_home_ano_display.columns
            if c in year_cols_existentes or c == "Total" or c.startswith("Var ")
        ]

        for c in abs_cols:
            df_home_ano_display[c] = df_home_ano_display[c].map(
                lambda x: f"{int(float(x)):,}".replace(",", ".") if pd.notna(x) and float(x) != 0 else ""
            )

        for c in pct_cols:
            df_home_ano_display[c] = df_home_ano_display[c].map(
                lambda x: f"{x:,.1f}%".replace(",", ".") if pd.notna(x) and float(x) != 0 else ""
            )

        # Conversão das colunas para MultiIndex (Super-Header por Ano)
        new_cols_home = []
        for c in df_home_ano_display.columns:
            if c == categoria_col_home:
                new_cols_home.append((categoria_col_home, ""))
            elif c == "Total":
                new_cols_home.append(("Total Geral", ""))
            elif c in year_cols_existentes:
                new_cols_home.append((c, "Qtd"))
            elif str(c).startswith("% Cobertura"):
                y_str = str(c).split(" ")[-1]
                new_cols_home.append((f"20{y_str}", c))
            elif str(c).startswith("Var%"):
                y_str = str(c).split(" ")[1].split("-")[0]
                new_cols_home.append((f"20{y_str}", c.replace("-", "/")))
            else:
                new_cols_home.append(("", c))
        df_home_ano_display.columns = pd.MultiIndex.from_tuples(new_cols_home)

        styler_home = df_home_ano_display.style.pipe(
            apply_saedas_design, categoria_col=categoria_col_home
        ).hide(axis="index")

        df_home_ano_aggrid, home_ano_column_defs, _ = prepare_comparativo_aggrid_data(
            styler_home, include_selection_column=False
        )
        df_home_ano_body, home_ano_footer_rows = split_aggrid_footer(
            df_home_ano_aggrid
        )

        home_ano_grid_options = {
            "columnDefs": home_ano_column_defs,
            "defaultColDef": {
                "resizable": True,
                "sortable": True,
                "filter": False,
                "editable": False,
                "suppressMenu": True,
            },
            "pinnedBottomRowData": home_ano_footer_rows,
            "domLayout": "normal",
            "enableCellTextSelection": True,
            "suppressContextMenu": False,
            "copyHeadersToClipboard": True,
        }

        # A altura é gerenciada pelo render_saedas_aggrid

        with st.container():
            df_home_ano_export = (
                pd.concat(
                    [df_home_ano_body, pd.DataFrame(home_ano_footer_rows)],
                    ignore_index=True,
                )
                if home_ano_footer_rows
                else df_home_ano_body.copy()
            )
            with st.container(key="home_ano_actions_toolbar"):
                render_table_toolbar(df_home_ano_export, "comparativo_geral_home.csv", "home_ano_table")
            st.markdown('<div class="selection-master-table">', unsafe_allow_html=True)
            render_saedas_aggrid(
                df_home_ano_body,
                grid_options=home_ano_grid_options,
                key="home_ano_comparativo_aggrid",
                incluir_total=bool(home_ano_footer_rows),
                max_rows=10
            )
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # --- NOVO: Tabela Comparativa de Performance por URG (Cross-Filtering) ---
    st.subheader(f"Tabela Comparativa de Performance por URG (Anos: {anos_str})")
    
    # Utiliza a função padronizada build_comparativo_anual
    current_selected_urgs = st.session_state.get("global_urgs", [])
    df_cmp_urg_home = build_comparativo_anual(df_for_performance_table, "URG", value_col="QtdAluno", active_row_value=current_selected_urgs)
    
    # Salva o dataframe para ser usado pelo callback no próximo clique
    st.session_state["last_df_cmp_urg_home"] = df_cmp_urg_home
    
    if df_cmp_urg_home is not None:
        df_cmp_urg_aggrid, column_defs, column_map = prepare_comparativo_aggrid_data(
            df_cmp_urg_home
        )
        df_cmp_urg_body, footer_rows = split_aggrid_footer(df_cmp_urg_aggrid)

        urg_field = next(
            (
                field
                for field, original_col in column_map.items()
                if original_col == ("URG", "") or original_col == "URG"
            ),
            None,
        )

        grid_options = {
            "columnDefs": column_defs,
            "defaultColDef": {
                "resizable": True,
                "sortable": True,
                "filter": False,
                "editable": False,
                "suppressMenu": True,
            },
            "rowSelection": "multiple",
            "rowMultiSelectWithClick": True,
            "suppressRowClickSelection": False,
            "pinnedBottomRowData": footer_rows,
            "domLayout": "normal",
            "enableCellTextSelection": True,
            "suppressContextMenu": False,
            "copyHeadersToClipboard": True,
        }

        selected_urgs_js = json.dumps(list(map(str, current_selected_urgs)))
        urg_field_js = json.dumps(urg_field) if urg_field else "null"
        sync_urg_selection_js = JsCode(
            f"""
            function(params) {{
                const selectedUrgs = new Set({selected_urgs_js});
                const urgField = {urg_field_js};
                if (!params.api || !urgField) return;
                params.api.forEachNode(function(node) {{
                    const rowUrg = node.data ? String(node.data[urgField] || '') : '';
                    node.setSelected(selectedUrgs.has(rowUrg));
                }});
            }}
            """
        )
        grid_options["onFirstDataRendered"] = sync_urg_selection_js

        # Chave dinâmica: muda quando a seleção muda, forçando re-mount e onFirstDataRendered.
        # Isso sincroniza sidebar→grid sem usar onRowDataUpdated (que dispara em todo rerun e
        # causa re-seleção indevida quando o usuário está desselecionando).
        _urg_key_sel = "_".join(sorted(map(str, current_selected_urgs))) if current_selected_urgs else "none"
        urg_grid_key = f"urg_home_aggrid_{_urg_key_sel}"
        
        # Monitoramos se houve mudança de seleção vinda da sidebar
        sidebar_urg_filter = st.session_state.get("sidebar_urg_filter", [])
        urg_key_changed = set(map(str, st.session_state.get("_prev_urg_filter_val") or [])) != set(map(str, sidebar_urg_filter))
        st.session_state["_prev_urg_filter_val"] = sidebar_urg_filter
        st.session_state["_prev_urg_grid_key"] = urg_grid_key

        with st.container():
            df_cmp_urg_export = (
                pd.concat(
                    [df_cmp_urg_body, pd.DataFrame(footer_rows)],
                    ignore_index=True,
                )
                if footer_rows
                else df_cmp_urg_body.copy()
            )
            with st.container(key="home_urg_actions_toolbar"):
                render_table_toolbar(df_cmp_urg_export, "comparativo_urg_home.csv", "home_urg_table")
            st.markdown('<div class="selection-master-table">', unsafe_allow_html=True)
            aggrid_response = render_saedas_aggrid(
                df_cmp_urg_body,
                grid_options=grid_options,
                key=urg_grid_key,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                incluir_total=bool(footer_rows),
            )
            st.markdown('</div>', unsafe_allow_html=True)

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

        if not urg_key_changed:
            if urg_field:
                selected_urgs = [
                    str(row.get(urg_field))
                    for row in selected_rows
                    if row.get(urg_field) and str(row.get(urg_field)) != "TOTAL"
                ]
                
                # Normalizamos ambos os sets para string para garantir paridade (especialmente em itens únicos)
                current_urgs_str_set = set(map(str, current_selected_urgs))
                new_urgs_str_set = set(selected_urgs)

                if new_urgs_str_set != current_urgs_str_set:
                    st.session_state["global_urgs"] = selected_urgs
                    st.session_state["pending_sidebar_urg_filter"] = selected_urgs
                    st.session_state["pending_sidebar_escola_filter"] = []
                    st.session_state["last_interaction_source"] = "table"
                    st.rerun()
    else:
        st.info("Dados insuficientes para gerar a tabela comparativa de URGs.")

    st.subheader("Tabela Comparativa de Escola por Ano")

    selected_escolas_sidebar = st.session_state.get("sidebar_escola_filter", [])

    if not current_selected_urgs:
        st.info("Selecione uma URG para exibir a tabela comparativa de escolas.")
    else:
        df_for_school_comparison = df_for_performance_table[
            df_for_performance_table["URG"].isin(current_selected_urgs)
        ].copy()
        df_cmp_escola_home = build_comparativo_anual(
            df_for_school_comparison,
            "Escola",
            value_col="QtdAluno",
            active_row_value=selected_escolas_sidebar,
        )

        if df_cmp_escola_home is not None:
            df_cmp_escola_aggrid, escola_column_defs, escola_column_map = (
                prepare_comparativo_aggrid_data(df_cmp_escola_home)
            )
            df_cmp_escola_body, escola_footer_rows = split_aggrid_footer(
                df_cmp_escola_aggrid
            )

            escola_field = next(
                (
                    field
                    for field, original_col in escola_column_map.items()
                    if original_col == ("Escola", "") or original_col == "Escola"
                ),
                None,
            )

            escola_grid_options = {
                "columnDefs": escola_column_defs,
                "defaultColDef": {
                    "resizable": True,
                    "sortable": True,
                    "filter": False,
                    "editable": False,
                    "suppressMenu": True,
                },
                "rowSelection": "multiple",
                "rowMultiSelectWithClick": True,
                "suppressRowClickSelection": False,
                "pinnedBottomRowData": escola_footer_rows,
                "domLayout": "normal",
                "enableCellTextSelection": True,
                "suppressContextMenu": False,
                "copyHeadersToClipboard": True,
            }

            selected_escolas_js = json.dumps(list(map(str, selected_escolas_sidebar)))
            escola_field_js = json.dumps(escola_field) if escola_field else "null"
            sync_escola_selection_js = JsCode(
                f"""
                function(params) {{
                    const selectedEscolas = new Set({selected_escolas_js});
                    const escolaField = {escola_field_js};
                    if (!params.api || !escolaField) return;
                    params.api.forEachNode(function(node) {{
                        const rowEscola = node.data ? String(node.data[escolaField] || '') : '';
                        node.setSelected(selectedEscolas.has(rowEscola));
                    }});
                }}
                """
            )
            escola_grid_options["onFirstDataRendered"] = sync_escola_selection_js

            df_cmp_escola_export = (
                pd.concat(
                    [df_cmp_escola_body, pd.DataFrame(escola_footer_rows)],
                    ignore_index=True,
                )
                if escola_footer_rows
                else df_cmp_escola_body.copy()
            )
            with st.container(key="home_escola_actions_toolbar"):
                render_table_toolbar(df_cmp_escola_export, "comparativo_escola_home.csv", "home_escola_table")
            st.markdown('<div class="selection-master-table">', unsafe_allow_html=True)

            # Chave dinâmica: re-monta quando a seleção muda, acionando onFirstDataRendered.
            _escola_key_sel = "_".join(sorted(map(str, selected_escolas_sidebar))) if selected_escolas_sidebar else "none"
            escola_grid_key = f"escola_home_aggrid_{_escola_key_sel}"

            # Monitoramos se houve mudança de seleção vinda da sidebar
            sidebar_escola_val = st.session_state.get("sidebar_escola_filter", [])
            escola_key_changed = set(map(str, st.session_state.get("_prev_escola_filter_val") or [])) != set(map(str, sidebar_escola_val))
            st.session_state["_prev_escola_filter_val"] = sidebar_escola_val
            st.session_state["_prev_escola_grid_key"] = escola_grid_key

            escola_aggrid_response = render_saedas_aggrid(
                df_cmp_escola_body,
                grid_options=escola_grid_options,
                key=escola_grid_key,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                incluir_total=bool(escola_footer_rows),
                max_rows=10,
            )
            st.markdown("</div>", unsafe_allow_html=True)

            # AgGrid pode retornar None quando não há seleção, tratamos como lista vazia []
            escola_selected_rows_raw = escola_aggrid_response.get("selected_rows")
            escola_selected_rows = []
            if escola_selected_rows_raw is not None:
                if isinstance(escola_selected_rows_raw, pd.DataFrame):
                    escola_selected_rows = escola_selected_rows_raw.to_dict(orient="records")
                elif isinstance(escola_selected_rows_raw, dict):
                    escola_selected_rows = [escola_selected_rows_raw]
                else:
                    escola_selected_rows = list(escola_selected_rows_raw)

            if not escola_key_changed:
                if escola_field:
                    selected_escolas = [
                        row.get(escola_field)
                        for row in escola_selected_rows
                        if row.get(escola_field) and row.get(escola_field) != "TOTAL"
                    ]

                    if set(map(str, selected_escolas)) != set(map(str, selected_escolas_sidebar)):
                        st.session_state["pending_sidebar_escola_filter"] = selected_escolas
                        st.session_state["last_interaction_source"] = "table_school"
                        st.session_state["_suppress_escola_key_change"] = True
                        st.rerun()

            st.caption(
                "Nota: Clique em qualquer linha de Escola para filtrar o restante do dashboard. "
                "As colunas '% Total' representam o percentual sobre o total da(s) URG(s) "
                f"{', '.join(current_selected_urgs)} no respectivo ano."
            )
        else:
            st.info("Dados insuficientes para gerar a tabela comparativa de escolas.")

    st.markdown("---")



    # --- Gráfico de Rosca: Cobertura de Alunos (Refatorado para múltiplos anos) ---
    if not selected_years_comp:
        st.info("Selecione um ou mais anos para visualizar a cobertura de alunos.")
    else:
        st.subheader(f"Cobertura de alunos da escola (atendidos / cadastrados)")
        
        # Legenda Unificada (Manual) para manter a interface limpa
        st.markdown(
            """
            <div style="display: flex; justify-content: center; gap: 24px; margin-bottom: 10px; font-size: 0.95rem;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 14px; height: 14px; background-color: #16a34a; border-radius: 3px;"></div>
                    <span style="color: #e5e7eb;">Atendidos</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 14px; height: 14px; background-color: #9ca3af; border-radius: 3px;"></div>
                    <span style="color: #e5e7eb;">Não atendidos</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        anos_ordenados = sorted(selected_years_comp)
        # Define o número de colunas (máximo 3)
        n_cols_grid = min(3, len(anos_ordenados))
        
        # Itera pelos anos em chunks para criar as linhas do grid
        for i in range(0, len(anos_ordenados), n_cols_grid):
            cols = st.columns(3) # Sempre cria 3 colunas para manter o tamanho do gráfico consistente
            chunk = anos_ordenados[i : i + n_cols_grid]
            
            for idx, ano in enumerate(chunk):
                # Filtra dados específicos do ano
                df_ano = df_master_filtrado[df_master_filtrado["Ano"] == ano]
                
                total_cadastrados = df_ano["QtdAlunoEscola"].sum() if not df_ano.empty else 0
                total_atendidos = df_ano["QtdAluno"].sum() if not df_ano.empty else 0
                
                with cols[idx]:
                    if total_cadastrados > 0:
                        nao_atendidos = max(total_cadastrados - total_atendidos, 0)
                        pct_atendidos = (total_atendidos / total_cadastrados) * 100
                        
                        df_pie = pd.DataFrame([
                            {"Status": "Atendidos", "Qtd": total_atendidos},
                            {"Status": "Não atendidos", "Qtd": nao_atendidos},
                        ])
                        
                        fig_cov = px.pie(
                            df_pie,
                            names="Status",
                            values="Qtd",
                            hole=0.55,
                            color="Status",
                            color_discrete_map={"Atendidos": "#16a34a", "Não atendidos": "#9ca3af"},
                        )
                        
                        fig_cov.update_traces(
                            texttemplate="%{percent:.1%}<br>(%{value:,.0f})", 
                            textposition="outside",
                            hoverinfo="label+percent+value",
                            marker=dict(line=dict(color='#0f172a', width=2))
                        )
                        
                        fig_cov.update_layout(
                            separators=",.",
                            showlegend=False, # Legenda unificada acima
                            margin=dict(t=60, b=20, l=10, r=10),
                            height=350,
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            title={
                                "text": f"<b>ANO {ano}</b><br><span style='font-size: 1.2rem; color: #16a34a;'>{pct_atendidos:.1f}% de Cobertura</span>",
                                "x": 0.5,
                                "xanchor": "center",
                                "y": 0.95,
                                "font": {"size": 16, "color": "#f8fafc"},
                            },
                        )
                        
                        st.plotly_chart(fig_cov, use_container_width=True, key=f"donut_cov_{ano}")
                    else:
                        st.info(f"Sem dados de cobertura para {ano}")

    year_cols_present = [c for c in year_cols_existentes if c in df_home_ano_exibir.columns]

    if year_cols_present and "Descricao" in df_home_ano_exibir.columns:
        df_home_bar = df_home_ano_exibir[["Descricao"] + year_cols_present].copy()

        df_home_bar_long = df_home_bar.melt(
            id_vars="Descricao",
            value_vars=year_cols_present,
            var_name="Ano",
            value_name="Valor",
        )

        df_home_bar_long = df_home_bar_long.dropna(subset=["Valor"])

        if not df_home_bar_long.empty:
            df_home_bar_long["Ano"] = df_home_bar_long["Ano"].astype(str)

            fig_home_bar = px.bar(
                df_home_bar_long,
                x="Descricao",
                y="Valor",
                color="Ano",
                barmode="group",
                title="Comparativo Anual Geral (Barras)",
                labels={"Descricao": "Descrição", "Valor": "Quantidade"},
            )
            st.caption("Nota: As colunas '% Total' (na aba de Dados) representam o percentual sobre o total de atendimentos realizados no respectivo ano.")

            fig_home_bar.update_layout(separators=",.", legend_title_text="Ano")

            fig_home_bar.update_traces(
                texttemplate="%{y:,.0f}", textposition="outside"
            )

            st.plotly_chart(fig_home_bar, use_container_width=True)




    if df_master_filtrado.empty and (selected_years_comp or urgs_str != "Todos"):
        st.warning(
            f"Não há dados disponíveis para a combinação de filtros selecionada (Anos: {selected_years_comp}, URGs: {urgs_str})."
        )

    elif df.empty:
        st.warning("Não há dados carregados no arquivo CSV para exibir.")

    # Gráfico: Distribuição de Atendimentos por Profissional (Pizza)

    st.subheader("Distribuição de Atendimentos por Profissional")

    if not df_master_filtrado.empty:
        anos_ordenados = sorted(selected_years_comp) if selected_years_comp else []
        
        if anos_ordenados:
            # Color map fixo para consistência entre os múltiplos gráficos
            prof_color_map = {
                "Professor": "#38bdf8",     # Azul claro
                "Enfermagem": "#0284c7",    # Azul médio
                "Assist. Social": "#fca5a5", # Rosa/Salmão
                "Médico": "#ef4444",        # Vermelho
                "Psicólogo": "#4ade80"      # Verde
            }
            
            n_cols_grid = min(3, len(anos_ordenados))
            
            for i in range(0, len(anos_ordenados), n_cols_grid):
                cols = st.columns(3)
                chunk = anos_ordenados[i : i + n_cols_grid]
                
                for idx, ano in enumerate(chunk):
                    df_ano = df_master_filtrado[df_master_filtrado["Ano"] == ano]
                    
                    if not df_ano.empty:
                        prof_atendimentos_sums = {
                            "Professor": (df_ano["QtdProfessor"].sum() if "QtdProfessor" in df_ano else 0),
                            "Psicólogo": (df_ano["QtdPsicologo"].sum() if "QtdPsicologo" in df_ano else 0),
                            "Assist. Social": (df_ano["QtdAssistSocial"].sum() if "QtdAssistSocial" in df_ano else 0),
                            "Enfermagem": (df_ano["QtdEnfermagem"].sum() if "QtdEnfermagem" in df_ano else 0),
                            "Médico": (df_ano["QtdMedico"].sum() if "QtdMedico" in df_ano else 0),
                        }
                        
                        prof_atendimentos_filtered = {
                            key: value for key, value in prof_atendimentos_sums.items() if value > 0
                        }
                        
                        with cols[idx]:
                            if prof_atendimentos_filtered:
                                df_prof_atend = pd.DataFrame(
                                    list(prof_atendimentos_filtered.items()),
                                    columns=["Profissional", "Total Atendimentos"],
                                )
                                
                                fig_prof_pie = px.pie(
                                    df_prof_atend,
                                    names="Profissional",
                                    values="Total Atendimentos",
                                    hole=0.45,
                                    color="Profissional",
                                    color_discrete_map=prof_color_map,
                                )
                                
                                fig_prof_pie.update_traces(
                                    texttemplate="%{percent:.1%}",
                                    textposition="inside",
                                    marker=dict(line=dict(color='#0f172a', width=2))
                                )
                                
                                fig_prof_pie.update_layout(
                                    separators=".",
                                    showlegend=(idx == 0 and i == 0),
                                    margin=dict(t=50, b=20, l=10, r=10),
                                    height=320,
                                    paper_bgcolor="rgba(0,0,0,0)",
                                    plot_bgcolor="rgba(0,0,0,0)",
                                    title={
                                        "text": f"<b>ANO {ano}</b>",
                                        "x": 0.5,
                                        "xanchor": "center",
                                        "font": {"size": 16, "color": "#f8fafc"},
                                    },
                                    legend_title_text="Atendimento"
                                )
                                
                                st.plotly_chart(fig_prof_pie, use_container_width=True, key=f"donut_prof_{ano}")
                            else:
                                st.info(f"Sem dados de atendimentos para {ano}")
        else:
            st.info("Selecione um ou mais anos para visualizar a distribuição por profissional.")

    elif not df.empty:
        st.info(
            f"Não há dados de atendimentos por profissionais para exibir para a combinação de filtros selecionada (Anos: {anos_str}, URGs: {urgs_str})."
        )

    # Gráfico: Total Anual de Alunos Atendidos por Profissional (Barras)

    st.subheader(f"Total de Alunos Atendidos por Profissional e URG ({filtro_titulo})")

    df_prof_base = df_master_filtrado.copy()

    if not df_prof_base.empty and "Ano" in df_prof_base.columns:
        prof_cols = {
            "QtdProfessor": "Professor",
            "QtdPsicologo": "Psicólogo",
            "QtdAssistSocial": "Assist. Social",
            "QtdEnfermagem": "Enfermagem",
            "QtdMedico": "Médico",
        }

        total_atendimentos_yearly_data = []

        actual_prof_cols = {
            k: v for k, v in prof_cols.items() if k in df_prof_base.columns
        }

        if actual_prof_cols:
            # Agrupa por Ano e URG para permitir a visão regional
            grouped_cols = ["Ano", "URG"]
            grouped_by_year_urg = df_prof_base.groupby(grouped_cols)

            for (year, urg), group_df in grouped_by_year_urg:
                for col, name in actual_prof_cols.items():
                    total_atendidos_ano_profissional = group_df[col].sum()

                    if total_atendidos_ano_profissional > 0:
                        total_atendimentos_yearly_data.append(
                            {
                                "Ano": str(year),
                                "URG": str(urg),
                                "Profissional": name,
                                "Total Alunos Atendidos": total_atendidos_ano_profissional,
                            }
                        )

        if total_atendimentos_yearly_data:
            df_prof_total_yearly = pd.DataFrame(total_atendimentos_yearly_data)

            # Ordenação consistente
            df_prof_total_yearly = df_prof_total_yearly.sort_values(
                by=["Ano", "URG", "Profissional"]
            )

            # Determina se usamos facetas para os anos (se houver mais de um)
            n_years = df_prof_total_yearly["Ano"].nunique()
            
            fig_args = {
                "data_frame": df_prof_total_yearly,
                "x": "Profissional",
                "y": "Total Alunos Atendidos",
                "color": "URG",
                "barmode": "group",
                "title": "Total de Alunos Atendidos por Profissional e URG",
                "text": "Total Alunos Atendidos",
            }
            
            if n_years > 1:
                fig_args["facet_col"] = "Ano"
                fig_args["facet_col_wrap"] = 2

            fig_prof_total_bar_yearly = px.bar(**fig_args)

            fig_prof_total_bar_yearly.update_layout(
                xaxis={
                    "categoryorder": "array",
                    "categoryarray": list(actual_prof_cols.values()),
                },
                legend_title_text="URG",
                separators=",.",
            )

            fig_prof_total_bar_yearly.update_traces(
                texttemplate="%{text:,.0f}", textposition="outside"
            )

            st.plotly_chart(fig_prof_total_bar_yearly, use_container_width=True)

        else:
            st.info(
                "Não há dados de atendimentos por profissionais para exibir o total anual."
            )

    elif not df.empty:
        st.info("Não há dados de atendimentos por profissionais para exibir.")

    # --- NOVO Gráfico: Total Anual por Tipo de Ação ---

    st.subheader(f"Total por Tipo de Ação e URG ({filtro_titulo})")

    df_action_base = df_master_filtrado.copy()

    if not df_action_base.empty and "Ano" in df_action_base.columns:
        action_cols_orig = [
            "QtdEncaminhamento",
            "QtdExame",
            "QtdVacinacao",
            "QtdVacina",
        ]

        actual_action_cols_orig = [
            col for col in action_cols_orig if col in df_action_base.columns
        ]

        if actual_action_cols_orig:
            # Agrupa por Ano e URG
            ano_urg_action_group = (
                df_action_base.groupby(["Ano", "URG"])[actual_action_cols_orig]
                .sum()
                .reset_index()
            )

            mask_action_not_all_zero = (
                ano_urg_action_group[actual_action_cols_orig].ne(0).any(axis=1)
            )

            ano_urg_action_group = ano_urg_action_group[mask_action_not_all_zero]

            if not ano_urg_action_group.empty:
                rename_map_action_ano = {
                    "QtdEncaminhamento": "Encaminhamento",
                    "QtdExame": "Exame",
                    "QtdVacinacao": "Alunos Vacinados",
                    "QtdVacina": "Doses Vacina",
                }

                actual_rename_map_action_ano = {
                    k: v
                    for k, v in rename_map_action_ano.items()
                    if k in ano_urg_action_group.columns
                }

                ano_urg_action_group_display = ano_urg_action_group.rename(
                    columns=actual_rename_map_action_ano
                )

                id_vars_melt = ["Ano", "URG"]

                value_vars_melt = [
                    v
                    for k, v in actual_rename_map_action_ano.items()
                    if v in ano_urg_action_group_display.columns
                ]

                if value_vars_melt:
                    ano_urg_action_group_melted = pd.melt(
                        ano_urg_action_group_display,
                        id_vars=id_vars_melt,
                        value_vars=value_vars_melt,
                        var_name="Ação",
                        value_name="Quantidade",
                    )

                    ano_urg_action_group_melted["Ano"] = ano_urg_action_group_melted[
                        "Ano"
                    ].astype(str)

                    ano_urg_action_group_melted = ano_urg_action_group_melted.sort_values(
                        by=["Ano", "URG"]
                    )

                    n_years = ano_urg_action_group_melted["Ano"].nunique()
                    
                    fig_args = {
                        "data_frame": ano_urg_action_group_melted,
                        "x": "Ação",
                        "y": "Quantidade",
                        "color": "URG",
                        "barmode": "group",
                        "title": "Total por Tipo de Ação e URG",
                        "text": "Quantidade",
                    }
                    
                    if n_years > 1:
                        fig_args["facet_col"] = "Ano"
                        fig_args["facet_col_wrap"] = 2

                    fig_ano_action = px.bar(**fig_args)

                    fig_ano_action.update_layout(
                        separators=",.", 
                        legend_title_text="URG"
                    )

                    fig_ano_action.update_traces(
                        texttemplate="%{text:,.0f}", textposition="outside"
                    )

                    st.plotly_chart(fig_ano_action, use_container_width=True)

                else:
                    st.info(
                        "Não há dados suficientes de ações para exibir o total anual."
                    )

            else:
                st.info("Não há dados de ações para exibir para os anos disponíveis.")

        else:
            st.info("Colunas de ações não encontradas para gerar o gráfico.")

    elif not df.empty:
        st.info("Não há dados de ações para exibir.")

    # Gráfico: Distribuição de Atendimentos por Profissional por URG

    st.subheader(f"Distribuição de Atendimentos por Profissional por URG ({filtro_titulo})")

    if not df_master_filtrado.empty:
        prof_cols_orig = [
            "QtdProfessor",
            "QtdPsicologo",
            "QtdAssistSocial",
            "QtdEnfermagem",
            "QtdMedico",
        ]

        urg_prof_group = df_master_filtrado.groupby("URG")[prof_cols_orig].sum().reset_index()

        mask_prof_not_all_zero = urg_prof_group[prof_cols_orig].ne(0).any(axis=1)

        urg_prof_group = urg_prof_group[mask_prof_not_all_zero]

        if not urg_prof_group.empty:
            rename_map_prof_urg = {
                "QtdProfessor": "Professor",
                "QtdPsicologo": "Psicólogo",
                "QtdAssistSocial": "Assist. Social",
                "QtdEnfermagem": "Enfermagem",
                "QtdMedico": "Médico",
            }

            urg_prof_group_display = urg_prof_group.rename(columns=rename_map_prof_urg)

            y_cols_prof_urg = list(rename_map_prof_urg.values())

            fig_urg_prof = px.bar(
                urg_prof_group_display,
                x="URG",
                y=y_cols_prof_urg,
                barmode="group",
                title=f"Atendimentos por Profissional por URG ({filtro_titulo})",
                labels={"value": "Quantidade", "variable": "Atendimento"},
            )

            fig_urg_prof.update_layout(separators=",.")

            fig_urg_prof.update_traces(
                texttemplate="%{value:,.0f}", textposition="outside"
            )

            st.plotly_chart(fig_urg_prof, use_container_width=True)

        else:
            st.info(
                f"Não há dados de atendimentos por profissionais para exibir para as URGs selecionadas ({urgs_str}) nos anos ({anos_str})."
            )


    # Detalhamento dos Dados

    st.markdown("---")

    st.subheader(f"Detalhamento dos Dados ({filtro_titulo})")

    # Initialize df_for_export. It will be populated if df_filtrado is not empty.

    # Otherwise, it remains an empty DataFrame, which to_csv handles by producing an empty file or just headers.

    df_for_export = pd.DataFrame()

    if not current_urgs:
        st.info("Selecione uma URG para exibir o detalhamento dos dados.")

    elif not df_master_filtrado.empty:
        df_for_school_filter = df_master_filtrado.copy()

        if "selected_schools_detalhamento" not in st.session_state:
            st.session_state.selected_schools_detalhamento = []

        if "closing_date_filter_option" not in st.session_state:
            st.session_state.closing_date_filter_option = "Ambas"

        # Estado para o filtro "Situação da Escola"

        if "inicio_sem_fechamento_option" not in st.session_state:
            st.session_state.inicio_sem_fechamento_option = (
                "Todas"  # ATUALIZADO para o novo valor padrão
            )

        if "zero_value_cols_selected" not in st.session_state:
            st.session_state.zero_value_cols_selected = []
        df_after_school_filter = df_for_school_filter.copy()

        def _filter_detail_by_school_status(
            df_status_source: pd.DataFrame, status_option: str
        ) -> pd.DataFrame:
            if status_option == "Aberto":
                if "DtInicio" not in df_status_source.columns:
                    return df_status_source.iloc[0:0].copy()

                condition_inicio_present = df_status_source["DtInicio"].notnull()
                if "DtFechamento" in df_status_source.columns:
                    condition_fechamento_absent = df_status_source[
                        "DtFechamento"
                    ].isnull()
                    return df_status_source[
                        condition_inicio_present & condition_fechamento_absent
                    ].copy()

                return df_status_source[condition_inicio_present].copy()

            if status_option == "Fechado":
                if "DtFechamento" not in df_status_source.columns:
                    return df_status_source.iloc[0:0].copy()

                return df_status_source[
                    df_status_source["DtFechamento"].notnull()
                ].copy()

            return df_status_source.copy()

        current_status_option = st.session_state.get(
            "inicio_sem_fechamento_option", "Todas"
        )
        if (
            current_status_option in {"Aberto", "Fechado"}
            and not df_after_school_filter.empty
            and _filter_detail_by_school_status(
                df_after_school_filter, current_status_option
            ).empty
        ):
            st.session_state.inicio_sem_fechamento_option = "Todas"

        rename_map_table_for_zero_filter = {
            "QtdAluno": "Aluno Atend.",
            "QtdProfessor": "Atend. Professor",
            "QtdPsicologo": "Atend. Psicólogo",
            "QtdAssistSocial": "Atend. Assist. Social",  # Corrigido "Psicólogo"
            "QtdEnfermagem": "Atend. Enfermagem",
            "QtdMedico": "Atend. MǸdico",  # Corrigido "Psicólogo"
            "QtdVacinacao": "Alunos Vacinados",
            "QtdVacina": "Doses Vacina",
            "QtdEncaminhamento": "Encaminhamento",
            "QtdExame": "Exame",
            "QtdAlunoEscola": "Aluno Escola",
        }

        original_numeric_cols_for_zero_check = [
            "QtdAluno",
            "QtdProfessor",
            "QtdPsicologo",
            "QtdAssistSocial",
            "QtdEnfermagem",
            "QtdMedico",
            "QtdVacinacao",
            "QtdVacina",
            "QtdEncaminhamento",
            "QtdExame",
            "QtdAlunoEscola",
        ]

        available_renamed_cols_for_zero_filter = [
            rename_map_table_for_zero_filter[col]
            for col in original_numeric_cols_for_zero_check
            if col in df_for_school_filter.columns
            and col in rename_map_table_for_zero_filter
        ]

        # Usar colunas para posicionar os filtros de rádio lado a lado

        col_filtro_data1, col_filtro_data2 = st.columns(2)

        with col_filtro_data1:
            st.multiselect(
                "Exibir a escola caso alguma destas colunas contenha o valor zero:",
                options=sorted(available_renamed_cols_for_zero_filter),
                placeholder="Escolha uma opção",
                key="zero_value_cols_selected",
            )

        with col_filtro_data2:
            st.radio(
                "Status da Escola:",
                options=["Aberto", "Fechado", "Todas"],  # ATUALIZADO para novas opções
                # index parameter removed; Streamlit uses st.session_state.inicio_sem_fechamento_option
                key="inicio_sem_fechamento_option",
                horizontal=True,
            )

        df_currently_filtered = df_after_school_filter.copy()

        # Filtro: Status da Escola (Opções: "Aberto", "Fechado", "Todas")

        df_currently_filtered = _filter_detail_by_school_status(
            df_currently_filtered, st.session_state.inicio_sem_fechamento_option
        )

        if st.session_state.zero_value_cols_selected:
            selected_original_cols_for_zero_check = [
                original_col
                for original_col, renamed_col in rename_map_table_for_zero_filter.items()
                if renamed_col in st.session_state.zero_value_cols_selected
                and original_col in df_currently_filtered.columns
            ]

            if selected_original_cols_for_zero_check:
                df_currently_filtered = df_currently_filtered[
                    (
                        df_currently_filtered[selected_original_cols_for_zero_check]
                        == 0
                    ).any(axis=1)
                ].copy()

        # Adicionar Coluna de Percentual: (QtdAlunoEscola da linha / Total QtdAlunoEscola para TODAS AS ESCOLAS naquele Ano) * 100

        if (
            "Ano" in df_currently_filtered.columns
            and "QtdAlunoEscola" in df_currently_filtered.columns
            and not df_currently_filtered.empty
        ):
            # Garantir que QtdAlunoEscola em df_currently_filtered (numerador) seja numérico.

            df_currently_filtered.loc[:, "QtdAlunoEscola"] = pd.to_numeric(
                df_currently_filtered["QtdAlunoEscola"], errors="coerce"
            ).fillna(0)

            # Calcular o total de QtdAlunoEscola para cada ANO usando df_filtrado (que tem filtros da sidebar)

            # Isso garante que o denominador seja o total do ano conforme os filtros gerais da página.

            if (
                not df_filtrado.empty
                and "Ano" in df_filtrado.columns
                and "QtdAlunoEscola" in df_filtrado.columns
            ):
                df_filtrado_for_sum = df_master_filtrado.copy()

                df_filtrado_for_sum.loc[:, "QtdAlunoEscola"] = pd.to_numeric(
                    df_filtrado_for_sum["QtdAlunoEscola"], errors="coerce"
                ).fillna(0)

                total_aluno_sum_per_ano_from_sidebar = df_master_filtrado.groupby(
                    "Ano"
                )["QtdAlunoEscola"].sum()

                # Mapear o total do ano (denominador) para cada linha em df_currently_filtered

                df_currently_filtered.loc[:, "DenominatorTotalAno"] = (
                    df_currently_filtered["Ano"].map(
                        total_aluno_sum_per_ano_from_sidebar
                    )
                )

            else:
                # Se df_filtrado for vazio ou não tiver as colunas, o denominador não pode ser calculado.

                df_currently_filtered.loc[:, "DenominatorTotalAno"] = 0

            # Calcular o percentual

            df_currently_filtered.loc[:, "PercentualAlunoEscola"] = np.where(
                df_currently_filtered["DenominatorTotalAno"].isnull()
                | (df_currently_filtered["DenominatorTotalAno"] == 0),
                0.0,
                (
                    df_currently_filtered["QtdAlunoEscola"]
                    / df_currently_filtered["DenominatorTotalAno"]
                )
                * 100,
            )

            df_currently_filtered = df_currently_filtered.drop(
                columns=["DenominatorTotalAno"], errors="ignore"
            )  # Limpar coluna temporária

            # Arredondar para duas casas decimais

            df_currently_filtered.loc[:, "PercentualAlunoEscola"] = (
                df_currently_filtered["PercentualAlunoEscola"].round(1)
            )

        elif "PercentualAlunoEscola" not in df_currently_filtered.columns:
            # Garantir que a coluna exista com NA se o cálculo não puder ser feito ou se o df estiver vazio

            df_currently_filtered["PercentualAlunoEscola"] = pd.NA

        # Adicionar Coluna de Percentual Aluno Atendido (PAA %): (QtdAluno / QtdAlunoEscola) * 100

        if (
            "QtdAluno" in df_currently_filtered.columns
            and "QtdAlunoEscola" in df_currently_filtered.columns
            and not df_currently_filtered.empty
        ):
            df_currently_filtered.loc[:, "QtdAluno"] = pd.to_numeric(
                df_currently_filtered["QtdAluno"], errors="coerce"
            ).fillna(0)

            # QtdAlunoEscola já foi convertida para numérico acima para o cálculo de PAE (%)

            df_currently_filtered.loc[:, "PercentualAlunoAtendido"] = np.where(
                df_currently_filtered["QtdAlunoEscola"] == 0,
                0.0,
                (
                    df_currently_filtered["QtdAluno"]
                    / df_currently_filtered["QtdAlunoEscola"]
                )
                * 100,
            )

            df_currently_filtered.loc[:, "PercentualAlunoAtendido"] = (
                df_currently_filtered["PercentualAlunoAtendido"].round(1)
            )

        elif "PercentualAlunoAtendido" not in df_currently_filtered.columns:
            df_currently_filtered["PercentualAlunoAtendido"] = pd.NA

        # Adicionar Colunas de Percentual para outros atendimentos e vacinação

        # O denominador comum é 'QtdAlunoEscola'

        cols_for_percentage_calculation = {
            "QtdProfessor": "PercentualProfessor",
            "QtdPsicologo": "PercentualPsicólogo",
            "QtdAssistSocial": "PercentualAssistSocial",
            "QtdEnfermagem": "PercentualEnfermagem",
            "QtdMedico": "PercentualMedico",
            "QtdVacinacao": "PercentualVacinacao",
        }

        if (
            "QtdAlunoEscola" in df_currently_filtered.columns
            and not df_currently_filtered.empty
        ):
            # QtdAlunoEscola já foi convertida para numérico e tratada para os cálculos de PAE e PAA

            # Garantir que QtdAlunoEscola seja numérico para os cálculos abaixo, caso não tenha sido antes.

            df_currently_filtered.loc[:, "QtdAlunoEscola"] = pd.to_numeric(
                df_currently_filtered["QtdAlunoEscola"], errors="coerce"
            ).fillna(0)

            for (
                numerator_col,
                new_percent_col_name,
            ) in cols_for_percentage_calculation.items():
                if numerator_col in df_currently_filtered.columns:
                    df_currently_filtered.loc[:, numerator_col] = pd.to_numeric(
                        df_currently_filtered[numerator_col], errors="coerce"
                    ).fillna(0)

                    df_currently_filtered.loc[:, new_percent_col_name] = np.where(
                        df_currently_filtered["QtdAlunoEscola"] == 0,
                        0.0,
                        (
                            df_currently_filtered[numerator_col]
                            / df_currently_filtered["QtdAlunoEscola"]
                        )
                        * 100,
                    )

                    df_currently_filtered.loc[:, new_percent_col_name] = (
                        df_currently_filtered[new_percent_col_name].round(1)
                    )

                elif new_percent_col_name not in df_currently_filtered.columns:
                    df_currently_filtered[new_percent_col_name] = pd.NA

        else:
            # Se QtdAlunoEscola não estiver presente ou df for vazio, preencher com NA

            for _, new_percent_col_name in cols_for_percentage_calculation.items():
                if new_percent_col_name not in df_currently_filtered.columns:
                    df_currently_filtered[new_percent_col_name] = pd.NA

        df_display = (
            df_currently_filtered.copy()
        )  # Usar uma cópia para modificações de exibição

        # Convert date columns to string and replace NaT/NaN with empty string for display

        # Faça isso *antes* de renomear para exibição.

        # O objetivo é que, ao final, as colunas de data contenham strings formatadas ou strings vazias.

        if "DtInicio" in df_display.columns:
            # 1. Converter para string e substituir strings comuns de nulo/vazio por np.nan

            cleaned_strings_inicio = (
                df_display["DtInicio"]
                .astype(str)
                .replace(["None", "none", "NaN", "nan", ""], np.nan)
                .infer_objects(copy=False)
            )

            # 2. Converter para datetime. np.nan e strings não parseáveis viram NaT.

            #    A série series_dt_inicio deve ser do tipo datetime64[ns].

            series_dt_inicio = pd.to_datetime(
                cleaned_strings_inicio, format="%d/%m/%Y", errors="coerce"
            )

            # 3. Formatar datas válidas para string 'dd/mm/yyyy'. NaT permanece NaT (objeto).

            formatted_dates_inicio = series_dt_inicio.dt.strftime("%d/%m/%Y")

            # 4. Substituir NaT (e np.nan como segurança) por string vazia.

            df_display.loc[:, "DtInicio"] = formatted_dates_inicio.replace(
                {pd.NaT: ""}
            ).fillna("")

        if "DtFechamento" in df_display.columns:
            # 1. Converter para string e substituir strings comuns de nulo/vazio por np.nan

            cleaned_strings_fechamento = (
                df_display["DtFechamento"]
                .astype(str)
                .replace(["None", "none", "NaN", "nan", ""], np.nan)
                .infer_objects(copy=False)
            )

            # 2. Converter para datetime. np.nan e strings não parseáveis viram NaT.

            series_dt_fechamento = pd.to_datetime(
                cleaned_strings_fechamento, format="%d/%m/%Y", errors="coerce"
            )

            # 3. Formatar datas válidas para string 'dd/mm/yyyy'. NaT permanece NaT (objeto).

            formatted_dates_fechamento = series_dt_fechamento.dt.strftime("%d/%m/%Y")

            # 4. Substituir NaT (e np.nan como segurança) por string vazia.

            df_display.loc[:, "DtFechamento"] = formatted_dates_fechamento.replace(
                {pd.NaT: ""}
            ).fillna("")

        if "item" in df_display.columns:
            df_display = df_display.drop(columns=["item"])

        # Adicionado para remover IdUrg

        # Removido o comentário duplicado "Adicionado para remover IdUrg"

        if "IdUrg" in df_display.columns:  # Adicionado para remover IdUrg
            df_display = df_display.drop(columns=["IdUrg"])

        df_total_row_for_display = pd.DataFrame()

        df_for_export = df_display.copy()

        if not df_display.empty:
            rename_map_table = {
                "DtInicio": "Início",
                "DtFechamento": "Fechamento",
                "QtdAluno": "Aluno Atend.",
                "QtdProfessor": "Atend. Professor",  # Corrigido "Psicólogo"
                "QtdPsicologo": "Atend. Psicólogo",
                "QtdAssistSocial": "Atend. Assist. Social",  # Corrigido "Psicólogo"
                "QtdEnfermagem": "Atend. Enfermagem",
                "QtdMedico": "Atend. MǸdico",
                "QtdVacinacao": "Alunos Vacinados",
                "QtdVacina": "Doses Vacina",
                "QtdEncaminhamento": "Encaminhamento",
                "QtdExame": "Exame",
                "QtdAlunoEscola": "Aluno Escola",
                "PercentualAlunoEscola": "PAE (%)",
                "PercentualAlunoAtendido": "PAA (%)",
                "PercentualProfessor": "PAP (%)",  # Percentual Atendimento Professor
                "PercentualPsicólogo": "PAPS (%)",  # Percentual Atendimento Psicólogo
                "PercentualAssistSocial": "PAAS (%)",  # Percentual Atendimento Assistente Social
                "PercentualEnfermagem": "PAENF (%)",  # Percentual Atendimento Enfermagem
                "PercentualMedico": "PAM (%)",  # Percentual Atendimento Médico
                "PercentualVacinacao": "PAV (%)",  # Percentual Alunos Vacinados
            }

            # Definir nomes das colunas de percentual após renomeação e reordenação

            # Esta lista será usada para formatação com '%', para a linha de total e para a configuração da tabela.

            percentage_column_names_in_display = [
                "PAE (%)",
                "PAA (%)",
                "PAP (%)",
                "PAPS (%)",
                "PAAS (%)",
                "PAENF (%)",
                "PAM (%)",
                "PAV (%)",
            ]

            # Renomear colunas ANTES de definir a ordem e ANTES de df_for_export

            # para que df_for_export tenha os nomes corretos.

            # As colunas de percentual ainda são numéricas aqui.

            df_display = df_display.rename(
                columns={
                    k: v for k, v in rename_map_table.items() if k in df_display.columns
                }
            )

            col_order_base = ["Ano", "URG", "Escola", "Início", "Fechamento"]

            col_order_quantitativas = [
                "Aluno Escola",
                "PAE (%)",
                "Aluno Atend.",
                "PAA (%)",
                "Atend. Professor",
                "PAP (%)",
                "Atend. Psicólogo",
                "PAPS (%)",
                "Atend. Assist. Social",
                "PAAS (%)",
                "Atend. Enfermagem",
                "PAENF (%)",
                "Atend. MǸdico",
                "PAM (%)",
                "Alunos Vacinados",
                "PAV (%)",
                "Doses Vacina",
                "Encaminhamento",
                "Exame",
            ]

            final_col_order = []

            for col in col_order_base:
                if col in df_display.columns:
                    final_col_order.append(col)

            for col in col_order_quantitativas:
                if col in df_display.columns:
                    final_col_order.append(col)

            remaining_cols_display = [
                col for col in df_display.columns if col not in final_col_order
            ]

            df_display = df_display[final_col_order + remaining_cols_display]

            auto_generated_cols = [
                col for col in df_display.columns if col == AUTO_ID_COLUMN
            ]

            if auto_generated_cols:
                df_display = df_display.drop(columns=auto_generated_cols)

            percentage_column_names_in_display = [
                col
                for col in percentage_column_names_in_display
                if col in df_display.columns
            ]

            # --- Capture df_for_export BEFORE adding the total row ---

            # This ensures the exported data does not include the total row.

            df_for_export = df_display.copy()

            # Container to hold a detached total row for display purposes

            df_total_row_for_display = pd.DataFrame()

            # --- Total row logic ---

            cols_to_sum_renamed = [
                "Aluno Escola",
                "Aluno Atend.",
                "Atend. Professor",
                "Atend. Psicólogo",  # Corrigido "Psicólogo"
                "Atend. Assist. Social",
                "Atend. Enfermagem",
                "Atend. MǸdico",
                "Alunos Vacinados",
                "Doses Vacina",
                "Encaminhamento",
                "Exame",
            ]

            # Para a soma, precisamos verificar o dtype no df_display *antes* de qualquer conversão para string (como a do 'Ano')

            # No entanto, as colunas de percentual não devem ser somadas.

            numeric_cols_in_df_display_for_sum_check = df_display.select_dtypes(
                include=np.number
            ).columns

            actual_cols_to_sum = [
                col
                for col in cols_to_sum_renamed
                if col in numeric_cols_in_df_display_for_sum_check
            ]

            if actual_cols_to_sum:
                label_col_name_display = None

                if "Escola" in df_display.columns and pd.api.types.is_string_dtype(
                    df_display["Escola"].dtype
                ):
                    label_col_name_display = "Escola"

                elif "URG" in df_display.columns and pd.api.types.is_string_dtype(
                    df_display["URG"].dtype
                ):
                    label_col_name_display = "URG"

                totals_series = df_display[actual_cols_to_sum].sum()

                total_row_values = {}

                for col_name_display in df_display.columns:
                    if (
                        col_name_display in totals_series
                    ):  # Colunas que devem ser somadas
                        total_value = totals_series[col_name_display]

                        # Formatar inteiros corretamente, manter floats se tiverem decimais

                        if pd.api.types.is_integer(total_value) or (
                            isinstance(total_value, float) and total_value.is_integer()
                        ):
                            total_row_values[col_name_display] = int(total_value)

                        else:
                            total_row_values[col_name_display] = total_value

                    elif (
                        col_name_display == label_col_name_display
                    ):  # Coluna de Rótulo (Escola ou URG)
                        total_row_values[col_name_display] = "TOTAL"

                    elif col_name_display in percentage_column_names_in_display:
                        # Colunas de percentual ficam em branco na linha de total
                        
                        total_row_values[col_name_display] = ""

                    elif col_name_display in ["Ano", "Início", "Fechamento"]:
                        total_row_values[col_name_display] = ""  # Usar '' diretamente

                    elif (
                        col_name_display in df_display.columns
                        and (
                            pd.api.types.is_numeric_dtype(
                                df_display[col_name_display].dtype
                            )
                            or pd.api.types.is_datetime64_any_dtype(
                                df_display[col_name_display].dtype
                            )
                            or isinstance(
                                df_display[col_name_display].dtype, pd.BooleanDtype
                            )
                        )
                        and col_name_display not in actual_cols_to_sum
                    ):
                        # Outras colunas numéricas/data/booleanas não somadas (e não sendo 'Ano' ou %)

                        total_row_values[col_name_display] = (
                            ""  # Ou pd.NA se preferir, mas '' é consistente com as outras strings
                        )

                    else:
                        # Demais colunas (provavelmente strings que não são label nem percentual)

                        total_row_values[col_name_display] = ""

                totals_df_row = pd.DataFrame(
                    [total_row_values], columns=df_display.columns
                )

                # Prepare a detached total row so it can be displayed separately and stay at the bottom

                if df_display.empty:
                    # When there are no detailed rows, fall back to showing just the total row

                    df_display = totals_df_row.copy().reset_index(drop=True)

                else:
                    df_total_row_for_display = totals_df_row.copy().reset_index(
                        drop=True
                    )

                # Clean percentage columns in the total row so they render as blanks instead of 'nan'

                target_total_df = (
                    df_total_row_for_display
                    if not df_total_row_for_display.empty
                    else df_display
                )

                for col_name_pct in percentage_column_names_in_display:
                    if col_name_pct in target_total_df.columns:
                        # Garantir tipo object para permitir strings e números/NaNs
                        target_total_df[col_name_pct] = target_total_df[col_name_pct].astype(object)
                        
                        # Limpar NaNs na linha de total
                        if pd.isna(target_total_df.at[target_total_df.index[-1], col_name_pct]):
                            target_total_df.at[target_total_df.index[-1], col_name_pct] = ""

            # End of 'if actual_cols_to_sum:'

        # Após adicionar a linha de total, converter 'Ano' para string para evitar problemas com Arrow

        if "Ano" in df_display.columns:
            df_display["Ano"] = (
                df_display["Ano"]
                .astype(str)
                .replace({"<NA>": "", "nan": "", "None": ""})
            )

        if not df_total_row_for_display.empty:
            if "Ano" in df_total_row_for_display.columns:
                df_total_row_for_display["Ano"] = (
                    df_total_row_for_display["Ano"]
                    .astype(str)
                    .replace({"<NA>": "", "nan": "", "None": ""})
                )

        # Display message if df_display is empty after all filtering and processing.

        # (df_display pode ser vazio se df_currently_filtered for vazio e não houver colunas para somar)

        if df_display.empty and not df_filtrado.empty:
            st.info(
                "Nenhum dado detalhado para exibir com os filtros aplicados na tabela."
            )

        # --- Table display logic ---

        if not df_display.empty:  # Only display if there's data to show
            empty_rows_mask = df_display.replace("", np.nan).infer_objects(copy=False).isna().all(axis=1)

            if empty_rows_mask.any():
                df_display = df_display.loc[~empty_rows_mask].copy()

            height_options_config = {"Padrão": 10, "20": 20, "50": 50, "100": 100}

            height_option_session_key = "home_table_height_option"

            selected_option = st.radio(
                label="Linhas visíveis na tabela:",
                options=list(height_options_config.keys()),
                horizontal=True,
                key=height_option_session_key,
                index=(
                    list(height_options_config.keys()).index(
                        st.session_state.get(height_option_session_key, "Padrão")
                    )
                    if st.session_state.get(height_option_session_key, "Padrão")
                    in height_options_config
                    else 0
                ),
            )

            selected_limit = height_options_config.get(selected_option)

            # Mantém todos os dados; o limite controla apenas a altura/rolagem

            df_grid_data = df_display.reset_index(drop=True)
            df_grid_data.index = range(1, len(df_grid_data) + 1)

            # A altura agora é gerenciada internamente pelo render_saedas_aggrid via parâmetro max_rows

            st.markdown(
                """
            <style>
                /* O estilo de toolbar já é coberto pelo bloco global no início da página */
                .home-columns-panel-title {
                    font-size: 0.72rem;
                    font-weight: 700;
                    color: #cbd5e1;
                    letter-spacing: 0.01em;
                    text-transform: uppercase;
                    margin-bottom: 1px;
                }
                .home-columns-panel-subtitle {
                    font-size: 0.7rem;
                    color: #94a3b8;
                    margin-bottom: 2px;
                }
                .st-key-home_columns_panel {
                    margin: 2px 0 4px 0 !important;
                }
                .st-key-home_columns_panel div[data-testid="stVerticalBlockBorderWrapper"] {
                    padding: 4px 6px !important;
                    border-radius: 6px !important;
                }
                .st-key-home_columns_panel div[data-testid="stHorizontalBlock"] {
                    gap: 0 !important;
                    justify-content: flex-start !important;
                    align-items: flex-start !important;
                    flex-wrap: nowrap !important;
                }
                .st-key-home_columns_grid {
                    margin-top: 0 !important;
                }
                .st-key-home_columns_grid div[data-testid="stHorizontalBlock"] {
                    gap: 0 !important;
                    justify-content: flex-start !important;
                    align-items: flex-start !important;
                    flex-wrap: nowrap !important;
                    width: fit-content !important;
                }
                .st-key-home_columns_grid div[data-testid="stElementContainer"] {
                    width: fit-content !important;
                    min-width: fit-content !important;
                    flex: 0 0 auto !important;
                    padding: 0 !important;
                    margin: 0 12px 0 0 !important;
                }
                .st-key-home_columns_panel div[data-testid="stCheckbox"] {
                    margin: 0 !important;
                }
                .st-key-home_columns_panel div[data-testid="stCheckbox"] label {
                    min-height: 22px !important;
                    padding-top: 0 !important;
                    padding-bottom: 0 !important;
                }
                .st-key-home_columns_panel div[data-testid="stCheckbox"] p {
                    white-space: nowrap !important;
                }
                .st-key-home_columns_panel div[data-testid="stLayoutWrapper"] {
                    width: fit-content !important;
                }
                .st-key-home_columns_panel .stVerticalBlock {
                    gap: 0 !important;
                }
                .stVerticalBlock .st-key-home_columns_panel {
                    width: fit-content !important;
                    min-width: fit-content !important;
                    align-self: end !important;
                }
            </style>
            """,
                unsafe_allow_html=True,
            )

            st.session_state.setdefault("home_show_column_selector", False)

            st.session_state.setdefault("home_hidden_columns", [])

            available_columns = list(df_display.columns)

            selected_hidden_columns = [
                col
                for col in st.session_state["home_hidden_columns"]
                if col in available_columns
            ]

            thousands_js = JsCode(
                """
                function(params) {
                    if (params.value === null || params.value === undefined) {
                        return '';
                    }
                    if (typeof params.value === 'number') {
                        return params.value.toLocaleString('pt-BR');
                    }
                    const num = Number(params.value);
                    if (!isNaN(num) && params.value !== true && params.value !== false) {
                        return num.toLocaleString('pt-BR');
                    }
                    return params.value;
                }
                """
            )

            grid_builder = GridOptionsBuilder.from_dataframe(df_grid_data)

            grid_builder.configure_default_column(
                resizable=True,
                sortable=True,
                filter=True,
                suppressMenu=False,
                editable=False,
            )

            # Aplica formatação de milhar (pt-BR) apenas nas colunas numéricas
            numeric_cols_for_formatter = []
            for col in df_grid_data.columns:
                try:
                    ser = pd.to_numeric(df_grid_data[col], errors="coerce")
                    if ser.notna().any():
                        numeric_cols_for_formatter.append(col)
                except Exception:
                    continue
            for col in numeric_cols_for_formatter:
                grid_builder.configure_column(col, valueFormatter=thousands_js)

            auto_size_js = JsCode(
                """
                function(params) {
                    if (params.api) {
                        params.api.autoSizeAllColumns(false);
                    }
                }
                """
            )

            grid_options_kwargs = {
                "domLayout": "normal",
                "onFirstDataRendered": auto_size_js,
                "onGridSizeChanged": auto_size_js,
                "enableRangeSelection": True,
                "enableCellTextSelection": True,
                "suppressRowClickSelection": False,
                "copyHeadersToClipboard": True,
                "clipboardDelimiter": "	",
                "suppressContextMenu": False,
            }

            if not df_total_row_for_display.empty:
                totals_row_for_grid = df_total_row_for_display.copy()

                if percentage_column_names_in_display:
                    pct_cols_for_grid = [
                        col
                        for col in percentage_column_names_in_display
                        if col in totals_row_for_grid.columns
                    ]

                    if pct_cols_for_grid:
                        totals_row_for_grid.loc[:, pct_cols_for_grid] = (
                            totals_row_for_grid.loc[:, pct_cols_for_grid].replace(
                                "", None
                            )
                        )

                totals_row_records = totals_row_for_grid.replace(
                    {np.nan: None}
                ).to_dict(orient="records")

                grid_options_kwargs["pinnedBottomRowData"] = totals_row_records

            grid_builder.configure_grid_options(**grid_options_kwargs)

            grid_builder.configure_selection(
                selection_mode="single",
                use_checkbox=False,
                suppressRowDeselection=False,
            )

            if not df_total_row_for_display.empty:
                df_display_for_copy = pd.concat(
                    [df_grid_data, df_total_row_for_display], ignore_index=True
                )

            else:
                df_display_for_copy = df_grid_data.copy()

            df_display_for_copy = df_display_for_copy.drop(
                columns=EXCLUDED_EXPORT_COLUMNS, errors="ignore"
            )

            df_display_for_export = df_grid_data.drop(
                columns=EXCLUDED_EXPORT_COLUMNS, errors="ignore"
            )

            _colunas_ativo = st.session_state["home_show_column_selector"]

            if st.session_state["home_show_column_selector"]:
                st.markdown('<div class="column-toggle-active"></div>', unsafe_allow_html=True)

            with st.container(key="home_detail_toolbar"):
                if render_table_toolbar(
                    df_display_for_copy,
                    "detalhamento_home.csv",
                    "home_detail",
                    df_download=df_display_for_export,
                    leading_action_label="Colunas",
                    leading_action_key="home_toolbar_column_toggle",
                    leading_action_help="Mostrar/ocultar colunas da tabela",
                    copy_key="home_toolbar_copy",
                    download_key="download_csv_home_toolbar",
                ):
                    st.session_state["home_show_column_selector"] = not _colunas_ativo
            if st.session_state["home_show_column_selector"]:
                with st.container(key="home_columns_panel", border=True):
                    st.markdown(
                        '<div class="home-columns-panel-title">Configuração de colunas</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        '<div class="home-columns-panel-subtitle">Marque para exibir e desmarque para ocultar</div>',
                        unsafe_allow_html=True,
                    )

                    selected_visible_columns = []
                    max_rows_per_column = 10
                    column_groups = [
                        available_columns[idx : idx + max_rows_per_column]
                        for idx in range(0, len(available_columns), max_rows_per_column)
                    ]

                    if column_groups:
                        cols_grid = st.columns(len(column_groups))
                        for group_idx, group_columns in enumerate(column_groups):
                            with cols_grid[group_idx]:
                                with st.container(
                                    key=f"home_columns_group_{group_idx}", border=False
                                ):
                                    for item_idx, column_name in enumerate(group_columns):
                                        default_visible = (
                                            column_name not in selected_hidden_columns
                                        )
                                        checkbox_key = (
                                            f"home_col_visible_g{group_idx}_i{item_idx}"
                                        )
                                        is_visible = st.checkbox(
                                            str(column_name),
                                            value=default_visible,
                                            key=checkbox_key,
                                        )
                                        if is_visible:
                                            selected_visible_columns.append(column_name)

                    st.session_state["home_hidden_columns"] = [
                        col for col in available_columns if col not in selected_visible_columns
                    ]
            else:
                st.session_state["home_hidden_columns"] = selected_hidden_columns

            hidden_columns = [
                col
                for col in st.session_state["home_hidden_columns"]
                if col in available_columns
            ]

            for column_name in hidden_columns:
                grid_builder.configure_column(column_name, hide=True)

            grid_options = grid_builder.build()

            render_saedas_aggrid(
                df_grid_data,
                grid_options=grid_options,
                key="home_detalhamento_aggrid",
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                incluir_total=not df_total_row_for_display.empty,
                max_rows=selected_limit
            )

        # If df_display is empty but df_filtrado wasn't (meaning filters resulted in no detailed rows)

        # The message "Nenhum dado detalhado para exibir..." is already handled above.

        # No need to display the table or height options if df_display is empty.

        # --- Sidebar Export ---

        st.sidebar.markdown("---")

        st.sidebar.subheader("Exportar dados")

        csv_export_encoding = "utf-8"

        # df_for_export is the detailed data *without* the total row

        df_for_export_clean = df_for_export.drop(
            columns=EXCLUDED_EXPORT_COLUMNS, errors="ignore"
        )

        csv_data = df_for_export_clean.to_csv(index=False, sep=";").encode(
            csv_export_encoding
        )

        st.sidebar.download_button(
            label="Exportar CSV (Detalhado)",
            data=csv_data,
            file_name="dados_detalhados_home.csv",
            mime="text/csv",
            key="download_csv_home_detalhado",
        )

        if not df_display.empty:
            st.markdown(
                """
                <style>
                    .home-legend-grid {
                        display: grid;
                        grid-template-columns: repeat(2, minmax(280px, 1fr));
                        column-gap: 24px;
                        row-gap: 6px;
                    }

                    .home-legend-item {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }
                </style>
                """,
                unsafe_allow_html=True,
            )

            legend_items = [
                "PAE (%): Percentual de Alunos da Escola",
                "PAA (%): Percentual de Alunos Atendidos",
                "PAP (%): Percentual de Atendimentos de Professor",
                "PAPS (%): Percentual de Atendimentos de Psicólogo",
                "PAAS (%): Percentual de Atendimentos de Assistência Social",
                "PAENF (%): Percentual de Atendimentos de Enfermagem",
                "PAM (%): Percentual de Atendimentos de Médico",
                "PAV (%): Percentual de Alunos Vacinados",
            ]

            st.markdown("**Legenda das colunas percentuais**")

            legend_html = (
                "<div class='home-legend-grid'>"
                + "".join(
                    [
                        f"<div class='home-legend-item'>• {item}</div>"
                        for item in legend_items
                    ]
                )
                + "</div>"
            )

            st.markdown(legend_html, unsafe_allow_html=True)

    footer_personal()


# streamlit run main.py
