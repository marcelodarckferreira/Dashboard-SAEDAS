# Especificação Técnica — Interação e Sincronização de Estado

Este documento detalha o funcionamento do motor de sincronização de estado do dashboard SAEDAS, abrangendo a persistência de filtros, a comunicação entre componentes e a prevenção de resets indesejados no AgGrid.

---

## 1. Arquitetura de Estado (Session State)

O SAEDAS utiliza um modelo de estado centralizado via `st.session_state`, dividido em três categorias:

| Categoria | Prefixo/Chave | Escopo | Descrição |
| :--- | :--- | :--- | :--- |
| **Global** | `global_` | Aplicativo | Filtros de Ano e URG que afetam todas as páginas. |
| **Widget** | `sidebar_` | Página (Prunável) | Chaves vinculadas diretamente aos widgets da sidebar. O Streamlit remove estas chaves se o widget não for renderizado. |
| **Persistente** | `persistent_` | Aplicativo | Shadow-keys que armazenam seleções locais (ex: Vacina) para sobreviver à navegação. |

---

## 2. Ciclo de Vida da Inicialização (`state_manager.py`)

A função `init_global_state()` deve ser chamada no topo de cada página (`page_...`) e no `main.py`.

### 2.1 Regra de Valores Padrão (Default)
- **Ano:** O único filtro com seleção inicial obrigatória. Deve carregar o **maior ano** disponível no arquivo `DashboardHome.csv`.
- **Demais Filtros:** Devem iniciar vazios (`[]`), o que o sistema interpreta como "Todos".

---

## 3. Persistência de Filtros Locais

Para evitar que filtros específicos de módulo (ex: "Encaminhamento" na página de Consulta) sejam limpos ao navegar para outra aba, aplica-se a seguinte estratégia:

1. **Definição:** Uma chave `persistent_{modulo}_{filtro}` é criada no `init_global_state`.
2. **Sincronização:** Um callback `sync_local_{modulo}_{filtro}` atualiza a chave persistente sempre que o widget muda.
3. **Restauração de Renderização:** No carregamento da página, se a chave do widget estiver ausente (podada), ela é restaurada a partir da chave persistente **antes** da chamada do widget:
   ```python
   if "meu_widget_key" not in st.session_state:
       st.session_state["meu_widget_key"] = st.session_state.get("persistent_filtro", [])
   ```

---

## 4. Sincronização Bidirecional AgGrid-Sidebar

As tabelas de "Performance por URG" e "Escolas" funcionam como navegadores globais.

### 4.1 Estratégia de "Key Hardening" (Proteção contra Resets)
Para evitar que a mudança de um filtro externo (ex: mudar o Ano ou a Vacina) cause o reset da seleção na tabela AgGrid, a chave do componente deve ser composta por todos os fatores que alteram seus dados:

- **Fórmula da Chave (URG):** `urg_table_{modulo}_{anos_selecionados}_{filtros_locais}_{selecao_atual_urg}`
- **Fórmula da Chave (Escola):** `escola_table_{modulo}_{anos_selecionados}_{urgs_selecionadas}_{selecao_atual_escola}`

### 4.2 Proteção `_key_changed`
Sempre que a chave da tabela muda (indicando uma nova instância/rerender), o sistema deve:
1. Ativar a flag `_key_changed = True`.
2. Ignorar a resposta de seleção do AgGrid neste ciclo de processamento (evitando que o estado `[]` inicial da nova tabela sobrescreva o `st.session_state` global).
3. Utilizar o JavaScript `onFirstDataRendered` para re-aplicar visualmente a seleção correta nas linhas.

---

## 5. Implementação de Master Tables (Regras de Ouro)

1. **Imunidade Seletiva:** Tabelas Mestre de URG não devem ser filtradas por elas mesmas (coluna URG), permitindo que o usuário veja e selecione qualquer unidade.
2. **Reatividade:** Devem reagir instantaneamente a filtros de **Ano** e **Categoria** (Vacina, Encaminhamento, etc.).
3. **Deep Linking:** Mudanças na tabela devem disparar `st.rerun()` para propagar a nova seleção para os demais componentes (KPIs e Gráficos).

---

## 6. Callbacks Disponíveis (`app/utils/state_manager.py`)

- `sync_sidebar_to_home`: Propaga anos da sidebar para os botões da Home.
- `sync_home_to_sidebar`: Propaga anos dos botões da Home para a sidebar.
- `sync_sidebar_urg_to_home`: Atualiza a seleção global de URG.
- `apply_pending_table_filters`: Processa seleções de tabela que estão aguardando para atualizar a sidebar no próximo ciclo de renderização.

---

## 8. Regras de Filtragem por Categoria (Regulação)

Nos módulos de regulação (Consulta, Exame, Nutrição, Vacinação), aplica-se um modelo híbrido de filtragem para a dimensão principal (ex: Tipo de Exame ou Encaminhamento):

### 8.1 Imunidade Seletiva (KPIs e Cards)
- **Cards de Indicadores Principais:** Devem ser **imunes** ao filtro de categoria local para exibir o volume total do módulo sob os filtros globais (Ano, URG, Escola, Tipo).
- **Botões de Toggle KPI:** Devem utilizar uma base de dados **imune** à própria seleção de categoria. Isso garante que todos os botões permaneçam visíveis e interativos, mesmo que alguns estejam desmarcados.

### 8.2 Reatividade Total (Tabelas e Gráficos)
- **Tabelas de Performance (Ano/URG):** Devem **reagir** instantaneamente à seleção de categorias. Se "RX" for desmarcado, ele deve desaparecer da tabela de performance.
- **Gráficos de Distribuição:** Devem refletir apenas as categorias selecionadas, permitindo comparações focadas.
- **Detalhamento de Alunos:** Filtra rigorosamente os registros para exibir apenas os alunos vinculados às categorias ativas na sidebar ou nos cards.

---

## 9. Reatividade de Tabelas de Detalhamento (Alunos)

As tabelas de detalhamento de alunos (históricos) possuem um comportamento reativo específico baseado no contexto de filtragem global:

1. **Seleção de URG (Trigger de Expansão):**
   - Quando `global_urgs` está vazio (nenhuma URG selecionada), a tabela opera em **Modo de Resumo**, limitada visualmente a 20 linhas para manter a performance e a fluidez do scroll da página.
   - Quando uma ou mais URGs são selecionadas, a tabela entra em **Modo de Análise Profunda**, expandindo sua altura para exibir **todos os registros** do dataframe.

2. **Altura Mínima:**
   - O componente mantém uma altura mínima equivalente a **5 linhas** para evitar layout shifts.
