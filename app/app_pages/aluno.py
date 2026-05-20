import pandas as pd
import plotly.express as px
import streamlit as st

from components.footer_personal import footer_personal
from app.utils.data_loader import load_csv
from app.utils.page_helpers import (
    render_metric_cards,
    render_metric,
    format_filters_applied,
)
from app.utils.styles import apply_global_css
from app.utils.schemas import (
    SCHEMA_CONSULTA_ALUNO,
    SCHEMA_EXAME_ALUNO,
    SCHEMA_VACINACAO_ALUNO,
    SCHEMA_NUTRICAO_ALUNO,
    SCHEMA_MEDICO_ALUNO,
    SCHEMA_ENFERMAGEM_ALUNO,
    SCHEMA_PROFESSOR_ALUNO,
    SCHEMA_PSICOLOGO_ALUNO,
    SCHEMA_ASSISTENCIA_SOCIAL_ALUNO,
)


def carregar_dados_aluno():
    def load_wrapper(path: str, schema: set[str]):
        df, info = load_csv(path, expected_cols=schema)
        return df, info

    consulta_df, consulta_info = load_wrapper(
        "data/DashboardConsultaAluno.csv", SCHEMA_CONSULTA_ALUNO
    )
    exame_df, exame_info = load_wrapper(
        "data/DashboardExameAluno.csv", SCHEMA_EXAME_ALUNO
    )
    vac_df, vac_info = load_wrapper(
        "data/DashboardVacinacaoAluno.csv", SCHEMA_VACINACAO_ALUNO
    )
    nutri_df, nutri_info = load_wrapper(
        "data/DashboardNutricaoAluno.csv", SCHEMA_NUTRICAO_ALUNO
    )
    med_df, med_info = load_wrapper(
        "data/DashboardMedicoAluno.csv", SCHEMA_MEDICO_ALUNO
    )
    enf_df, enf_info = load_wrapper(
        "data/DashboardEnfermagemAluno.csv", SCHEMA_ENFERMAGEM_ALUNO
    )
    prof_df, prof_info = load_wrapper(
        "data/DashboardProfessorAluno.csv", SCHEMA_PROFESSOR_ALUNO
    )
    psico_df, psico_info = load_wrapper(
        "data/DashboardPsicologoAluno.csv", SCHEMA_PSICOLOGO_ALUNO
    )
    as_df, as_info = load_wrapper(
        "data/DashboardAssistenciaSocialAluno.csv", SCHEMA_ASSISTENCIA_SOCIAL_ALUNO
    )

    return {
        "consulta": {
            "df": consulta_df,
            "info": consulta_info,
            "label": "Encaminhamento",
            "arquivo": "DashboardConsultaAluno.csv",
        },
        "exame": {
            "df": exame_df,
            "info": exame_info,
            "label": "Exame",
            "arquivo": "DashboardExameAluno.csv",
        },
        "vacina": {
            "df": vac_df,
            "info": vac_info,
            "label": "Vacinação",
            "arquivo": "DashboardVacinacaoAluno.csv",
        },
        "nutricao": {
            "df": nutri_df,
            "info": nutri_info,
            "label": "Nutrição",
            "arquivo": "DashboardNutricaoAluno.csv",
        },
        "medico": {
            "df": med_df,
            "info": med_info,
            "label": "Médico",
            "arquivo": "DashboardMedicoAluno.csv",
        },
        "enfermagem": {
            "df": enf_df,
            "info": enf_info,
            "label": "Enfermagem",
            "arquivo": "DashboardEnfermagemAluno.csv",
        },
        "professor": {
            "df": prof_df,
            "info": prof_info,
            "label": "Professor",
            "arquivo": "DashboardProfessorAluno.csv",
        },
        "psicologo": {
            "df": psico_df,
            "info": psico_info,
            "label": "Psicólogo",
            "arquivo": "DashboardPsicologoAluno.csv",
        },
        "assistencia_social": {
            "df": as_df,
            "info": as_info,
            "label": "Assistência Social",
            "arquivo": "DashboardAssistenciaSocialAluno.csv",
        },
    }


def page_aluno():
    # Suporte a deep-link direto (?menu=Aluno&aluno=...&nasc=YYYY-MM-DD)
    params = st.query_params
    if "aluno_preselect" not in st.session_state and (
        "aluno" in params or params.get("menu") in (["Aluno"], "Aluno")
    ):
        def _first(value):
            if isinstance(value, list):
                return value[0] if value else None
            return value

        aluno_param = _first(params.get("aluno"))
        nasc_param = _first(params.get("nasc"))
        if aluno_param:
            st.session_state["aluno_preselect"] = {
                "nome": str(aluno_param),
                "nasc": nasc_param,
            }

    st.title("Perfil do Aluno")
    st.markdown(
        "Resumo unificado com histórico de encaminhamentos, exames, vacinação e nutrição."
    )
    filters_placeholder = st.empty()
    # apply_global_css() — Já injetado no main.py
    st.markdown("---")

    datasets = carregar_dados_aluno()

    # Avisos de carga
    for key, meta in datasets.items():
        info = meta["info"]
        if info["erros"]:
            st.warning(f"Falha ao ler '{meta['arquivo']}': " + "; ".join(info["erros"]))
            meta["df"] = pd.DataFrame()
        elif info["alertas"]:
            st.info("; ".join(info["alertas"]))

    def prepare_df(
        df: pd.DataFrame,
        categoria: str,
        evento_col: str,
        evento_label: str = "Evento",
    ) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        renamed = df.rename(
            columns={evento_col: evento_label, "DtNasc": "DataNascimento"}
        ).copy()
        renamed["Categoria"] = categoria
        if "Ano" in renamed:
            renamed["Ano"] = pd.to_numeric(renamed["Ano"], errors="coerce")
        if "Aluno" in renamed:
            renamed["Aluno"] = renamed["Aluno"].astype(str).str.strip()
        if "DataNascimento" in renamed:
            renamed["DataNascimento"] = pd.to_datetime(
                renamed["DataNascimento"], errors="coerce"
            )
        return renamed

    df_consulta = prepare_df(datasets["consulta"]["df"], "Encaminhamento", "Consulta")
    df_exame = prepare_df(datasets["exame"]["df"], "Exame", "Exame")
    df_vac = prepare_df(datasets["vacina"]["df"], "Vacinação", "Vacina")
    df_nutri = prepare_df(
        datasets["nutricao"]["df"], "Nutrição", "Nutricao", evento_label="Classificação"
    )
    df_med = prepare_df(datasets["medico"]["df"], "Médico", "Profissional")
    df_enf = prepare_df(datasets["enfermagem"]["df"], "Enfermagem", "Profissional")
    df_prof = prepare_df(datasets["professor"]["df"], "Professor", "Profissional")
    df_psico = prepare_df(datasets["psicologo"]["df"], "Psicólogo", "Profissional")
    df_as = prepare_df(datasets["assistencia_social"]["df"], "Assistência Social", "Profissional")

    df_all = pd.concat([df_consulta, df_exame, df_vac, df_nutri, df_med, df_enf, df_prof, df_psico, df_as], ignore_index=True)

    st.sidebar.title("Filtros - Aluno")
    busca_aluno = st.sidebar.text_input(
        "Buscar aluno (nome ou data de nascimento)", ""
    ).strip()
    df_para_alunos = df_all

    if df_para_alunos.empty:
        st.info("Nenhum aluno encontrado com os filtros atuais.")
        footer_personal()
        return

    alunos_base = df_para_alunos[["Aluno", "DataNascimento"]].copy()
    alunos_base["Aluno"] = alunos_base["Aluno"].astype(str).str.strip()
    if "DataNascimento" not in alunos_base.columns:
        alunos_base["DataNascimento"] = pd.NaT

    if busca_aluno:
        alunos_base = alunos_base[
            alunos_base["Aluno"].str.contains(busca_aluno, case=False, na=False)
            | alunos_base["DataNascimento"]
            .dt.strftime("%d/%m/%Y")
            .str.contains(busca_aluno, na=False)
        ]

    alunos_unicos = (
        alunos_base.dropna(subset=["Aluno"])
        .drop_duplicates(subset=["Aluno", "DataNascimento"])
        .sort_values(["Aluno", "DataNascimento"])
    )

    if alunos_unicos.empty:
        st.info("Nenhum aluno encontrado com os filtros atuais.")
        footer_personal()
        return

    aluno_labels = [
        f"{row.Aluno} - {row.DataNascimento.strftime('%d/%m/%Y') if not pd.isna(row.DataNascimento) else 'sem data'}"
        for row in alunos_unicos.itertuples(index=False)
    ]

    preselect = st.session_state.pop("aluno_preselect", None)
    default_idx = None
    if preselect:
        nome_target = str(preselect.get("nome", "")).strip()
        nasc_target = preselect.get("nasc")
        nasc_dt = pd.to_datetime(nasc_target, errors="coerce") if nasc_target else pd.NaT
        for i, row in enumerate(alunos_unicos.itertuples(index=False)):
            nasc_row = pd.to_datetime(row.DataNascimento, errors="coerce")
            nasc_match = pd.isna(nasc_dt) or pd.isna(nasc_row) or nasc_row == nasc_dt
            if row.Aluno.strip() == nome_target and nasc_match:
                default_idx = i
                break

    aluno_idx = st.sidebar.selectbox(
        "Selecione o aluno",
        options=list(range(len(aluno_labels))),
        format_func=lambda i: aluno_labels[i],
        index=default_idx,
        placeholder="Escolha o aluno",
    )

    if aluno_idx is None:
        st.info("Selecione um aluno para visualizar os detalhes.")
        footer_personal()
        return

    aluno_sel_row = alunos_unicos.iloc[aluno_idx]
    aluno_sel = aluno_sel_row["Aluno"]
    nasc_sel = aluno_sel_row["DataNascimento"]
    
    # Busca o Sexo no dataframe filtrado
    df_filtrado_temp = df_all[df_all["Aluno"].astype(str) == aluno_sel].copy()
    if "DataNascimento" in df_filtrado_temp.columns and not pd.isna(nasc_sel):
        df_filtrado_temp = df_filtrado_temp[
            pd.to_datetime(df_filtrado_temp["DataNascimento"], errors="coerce") == nasc_sel
        ]
    sexo_sel = df_filtrado_temp["Sexo"].iloc[0] if not df_filtrado_temp.empty and "Sexo" in df_filtrado_temp.columns else "N/A"

    nasc_display = (
        [nasc_sel.strftime("%d/%m/%Y")] if not pd.isna(nasc_sel) else []
    )

    filters_placeholder.markdown(
        format_filters_applied(
            {
                "aluno": [aluno_sel],
                "nascimento": nasc_display,
                "sexo": [sexo_sel]
            },
            df_all,
            [
                ("aluno", "Aluno", "Aluno"),
                ("nascimento", "DataNascimento", "Nascimento"),
                ("sexo", "Sexo", "Sexo"),
            ],
        )
    )

    df_filtrado = df_filtrado_temp # Usa o que já filtramos

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para o filtro selecionado.")
        footer_personal()
        return

    #st.subheader(f"Aluno(a): {aluno_sel}")
    tot_por_cat = df_filtrado.groupby("Categoria").size().to_dict()
    total_registros = len(df_filtrado)
    
    #st.markdown("---")
    # Injeta CSS local para garantir que os links dos cards não tenham sublinhado
    st.markdown("""
        <style>
            .home-metric-link-wrapper, .home-metric-link-wrapper:hover {
                text-decoration: none !important;
            }
            .home-metric-link:hover {
                text-decoration: none !important;
            }
            /* Adiciona espaçamento vertical entre as linhas de cards */
            div[data-testid="stColumn"] {
                margin-bottom: 15px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("Indicadores Gerais")
    
    # 1. Card de Total em grade de 5 colunas (para manter paridade de largura)
    render_metric_cards([{"label": "Total de registros", "value": total_registros}], fixed_columns=5)
    
    # 2. Demais cards em grade de 5 colunas
    cat_order = [
        ("Encaminhamento", "Encaminhamento", "#encaminhamentos"),
        ("Exame", "Exame", "#exames"),
        ("Vacinação", "Vacinação", "#vacinacao"),
        ("Nutrição", "Nutrição", "#nutricao"),
        ("Médico", "Médico", "#medico"),
        ("Enfermagem", "Enfermagem", "#enfermagem"),
        ("Professor", "Professor", "#professor"),
        ("Psicólogo", "Psicólogo", "#psicologo"),
        ("Assistência Social", "Assist. Social", "#assistencia_social"),
    ]
    
    linha_categorias = []
    for cat_key, label, link in cat_order:
        val = tot_por_cat.get(cat_key, 0)
        linha_categorias.append({"label": label, "value": val, "link": link})

    # Exibe os indicadores de categoria em uma grade de 5 colunas com estilo Premium (Blue Glow)
    render_metric_cards(linha_categorias, fixed_columns=5)

    st.markdown("---")
    st.subheader("Evolução nutricional do aluno", anchor="nutricao_evolucao")
    nutri_evol = df_filtrado[df_filtrado["Categoria"] == "Nutrição"].dropna(
        subset=["Ano"]
    )
    if nutri_evol.empty:
        st.info("Sem dados nutricionais para o período filtrado.")
    else:
        nutri_evol["Ano"] = nutri_evol["Ano"].astype(int)
        if "Classificação" in nutri_evol.columns:
            nutri_evol["Classificação"] = nutri_evol["Classificação"].astype(str).str.strip()
        for col in ["Peso", "Altura", "IMC"]:
            if col in nutri_evol.columns:
                nutri_evol[col] = pd.to_numeric(nutri_evol[col], errors="coerce")

        metric_cols = [c for c in ["Peso", "Altura", "IMC"] if c in nutri_evol.columns]
        if not metric_cols:
            st.info("Sem colunas numéricas de nutrição para exibir.")
        else:
            long_metrics = (
                nutri_evol[["Ano"] + metric_cols]
                .melt(id_vars="Ano", var_name="Métrica", value_name="Valor")
                .dropna(subset=["Valor"])
            )

            if long_metrics.empty:
                st.info("Sem dados numéricos de nutrição para exibir.")
            else:
                evol_medias = (
                    long_metrics.groupby(["Ano", "Métrica"])["Valor"]
                    .mean()
                    .reset_index()
                )
                fig = px.line(
                    evol_medias.sort_values(["Métrica", "Ano"]),
                    x="Ano",
                    y="Valor",
                    color="Métrica",
                    markers=True,
                )
                fig.update_layout(separators=",.")
                st.plotly_chart(fig, use_container_width=True)
                ordem_metricas = ["Peso", "Altura", "IMC"]
                tabela_metricas = evol_medias.pivot(
                    index="Métrica", columns="Ano", values="Valor"
                )
                tabela_metricas = tabela_metricas.reindex(ordem_metricas)
                tabela_metricas = tabela_metricas.sort_index(axis=1)
                tabela_metricas = tabela_metricas.reset_index().rename(
                    columns={"Métrica": "Item"}
                )
                tabela_metricas["Tipo"] = "Métrica"

                # Nova lógica: Uma única linha de Classificação com o texto do status
                tabela_classif = (
                    nutri_evol.dropna(subset=["Classificação", "Ano"])
                    .sort_values("Ano")
                    .groupby("Ano")["Classificação"]
                    .last()  # Pega a última classificação registrada no ano
                    .reset_index()
                )
                
                if not tabela_classif.empty:
                    # Transpõe os dados: Anos viram colunas e Classificações viram valores da linha
                    tabela_classif = (
                        tabela_classif.set_index("Ano")["Classificação"]
                        .to_frame()
                        .T
                        .reset_index(drop=True)
                    )
                    tabela_classif["Item"] = "Classificação"
                    tabela_classif["Tipo"] = "Classificação"
                else:
                    tabela_classif = pd.DataFrame(columns=["Item", "Tipo"])

                if tabela_metricas.empty and tabela_classif.empty:
                    st.info("Sem dados nutricionais para the tabela por ano.")
                else:
                    # Identifica todos os anos presentes em ambas as tabelas
                    anos_metricas = [c for c in tabela_metricas.columns if c not in ["Item", "Tipo"]]
                    anos_classif = [c for c in tabela_classif.columns if c not in ["Item", "Tipo"]]
                    anos_cols = sorted(list(set(anos_metricas) | set(anos_classif)))

                    # Garante que ambas as tabelas tenham todas as colunas de anos
                    for df_temp in (tabela_metricas, tabela_classif):
                        for ano_col in anos_cols:
                            if ano_col not in df_temp.columns:
                                df_temp[ano_col] = pd.NA

                    tabela_comb = pd.concat(
                        [
                            tabela_metricas[["Tipo", "Item"] + anos_cols],
                            tabela_classif[["Tipo", "Item"] + anos_cols],
                        ],
                        ignore_index=True,
                    ).fillna("-")
                    tabela_comb = tabela_comb.rename(columns={"Item": "Métrica/Classe"})
                    
                    # Oculta linhas apenas para métricas vazias. 
                    # Para Classificação, mantemos todas as linhas conforme solicitado para mostrar o perfil completo.
                    soma_anos = (
                        tabela_comb[anos_cols]
                        .apply(pd.to_numeric, errors="coerce")
                        .fillna(0)
                        .sum(axis=1)
                    )
                    tabela_comb = tabela_comb[
                        (tabela_comb["Tipo"] == "Classificação") | (soma_anos != 0)
                    ]
                    tabela_comb = tabela_comb.drop(columns=["Tipo"], errors="ignore")
                    # Converte nomes de colunas de ano para string para evitar formatador de milhar no cabeçalho
                    tabela_comb.columns = [str(c) for c in tabela_comb.columns]
                    st.dataframe(
                        tabela_comb,
                        use_container_width=True,
                        hide_index=True,
                    )

    st.markdown("---")
    st.subheader("Categorias por ano", anchor="categorias_por_ano")
    categorias_ano = (
        df_filtrado.dropna(subset=["Ano"])
        .groupby(["Categoria", "Ano"])
        .size()
        .reset_index(name="Quantidade")
    )
    if categorias_ano.empty:
        st.info("Sem dados para categorização por ano.")
    else:
        categorias_ano["Ano"] = categorias_ano["Ano"].astype(int)
        pivot_categorias = (
            categorias_ano.pivot(index="Categoria", columns="Ano", values="Quantidade")
            .fillna(0)
            .astype(int)
        )
        # Converte nomes de colunas para string para evitar formatador de milhar
        pivot_categorias.columns = [str(c) for c in pivot_categorias.columns]
        st.dataframe(pivot_categorias, use_container_width=True)

    def render_section(
        df_base: pd.DataFrame, titulo: str, extra_cols: list[str] | None = None
    ):
        # Gera anchor ASCII-friendly
        import unicodedata
        anchor_val = titulo.lower().replace(" ", "_")
        anchor_val = "".join(
            c for c in unicodedata.normalize('NFD', anchor_val)
            if unicodedata.category(c) != 'Mn'
        )

        st.markdown("---")
        st.subheader(titulo, anchor=anchor_val)
        if df_base.empty:
            st.info(f"Nenhum dado de {titulo.lower()} para exibir.")
            return
        cols_to_show = [
            "Ano",
            "ID",
            "URG",
            "Escola",
            "Evento",
            "Classificação",
            "Tipo",
            "Serie",
            "Turma",
        ]
        if extra_cols:
            cols_to_show.extend(extra_cols)
        cols_to_show = [c for c in cols_to_show if c in df_base.columns]
        sort_cols = [
            c for c in ["Ano", "Evento", "Classificação"] if c in df_base.columns
        ]
        st.dataframe(
            df_base[cols_to_show].sort_values(sort_cols, na_position="last"),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ano": st.column_config.NumberColumn(format="%d"),
                "ID": st.column_config.NumberColumn(format="%d"),
            }
        )

    render_section(
        df_filtrado[df_filtrado["Categoria"] == "Encaminhamento"], "Encaminhamentos"
    )
    render_section(df_filtrado[df_filtrado["Categoria"] == "Exame"], "Exames")
    render_section(
        df_filtrado[df_filtrado["Categoria"] == "Vacinação"],
        "Vacinação",
        extra_cols=["Dose", "Lote"],
    )
    render_section(
        df_filtrado[df_filtrado["Categoria"] == "Nutrição"],
        "Nutrição",
        extra_cols=["Peso", "Altura", "IMC"],
    )
    render_section(df_filtrado[df_filtrado["Categoria"] == "Médico"], "Médico")
    render_section(df_filtrado[df_filtrado["Categoria"] == "Enfermagem"], "Enfermagem")
    render_section(df_filtrado[df_filtrado["Categoria"] == "Professor"], "Professor")
    render_section(df_filtrado[df_filtrado["Categoria"] == "Psicólogo"], "Psicólogo")
    render_section(df_filtrado[df_filtrado["Categoria"] == "Assistência Social"], "Assistência Social")

    st.markdown(" ")
    footer_personal()
