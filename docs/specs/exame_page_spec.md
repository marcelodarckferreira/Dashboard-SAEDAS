# Especificação Técnica — Página Exames (Regulação)

A página Exames fornece uma visão detalhada da regulação de exames e procedimentos na rede SAEDAS, permitindo análise por tipo de regulação, URG e evolução temporal.

---

## 1. Visão Geral e Propósito
- **Objetivo:** Monitorar o volume de regulações e procedimentos por especialidade.
- **Diferencial:** Foco na distribuição por "Regulação" (originalmente campo "Exame").

---

## 2. Fontes de Dados e Schemas
Datasets carregados em `carregar_dados_exame()`:
- **Principal:** `DashboardExame.csv` (`SCHEMA_EXAME`)
- **Detalhamento Aluno:** `DashboardExameAluno.csv` (`SCHEMA_EXAME_ALUNO`)
- **Performance Anual:** `DashboardExameAno.csv` (`SCHEMA_EXAME_ANO`)
- **Demográfico (Referência):** `DashboardHome.csv` (`SCHEMA_HOME`)

---

## 3. Filtros e Navegação
### 3.1 Sidebar
- **Filtros Padrão:** Ano, URG, Escola, Tipo.
- **Filtro Específico:** Multiselect de "Regulação" (interativo via cards).

### 3.2 Sincronização
- Mesma lógica de cross-page via `init_global_state()` e [Seletor Temporal Mestre](shared_components_spec.md#2-seletor-temporal-mestre-botoes-de-ano).
- Sincronização bidirecional de URG e Escola via tabelas mestras.

---

## 4. Componentes de Interface

### 4.1 KPI Cards (Regulação)
- **Cálculo:** Volume total por tipo de regulação.
- **Interatividade:** Cards do tipo Toggle que atualizam o multiselect da sidebar ao clicar.
- **Padrão:** Grade de 5 colunas por linha.

### 4.2 Tabela Comparativa de Performance por ANO
- **Métricas:** Volume absoluto por regulação.
- **Ordenação:** Segue a ordem visual dos KPI Cards (prioridade de volume).
- **Cálculos:** % Total (share no ano) e Var% (crescimento interanual).
- **Toolbar:** `exame_ano_actions_toolbar`.

### 4.3 Tabela de Performance por URG (Mestre)
- **Base:** `build_comparativo_anual(df, "URG")`.
- **Sync:** JavaScript `onFirstDataRendered` para destacar URGs selecionadas na sidebar.
- **Toolbar:** `exame_urg_actions_toolbar`.

### 4.4 Detalhamento por Aluno
- **Colunas Dinâmicas:** Anos de referência como colunas, contendo os nomes das regulações realizadas.
- **Navegação:** LinkColumn "📄 Ver Perfil" para a página de perfil do aluno.
- **Toolbar:** `exame_aluno_actions_toolbar`.

---

## 5. Regras de Negócio
- **Métricas Demográficas:** "Total de Alunos" e "Alunos Atendidos" são extraídos de `DashboardHome.csv` para garantir consistência com a página Início.
- **Filtragem:** A tabela de Performance por URG é imune ao próprio filtro de URG (mostra a rede inteira) para permitir navegação.

---

## 6. Observações Técnicas
- **Chaves de AgGrid:** Seguem o padrão `{prefix}_aggrid_{selecao_ativa}` para evitar problemas de estado stale.
- **CSS Local:** Injeta regras para garantir o arredondamento correto dos botões da toolbar (Cópia/CSV) se não estiverem usando o padrão unificado.
