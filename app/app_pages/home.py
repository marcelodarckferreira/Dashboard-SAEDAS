import streamlit as st
import pandas as pd
import plotly.express as px
from components.footer_personal import footer_personal
from components.sidebar_filters import sidebar_filters
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from app.utils.page_helpers import format_filters_applied
from app.utils.data_loader import load_csv
from app.utils.schemas import (
    SCHEMA_HOME,
    SCHEMA_HOME_ANO,
    SCHEMA_HOME_ESCOLA_ANO,
    SCHEMA_HOME_URG_ANO,
)

AUTO_ID_COLUMN = "::auto_unique_id::"

EXCLUDED_EXPORT_COLUMNS = [AUTO_ID_COLUMN]


@st.cache_data(ttl=3600, show_spinner="Carregando dados gerais...")
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


def calcular_altura_aggrid(
    df: pd.DataFrame, limite_linhas: int | str | None, incluir_total: bool = False
) -> int:
    """
    Calcula a altura ideal para uma tabela AgGrid com base no número de linhas.
    Args:
        df (pd.DataFrame): O DataFrame que será exibido.
        limite_linhas (int | str | None): O limite de linhas selecionado pelo usuário.
                                          Pode ser um inteiro, "Todas as linhas", ou None.
        incluir_total (bool): Se uma linha de total fixada (pinned) será adicionada.
    Returns:
        int: A altura calculada em pixels para a grade.
    """

    APPROX_ROW_HEIGHT = 34

    APPROX_HEADER_HEIGHT = 36

    SAFETY_PADDING = 6  # Espaço extra para evitar barras de rolagem desnecessárias

    if not isinstance(df, pd.DataFrame):
        return APPROX_HEADER_HEIGHT + SAFETY_PADDING

    num_data_rows = len(df)

    if isinstance(limite_linhas, int) and limite_linhas > 0:
        num_rows_to_display = min(num_data_rows, limite_linhas)

    else:  # Inclui "Todas as linhas", None, ou qualquer outro valor não-inteiro
        num_rows_to_display = num_data_rows

    # A altura da área de dados

    data_height = num_rows_to_display * APPROX_ROW_HEIGHT

    # A linha de total é *adicionada* à altura total, pois fica em uma área separada

    total_row_height = APPROX_ROW_HEIGHT if incluir_total and num_data_rows > 0 else 0

    # Altura final

    grid_height = APPROX_HEADER_HEIGHT + data_height + total_row_height + SAFETY_PADDING

    # Define uma altura mínima para a tabela não "sumir" se estiver vazia

    min_height = (
        APPROX_HEADER_HEIGHT
        + (APPROX_ROW_HEIGHT if incluir_total else 0)
        + SAFETY_PADDING
    )

    return max(grid_height, min_height)


def page_home():
    st.title("Visão Geral do SAEDAS")

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

    # SCHEMA_HOME já foi validado no load_csv; mensagens de alerta foram exibidas acima.

    # --- Filtros na Sidebar ---

    home_filter_config = {"ano": True, "urg": True, "escola": True, "tipo": False}

    df_filtrado, selections = sidebar_filters(df, home_filter_config)
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

    anos_selecionados_validos = selections.get("ano", [])

    urgs_selecionadas_validos = selections.get("urg", [])

    def get_filter_display_string_for_title(
        selected_items_list, all_available_items_list_from_original_df
    ):
        if not selected_items_list or (
            all_available_items_list_from_original_df
            and set(map(str, selected_items_list))
            == set(map(str, all_available_items_list_from_original_df))
        ):
            return "Todos"
        return ", ".join(map(str, sorted(list(set(selected_items_list)))))

    processed_df_for_options = df.copy()
    ano_col_for_options_title = "Ano"

    if (
        "Ano" not in processed_df_for_options.columns
        or processed_df_for_options["Ano"].isnull().all()
    ):
        date_col_for_year_title = None

        if (
            "DtFechamento" in processed_df_for_options.columns
            and pd.api.types.is_datetime64_any_dtype(
                processed_df_for_options["DtFechamento"]
            )
        ):
            date_col_for_year_title = "DtFechamento"

        elif (
            "Data" in processed_df_for_options.columns
            and pd.api.types.is_datetime64_any_dtype(processed_df_for_options["Data"])
        ):
            date_col_for_year_title = "Data"

        if date_col_for_year_title:
            processed_df_for_options = (
                processed_df_for_options.copy()
            )  # Evitar SettingWithCopyWarning

            processed_df_for_options["Ano_derived_title"] = processed_df_for_options[
                date_col_for_year_title
            ].dt.year

            ano_col_for_options_title = "Ano_derived_title"

    all_anos_in_df_for_title = []

    if ano_col_for_options_title in processed_df_for_options.columns:
        try:
            year_series_title = pd.to_numeric(
                processed_df_for_options[ano_col_for_options_title], errors="coerce"
            )

            all_anos_in_df_for_title = sorted(
                list(year_series_title.dropna().astype(int).unique())
            )

        except Exception:
            pass

    all_urgs_in_df_for_title = []

    if "URG" in df.columns:
        try:
            temp_series_urg_title = df["URG"].astype(str).str.strip().replace("", pd.NA)

            all_urgs_in_df_for_title = sorted(
                list(temp_series_urg_title.dropna().unique())
            )

        except Exception:
            pass

    anos_str = get_filter_display_string_for_title(
        anos_selecionados_validos, all_anos_in_df_for_title
    )

    urgs_str = get_filter_display_string_for_title(
        urgs_selecionadas_validos, all_urgs_in_df_for_title
    )

    filtro_titulo = f"Anos: {anos_str} / URGs: {urgs_str}"

    # --- Exibição dos Dados e Gráficos ---

    st.subheader("Indicadores Gerais")

    if not df_filtrado.empty:
        total_alunos_escola = df_filtrado["QtdAlunoEscola"].sum()

        total_alunos = df_filtrado["QtdAluno"].sum()

        total_professor = df_filtrado["QtdProfessor"].sum()
        total_psicologo = df_filtrado["QtdPsicologo"].sum()
        total_assist_social = df_filtrado["QtdAssistSocial"].sum()
        total_enfermagem = df_filtrado["QtdEnfermagem"].sum()
        total_medico = df_filtrado["QtdMedico"].sum()
        total_atendimentos_profissionais = (
            df_filtrado[
                [
                    "QtdProfessor",
                    "QtdPsicologo",
                    "QtdAssistSocial",
                    "QtdEnfermagem",
                    "QtdMedico",
                ]
            ]
            .sum()
            .sum()
        )
        total_vacinacao_alunos = df_filtrado["QtdVacinacao"].sum()
        total_doses_vacina = df_filtrado["QtdVacina"].sum()
        total_exames = df_filtrado["QtdExame"].sum()
        total_encaminhamentos = df_filtrado["QtdEncaminhamento"].sum()
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

    st.markdown(
        """
        <style>
            .home-metric-card {
                background: linear-gradient(135deg, #0f172a, #1f2937);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                padding: 14px 16px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.18);
                color: #e5e7eb;
                display: flex;
                flex-direction: column;
                gap: 6px;
                height: 100%;
            }

            .home-metric-label {
                font-size: 0.9rem;
                letter-spacing: 0.01em;
                color: #cbd5e1;
            }

            .home-metric-value {
                font-size: 1.8rem;
                font-weight: 700;
                color: #f8fafc;
                line-height: 1.2;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    primary_metrics = [
        ("Total de Alunos (Escola)", total_alunos_escola),
        ("Alunos Atendidos", total_alunos),
        ("Atendimentos (Profissionais)", total_atendimentos_profissionais),
    ]
    professional_metrics = [
        ("Atend. Professor", total_professor),
        ("Atend. Psicólogo", total_psicologo),
        ("Atend. Assist. Social", total_assist_social),
        ("Atend. Enfermagem", total_enfermagem),
        ("Atend. Médico", total_medico),
    ]
    service_metrics = [
        ("Encaminhamentos", total_encaminhamentos),
        ("Exames", total_exames),
        ("Doses de Vacina Aplicadas", total_doses_vacina),
        ("Alunos Vacinados", total_vacinacao_alunos),
    ]

    def render_metric_row(metrics):
        cols = st.columns(len(metrics))
        for col, (label, value) in zip(cols, metrics):
            value_fmt = f"{value:,}".replace(",", ".")
            card_html = (
                f'<div class="home-metric-card">'
                f'<div class="home-metric-label">{label}</div>'
                f'<div class="home-metric-value">{value_fmt}</div>'
                "</div>"
            )
            with col:
                st.markdown(card_html, unsafe_allow_html=True)

    render_metric_row(primary_metrics)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    render_metric_row(professional_metrics)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    render_metric_row(service_metrics)
    st.markdown("---")

    st.subheader("Comparativo Anual Geral")

    if df_home_ano.empty:
        st.info(
            "Dados agregados por ano não estão disponíveis ou houve erro na leitura do CSV."
        )

    else:
        df_home_ano_exibir = df_home_ano.copy()

        year_cols = ["2022", "2023", "2024", "2025"]

        numeric_cols = [
            col for col in year_cols + ["Total"] if col in df_home_ano_exibir.columns
        ]

        if numeric_cols:
            df_home_ano_exibir[numeric_cols] = df_home_ano_exibir[numeric_cols].apply(
                pd.to_numeric, errors="coerce"
            )

        for prev, curr in zip(year_cols, year_cols[1:]):
            if (
                prev in df_home_ano_exibir.columns
                and curr in df_home_ano_exibir.columns
            ):
                # Usar nomes curtos e únicos para evitar duplicação de colunas

                abs_col = f"Var {curr[-2:]}-{prev[-2:]}"

                pct_col = f"Var% {curr[-2:]}-{prev[-2:]}"

                df_home_ano_exibir[abs_col] = (
                    df_home_ano_exibir[curr] - df_home_ano_exibir[prev]
                )

                df_home_ano_exibir[pct_col] = (
                    df_home_ano_exibir[abs_col]
                    / df_home_ano_exibir[prev].replace({0: np.nan})
                    * 100
                )

        col_order = []

        if "Descricao" in df_home_ano_exibir.columns:
            col_order.append("Descricao")

        for prev, curr in zip(year_cols, year_cols[1:]):
            if prev in df_home_ano_exibir.columns:
                col_order.append(prev)

            abs_col = f"Var {curr[-2:]}-{prev[-2:]}"

            pct_col = f"Var% {curr[-2:]}-{prev[-2:]}"

            if abs_col in df_home_ano_exibir.columns:
                col_order.append(abs_col)

            if pct_col in df_home_ano_exibir.columns:
                col_order.append(pct_col)

        if year_cols[-1] in df_home_ano_exibir.columns:
            col_order.append(year_cols[-1])

        if "Total" in df_home_ano_exibir.columns:
            col_order.append("Total")

        remaining_cols = [
            col for col in df_home_ano_exibir.columns if col not in col_order
        ]

        df_home_ano_exibir = df_home_ano_exibir[col_order + remaining_cols]

        pct_cols = [c for c in df_home_ano_exibir.columns if c.startswith("Var% ")]

        # Cria uma versão apenas para exibição formatada (mantém df_home_ano_exibir numérico para o gráfico)

        df_home_ano_display = df_home_ano_exibir.copy()

        abs_cols = [
            c
            for c in df_home_ano_display.columns
            if c in year_cols or c == "Total" or c.startswith("Var ")
        ]

        for c in abs_cols:
            df_home_ano_display[c] = df_home_ano_display[c].map(
                lambda x: f"{x:,.0f}".replace(",", ".") if pd.notna(x) else ""
            )

        for c in pct_cols:
            df_home_ano_display[c] = df_home_ano_display[c].map(
                lambda x: f"{x:,.1f}".replace(",", ".") if pd.notna(x) else ""
            )

        numeric_like_cols = [c for c in df_home_ano_display.columns if c != "Descricao"]

        right_align_props = {"text-align": "right"}

        styler_home = df_home_ano_display.style.set_properties(
            subset=numeric_like_cols, **right_align_props
        ).hide(axis="index")

        st.dataframe(styler_home, use_container_width=True, hide_index=True)

        if st.button("Copiar tabela (Comparativo Geral)", key="copy_home_ano_table"):
            try:
                df_home_ano_exibir.to_clipboard(index=False, excel=True)

                st.success("Tabela copiada. Cole no Excel com Ctrl+V.")

            except Exception as exc:
                st.error(f"Não foi possível copiar automaticamente: {exc}")

        # Donut de cobertura (respeita filtros da sidebar)

        cobertura_df = df_filtrado if not df_filtrado.empty else df

        total_cadastrados = (
            cobertura_df["QtdAlunoEscola"].sum()
            if "QtdAlunoEscola" in cobertura_df
            else 0
        )

        total_atendidos = (
            cobertura_df["QtdAluno"].sum() if "QtdAluno" in cobertura_df else 0
        )

        if total_cadastrados and total_cadastrados > 0:
            nao_atendidos = max(total_cadastrados - total_atendidos, 0)

            pct_atendidos = (total_atendidos / total_cadastrados) * 100

            df_pie = pd.DataFrame(
                [
                    {"Status": "Atendidos", "Qtd": total_atendidos},
                    {"Status": "Não atendidos", "Qtd": nao_atendidos},
                ]
            )

            fig_cov = px.pie(
                df_pie,
                names="Status",
                values="Qtd",
                hole=0.55,
                title=f"Cobertura de alunos da escola (atendidos / cadastrados) - {pct_atendidos:.1f}%",
                color="Status",
                color_discrete_map={"Atendidos": "#16a34a", "Não atendidos": "#9ca3af"},
            )

            fig_cov.update_traces(
                texttemplate="%{percent:.1%}\n(%{value:,.0f})", textposition="outside"
            )

            fig_cov.update_layout(
                separators=",.",
                showlegend=True,
                title={
                    "text": fig_cov.layout.title.text,
                    "font": {"size": 22},
                },  # mantém padrão de subtítulos
            )

            st.plotly_chart(fig_cov, use_container_width=True)

        else:
            st.info("Sem dados de cobertura para os filtros selecionados.")

        year_cols_present = [c for c in year_cols if c in df_home_ano_exibir.columns]

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

                fig_home_bar.update_layout(separators=",.", legend_title_text="Ano")

                fig_home_bar.update_traces(
                    texttemplate="%{y:,.0f}", textposition="outside"
                )

                st.plotly_chart(fig_home_bar, use_container_width=True)

    if df_filtrado.empty and (anos_str != "Todos" or urgs_str != "Todos"):
        st.warning(
            f"Não há dados disponíveis para a combinação de filtros selecionada (Anos: {anos_str}, URGs: {urgs_str})."
        )

    elif df.empty:
        st.warning("Não há dados carregados no arquivo CSV para exibir.")

    # Gráfico: Distribuição de Atendimentos por Profissional (Pizza)

    st.subheader("Distribuição de Atendimentos por Profissional")

    if not df_filtrado.empty:
        prof_atendimentos_sums = {
            "Professor": (
                df_filtrado["QtdProfessor"].sum()
                if "QtdProfessor" in df_filtrado
                else 0
            ),
            "Psicólogo": (
                df_filtrado["QtdPsicologo"].sum()
                if "QtdPsicologo" in df_filtrado
                else 0
            ),
            "Assist. Social": (
                df_filtrado["QtdAssistSocial"].sum()
                if "QtdAssistSocial" in df_filtrado
                else 0
            ),
            "Enfermagem": (
                df_filtrado["QtdEnfermagem"].sum()
                if "QtdEnfermagem" in df_filtrado
                else 0
            ),
            "Médico": (
                df_filtrado["QtdMedico"].sum() if "QtdMedico" in df_filtrado else 0
            ),
        }

        prof_atendimentos_filtered = {
            key: value for key, value in prof_atendimentos_sums.items() if value > 0
        }

        if prof_atendimentos_filtered:
            df_prof_atend = pd.DataFrame(
                list(prof_atendimentos_filtered.items()),
                columns=["Profissional", "Total Atendimentos"],
            )

            if "Psicólogo" in df_prof_atend["Profissional"].values:
                df_prof_atend["Profissional"] = df_prof_atend["Profissional"].replace(
                    {"Psicólogo": "Psicólogo"}
                )

            fig_prof_pie = px.pie(
                df_prof_atend,
                names="Profissional",
                values="Total Atendimentos",
                hole=0.3,
                title=f"Distribuição do Volume Total de Atendimentos ({filtro_titulo})",
            )

            fig_prof_pie.update_layout(separators=".", legend_title_text="Atendimento")

            st.plotly_chart(fig_prof_pie, use_container_width=True)

        else:
            st.info(
                "Não há dados de atendimentos por profissionais para exibir para a combinação de filtros selecionada."
            )

    elif not df.empty:
        st.info(
            f"Não há dados de atendimentos por profissionais para exibir para a combinação de filtros selecionada (Anos: {anos_str}, URGs: {urgs_str})."
        )

    # Gráfico: Total Anual de Alunos Atendidos por Profissional (Barras)

    st.subheader("Total Anual de Alunos Atendidos por Profissional")

    df_prof_base = df.copy()

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
            grouped_by_year = df_prof_base.groupby("Ano")

            for year, group_df in grouped_by_year:
                for col, name in actual_prof_cols.items():
                    total_atendidos_ano_profissional = group_df[col].sum()

                    if total_atendidos_ano_profissional > 0:
                        total_atendimentos_yearly_data.append(
                            {
                                "Ano": int(year),
                                "Profissional": name,
                                "Total Alunos Atendidos": total_atendidos_ano_profissional,
                            }
                        )

        if total_atendimentos_yearly_data:
            df_prof_total_yearly = pd.DataFrame(total_atendimentos_yearly_data)

            df_prof_total_yearly["Ano"] = df_prof_total_yearly["Ano"].astype(int)

            df_prof_total_yearly = df_prof_total_yearly.sort_values(
                by=["Profissional", "Ano"]
            )

            fig_prof_total_bar_yearly = px.bar(
                df_prof_total_yearly,
                x="Profissional",
                y="Total Alunos Atendidos",
                color=df_prof_total_yearly["Ano"].astype(str),
                barmode="group",
                title="Total Anual de Alunos Atendidos por Profissional",
                text="Total Alunos Atendidos",
            )

            fig_prof_total_bar_yearly.update_layout(
                xaxis={
                    "categoryorder": "array",
                    "categoryarray": list(actual_prof_cols.values()),
                },
                legend_title_text="Ano",
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

    st.subheader("Total Anual por Tipo de Ação")

    df_action_base = df.copy()

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
            ano_action_group = (
                df_action_base.groupby("Ano")[actual_action_cols_orig]
                .sum()
                .reset_index()
            )

            mask_action_not_all_zero = (
                ano_action_group[actual_action_cols_orig].ne(0).any(axis=1)
            )

            ano_action_group = ano_action_group[mask_action_not_all_zero]

            if not ano_action_group.empty:
                rename_map_action_ano = {
                    "QtdEncaminhamento": "Encaminhamento",
                    "QtdExame": "Exame",
                    "QtdVacinacao": "Alunos Vacinados",
                    "QtdVacina": "Doses Vacina",
                }

                actual_rename_map_action_ano = {
                    k: v
                    for k, v in rename_map_action_ano.items()
                    if k in ano_action_group.columns
                }

                ano_action_group_display = ano_action_group.rename(
                    columns=actual_rename_map_action_ano
                )

                id_vars_melt = ["Ano"]

                value_vars_melt = [
                    v
                    for k, v in actual_rename_map_action_ano.items()
                    if v in ano_action_group_display.columns
                ]

                if value_vars_melt:
                    ano_action_group_melted = pd.melt(
                        ano_action_group_display,
                        id_vars=id_vars_melt,
                        value_vars=value_vars_melt,
                        var_name="Ação",
                        value_name="Quantidade",
                    )

                    ano_action_group_melted["Ano"] = ano_action_group_melted[
                        "Ano"
                    ].astype(str)

                    ano_action_group_melted = ano_action_group_melted.sort_values(
                        by="Ano"
                    )

                    fig_ano_action = px.bar(
                        ano_action_group_melted,
                        x="Ano",
                        y="Quantidade",
                        color="Ação",
                        barmode="group",
                        title="Total Anual por Tipo de Ação",
                        text="Quantidade",
                    )

                    fig_ano_action.update_layout(
                        separators=",.", xaxis={"type": "category"}
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

    st.markdown("---")

    st.subheader("Comparativo Anual por URG")

    if df_urg_ano.empty:
        st.info(
            "Dados agregados por URG/ano não estão disponíveis ou houve erro na leitura do CSV."
        )

    else:
        df_urg_exibir = df_urg_ano.copy()

        urgs_aplicadas_home = selections.get("urg", [])

        if urgs_aplicadas_home and "URG" in df_urg_exibir.columns:
            df_urg_exibir = df_urg_exibir[
                df_urg_exibir["URG"].isin(urgs_aplicadas_home)
            ]

        year_cols = ["2022", "2023", "2024", "2025"]

        numeric_cols = [
            col for col in year_cols + ["Total"] if col in df_urg_exibir.columns
        ]

        if numeric_cols:
            df_urg_exibir[numeric_cols] = df_urg_exibir[numeric_cols].apply(
                pd.to_numeric, errors="coerce"
            )

        for prev, curr in zip(year_cols, year_cols[1:]):
            if prev in df_urg_exibir.columns and curr in df_urg_exibir.columns:
                abs_col = f"Var {curr[-2:]}-{prev[-2:]}"

                pct_col = f"Var% {curr[-2:]}-{prev[-2:]}"

                df_urg_exibir[abs_col] = df_urg_exibir[curr] - df_urg_exibir[prev]

                df_urg_exibir[pct_col] = (
                    df_urg_exibir[abs_col]
                    / df_urg_exibir[prev].replace({0: np.nan})
                    * 100
                )

        col_order_urg = []

        if "URG" in df_urg_exibir.columns:
            col_order_urg.append("URG")

        if "Descricao" in df_urg_exibir.columns:
            col_order_urg.append("Descricao")

        for prev, curr in zip(year_cols, year_cols[1:]):
            if prev in df_urg_exibir.columns:
                col_order_urg.append(prev)

            abs_col = f"Var {curr[-2:]}-{prev[-2:]}"

            pct_col = f"Var% {curr[-2:]}-{prev[-2:]}"

            if abs_col in df_urg_exibir.columns:
                col_order_urg.append(abs_col)

            if pct_col in df_urg_exibir.columns:
                col_order_urg.append(pct_col)

        if year_cols[-1] in df_urg_exibir.columns:
            col_order_urg.append(year_cols[-1])

        if "Total" in df_urg_exibir.columns:
            col_order_urg.append("Total")

        remaining_cols_urg = [
            col for col in df_urg_exibir.columns if col not in col_order_urg
        ]

        df_urg_exibir = df_urg_exibir[col_order_urg + remaining_cols_urg]

        pct_cols_urg = [c for c in df_urg_exibir.columns if c.startswith("Var% ")]

        df_urg_display = df_urg_exibir.copy()

        abs_cols_urg = [
            c
            for c in df_urg_display.columns
            if c in year_cols or c == "Total" or c.startswith("Var ")
        ]

        for c in abs_cols_urg:
            df_urg_display[c] = df_urg_display[c].map(
                lambda x: f"{x:,.0f}".replace(",", ".") if pd.notna(x) else ""
            )

        for c in pct_cols_urg:
            df_urg_display[c] = df_urg_display[c].map(
                lambda x: f"{x:,.1f}".replace(",", ".") if pd.notna(x) else ""
            )

        numeric_like_cols_urg = [
            c for c in df_urg_display.columns if c not in ["Descricao", "URG"]
        ]

        styler_urg = df_urg_display.style.set_properties(
            subset=numeric_like_cols_urg, **{"text-align": "right"}
        ).hide(axis="index")

        st.dataframe(styler_urg, use_container_width=True, hide_index=True)

        if st.button("Copiar tabela (Comparativo URG)", key="copy_home_urg_table"):
            try:
                df_urg_exibir.to_clipboard(index=False, excel=True)

                st.success("Tabela copiada. Cole no Excel com Ctrl+V.")

            except Exception as exc:
                st.error(f"Não foi possível copiar automaticamente: {exc}")

    # Gráfico: Distribuição de Atendimentos por Profissional por URG

    st.subheader("Distribuição de Atendimentos por Profissional por URG")

    if not df_filtrado.empty:
        prof_cols_orig = [
            "QtdProfessor",
            "QtdPsicologo",
            "QtdAssistSocial",
            "QtdEnfermagem",
            "QtdMedico",
        ]

        urg_prof_group = df_filtrado.groupby("URG")[prof_cols_orig].sum().reset_index()

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

    elif not df.empty:
        st.info(
            f"Não há dados de profissionais por URG para exibir para a combinação de filtros selecionada (Anos: {anos_str}, URGs: {urgs_str})."
        )

    # Gráfico: Distribuição de Ações por URG

    st.subheader("Distribuição de Ações por URG")

    if not df_filtrado.empty:
        urg_group = (
            df_filtrado.groupby("URG")[
                ["QtdEncaminhamento", "QtdExame", "QtdVacinacao", "QtdVacina"]
            ]
            .sum()
            .reset_index()
        )

        urg_group = urg_group[
            (urg_group["QtdEncaminhamento"] != 0)
            | (urg_group["QtdExame"] != 0)
            | (urg_group["QtdVacinacao"] != 0)
            | (urg_group["QtdVacina"] != 0)
        ]

        if not urg_group.empty:
            urg_group_display = urg_group.rename(
                columns={
                    "QtdEncaminhamento": "Encaminhamento",
                    "QtdExame": "Exame",
                    "QtdVacinacao": "Alunos Vacinados",
                    "QtdVacina": "Doses Vacina",
                }
            )

            fig_urg = px.bar(
                urg_group_display,
                x="URG",
                y=["Encaminhamento", "Exame", "Alunos Vacinados", "Doses Vacina"],
                barmode="group",
                title=f"Ações por URG ({filtro_titulo})",
                labels={"value": "Quantidade", "variable": "Ação"},
            )

            fig_urg.update_layout(separators=",.")

            fig_urg.update_traces(texttemplate="%{value:,.0f}", textposition="outside")

            st.plotly_chart(fig_urg, use_container_width=True)

        else:
            st.info(
                f"Não há dados de ações para exibir para as URGs selecionadas ({urgs_str}) nos anos ({anos_str})."
            )

    elif not df.empty:
        st.info(
            f"Não há dados de URG para exibir para a combinação de filtros selecionada (Anos: {anos_str}, URGs: {urgs_str})."
        )

    # Detalhamento dos Dados

    st.markdown("---")

    st.subheader(f"Detalhamento dos Dados ({filtro_titulo})")

    # Initialize df_for_export. It will be populated if df_filtrado is not empty.

    # Otherwise, it remains an empty DataFrame, which to_csv handles by producing an empty file or just headers.

    df_for_export = pd.DataFrame()

    if not df_filtrado.empty:
        df_for_school_filter = df_filtrado.copy()

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

        if (
            st.session_state.inicio_sem_fechamento_option == "Aberto"
        ):  # ATUALIZADO para "Aberto"
            # Regra 1: Escolas com DtInicio E sem DtFechamento

            if "DtInicio" in df_currently_filtered.columns:
                condition_inicio_present = df_currently_filtered["DtInicio"].notnull()

                if "DtFechamento" in df_currently_filtered.columns:
                    condition_fechamento_absent = df_currently_filtered[
                        "DtFechamento"
                    ].isnull()

                    df_currently_filtered = df_currently_filtered[
                        condition_inicio_present & condition_fechamento_absent
                    ].copy()

                else:  # Coluna DtFechamento não existe, então é efetivamente sempre nula para esta condição
                    df_currently_filtered = df_currently_filtered[
                        condition_inicio_present
                    ].copy()

            else:  # Coluna DtInicio não existe, então nenhuma escola pode satisfazer a condição "Início"
                df_currently_filtered = df_currently_filtered.iloc[
                    0:0
                ].copy()  # Retorna DataFrame vazio

        elif (
            st.session_state.inicio_sem_fechamento_option == "Fechado"
        ):  # ATUALIZADO para "Fechado"
            # Regra 2: Filtra todas as escolas com data de fechamento

            if "DtFechamento" in df_currently_filtered.columns:
                df_currently_filtered = df_currently_filtered[
                    df_currently_filtered["DtFechamento"].notnull()
                ].copy()

            else:  # Coluna DtFechamento não existe, então nenhuma escola pode satisfazer a condição "Fechamento"
                df_currently_filtered = df_currently_filtered.iloc[
                    0:0
                ].copy()  # Retorna DataFrame vazio

        # Se st.session_state.inicio_sem_fechamento_option == "Todas":

        # Nenhuma ação é necessária, df_currently_filtered permanece como está.

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
                df_filtrado_for_sum = df_filtrado.copy()

                df_filtrado_for_sum.loc[:, "QtdAlunoEscola"] = pd.to_numeric(
                    df_filtrado_for_sum["QtdAlunoEscola"], errors="coerce"
                ).fillna(0)

                total_aluno_sum_per_ano_from_sidebar = df_filtrado_for_sum.groupby(
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
                        if not pd.api.types.is_object_dtype(
                            target_total_df[col_name_pct].dtype
                        ):
                            target_total_df.loc[:, col_name_pct] = target_total_df[
                                col_name_pct
                            ].astype("object")

                        if pd.isna(
                            target_total_df.at[target_total_df.index[-1], col_name_pct]
                        ):
                            target_total_df.at[
                                target_total_df.index[-1], col_name_pct
                            ] = ""

            # End of 'if actual_cols_to_sum:'

        # Após adicionar a linha de total, converter 'Ano' para string para evitar problemas com Arrow

        if "Ano" in df_display.columns:
            df_display.loc[:, "Ano"] = (
                df_display["Ano"]
                .astype(str)
                .replace({"<NA>": "", "nan": "", "None": ""})
            )

        if not df_total_row_for_display.empty:
            if "Ano" in df_total_row_for_display.columns:
                df_total_row_for_display.loc[:, "Ano"] = (
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
            empty_rows_mask = df_display.replace("", np.nan).isna().all(axis=1)

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

            df_grid_data = df_display

            # Cálculo de altura usando a nova função genérica

            grid_height = calcular_altura_aggrid(
                df=df_grid_data,
                limite_linhas=selected_limit,
                incluir_total=not df_total_row_for_display.empty,
            )

            st.markdown(
                """
            <style>
                .home-toolbar-row {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    justify-content: flex-start;
                    margin-bottom: 0.25rem;
                }

                .home-toolbar-row div[data-testid="stHorizontalBlock"] {
                    gap: 10px !important;
                    justify-content: flex-start !important;
                    align-items: center !important;
                }

                .home-toolbar-row div[data-testid="column"] {
                    flex: 0 0 auto !important;
                    min-width: 0 !important;
                }

                .home-toolbar-status {
                    font-size: 0.75rem;
                    color: #666666;
                    display: inline-block;
                    margin-top: 0.25rem;
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
                    if (!params.columnApi) {
                        return;
                    }
                    const allColumnIds = [];
                    params.columnApi.getColumns().forEach(function(column) {
                        if (column && column.getId) {
                            allColumnIds.push(column.getId());
                        }
                    });
                    if (allColumnIds.length > 0) {
                        params.columnApi.autoSizeColumns(allColumnIds, false);
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

            csv_visible_data = df_display_for_export.to_csv(
                index=False, sep=";"
            ).encode("utf-8-sig")

            toolbar_container = st.container()

            with toolbar_container:
                st.markdown('<div class="home-toolbar-row">', unsafe_allow_html=True)

                column_col, export_col = st.columns([1, 1], gap="small")

                with column_col:
                    column_toggle_clicked = st.button(
                        "Colunas",
                        key="home_toolbar_column_toggle",
                        help="Mostrar/ocultar colunas da tabela",
                    )

                    if column_toggle_clicked:
                        st.session_state["home_show_column_selector"] = (
                            not st.session_state["home_show_column_selector"]
                        )

                st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state["home_show_column_selector"]:
                selected_hidden_columns = st.multiselect(
                    "Colunas a ocultar",
                    options=available_columns,
                    default=selected_hidden_columns,
                    key="home_hidden_columns_selector",
                    help="Selecione as colunas que deseja ocultar na tabela",
                )

                st.session_state["home_hidden_columns"] = selected_hidden_columns

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

            AgGrid(
                df_grid_data,
                gridOptions=grid_options,
                height=grid_height,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=False,
                theme="streamlit",
            )

            copy_feedback_placeholder = st.empty()
            copy_row = st.columns([1.4, 1.2, 4.4])
            with copy_row[0]:
                if st.button(
                    "Copiar tabela (Detalhamento)",
                    key="copy_home_detail_table_aggrid",
                    help="Copiar tabela (Detalhamento dos Dados) para a área de transferência",
                ):
                    try:
                        df_display_for_copy.to_clipboard(index=False, excel=True)
                        copy_feedback_placeholder.success(
                            "Tabela copiada. Cole no Excel usando Ctrl+V."
                        )
                    except Exception as clipboard_exc:
                        copy_feedback_placeholder.error(
                            f"Não foi possível copiar automaticamente: {clipboard_exc}"
                        )
            with copy_row[1]:
                st.download_button(
                    label="Exportar CSV",
                    data=csv_visible_data,
                    file_name="detalhamento_home.csv",
                    mime="text/csv",
                    key="download_csv_home_visible_aggrid_bottom",
                    help="Exportar tabela (CSV)",
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

    st.markdown("---")

    st.subheader("Comparativo Anual por Escola")

    if df_escola_ano.empty:
        st.info(
            "Dados agregados por escola/ano não estão disponíveis ou houve erro na leitura do CSV."
        )

    else:
        df_escola_exibir = df_escola_ano.copy()

        urgs_aplicadas_home = selections.get("urg", [])

        if urgs_aplicadas_home and "URG" in df_escola_exibir.columns:
            df_escola_exibir = df_escola_exibir[
                df_escola_exibir["URG"].isin(urgs_aplicadas_home)
            ]
        escolas_aplicadas_home = selections.get("escola", [])
        if escolas_aplicadas_home and "Escola" in df_escola_exibir.columns:
            df_escola_exibir = df_escola_exibir[
                df_escola_exibir["Escola"].astype(str).isin(escolas_aplicadas_home)
            ]
        year_cols_escola = ["2022", "2023", "2024", "2025"]

        numeric_cols_escola = [
            c for c in year_cols_escola + ["Total"] if c in df_escola_exibir.columns
        ]

        if numeric_cols_escola:
            df_escola_exibir[numeric_cols_escola] = df_escola_exibir[
                numeric_cols_escola
            ].apply(pd.to_numeric, errors="coerce")

        for prev, curr in zip(year_cols_escola, year_cols_escola[1:]):
            if prev in df_escola_exibir.columns and curr in df_escola_exibir.columns:
                abs_col = f"Var {curr[-2:]}-{prev[-2:]}"

                pct_col = f"Var% {curr[-2:]}-{prev[-2:]}"

                df_escola_exibir[abs_col] = (
                    df_escola_exibir[curr] - df_escola_exibir[prev]
                )

                df_escola_exibir[pct_col] = (
                    df_escola_exibir[abs_col]
                    / df_escola_exibir[prev].replace({0: np.nan})
                    * 100
                )

        col_order_escola = []

        if "URG" in df_escola_exibir.columns:
            col_order_escola.append("URG")

        if "Escola" in df_escola_exibir.columns:
            col_order_escola.append("Escola")

        if "Descricao" in df_escola_exibir.columns:
            col_order_escola.append("Descricao")

        for prev, curr in zip(year_cols_escola, year_cols_escola[1:]):
            if prev in df_escola_exibir.columns:
                col_order_escola.append(prev)

            abs_col = f"Var {curr[-2:]}-{prev[-2:]}"

            pct_col = f"Var% {curr[-2:]}-{prev[-2:]}"

            if abs_col in df_escola_exibir.columns:
                col_order_escola.append(abs_col)

            if pct_col in df_escola_exibir.columns:
                col_order_escola.append(pct_col)

        if year_cols_escola[-1] in df_escola_exibir.columns:
            col_order_escola.append(year_cols_escola[-1])

        if "Total" in df_escola_exibir.columns:
            col_order_escola.append("Total")

        remaining_cols_escola = [
            c for c in df_escola_exibir.columns if c not in col_order_escola
        ]

        df_escola_exibir = df_escola_exibir[col_order_escola + remaining_cols_escola]

        pct_cols_escola = [c for c in df_escola_exibir.columns if c.startswith("Var% ")]

        df_escola_display = df_escola_exibir.copy()

        abs_cols_escola = [
            c
            for c in df_escola_display.columns
            if c in year_cols_escola or c == "Total" or c.startswith("Var ")
        ]

        for c in abs_cols_escola:
            df_escola_display[c] = df_escola_display[c].map(
                lambda x: f"{x:,.0f}".replace(",", ".") if pd.notna(x) else ""
            )

        for c in pct_cols_escola:
            df_escola_display[c] = df_escola_display[c].map(
                lambda x: f"{x:,.1f}".replace(",", ".") if pd.notna(x) else ""
            )

        numeric_like_cols_escola = [
            c
            for c in df_escola_display.columns
            if c not in ["Descricao", "URG", "Escola"]
        ]

        styler_escola = df_escola_display.style.set_properties(
            subset=numeric_like_cols_escola, **{"text-align": "right"}
        ).hide(axis="index")

        st.dataframe(styler_escola, use_container_width=True, hide_index=True)

        if st.button(
            "Copiar tabela (Comparativo Escola)", key="copy_home_escola_table"
        ):
            try:
                df_escola_exibir.to_clipboard(index=False, excel=True)

                st.success("Tabela copiada. Cole no Excel com Ctrl+V.")

            except Exception as exc:
                st.error(f"Não foi possível copiar automaticamente: {exc}")

    footer_personal()


# streamlit run app.py
