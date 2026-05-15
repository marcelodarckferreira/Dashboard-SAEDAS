# Especificação Técnica — Arquitetura de Sidebar (Híbrida)

O SAEDAS utiliza uma arquitetura de sidebar híbrida para equilibrar a consistência de navegação global com a flexibilidade necessária para filtros específicos de cada módulo.

---

## 1. Visão Geral
A sidebar é composta por três camadas de responsabilidade:
1.  **Componente Compartilhado (`sidebar_filters`):** Filtros dimensionais comuns.
2.  **Lógica Local da Página:** Filtros específicos de domínio (ex: Vacinas, Especialidades).
3.  **Ações de Saída:** Exportação de dados e utilitários.

---

## 2. Componente `sidebar_filters` (Shared)
Localizado em `app/components/sidebar_filters.py`.

### 2.1 Filtros Gerenciados
- **Ano:** Suporta seleção múltipla e derivação automática de colunas de data (`DtFechamento`, `Data`).
- **URG:** Filtro mestre de unidade regional.
- **Escola:** Filtro em cascata (reage à seleção de URG).
- **Tipo:** Filtro por tipo de instituição (Pública, Privada, etc.).

### 2.2 Sincronização e Estado
O componente é responsável por disparar os callbacks de sincronização definidos no `state_manager.py`:
- `sync_sidebar_to_home`
- `sync_sidebar_urg_to_home`
- `sync_sidebar_escola_to_global`

---

## 3. Implementação Local (Páginas)
Cada arquivo de página (`home.py`, `vacinacao.py`, etc.) deve seguir a seguinte ordem de montagem:

1.  **Título:** `st.sidebar.title("Filtros - [Nome da Página]")`.
2.  **Filtros Core:** Chamada da função `sidebar_filters()`.
3.  **Filtros Específicos:** Injeção de multiselects locais (ex: `vacinacao_vacina_multiselect`).
    - *Nota:* Filtros específicos que afetam KPI cards devem usar chaves de session state consistentes para suportar a funcionalidade de toggle.
4.  **Exportação:** Seção de "Exportar dados" com o `download_button`.

---

## 4. Regras de Negócio e Comportamento dos Filtros

Para garantir a integridade dos dados, a sidebar segue regras estritas de interdependência:

### 4.1 Hierarquia de Cascata (URG → Escola)
- **Regra:** A seleção de uma ou mais URGs na sidebar (ou via tabela mestre) deve filtrar obrigatoriamente a lista de opções disponíveis no filtro de Escolas.
- **Implementação:** O componente `sidebar_filters` gerencia essa cascata internamente para evitar que o usuário selecione uma escola que não pertence à URG ativa.

### 4.2 Persistência Temporal (Ano)
- **Regra:** O ano selecionado é uma variável global (`global_years`).
- **Comportamento:** Ao navegar entre abas, a sidebar deve persistir a seleção de ano anterior, garantindo uma análise comparativa fluida sem a necessidade de re-filtragem.

### 4.3 Regras de Imunidade
Alguns componentes ignoram filtros específicos da sidebar para manter o contexto estatístico:
- **KPIs Demográficos:** Devem ignorar filtros de categoria (ex: Vacina, Exame) para manter o denominador (Total de Alunos) constante.
- **Tabelas de Cobertura:** Devem mostrar todas as URGs da rede, mesmo que não haja dados para o filtro específico selecionado (exibindo zero ou vazio).

---

---

## 5. Regras de Ouro de Sincronização e Filtragem

Para garantir que o dashboard seja preditivo e coeso, as seguintes regras de sincronização bidirecional são obrigatórias:

### 5.1 Sincronismo Temporal (Botões ↔ Sidebar)
- **Regra:** O [Seletor Temporal Mestre](shared_components_spec.md#2-seletor-temporal-mestre-botoes-de-ano) (botões de ano no topo da página) e o filtro de Ano na Sidebar devem atuar em espelhamento perfeito.
- **Comportamento:** Qualquer alteração em um deve atualizar instantaneamente o outro, garantindo que o contexto temporal seja único e visível em ambos os controles.

### 5.2 Propagação de Seleção e Limpeza Granular (Tabelas ↔ Sidebar)
- **Seleção:** Clicar em uma linha de URG ou Escola em uma Tabela Mestre deve marcar o respectivo item na Sidebar.
- **Desseleção Total (Limpeza por Filtro):** Caso o usuário desmarque **todas** as opções em uma tabela de seleção específica, apenas o filtro equivalente na Sidebar deve ser limpo (retornando ao estado "Todos").
- **Regra de Isolamento:** A limpeza de uma dimensão (ex: Escola) **não deve** afetar as seleções ativas em outras dimensões (ex: URG ou Ano). A propagação da limpeza é estritamente **por cada filtro** individualmente.

### 5.3 Imunidade ao Auto-Filtro
- **Regra:** Componentes usados para **seleção** (Tabelas Mestres) ou **Indicadores Gerais** (KPI Cards) não podem sofrer o efeito do filtro gerado por eles mesmos.
- **Razão:** Uma tabela de URGs deve continuar mostrando todas as URGs disponíveis para permitir que o usuário selecione múltiplos itens. Se ela fosse filtrada pela própria seleção, os outros itens sumiriam, impedindo a multi-seleção.

### 5.4 Escopo Global e Exceções
- **Regra Geral:** Os filtros globais (Ano, URG, Escola, Tipo) exercem influência sobre **todos** os componentes da tela (Gráficos, KPIs, Tabelas de Detalhe).
- **Exceção:** A única exceção automática é a Regra 5.3 (Imunidade). Qualquer outra exceção específica (ex: um gráfico que deve mostrar sempre a rede toda para comparação) deve ser informada explicitamente na regra da própria tela (SPEC da página).

---

## 6. Sincronização Bidirecional (Técnica)
A implementação técnica utiliza o `session_state` como barramento de dados:
1.  **Tabela AgGrid:** Dispara evento `SELECTION_CHANGED`.
2.  **Callback Python:** Atualiza chaves como `pending_sidebar_urg_filter`.
3.  **Sidebar Widget:** Renderiza com o novo `default_value` no rerun.

---

## 7. Fontes de Verdade (Data Governance)
... [conteúdo mantido] ...

---

## 8. Checklist de Governança
- [ ] O seletor de ano reflete a sidebar?
- [ ] Ao desmarcar tudo na tabela, o filtro da sidebar limpou?
- [ ] As tabelas mestres continuam mostrando todos os itens mesmo após seleção?
- [ ] Todos os gráficos da página reagiram ao filtro da sidebar?
