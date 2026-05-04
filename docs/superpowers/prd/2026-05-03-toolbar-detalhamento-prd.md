# PRD: Toolbar e Configuração de Colunas — Detalhamento Home

**Data:** 2026-05-03  
**Status:** Ativo  
**Página alvo:** `Home` (`app/app_pages/home.py`)

---

## 1. Problema

Na tabela de detalhamento da Home, os controles estavam dispersos e com baixa ergonomia:
- ação de colunas em um ponto;
- ações de copiar/exportar em outro;
- experiência inconsistente para exibir/ocultar colunas.

Isso aumentava o custo de uso recorrente e dificultava ajustes rápidos da visão de dados.

---

## 2. Objetivo do Produto

Consolidar os controles da tabela de detalhamento em um único fluxo, com:
- toolbar unificada e previsível;
- configuração de colunas rápida;
- menor ruído visual e menor espaço desperdiçado.

---

## 3. Escopo

Incluído:
- Toolbar superior da tabela de detalhamento com 3 ações: `Colunas`, `Copiar`, `CSV`.
- Painel expansível de configuração de colunas acionado por `Colunas`.
- Controle de visibilidade por checkbox (marcado exibe, desmarcado oculta).
- Distribuição automática das colunas do painel: máximo de 10 itens por coluna.

Não incluído:
- Persistência entre sessões/usuários (mantido em `st.session_state`).
- Replicação automática em outras páginas.
- Mudança de comportamento dos filtros globais da aplicação.

---

## 4. Usuários e Fluxo Principal

Usuário analítico da Home:
1. abre a tabela de detalhamento;
2. clica em `Colunas`;
3. marca/desmarca campos para ajustar a grade;
4. copia para Excel (`Copiar`) ou exporta CSV (`CSV`).

---

## 5. Critérios de Sucesso

- Controles de tabela ficam disponíveis em uma única toolbar.
- Usuário ajusta visibilidade de colunas sem perder contexto da tabela.
- Painel de colunas reduz espaços vazios e mantém legibilidade.
- Exportação/cópia continuam funcionando com os dados visíveis.

---

## 6. Requisitos Funcionais

- RF1: `Colunas` alterna exibição do painel.
- RF2: Painel usa checkboxes por coluna da tabela.
- RF3: Ocultação aplica `hide=True` no AgGrid para colunas desmarcadas.
- RF4: Painel organiza itens em múltiplas colunas com no máximo 10 linhas por coluna.
- RF5: `Copiar` envia dados para clipboard (Excel-friendly).
- RF6: `CSV` baixa arquivo `detalhamento_home.csv`.

---

## 7. Requisitos Não Funcionais

- RNF1: Estilos devem ser escopados por chaves fixas (`st-key-*`) e seletores estáveis.
- RNF2: Evitar dependência de classes dinâmicas `st-emotion-cache-*`.
- RNF3: Mudanças devem ficar isoladas à Home, sem regressão visual global.

---

## 8. Dependências e Referências

- SPEC técnico: `docs/superpowers/specs/2026-05-03-toolbar-detalhamento-design.md`
- Documentação base:
  - `docs/architecture.md`
  - `docs/data_interaction.md`
  - `docs/design_system.md`
