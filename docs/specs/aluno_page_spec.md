# Especificação Técnica — Página Perfil do Aluno

A página Perfil do Aluno (`app/app_pages/aluno.py`, função `page_aluno`) é a visão 360° individual, consolidando o histórico de saúde, atendimentos profissionais e indicadores nutricionais de um único estudante a partir de múltiplos datasets do sistema.

---

## 1. Visão Geral e Propósito
- **Objetivo:** Oferecer um prontuário unificado por aluno, agregando encaminhamentos, exames, vacinação, nutrição e atendimentos profissionais.
- **Integração:** Recebe tráfego de outras telas via deep-link (`?menu=Aluno&aluno=...&nasc=YYYY-MM-DD`) e via `aluno_preselect` no `st.session_state`.

---

## 2. Fontes de Dados e Schemas
Datasets carregados em `carregar_dados_aluno()` via `load_csv()` com schemas validados:

| Categoria | Arquivo CSV | Schema |
|-----------|-------------|--------|
| Encaminhamento | `data/DashboardConsultaAluno.csv` | `SCHEMA_CONSULTA_ALUNO` |
| Exame | `data/DashboardExameAluno.csv` | `SCHEMA_EXAME_ALUNO` |
| Vacinação | `data/DashboardVacinacaoAluno.csv` | `SCHEMA_VACINACAO_ALUNO` |
| Nutrição | `data/DashboardNutricaoAluno.csv` | `SCHEMA_NUTRICAO_ALUNO` |
| Médico | `data/DashboardMedicoAluno.csv` | `SCHEMA_MEDICO_ALUNO` |
| Enfermagem | `data/DashboardEnfermagemAluno.csv` | `SCHEMA_ENFERMAGEM_ALUNO` |
| Professor | `data/DashboardProfessorAluno.csv` | `SCHEMA_PROFESSOR_ALUNO` |
| Psicólogo | `data/DashboardPsicologoAluno.csv` | `SCHEMA_PSICOLOGO_ALUNO` |
| Assistência Social | `data/DashboardAssistenciaSocialAluno.csv` | `SCHEMA_ASSISTENCIA_SOCIAL_ALUNO` |

Avisos de carga: erros viram `st.warning` e zeram o DataFrame; alertas viram `st.info`.

---

## 3. Navegação e Seleção
### 3.1 Deep-Linking
- Lê `st.query_params` na entrada da função. Aceita `aluno` (nome) e `nasc` (data ISO).
- Quando presente, grava `st.session_state["aluno_preselect"] = {"nome": ..., "nasc": ...}` (apenas se ainda não definido).
- Função interna `_first()` normaliza valores que vêm como lista ou string.

### 3.2 Busca e Filtro
- **Sidebar título:** "Filtros - Aluno".
- **Busca:** `st.sidebar.text_input("Buscar aluno (nome ou data de nascimento)")`. Filtra por substring case-insensitive no nome ou no `DataNascimento` formatado como `dd/mm/yyyy`.
- **Selectbox:** "Selecione o aluno" com `format_func` exibindo `Nome - dd/mm/yyyy` (ou `sem data`). Suporta `default_idx` quando há `aluno_preselect` casando nome e (opcionalmente) nascimento.
- Se nenhum aluno encontrado ou nenhum selecionado, exibe `st.info` e renderiza o `footer_personal()`.

---

## 4. Preparação dos Dados
- Função interna `prepare_df(df, categoria, evento_col, evento_label="Evento")`:
  - Renomeia a coluna específica para `Evento` (ou `Classificação` no caso de nutrição) e `DtNasc` para `DataNascimento`.
  - Acrescenta coluna `Categoria` com o rótulo da fonte.
  - Converte `Ano` para numérico, normaliza `Aluno` (strip) e `DataNascimento` para datetime.
- Os 9 DataFrames preparados são unificados em `df_all` via `pd.concat`.
- O filtro do aluno é aplicado em `df_filtrado_temp` (matching por `Aluno` + `DataNascimento`), com extração do `Sexo` a partir da primeira linha disponível.
- A faixa "Filtros aplicados" é renderizada por `format_filters_applied` mostrando Aluno, Nascimento e Sexo.

---

## 5. Componentes de Interface

### 5.1 Cabeçalho
- Título: `st.title("Perfil do Aluno")`.
- Subtítulo: "Resumo unificado com histórico de encaminhamentos, exames, vacinação e nutrição."
- `filters_placeholder` recebe o sumário de filtros após a seleção do aluno.

### 5.2 Indicadores Gerais (Cards)
- CSS local injetado para remover sublinhado dos links dos cards e adicionar `margin-bottom` em colunas.
- **Linha 1:** card único "Total de registros" via `render_metric_cards([...], fixed_columns=5)`.
- **Linha 2:** grade de 5 colunas com 9 categorias, cada uma com `link` âncora interna:
  - Encaminhamento (`#encaminhamentos`), Exame (`#exames`), Vacinação (`#vacinacao`), Nutrição (`#nutricao`), Médico (`#medico`), Enfermagem (`#enfermagem`), Professor (`#professor`), Psicólogo (`#psicologo`), Assist. Social (`#assistencia_social`).

### 5.3 Evolução Nutricional (`anchor="nutricao_evolucao"`)
- Base: linhas com `Categoria == "Nutrição"` e `Ano` não nulo.
- Converte `Peso`, `Altura`, `IMC` para numérico.
- **Gráfico:** `plotly.express.line` com X=Ano, Y=Valor, color=Métrica (Peso/Altura/IMC), markers ativos. `separators=",."`.
- **Tabela combinada:** pivot ano-coluna contendo:
  - Linhas de métrica (Peso, Altura, IMC) com média anual.
  - Linha "Classificação" com o último valor textual de cada ano.
  - Filtragem oculta métricas zeradas mas mantém classificação.
  - Cabeçalhos de ano convertidos para string (evita separador de milhar).

### 5.4 Categorias por Ano (`anchor="categorias_por_ano"`)
- Pivot `Categoria x Ano` com `Quantidade`. Renderizado via `st.dataframe`.

### 5.5 Seções Detalhadas
Função `render_section(df_base, titulo, extra_cols=None)`:
- Gera anchor ASCII via `unicodedata.NFD`.
- Colunas padrão: `Ano, ID, URG, Escola, Evento, Classificação, Tipo, Serie, Turma`.
- `extra_cols` adicionais por categoria.
- Renderiza `st.dataframe` ordenado por `Ano, Evento, Classificação`, com `column_config` numérico (`%d`) para `Ano` e `ID`.

Categorias renderizadas:
- Encaminhamentos
- Exames
- Vacinação (`extra_cols=["Dose", "Lote"]`)
- Nutrição (`extra_cols=["Peso", "Altura", "IMC"]`)
- Médico
- Enfermagem
- Professor
- Psicólogo
- Assistência Social

### 5.6 Rodapé
- `footer_personal()` ao final ou em qualquer early-return.

---

## 6. Regras de Negócio e Tratamento de Dados
- **Unificação:** `pd.concat` de 9 DataFrames preparados (`df_consulta`, `df_exame`, `df_vac`, `df_nutri`, `df_med`, `df_enf`, `df_prof`, `df_psico`, `df_as`).
- **Chave de identificação:** `Aluno` + `DataNascimento` (diferencia homônimos). `nasc_match` aceita NaT em qualquer lado.
- **Sexo:** Obtido na primeira linha do `df_filtrado_temp` que possuir a coluna; default `"N/A"`.
- **Formatação:** Datas em `dd/mm/yyyy`; cabeçalhos de ano em string para evitar formatador numérico.

---

## 7. Observações Técnicas
- `apply_global_css()` não é invocado aqui — é injetado em `app/main.py`.
- CSS local específico para `.home-metric-link-wrapper` / `.home-metric-link` e `div[data-testid="stColumn"]`.
- Não usa AgGrid; todas as tabelas são `st.dataframe`.
- Helpers usados de `app/utils/page_helpers.py`: `render_metric_cards`, `render_metric`, `format_filters_applied`.
