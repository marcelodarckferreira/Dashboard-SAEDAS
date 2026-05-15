# Especificação Técnica — Página Vacinação

A página Vacinação monitora a cobertura vacinal e a aplicação de doses na rede SAEDAS, permitindo rastrear a imunização por tipo de vacina, URG e detalhamento individual por aluno.

---

## 1. Visão Geral e Propósito
- **Objetivo:** Controlar o status vacinal dos alunos e o volume de doses aplicadas.
- **KPI Chave:** "Vacinados/Aplicação" (Alunos Únicos / Total de Doses).

---

## 2. Fontes de Dados e Schemas
Datasets carregados em `carregar_dados_vacinacao()`:
- **Principal:** `DashboardVacinacao.csv` (`SCHEMA_VACINACAO`)
- **Detalhamento Aluno:** `DashboardVacinacaoAluno.csv` (`SCHEMA_VACINACAO_ALUNO`)
- **Performance Anual:** `DashboardVacinacaoAno.csv` (`SCHEMA_VACINACAO_ANO`)
- **Demográfico (Referência):** `DashboardHome.csv` (`SCHEMA_HOME`)

---

## 3. Filtros e Estados
### 3.1 Filtros Globais
- **Sidebar:** Ano, URG, Escola, Tipo.
- **Filtro de Vacina:** Multiselect na sidebar, sincronizado com os KPI Cards do tipo Toggle.

### 3.2 Sincronização de Estado
- Usa `init_global_state()` e [Seletor Temporal Mestre](shared_components_spec.md#2-seletor-temporal-mestre-botoes-de-ano).
- Bidirecionalidade múltipla para Escola e URG via tabelas AgGrid.

---

## 4. Componentes de Interface

### 4.1 Card "Vacinados/Aplicação"
- **Cálculo Alunos Vacinados:** Contagem única de `(Aluno, DataNascimento)` no dataset de alunos, respeitando os filtros de tempo/espaço, mas ignorando o filtro de tipo de vacina.
- **Cálculo Aplicação:** Soma total de doses no período filtrado.

### 4.2 KPI Cards por Vacina
- **Tipo:** Toggle buttons que permitem filtrar o dashboard por tipos específicos de vacina.
- **Visual:** Padrão Premium com hover effect e glow.

### 4.3 Tabela Comparativa de Performance por ANO
- **Base:** `build_comparativo_anual` com agrupamento por "Vacina".
- **Ordenação:** Segue a ordem de volume dos KPI Cards.
- **Cálculos:** % Total e Var% Interanual.
- **Toolbar:** `vacinacao_ano_actions_toolbar`.

### 4.4 Tabelas Top por URG
- **Principais Escolas:** Lista as escolas com maior volume de doses, sensível ao filtro de vacina.
- **Principais Vacinas:** Lista as vacinas mais aplicadas por URG, imune ao filtro de vacina.

### 4.5 Detalhamento por Aluno
- **Visual:** Tabela com colunas de anos de referência mostrando as vacinas aplicadas.
- **Destaque:** Encaminhamentos/Vacinas na seleção ativa podem ser destacados via CSS/JS.
- **Navegação:** LinkColumn para o perfil do aluno.

---

## 5. Regras de Negócio
- **Imunidade de Filtro:** Os indicadores de "Total de Alunos" e "Alunos Atendidos" são globais e não reagem ao filtro de tipo de vacina, servindo como base de cobertura.
- **Cross-Filtering:** Seleções na tabela de performance por URG propagam o filtro de unidade para todo o sistema via `global_urgs`.

---

## 6. Observações Técnicas
- **Chaves de AgGrid:** `urg_table_vacinacao_{selecao}` e `escola_table_selection_vacinacao`.
- **CSS:** Injeção de estilos para toolbars e botões de KPI consistente com o Design System.
