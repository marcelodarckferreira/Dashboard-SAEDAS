# Protocolo de Manutenção e Governança — SAEDAS

Este documento define o fluxo obrigatório para a manutenção corretiva, evolutiva ou estética de qualquer módulo do sistema SAEDAS. O objetivo é garantir que código, design e documentação permaneçam sempre sincronizados.

---

## 🔄 Fluxo de Trabalho (5 Passos)

Para qualquer intervenção em uma tela ou componente, o desenvolvedor (ou agente de IA) deve seguir rigorosamente esta ordem:

### 1. Carregamento de Contexto (Spec)
Antes de iniciar qualquer código, deve-se ler a especificação da tela correspondente (ex: `docs/specs/home_page_spec.md`). Se a mudança envolver componentes globais, a `docs/specs/shared_components_spec.md` deve ser consultada.

### 2. Implementação e Ajustes
Executar as alterações solicitadas diretamente no código (`app/app_pages/`, `app/assets/styles.css`, etc.), seguindo os padrões de design estabelecidos no **Design System**.

### 3. Validação do Processo
Verificar se a alteração cumpre o requisito técnico e se não quebrou as regras de sincronização bidirecional, filtros ou layout (evitar "Layout Shifts").

### 4. Atualização da Documentação
Após a estabilização da funcionalidade, a documentação correspondente **deve ser atualizada**.
- Mudanças técnicas na tela → `docs/specs/{tela}_page_spec.md`.
- Mudanças em componentes reutilizados → `docs/specs/shared_components_spec.md`.
- Mudanças em tokens visuais → `docs/design_system.md`.

### 5. Controle de Checklist
Cada tela possui um checklist de validação (geralmente no final de sua respectiva SPEC ou na `docs/home_page_standards.md`). O processo só é considerado concluído quando todos os itens do checklist daquela tela forem validados.

---

## 🛡️ Regras de Ouro de Governança

1.  **Fonte Única de Verdade:** Se o código e a documentação divergem, a documentação deve ser corrigida para refletir o estado estável desejado.
2.  **Referência Cruzada:** Telas específicas não devem duplicar regras de componentes compartilhados; elas devem apenas apontar para as especificações globais.
3.  **Checklist Impeditivo:** Uma tarefa não é considerada "Done" sem a validação do checklist visual e funcional da tela afetada.
