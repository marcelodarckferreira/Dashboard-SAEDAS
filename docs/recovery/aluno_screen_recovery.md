# Runbook de Recuperação: Tela Aluno

## Objetivo
Documento operacional para restaurar rapidamente a tela `Aluno` (`app/app_pages/aluno.py`, função `page_aluno`) em caso de regressão visual/funcional.

> Esta tela é o destino dos deep-links gerados pelas demais telas do SAEDAS. Não segue o blueprint de telas analíticas — não há AgGrid, não há sidebar Ano/URG/Escola/Tipo, não há tabelas de seleção mestre.

## Escopo Funcional
- Deep-link `?menu=Aluno&aluno=...&nasc=YYYY-MM-DD` com pré-seleção via `aluno_preselect`.
- Sidebar "Filtros - Aluno" com busca por nome/data e selectbox de aluno único.
- Faixa de filtros aplicados (Aluno, Nascimento, Sexo).
- Indicadores em 2 linhas de 5 colunas: Total + 9 categorias com âncoras internas.
- Evolução nutricional: gráfico Plotly (Peso/Altura/IMC) + tabela combinada métricas/classificação por ano.
- Tabela "Categorias por ano" (pivot).
- 9 seções `render_section` com `st.dataframe`.

## Fontes de Dados
Carregadas em `carregar_dados_aluno()`:
- `data/DashboardConsultaAluno.csv` — `SCHEMA_CONSULTA_ALUNO`
- `data/DashboardExameAluno.csv` — `SCHEMA_EXAME_ALUNO`
- `data/DashboardVacinacaoAluno.csv` — `SCHEMA_VACINACAO_ALUNO`
- `data/DashboardNutricaoAluno.csv` — `SCHEMA_NUTRICAO_ALUNO`
- `data/DashboardMedicoAluno.csv` — `SCHEMA_MEDICO_ALUNO`
- `data/DashboardEnfermagemAluno.csv` — `SCHEMA_ENFERMAGEM_ALUNO`
- `data/DashboardProfessorAluno.csv` — `SCHEMA_PROFESSOR_ALUNO`
- `data/DashboardPsicologoAluno.csv` — `SCHEMA_PSICOLOGO_ALUNO`
- `data/DashboardAssistenciaSocialAluno.csv` — `SCHEMA_ASSISTENCIA_SOCIAL_ALUNO`

## Fonte de Verdade de Estado
- `st.session_state["aluno_preselect"]`: dict `{"nome": str, "nasc": str|None}` consumido com `pop()` na entrada da seleção.
- `st.query_params`: lido apenas se `aluno_preselect` ainda não existir.
- Não utiliza `global_years`, `global_urgs`, `sidebar_*_filter` nem `pending_sidebar_*`.

## Regras de Filtro
- `df_all` = concat de 9 DataFrames preparados via `prepare_df()`.
- Lista de alunos: `dropna(subset=["Aluno"]).drop_duplicates(subset=["Aluno", "DataNascimento"])`.
- Busca textual: substring case-insensitive em `Aluno` ou `DataNascimento` formatada `dd/mm/yyyy`.
- `df_filtrado` = `df_all` filtrado por `Aluno == aluno_sel` e (quando não NaT) `DataNascimento == nasc_sel`.
- `Sexo` resolvido pela primeira linha disponível em `df_filtrado_temp`; default `"N/A"`.

## Preparação de DataFrames (`prepare_df`)
- Renomeia coluna de evento conforme categoria:
  - Consulta: `Consulta` → `Evento` (categoria `Encaminhamento`).
  - Exame: `Exame` → `Evento`.
  - Vacinação: `Vacina` → `Evento`.
  - Nutrição: `Nutricao` → `Classificação`.
  - Médico/Enfermagem/Professor/Psicólogo/Assistência Social: `Profissional` → `Evento`.
- Renomeia `DtNasc` → `DataNascimento`.
- Acrescenta coluna `Categoria` com o rótulo da fonte.
- Converte `Ano` (numeric), `Aluno` (str.strip), `DataNascimento` (datetime).

## Componentes Visuais Obrigatórios
- Cards via `render_metric_cards(..., fixed_columns=5)` em duas chamadas (Total + 9 categorias).
- CSS local injetado:
  - `.home-metric-link-wrapper`, `.home-metric-link` sem sublinhado.
  - `div[data-testid="stColumn"] { margin-bottom: 15px }`.
- Âncoras internas dos cards (devem casar com `anchor=` dos `st.subheader`):
  - `#encaminhamentos`, `#exames`, `#vacinacao`, `#nutricao`, `#medico`, `#enfermagem`, `#professor`, `#psicologo`, `#assistencia_social`.
- Âncoras extras: `nutricao_evolucao`, `categorias_por_ano`.
- Faixa de filtros aplicados via `format_filters_applied` com mapping `[("aluno","Aluno","Aluno"), ("nascimento","DataNascimento","Nascimento"), ("sexo","Sexo","Sexo")]`.

## Regras Específicas da Evolução Nutricional
- Filtra `Categoria == "Nutrição"` e `Ano` não nulo.
- Coage `Peso/Altura/IMC` para numérico antes do `melt`.
- `evol_medias`: média anual por métrica.
- Gráfico `px.line(..., markers=True)` com `separators=",."`.
- Tabela combinada:
  - Linhas de métrica via pivot (média anual) reindexadas em `["Peso", "Altura", "IMC"]`.
  - Linha única "Classificação" com `groupby("Ano")["Classificação"].last()` transposta.
  - Oculta linhas de métrica somando zero, mas mantém Classificação.
  - Cabeçalhos de ano convertidos para `str` (evita formatador de milhar).

## Regras Específicas das Seções Detalhadas (`render_section`)
- Anchor gerado por normalização Unicode NFD do título.
- Colunas exibidas (quando existirem): `Ano, ID, URG, Escola, Evento, Classificação, Tipo, Serie, Turma` + `extra_cols`.
- Ordenação: `Ano, Evento, Classificação` (apenas as presentes), `na_position="last"`.
- `column_config`: `Ano` e `ID` como `NumberColumn(format="%d")`.

## Não Aplicáveis (Exceções Intencionais)
- Não usar AgGrid, `render_table_toolbar`, `render_saedas_aggrid`, `.selection-master-table`, `.st-table-with-total`.
- Não há seletor temporal mestre, nem cross-filtering URG/Escola.
- Não há cards clicáveis estilo `st-key-btn_kpi_` — apenas links âncora.
- Não chamar `apply_global_css()` (já injetado em `app/main.py`).

## Checklist de Recuperação
1. Validar carga dos 9 datasets (mensagens de warning/info corretas em caso de erro).
2. Validar deep-link `?menu=Aluno&aluno=...&nasc=...` selecionando o aluno automaticamente.
3. Validar busca por nome e por data (`dd/mm/yyyy`).
4. Validar selectbox com `placeholder="Escolha o aluno"` e early-return quando `aluno_idx is None`.
5. Validar faixa de filtros aplicados (Aluno, Nascimento, Sexo).
6. Validar grid de 2 linhas × 5 colunas de cards.
7. Validar âncoras internas dos cards levando às seções correspondentes.
8. Validar gráfico Plotly + tabela combinada de evolução nutricional.
9. Validar pivot "Categorias por ano".
10. Validar 9 seções `render_section` com colunas/ordenação esperadas.
11. Validar `footer_personal()` em todos os caminhos de retorno.

## Comandos Úteis
- `streamlit run app/main.py`
- `python -m py_compile app/app_pages/aluno.py app/utils/page_helpers.py`
- `rg -n "carregar_dados_aluno|prepare_df|render_section|aluno_preselect|render_metric_cards|format_filters_applied" app/app_pages/aluno.py`
- `rg -n "anchor=" app/app_pages/aluno.py`
