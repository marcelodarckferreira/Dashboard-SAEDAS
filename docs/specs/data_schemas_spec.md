# Especificação Técnica — Schemas de Dados (CSV)

Este documento define a estrutura obrigatória (schemas) de cada arquivo CSV consumido pelo sistema SAEDAS. A validação desses campos ocorre durante a carga de dados no utilitário `load_csv`.

---

## 1. Módulo Home (Visão Geral)

### `DashboardHome.csv` (`SCHEMA_HOME`)
Colunas obrigatórias para os indicadores de contexto e filtros globais.

| Coluna | Descrição |
| :--- | :--- |
| `Ano` | Ano de referência (ex: 2024). |
| `URG` | Unidade Regional de Governo. |
| `Escola` | Nome da instituição de ensino. |
| `DtInicio` | Data de início do período. |
| `DtFechamento` | Data de fechamento do período (usada para filtro de ano). |
| `QtdAluno` | Total de alunos atendidos na rede. |
| `QtdProfessor` | Quantidade de atendimentos de Professor. |
| `QtdPsicologo` | Quantidade de atendimentos de Psicólogo. |
| `QtdAssistSocial` | Quantidade de atendimentos de Assistente Social. |
| `QtdEnfermagem` | Quantidade de atendimentos de Enfermagem. |
| `QtdMedico` | Quantidade de atendimentos de Médico. |
| `QtdVacinacao` | Quantidade de atendimentos de Vacinação. |
| `QtdVacina` | Quantidade total de vacinas aplicadas. |
| `QtdEncaminhamento` | Quantidade de encaminhamentos realizados. |
| `QtdExame` | Quantidade de exames realizados. |
| `QtdAlunoEscola` | Denominador total de alunos matriculados na escola. |

---

## 2. Módulos de Atendimento (Consulta, Exame, Vacina, Nutrição)

Estes módulos seguem um padrão triplo de arquivos: Principal, Detalhado (Aluno) e Agregado (Ano).

### 2.1 Estrutura Principal (`SCHEMA_CONSULTA`, `SCHEMA_EXAME`, etc.)
Utilizado para os KPI Cards e tabelas de performance.

| Coluna | Comum a todos | Específica do Módulo |
| :--- | :--- | :--- |
| `Ano` | ✓ | — |
| `URG` | ✓ | — |
| `Escola` | ✓ | — |
| `Tipo` | ✓ | — |
| `Qtd` | ✓ | — |
| `Consulta` | — | Apenas em `DashboardConsulta.csv`. |
| `Exame` | — | Apenas em `DashboardExame.csv`. |
| `Vacina` | — | Apenas em `DashboardVacinacao.csv`. |
| `Nutricao` | — | Apenas em `DashboardNutricao.csv`. |

### 2.2 Estrutura por Aluno (`SCHEMA_CONSULTA_ALUNO`, etc.)
Utilizado na tabela de detalhamento no rodapé das páginas.

| Coluna | Descrição |
| :--- | :--- |
| `Ano` | Ano do registro. |
| `Aluno` | Nome completo do aluno. |
| `DtNasc` | Data de nascimento (formato YYYY-MM-DD ou DD/MM/YYYY). |
| `Sexo` | Gênero (M/F). |
| `URG` / `IdUrg` | Identificação da regional. |
| `Escola` | Nome da escola. |
| `Serie` / `Turma` | Dados escolares. |
| `Dose` / `Lote` | Exclusivo para Vacinação. |
| `Peso` / `Altura` / `IMC` | Exclusivo para Nutrição. |

---

## 3. Módulos de Profissionais (Médico, Enfermagem, Psicólogo, Assist. Social, Professor)

Estes módulos possuem uma estrutura padronizada para atendimentos técnicos.

### 3.1 Estrutura Principal (`SCHEMA_MEDICO`, `SCHEMA_PROFESSOR`, etc.)
| Coluna | Descrição |
| :--- | :--- |
| `Ano` | Ano de referência. |
| `URG` | Unidade Regional. |
| `Escola` | Nome da instituição. |
| `Tipo` | Tipo de escola (Pública/Privada). |
| `Descricao` | Descrição do atendimento ou especialidade. |
| `Qtd` | Quantidade de atendimentos. |

### 3.2 Estrutura por Aluno (Tabela de Detalhes)
| Coluna | Descrição |
| :--- | :--- |
| `Ano` | Ano do registro. |
| `ID` | Identificador único do aluno. |
| `Aluno` | Nome do aluno. |
| `DtNasc` | Data de nascimento. |
| `Profissional` | Nome do profissional que realizou o atendimento. |
| `URG` / `Escola` | Localização do atendimento. |
| `Serie` / `Turma` | Contexto escolar. |

---

## 4. Tabelas Agregadas por Ano (`SCHEMA_XXX_ANO`)

Utilizadas para as tabelas comparativas horizontais (Performance por URG/Escola).

| Coluna | Descrição |
| :--- | :--- |
| `URG` | Nome da Regional. |
| `Escola` | Nome da Escola. |
| `Atendimento` / `Consulta` | A categoria sendo comparada. |
| `2022` a `2026` | Colunas de valores anuais. |
| `Total` | Soma horizontal dos anos. |

---

## 5. Regras de Validação e Tipagem

1.  **Datas**: Devem ser convertidas para `datetime` usando `errors='coerce'`.
2.  **Numéricos**: Colunas de `Qtd`, `Ano` e métricas de Nutrição devem ser convertidas para tipos numéricos durante a carga.
3.  **Case-Sensitivity**: O sistema diferencia maiúsculas de minúsculas nos nomes das colunas.
4.  **Colunas Extras**: Colunas presentes nos CSVs que não constam no Schema são carregadas, mas podem não ser utilizadas pelos componentes visuais.
