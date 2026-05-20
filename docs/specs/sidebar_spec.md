# Especificação Técnica — Arquitetura de Sidebar (Híbrida)

O SAEDAS utiliza uma arquitetura de sidebar híbrida para equilibrar a consistência de navegação global com a flexibilidade necessária para filtros específicos de cada módulo.

---

## 1. Visão Geral

A sidebar é composta por duas camadas de responsabilidade:

1. **Sidebar Global (`app/main.py`):** Logo, título, menu de navegação (`option_menu`) e botão de saída. **Não contém filtros de dados.**
2. **Sidebar Local de Página:** Cada página (`home.py`, `consulta.py`, etc.) acrescenta seus próprios filtros (Ano, URG, Escola, Tipo e filtros locais de domínio).

---

## 2. Sidebar Global (`app/main.py`)

A sidebar global é renderizada dentro de `with st.sidebar:` no `main.py` e contém apenas três blocos:

### 2.1 Logo Institucional
- Imagem `assets/logo-pcni.png` convertida para base64 e centralizada em um container com `background-color: #1e293b`, `border-radius: 12px`.
- Fallback: `st.warning("Logo 'logo-pcni.png' não encontrado.")` se o arquivo não existir.

### 2.2 Menu de Navegação (`option_menu`)
- Widget: `streamlit_option_menu.option_menu`.
- Chave: `sidebar_main_menu`.
- Opções (ordem fixa): `Início`, `Encaminhamentos`, `Exames`, `Vacinação`, `Nutrição`, `Enfermagem`, `Assistente Social`, `Psicólogo`, `Professor`, `Médico`, `Aluno`.
- Ícones (Bootstrap): `house`, `clipboard-check`, `file-medical`, `shield-plus`, `egg-fried`, `bandaid`, `people`, `person-heart`, `mortarboard`, `heart-pulse`, `person`.
- Orientação: vertical.
- Estado sincronizado em `st.session_state["menu_escolhido"]` via callback `sync_sidebar_menu(key)`.
- Suporta deep-linking via `?menu=...` ou `?aluno=...&nasc=...` (parâmetros tratados antes da renderização da sidebar). Quando ativo, usa `manual_select=default_index`.

### 2.3 Rodapé — Botão "Sair do Sistema"
- Spacer (`flex-grow: 1`) + divisor (`---`).
- Botão `st.sidebar.button("Sair do Sistema", icon=":material/logout:")`.
- Ao ser clicado, executa `st.session_state["authenticated"] = False` e `st.rerun()`, retornando à tela de login (`render_login_screen`).
- CSS específico aplica fundo transparente, borda `#334155`, hover vermelho (`#ef4444`).

### 2.4 Autenticação (Pré-Requisito)
Antes da sidebar ser renderizada, `main.py` verifica `st.session_state.get("authenticated", False)`. Se falso, renderiza `render_login_screen()` (token de 8 dígitos lido de `.env` via `SYSTEM_TOKEN`) e interrompe com `st.stop()`.

### 2.5 Detecção de Mudança de Página
Após o menu, `main.py` compara `current_menu` com `_last_active_menu` e define `_is_page_first_run` para uso pelas páginas (proteção de estado AgGrid).

---

## 3. Sidebar Local de Página

Cada arquivo de página é responsável por adicionar os filtros globais (Ano, URG, Escola, Tipo) e seus filtros locais, normalmente seguindo esta ordem:

1. **Título:** `st.sidebar.title("Filtros - [Nome da Página]")`.
2. **Filtros globais** (sincronizados com `global_years`, `global_urgs`, `sidebar_escola_filter`):
   - Ano (multiselect, chave `sidebar_year_filter`).
   - URG (multiselect, chave `sidebar_urg_filter`).
   - Escola (multiselect em cascata, chave `sidebar_escola_filter`).
   - Tipo (multiselect, opcional).
3. **Filtros específicos:** Ex.: `consulta_encaminhamento_multiselect`, `vacinacao_vacina_multiselect`, `exame_regulacao_multiselect`, `nutricao_situacao_multiselect` — com shadow-key `persistent_*` em `state_manager.py`.
4. **Exportação:** Seção "Exportar dados" com `st.download_button` (quando aplicável).

---

## 4. Regras de Negócio e Comportamento dos Filtros

### 4.1 Valores Padrão (Default)
- **Ano:** Único filtro com seleção inicial. `init_global_state()` lê o maior ano de `app/data/DashboardHome.csv` (via `get_max_year_from_data`) e atribui a `global_years`.
- **Demais filtros:** Iniciam vazios (equivalente a "Todos").

### 4.2 Hierarquia de Cascata (URG → Escola)
A seleção de URGs filtra obrigatoriamente a lista de Escolas disponíveis.

### 4.3 Persistência Temporal (Ano)
A variável `global_years` é preservada na navegação entre páginas via `init_global_state()`.

### 4.4 Regras de Imunidade
- **KPIs Demográficos:** Ignoram filtros de categoria.
- **Tabelas de Cobertura:** Mostram todas as URGs da rede.

---

## 5. Regras de Ouro de Sincronização e Filtragem

### 5.1 Sincronismo Temporal (Botões ↔ Sidebar)
O Seletor Temporal Mestre (botões no topo das páginas) e o filtro de Ano da sidebar atuam em espelhamento perfeito via `sync_sidebar_to_home` e `sync_home_to_sidebar`.

### 5.2 Propagação de Seleção e Limpeza Granular (Tabelas ↔ Sidebar)
- Clicar em uma URG/Escola em uma Tabela Mestre marca o item na sidebar.
- Desmarcar tudo limpa **apenas** o filtro equivalente (regra de isolamento por dimensão).

### 5.3 Imunidade ao Auto-Filtro
Tabelas Mestres e KPI Cards não devem ser filtrados pela própria seleção que geram.

### 5.4 Escopo Global e Exceções
Os 4 filtros globais (Ano, URG, Escola, Tipo) devem estar presentes em todas as páginas de dashboard.

### 5.5 Persistência de Navegação (Filtros Globais)
Garantida pelas chaves estáveis em `session_state` (ver `state_interaction_spec.md`).

### 5.6 Persistência de Filtros Locais (Específicos de Página)
Implementada via shadow-keys `persistent_*` inicializadas em `init_global_state()` e sincronizadas pelos callbacks `sync_local_*` em `state_manager.py`.

---

## 6. Sincronização Bidirecional (Técnica)

1. **AgGrid** dispara `SELECTION_CHANGED`.
2. **Callback Python** atualiza chaves `pending_sidebar_urg_filter` / `pending_sidebar_escola_filter`.
3. **`apply_pending_table_filters()`** processa essas chaves antes da renderização dos widgets da sidebar no próximo rerun.

---

## 7. Checklist de Governança

- [ ] O seletor de ano reflete a sidebar?
- [ ] Ao desmarcar tudo na tabela, o filtro da sidebar limpou?
- [ ] As tabelas mestres continuam mostrando todos os itens mesmo após seleção?
- [ ] Todos os gráficos da página reagiram ao filtro da sidebar?
- [ ] O botão "Sair" volta para a tela de login com token?
