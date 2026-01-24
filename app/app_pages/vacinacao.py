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
from app.utils.schemas import (
    SCHEMA_VACINACAO,
    SCHEMA_VACINACAO_ALUNO,
    SCHEMA_VACINACAO_ANO,
)
from app.utils.styles import apply_global_css, render_metric_cards


@st.cache_data(ttl=3600, show_spinner="Carregando dados de vacinação...")
def carregar_dados_vacinacao():
    csv_file = "data/DashboardVacinacao.csv"
    df, info = load_csv(csv_file, expected_cols=SCHEMA_VACINACAO)

    csv_file_aluno = "data/DashboardVacinacaoAluno.csv"
    df_aluno_raw, info_aluno = load_csv(
        csv_file_aluno, expected_cols=SCHEMA_VACINACAO_ALUNO
    )

    csv_file_ano = "data/DashboardVacinacaoAno.csv"
    df_ano, info_ano = load_csv(csv_file_ano, expected_cols=SCHEMA_VACINACAO_ANO)

    return {
        "principal": {"df": df, "info": info, "csv": csv_file},
        "aluno": {"df": df_aluno_raw, "info": info_aluno, "csv": csv_file_aluno},
        "ano": {"df": df_ano, "info": info_ano, "csv": csv_file_ano},
    }


def page_vacinacao():
    st.title("Visão Geral da Vacinação")
    st.markdown(
        "Resumo consolidado das ações realizadas por ano, URG e equipe técnica."
    )
    filters_placeholder = st.empty()
    st.markdown("---")

    apply_global_css()
    datasets = carregar_dados_vacinacao()

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
            "Vacina": "Vacina",
            "Qtd": "Quantidade",
            "tipo": "Tipo",
        }
    )

    df_aluno = df_aluno_raw.rename(
        columns={
            "Vacina": "Vacina",
            "DtNasc": "DataNascimento",
        }
    ).copy()
    if not df_aluno.empty and "DataNascimento" in df_aluno.columns:
        df_aluno["DataNascimento"] = pd.to_datetime(
            df_aluno["DataNascimento"], errors="coerce"
        )

    df_ano_exibir = df_ano.copy() if not df_ano.empty else pd.DataFrame()

    st.sidebar.title("Filtros - Vacinação")

    df_filt_sidebar, selections = sidebar_filters(
        df,
        {"ano": True, "urg": True, "escola": True, "tipo": True},
    )

    vacina_col = "Vacina"
    vacinas_disponiveis = (
        sorted(df_filt_sidebar[vacina_col].dropna().unique())
        if vacina_col in df_filt_sidebar.columns
        else []
    )
    vacinas_selecionadas = st.sidebar.multiselect(
        "Selecione o(s) Tipo(s) de Vacina:",
        options=vacinas_disponiveis,
        default=[],
        placeholder="Todas",
        key="vacinacao_vacina_multiselect",
    )

    df_filt = (
        df_filt_sidebar[df_filt_sidebar[vacina_col].isin(vacinas_selecionadas)]
        if vacinas_selecionadas and vacina_col in df_filt_sidebar.columns
        else df_filt_sidebar
    )
    selections["vacina"] = vacinas_selecionadas or vacinas_disponiveis
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
                ("vacina", "Vacina", "Vacina"),
            ],
        )
    )
    urgs_aplicadas = selections.get("urg", [])

    st.sidebar.markdown("---")
    st.sidebar.subheader("Exportar dados")
    csv_export_encoding = "utf-8"
    csv = df_filt.to_csv(index=False, sep=";").encode(csv_export_encoding)
    st.sidebar.download_button(
        label="Exportar CSV (Vacinação)",
        data=csv,
        file_name="dados_filtrados_vacinacao.csv",
        mime="text/csv",
    )

    st.subheader("Indicadores Gerais")
    render_metric("Total de Aplicações de Vacinas", df_filt["Quantidade"].sum())
    # Sumário por tipo de Vacina em linhas de 5 colunas, apenas com totais > 0
    vacinas_sum = (
        df_filt.groupby("Vacina")["Quantidade"].sum().sort_values(ascending=False)
        if not df_filt.empty and "Vacina" in df_filt.columns
        else pd.Series(dtype="float")
    )
    vacinas_sum = vacinas_sum[vacinas_sum > 0]
    if not vacinas_sum.empty:
        for start in range(0, len(vacinas_sum), 5):
            slice_vac = vacinas_sum.iloc[start : start + 5]
            cols = st.columns(5)
            for col, (nome, valor) in zip(cols, slice_vac.items()):
                with col:
                    render_metric_cards([(f"{nome}", valor)])
    st.markdown("---")

    st.subheader("Comparativo Anual Geral")
    df_cmp_display = build_comparativo_anual(df_filt, "Vacina")
    if df_cmp_display is None:
        st.info(
            "Nenhum dado disponível para o comparativo anual geral com os filtros atuais."
        )
    else:
        st.dataframe(df_cmp_display, width="stretch", hide_index=True)

    st.subheader("Distribuição por Tipo de Vacina")
    vacina_group = df_filt.groupby("Vacina")["Quantidade"].sum().reset_index()
    if vacina_group.empty:
        st.info("Nenhum dado de vacina para exibir.")
    else:
        vacina_group["% do Total"] = (
            100 * vacina_group["Quantidade"] / vacina_group["Quantidade"].sum()
        ).round(2).astype(str) + "%"
        fig_vacina = px.bar(
            vacina_group.sort_values("Quantidade", ascending=False),
            x="Quantidade",
            y="Vacina",
            orientation="h",
            text="% do Total",
            color="Vacina",
        )
        fig_vacina.update_traces(textposition="auto")
        st.plotly_chart(fig_vacina, width="stretch")
        st.dataframe(
            vacina_group.sort_values("Quantidade", ascending=False),
            width="stretch",
            hide_index=True,
        )
        st.markdown(
            f"**Total: {vacina_group['Quantidade'].sum():,.0f}**".replace(",", ".")
        )

    render_top_por_urg(df_filt, "Quantidade", "Principais Escolas por URG", "Escola")
    render_top_por_urg(df_filt, "Quantidade", "Principais Vacinas por URG", "Vacina")

    st.subheader("Comparativo Anual de Vacinação")
    if df_ano_exibir.empty:
        st.info(
            "Dados agregados de Vacinação por ano não estão disponíveis ou houve erro na leitura do CSV."
        )
    else:
        df_ano_filtrado = df_ano_exibir.copy()
        if urgs_aplicadas and "URG" in df_ano_filtrado.columns:
            df_ano_filtrado = df_ano_filtrado[
                df_ano_filtrado["URG"].isin(urgs_aplicadas)
            ]
        escolas_disponiveis_ano = (
            sorted(df_ano_filtrado["Escola"].dropna().astype(str).unique())
            if "Escola" in df_ano_filtrado.columns
            else []
        )
        escolas_selecionadas_ano = st.multiselect(
            "Filtrar Escola no comparativo anual",
            options=escolas_disponiveis_ano,
            default=[],
            placeholder="Todas as Escolas",
            key="vacinacao_comparativo_escola",
        )
        if escolas_selecionadas_ano and "Escola" in df_ano_filtrado.columns:
            df_ano_filtrado = df_ano_filtrado[
                df_ano_filtrado["Escola"].astype(str).isin(escolas_selecionadas_ano)
            ]

        st.dataframe(df_ano_filtrado, width="stretch", hide_index=True)

    st.markdown("---")
    st.subheader("Detalhamento por Aluno (VacinacaoAluno)")
    if df_aluno.empty:
        st.info(
            "Dados de alunos não estão disponíveis ou houve erro na leitura do CSV."
        )
    else:
        df_aluno_filtrado = filter_by_sidebar_selections(df_aluno, selections)
        if vacinas_selecionadas and "Vacina" in df_aluno_filtrado.columns:
            df_aluno_filtrado = df_aluno_filtrado[
                df_aluno_filtrado["Vacina"].isin(vacinas_selecionadas)
            ]

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
            + (" e de vacina" if vacinas_selecionadas else "")
        )

        if df_aluno_filtrado.empty:
            st.warning("Nenhum registro de aluno para os filtros selecionados." )
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
                df_aluno_para_exibir["Menu"] = df_aluno_para_exibir.apply(
                    build_perfil_link, axis=1
                )
            if "DataNascimento" in df_aluno_para_exibir.columns:
                df_aluno_para_exibir["DataNascimento"] = pd.to_datetime(
                    df_aluno_para_exibir["DataNascimento"], errors="coerce"
                ).dt.strftime("%d/%m/%Y")

            preview_limit = 500
            st.dataframe(
                df_aluno_para_exibir.head(preview_limit),
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
                label="Exportar CSV (Vacinacao por aluno)",
                data=csv_aluno,
                file_name="dados_filtrados_vacinacao_aluno.csv",
                mime="text/csv",
            )

    st.markdown(" ")
    footer_personal()
