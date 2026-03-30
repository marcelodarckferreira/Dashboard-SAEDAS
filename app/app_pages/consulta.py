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
    SCHEMA_CONSULTA,
    SCHEMA_CONSULTA_ALUNO,
    SCHEMA_CONSULTA_ANO,
)
from app.utils.styles import apply_global_css, render_metric_cards


@st.cache_data(ttl=3600, show_spinner="Carregando dados de consultas...")
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
    st.title("Visão Geral do Encaminhamento (Regulação)")
    st.markdown(
        "Resumo consolidado das ações realizadas por ano, URG e equipe técnica."
    )
    filters_placeholder = st.empty()
    st.markdown("---")

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

    encaminhamento_col = "Encaminhamento"
    encaminhamentos_disponiveis = (
        sorted(df_filt_sidebar[encaminhamento_col].dropna().unique())
        if encaminhamento_col in df_filt_sidebar.columns
        else []
    )
    encaminhamentos_selecionados = st.sidebar.multiselect(
        "Selecione a(s) Regulação(ões):",
        options=encaminhamentos_disponiveis,
        default=[],
        placeholder="Todas",
        key="consulta_encaminhamento_multiselect",
    )

    df_filt = (
        df_filt_sidebar[
            df_filt_sidebar[encaminhamento_col].isin(encaminhamentos_selecionados)
        ]
        if encaminhamentos_selecionados
        and encaminhamento_col in df_filt_sidebar.columns
        else df_filt_sidebar
    )
    selections["encaminhamento"] = (
        encaminhamentos_selecionados or encaminhamentos_disponiveis
    )
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
    urgs_aplicadas = selections.get("urg", [])

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

    st.subheader("Indicadores Gerais")
    render_metric("Total de Encaminhamentos", df_filt["Quantidade"].sum())

    # Sumário por tipo de consulta (Encaminhamento) em linhas de 5 colunas, apenas com totais > 0
    encaminhamentos_sum = (
        df_filt.groupby("Encaminhamento")["Quantidade"]
        .sum()
        .sort_values(ascending=False)
        if not df_filt.empty and "Encaminhamento" in df_filt.columns
        else pd.Series(dtype="float")
    )
    encaminhamentos_sum = encaminhamentos_sum[encaminhamentos_sum > 0]
    if not encaminhamentos_sum.empty:
        for start in range(0, len(encaminhamentos_sum), 5):
            slice_enc = encaminhamentos_sum.iloc[start : start + 5]
            cols = st.columns(5)
            for col, (nome, valor) in zip(cols, slice_enc.items()):
                with col:
                    render_metric_cards([(f"{nome}", valor)])
    st.markdown("---")

    st.subheader("Comparativo Anual Geral")
    df_cmp_display = build_comparativo_anual(df_filt, "Encaminhamento")
    if df_cmp_display is None:
        st.info(
            "Nenhum dado disponível para o comparativo anual geral com os filtros atuais."
        )
    else:
        st.dataframe(df_cmp_display, use_container_width=True, hide_index=True)

    st.subheader("Distribuição por Regulação")
    reg_group = df_filt.groupby("Encaminhamento")["Quantidade"].sum().reset_index()
    if reg_group.empty:
        st.info("Nenhum dado de Regulação para exibir.")
    else:
        reg_group["% do Total"] = (
            100 * reg_group["Quantidade"] / reg_group["Quantidade"].sum()
        ).round(2).astype(str) + "%"
        fig_reg = px.bar(
            reg_group.sort_values("Quantidade", ascending=False),
            x="Quantidade",
            y="Encaminhamento",
            orientation="h",
            text="% do Total",
            color="Encaminhamento",
        )
        fig_reg.update_traces(textposition="auto")
        st.plotly_chart(fig_reg, use_container_width=True)
        st.dataframe(
            reg_group.sort_values("Quantidade", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown(
            f"**Total: {reg_group['Quantidade'].sum():,.0f}**".replace(",", ".")
        )

    render_top_por_urg(df_filt, "Quantidade", "Principais Escolas por URG", "Escola")
    render_top_por_urg(
        df_filt, "Quantidade", "Principais Encaminhamentos por URG", "Encaminhamento"
    )

    st.subheader("Comparativo Anual de Encaminhamentos")
    if df_ano_exibir.empty:
        st.info(
            "Dados agregados de Encaminhamentos por ano não estão disponíveis ou houve erro na leitura do CSV."
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
            key="consulta_comparativo_escola",
        )
        if escolas_selecionadas_ano and "Escola" in df_ano_filtrado.columns:
            df_ano_filtrado = df_ano_filtrado[
                df_ano_filtrado["Escola"].astype(str).isin(escolas_selecionadas_ano)
            ]

        st.dataframe(df_ano_filtrado, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Detalhamento por Aluno (ConsultaAluno)")
    if df_aluno.empty:
        st.info(
            "Dados de alunos não estão disponíveis ou houve erro na leitura do CSV."
        )
    else:
        df_aluno_filtrado = filter_by_sidebar_selections(df_aluno, selections)
        if (
            encaminhamentos_selecionados
            and "Encaminhamento" in df_aluno_filtrado.columns
        ):
            df_aluno_filtrado = df_aluno_filtrado[
                df_aluno_filtrado["Encaminhamento"].isin(encaminhamentos_selecionados)
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
