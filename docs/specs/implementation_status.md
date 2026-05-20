# Quadro de Governança: Sincronismo e Filtros (SAEDAS)

Este documento atesta a conformidade técnica de cada módulo com as **Regras de Ouro** de sincronismo bidirecional, garantindo a integridade da experiência do usuário (UX).

## 1. Matriz de Conformidade

| Módulo | Sinc. Temporal | None -> [] | Limpeza Granular | Imunidade KPI | Imunidade Tabela | Toolbar CSS | AgGrid Aluno |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Home** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | N/A |
| **Consulta** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Exames** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Vacinação** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Nutrição** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Médico** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Enfermagem** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Psicólogo** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Assist. Social** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Professor** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## 2. Detalhamento das Regras Aplicadas

1.  **Sincronismo Temporal**: Espelhamento entre Botões Mestre e Sidebar (Ano).
2.  **None -> []**: Tratamento de retorno nulo do AgGrid para evitar travamentos de estado.
3.  **Limpeza Granular**: Desseleção total em uma tabela limpa apenas o seu respectivo filtro.
4.  **Imunidade KPI**: Indicadores de topo não somem ao filtrar categorias específicas.
5.  **Imunidade Tabela**: Tabelas de seleção não filtram a si mesmas (mantêm multiseleção).
6.  **Toolbar CSS**: Alinhamento e funcionalidade dos botões Copiar/Download.
7.  **AgGrid Aluno**: Uso do componente unificado com altura dinâmica (min 5, max 50/full).

## 3. Histórico de Validação

*   **15/05/2026**: Padronização universal concluída em todos os módulos operacionais. Arquitetura de "Sincronismo Robusto" validada pelo usuário.
*   **15/05/2026**: Implementada persistência de filtros locais entre páginas e técnica de "Key Hardening" para proteção do AgGrid contra resets.
*   **15/05/2026**: Migração total das tabelas de alunos para AgGrid (Consulta a Professor) com regras de altura dinâmica e expansão responsiva por URG.
*   **15/05/2026**: Criação da especificação técnica de [Schemas de Dados (CSV)](data_schemas_spec.md) e [Interação de Estado](state_interaction_spec.md).

---
**Status Global:** 🟢 ESTÁVEL E CONSOLIDADO
