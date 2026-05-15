# Especificação Técnica — Página Início (Home)

A página Início é o centro de inteligência do SAEDAS, fornecendo uma visão consolidada de todos os indicadores e servindo como navegador principal para as demais seções do sistema.

---

## 1. Visão Geral e Propósito
- **Objetivo:** Fornecer KPIs em tempo real e tabelas comparativas de performance por Ano, URG e Escola.
- **Navegação:** Funciona como um portal interativo, onde os cards de métricas levam às páginas específicas e seleções em tabelas filtram globalmente o dashboard.

---

## 2. Fontes de Dados e Schemas
Datasets carregados em `carregar_dados_home()`:
- **Master:** `DashboardHome.csv` (`SCHEMA_HOME`)
- **Performance por Escola:** `DashboardHomeEscolaAno.csv` (`SCHEMA_HOME_ESCOLA_ANO`)
- **Performance Geral:** `DashboardHomeAno.csv` (`SCHEMA_HOME_ANO`)
- **Performance por URG:** `DashboardHomeURGAno.csv` (`SCHEMA_HOME_URG_ANO`)

---

## 3. Filtros e Estado Global
### 3.1 Seletores Primários
- **Sidebar:** Ano, URG, Escola (Filtros padrão via `sidebar_filters`).
- **Seletor Temporal Mestre:** Componente global para filtragem de anos (`global_years`). Ver especificações em [Shared Components Spec](shared_components_spec.md#2-seletor-temporal-mestre-botoes-de-ano).
- **Cross-Filtering (URG):** Seleções na tabela "Performance por URG" atualizam `global_urgs` e refletem na sidebar e em todo o dashboard.

### 3.2 Lógica de Sincronização
- Usa `init_global_state()` para garantir que Anos e URGs sejam persistidos entre navegações.
- `apply_pending_table_filters()` resolve pendências de filtros vindas de seleções de tabela (`rerun()`).

---

## 4. Componentes de Interface

### 4.1 Card de Métricas (KPIs)
- **Primary:** Total de Alunos, Alunos Atendidos, Atendimentos.
- **Professional:** Atend. Professor, Psicólogo, Assist. Social, Enfermagem, Médico.
- **Service:** Encaminhamentos, Exames, Vacinação.
- **Estilo:** `render_metric_cards()` com cards dinâmicos (azuis com ícone ↗) e estáticos (cinzas).

### 4.2 Tabela Comparativa de Performance por ANO
- **Base:** Agregação dinâmica de `df_home_ano_source`.
- **Métricas:** 12 indicadores (mesma ordem dos cards).
- **Cálculos:** % Cobertura (sobre total de alunos) e Var% (em relação ao ano anterior).
- **Visual:** AgGrid com Super-Header por Ano.
- **Toolbar:** `home_ano_actions_toolbar`.

### 4.3 Tabela Comparativa de Performance por URG (Mestre)
- **Base:** `build_comparativo_anual(df, "URG")`.
- **Interação:** `rowSelection: "multiple"`. Selecionar uma URG filtra o dashboard inteiro.
- **Sync:** `onFirstDataRendered` via JS garante que seleções na sidebar marquem as linhas na tabela.
- **Toolbar:** `home_urg_actions_toolbar`.

### 4.4 Tabela de Top Escolas por URG
- **Base:** Agregação de `df_escola_ano`.
- **Filtros:** Reage a Ano e URG (clique na tabela mestre).
- **Toolbar:** `home_escola_actions_toolbar`.

### 4.5 Detalhamento dos Dados (AgGrid)
- **Base:** `df_display` com colunas dinâmicas.
- **Feature:** Seletor de Colunas (`⚙️ Colunas`) com persistência em `home_hidden_columns`.
- **Toolbar:** `home_detail_toolbar` (Padrão Unificado).

---

## 5. Regras de Negócio e Cálculos
- **Atendimentos Profissionais:** Soma de Professor, Psicólogo, Assist. Social, Enfermagem e Médico.
- **% Cobertura:** `(Indicador / Total Alunos Escola) * 100`.
- **Imunidade de Filtro:** A tabela de performance geral pode ignorar filtros de URG/Escola para mostrar a evolução da rede completa, conforme configurado na base de dados.

---

## 6. Observações Técnicas
- **Chave de AgGrid:** `urg_home_aggrid_{selecao_ativa}` para evitar resposta stale e garantir re-mount com o estado correto da sidebar.
- **Layout Shift:** Uso de containers com chaves fixas para evitar saltos visuais durante reruns.
