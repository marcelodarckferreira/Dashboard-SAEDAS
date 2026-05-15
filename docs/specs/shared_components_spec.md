# Especificação de Componentes Compartilhados — Dashboard SAEDAS

Este documento detalha os componentes de interface reutilizáveis do sistema SAEDAS, especificando seu comportamento, design e implementação técnica.

---

## 1. Toolbar Unificada (Copiar + CSV)

A Toolbar Unificada é um componente crítico utilizado em todas as tabelas do dashboard para fornecer funcionalidades de exportação e cópia de dados.

### 1.1 Motivação Técnica
Devido às restrições de segurança do navegador (Permissions Policy) em `iframes` gerados pelo Streamlit, o uso de `st.button` para operações de `navigator.clipboard` resultava em falhas. A solução foi unificar todos os botões de ação de tabela (Coluna, Copiar e CSV) em um único componente HTML personalizado (`st.components.v1.html`). 

Isso garante que o gesto do usuário ocorra dentro do contexto onde a API de Clipboard é permitida e mantém uma estética de **bloco único** (Triple Group), evitando reruns desnecessários para as funções de exportação.

### 1.2 Estrutura e Localização
- **Função:** `render_table_toolbar()`
- **Arquivo:** `app/utils/page_helpers.py`

### 1.3 Parâmetros e Funcionamento Híbrido
O componente opera em um modelo híbrido para suportar ações que exigem lógica do lado do servidor (como alternar colunas):

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `leading_action_label` | `str` | Ex: "Coluna". Se presente, ativa o modo Triple Group. |
| `key_prefix` | `str` | Chave única para o trigger de estado. |

**Mecanismo de Trigger:**
Quando o botão "Coluna" (dentro do HTML) é clicado, um script JavaScript localiza um `st.checkbox` oculto no Streamlit e simula um clique. Isso notifica o Python que a ação foi disparada, retornando `True` ou `False` para a página.

### 1.4 Implementação Visual (Triple Group)
O componente utiliza um layout `Flexbox` para agrupar os botões em um único bloco visual:
- **Botão de Ação (Coluna):** Arredondamento apenas na esquerda (`6px 0 0 6px`).
- **Botão Copiar:** Central, com bordas retas (se houver ação leading).
- **Botão CSV:** Arredondamento apenas na direita (`0 6px 6px 0`).
- **Bordas:** O componente gerencia bordas internas para evitar linhas duplas entre os botões.

### 1.5 Lógica de JavaScript (Unificada)
O script interno gerencia:
1.  **Trigger de Ação:** Comunicação via DOM com o pai para ações Streamlit.
2.  **Cópia (Clipboard):** TSV + Feedback "✅ Copiado!".
3.  **Download CSV:** Blob + Link virtual (Instantâneo).

### 1.6 Integração com a Página
A toolbar deve ser chamada dentro de um container:
- **Estrutura de Colunas:** 
  - Triple Group: `st.columns([0.65, 0.35])`
  - Dual Group: `st.columns([0.82, 0.18])`
- **Isolamento:** O `st.container` pai deve ter a chave `{prefix}_actions_toolbar` para controle de alinhamento.

---

## 2. Seletor Temporal Mestre (Botões de Ano)

O Seletor Temporal Mestre é o componente de controle cronológico global, presente no topo de todas as páginas (exceto Início) para definir o contexto de análise.

### 2.1 Estrutura Técnica
- **Container:** `st.container(key="massive_year_selector")`
- **Widget:** `st.segmented_control`
- **Modo:** `selection_mode="multi"`
- **Estado Global:** `st.session_state["global_years"]`

### 2.2 Sincronização de Estado
O seletor utiliza o callback `on_change=sync_home_to_sidebar` (definido em `app/utils/state_manager.py`).
1. O usuário seleciona um ou mais anos no componente visual.
2. O callback atualiza a variável global `global_years`.
3. A variável de sincronização `sidebar_year_filter` também é atualizada para manter a paridade com o multiselect da sidebar.
4. Um `st.rerun()` é disparado, e todas as tabelas e gráficos que utilizam `filter_by_sidebar_selections` ou lógica similar filtram os dados com base neste novo conjunto de anos.

### 2.3 Regras Visuais e UX (Estabilizadas)
- **Arquitetura de Grupo:** Bloco sólido conectado, sem espaços internos (`gap: 0`). O container pai deve ter `overflow: hidden` para respeitar o `border-radius: 12px`.
- **Destaque:** Borda de destaque persistente (`box-shadow` com `--accent-color`).
- **Dimensões:** Altura fixa de `80px` e fonte `2.4rem (800)`.
- **Centralização:** Garantida via Flexbox estrutural em todas as camadas (do container ao `<p>`). **Proibido o uso de `line-height` ou `transform`**.
- **Seletores Estáveis:**
  - Container: `.st-key-massive_year_selector [data-testid="stSegmentedControl"]`
  - Itens (Inativo): `div[data-testid="stBaseButton-segmented_control"]`
  - Itens (Ativo): `div[data-testid="stBaseButton-segmented_controlActive"]`

### 2.4 Estados de Interação
| Estado | Estilo |
| :--- | :--- |
| **Inativo** | Fundo transparente, texto `--text-muted`. |
| **Hover (Inativo)** | Fundo azul translúcido (`rgba(56, 189, 248, 0.08)`). |
| **Ativo** | Gradiente linear (`135deg, #38bdf8 0%, #1e40af 100%`), sombra interna e texto branco. |
| **Hover (Ativo)** | Gradiente azul intensificado (`7dd3fc` a `3b82f6`). |

---

## 3. Próximos Componentes (Backlog)
- [ ] Metric Cards Customizados
- [ ] Breadcrumb de Filtros Aplicados
- [ ] Footer Personalizado
