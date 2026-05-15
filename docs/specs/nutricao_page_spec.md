# Especificação Técnica — Página Nutrição

A página Nutrição monitora o estado nutricional dos alunos (IMC, Peso, Altura) e classifica as ocorrências de desnutrição, sobrepeso e obesidade na rede SAEDAS.

---

## 1. Visão Geral e Propósito
- **Objetivo:** Identificar e monitorar alunos em risco nutricional.
- **Foco:** Classificação antropométrica (OMS) por URG e Escola.

---

## 2. Fontes de Dados e Schemas
Datasets carregados em `carregar_dados_nutricao()`:
- **Principal:** `DashboardNutricao.csv` (`SCHEMA_NUTRICAO`)
- **Detalhamento Aluno:** `DashboardNutricaoAluno.csv` (`SCHEMA_NUTRICAO_ALUNO`)
- **Performance Anual:** `DashboardNutricaoAno.csv` (`SCHEMA_NUTRICAO_ANO`)
- **Demográfico (Referência):** `DashboardHome.csv` (`SCHEMA_HOME`)

---

## 3. Filtros e Estados
- **Sidebar:** Ano, URG, Escola, Tipo.
- **Seletor Temporal Mestre:** Ver especificações em [Shared Components Spec](shared_components_spec.md#2-seletor-temporal-mestre-botoes-de-ano).
- **Filtro de Situação:** Multiselect na sidebar sincronizado com KPI Cards (Desnutrição, Normal, Sobrepeso, etc.).
- **Sincronização:** Segue o padrão de `init_global_state()` e `sync_home_to_sidebar()`.

---

## 4. Componentes de Interface

### 4.1 KPI Cards (Situação Nutricional)
- **Tipo:** Toggle buttons com métricas de volume por categoria.
- **Destaque:** Categorias críticas como "DESNUTRIÇÃO AGUDA GRAVE" são visíveis no topo para ação imediata.

### 4.2 Tabela de Performance por URG (Mestre)
- **Base:** `build_comparativo_anual(df, "URG")`.
- **Interação:** Filtro mestre de navegação por unidade.
- **Toolbar:** `nutricao_urg_actions_toolbar`.

### 4.3 Detalhamento por Aluno
- **Dados:** Inclui colunas específicas para Peso, Altura e IMC.
- **Lógica:** Agrupamento por ID de Aluno com evolução temporal das medidas.
- **Função Auxiliar:** `prepare_nutricao_aluno_table`.
- **Navegação:** LinkColumn para o Perfil do Aluno.

### 4.4 Gráficos de Evolução
- **Distribuição por URG:** Barras agrupadas por ano.
- **Distribuição por Situação:** Barras horizontais por categoria nutricional.

---

## 5. Regras de Negócio
- **Imunidade de Filtro:** Os indicadores demográficos (Total de Alunos) ignoram o filtro de situação nutricional para servir de denominador de prevalência.
- **Métricas:** O Peso e Altura são processados como `pd.to_numeric` com tratamento de erros para garantir cálculos de média precisos se necessário.

---

## 6. Observações Técnicas
- **Chaves de AgGrid:** `urg_table_nutricao_{selecao}`.
- **Design:** Uso obrigatório de `apply_saedas_design` para garantir o padrão visual premium e alinhamento de toolbars.
