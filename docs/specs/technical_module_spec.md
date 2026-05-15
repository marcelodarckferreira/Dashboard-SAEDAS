# Especificação Técnica — Módulos Técnicos (Médico, Enfermagem, etc.)

Esta especificação cobre o padrão de implementação dos módulos especializados do SAEDAS: Médico, Enfermagem, Psicólogo, Assistente Social e Professor. Todos compartilham a mesma arquitetura de "template" para garantir consistência operacional.

---

## 1. Visão Geral e Propósito
- **Objetivo:** Monitorar o volume e a distribuição de atendimentos realizados por categoria profissional.
- **Módulos Abrangidos:**
  - `medico.py`
  - `enfermagem.py`
  - `psicologo.py`
  - `assistencia_social.py`
  - `professor.py`

---

## 2. Fontes de Dados e Schemas
Cada módulo carrega três datasets específicos e um demográfico de referência:
- **Atendimentos:** `Dashboard[Modulo].csv` (`SCHEMA_[MODULO]`)
- **Detalhamento Aluno:** `Dashboard[Modulo]Aluno.csv` (`SCHEMA_[MODULO]_ALUNO`)
- **Performance Anual:** `Dashboard[Modulo]Ano.csv` (`SCHEMA_[MODULO]_ANO`)
- **Demográfico (Referência):** `DashboardHome.csv` (`SCHEMA_HOME`)

---

## 3. Estrutura da Página e Filtros
### 3.1 Sidebar e Sincronização
- **Filtros Padrão:** Ano, URG, Escola, Tipo.
- **Sincronização:** Uso de `init_global_state()` e `sync_sidebar_escola_selection` para garantir que o estado seja preservado entre as páginas.

### 3.2 Seletor Temporal Mestre
Ver especificações em [Shared Components Spec](shared_components_spec.md#2-seletor-temporal-mestre-botoes-de-ano). Este componente altera o estado global de anos (`global_years`).

---

## 4. Componentes de Interface

### 4.1 Cabeçalho de Métricas
- **Indicadores Demográficos:** Total de Alunos e Alunos Atendidos (Vindos da `DashboardHome.csv`).
- **Indicador Profissional:** Total de atendimentos da categoria específica.
- **Estilo:** `render_metric_cards()` com 3 cards no topo.

### 4.2 Tabela de Performance por URG (Mestre)
- **Função:** `build_comparativo_anual(df, "URG")`.
- **Interação:** Clique na linha para filtrar o dashboard pela URG selecionada.
- **Sync:** JavaScript `onFirstDataRendered` para sincronizar seleções da sidebar com as linhas da tabela.
- **Toolbar:** `{modulo}_urg_actions_toolbar`.

### 4.3 Principais Escolas por URG
- **Função:** `render_top_por_urg`.
- **Comportamento:** Exibe o ranking de escolas que mais realizaram atendimentos na URG selecionada.
- **Toolbar:** `escola_table_selection_{modulo}_actions_toolbar`.

### 4.4 Gráfico de Distribuição por URG
- **Tipo:** Gráfico de barras agrupado por Ano e URG (Plotly).
- **Ordenação:** Ordenado pelo numeral romano da URG (I, II, III...).

### 4.5 Detalhamento por Aluno
- **Lógica de Agregação:** Consolida consultas por ID/Aluno, transformando anos em colunas dinâmicas.
- **Ações:** LinkColumn para o perfil individual do aluno.
- **Toolbar:** `{modulo}_aluno_actions_toolbar`.

---

## 5. Regras de Negócio e Cálculos
- **Imunidade de Filtro (URG):** A tabela mestre de URG deve mostrar todas as unidades disponíveis, reagindo apenas ao filtro de Ano, para permitir que o usuário selecione qualquer unidade.
- **Ordenação Romana:** As URGs devem ser ordenadas logicamente (I, II, III...) e não alfabeticamente.

---

## 6. Observações Técnicas
- **Chaves de AgGrid:** Devem ser dinâmicas (incluindo a seleção ativa no nome da chave) para garantir que o componente seja remontado com o estado correto do clipboard e seleções.
- **Toolbars:** Implementação unificada (HTML/JS) para garantir funcionalidade de cópia e download instantâneo.
