# Blueprint Reutilizável: Telas Semelhantes (Consulta, Nutrição, Vacinação, Exames)

## Objetivo
Padronizar a implementação de telas de mesma natureza para reaproveitar:
- estrutura de componentes;
- identidade visual;
- regras de sincronismo entre componentes (sidebar, cards, tabelas de seleção, gráficos).

Este documento é a referência de execução para novas telas e para manutenção.

## Quando usar
Use este blueprint sempre que a tela tiver:
- filtros de sidebar (Ano, URG, Escola, Tipo e/ou domínio específico);
- indicadores em cards;
- uma ou mais tabelas AgGrid;
- pelo menos uma tabela usada como controle de seleção.

## Estrutura Base Obrigatória
1. Carregamento + validação de CSV via `load_csv(...)` + schema.
2. Inicialização de estado global com `init_global_state()`.
3. Sidebar com `sidebar_filters(...)`.
4. Seletor temporal mestre no padrão Home (`massive_year_selector`).
5. Bases de dados separadas:
   - `df_filt`: base final filtrada para análise;
   - `df_*_no_*`: bases imunes para componentes de seleção mestre.
6. Indicadores (cards) + KPIs do domínio.
7. Tabelas AgGrid com toolbar unificada.
8. Gráficos de distribuição/comparativo.
9. Detalhamento final (quando houver).

## Contrato de Estado e Sincronismo
- Fonte de verdade global:
  - `global_years`, `global_urgs`
- Estado da sidebar:
  - `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`
- Estado auxiliar:
  - `last_interaction_source`
  - `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`

Regra:
- Se ação veio da sidebar, não sobrescrever imediatamente com estado transitório da tabela.
- Se ação veio da tabela, atualizar `pending_sidebar_*` e chamar `st.rerun()`.

## Regras de Negociação entre Componentes
1. Tabela mestre de seleção é imune ao próprio filtro.
2. Sidebar deve refletir seleção da tabela mestre.
3. Tabela mestre deve refletir seleção da sidebar.
4. Componentes analíticos (cards/gráficos/tabelas não-mestre) usam `df_filt`.
5. Componentes de seleção usam base imune dedicada.
6. Indicadores KPI por categoria (ex.: Encaminhamento/Regulação/Exame) não devem se auto-filtrar:
   - card total usa `df_filt` (todos os filtros aplicados);
   - cards de categoria usam base imune ao próprio filtro (ex.: `df_filt_no_enc`, `df_filt_no_reg`) para manter opções visíveis e comportamento de toggle.

## Padrão Visual Obrigatório
- Seletor de Ano: mesmo bloco CSS e estrutura de `home.py`.
- Cards:
  - `.home-metric-card`
  - `.metric-card-static`
  - `.home-metric-label`
  - `.home-metric-value`
- KPIs clicáveis:
  - `div[class*="st-key-btn_kpi_"] button` com tipografia consistente.
- AgGrid:
  - toolbar agrupada;
  - `.selection-master-table` para tabelas de seleção;
  - `.st-table-with-total` para tabelas padrão.

## Padrão Técnico AgGrid
- Sempre `render_saedas_aggrid(...)`.
- Sempre `render_table_toolbar(...)` antes da tabela.
- Quando houver total, usar `pinnedBottomRowData`.
- Altura inteligente com cap de 20 linhas.
- Evitar `st.dataframe` em telas padronizadas.

## Checklist de Implementação (Nova Tela)
1. Criar schema e carga de dados.
2. Copiar seletor anual da Home (exato).
3. Montar filtros sidebar e bases imunes.
4. Implementar tabela mestre URG (se aplicável).
5. Implementar tabela mestre Escola (se aplicável).
6. Implementar cards e KPIs com estilo padrão.
7. Implementar gráficos e comparativos com `df_filt`.
8. Garantir toolbar agrupada em toda AgGrid.
9. Validar sync sidebar <-> tabela (selecionar e remover).

## Checklist de Manutenção / Recuperação
1. Conferir chaves `session_state` e pendências.
2. Conferir fonte de verdade de cada componente (`df_filt` vs base imune).
3. Conferir presença de classes CSS críticas.
4. Conferir ausência de `st.dataframe`.
5. Executar testes manuais de sincronismo bidirecional.

## Comandos de Verificação
- `python -m py_compile app/app_pages/<tela>.py app/utils/page_helpers.py app/components/sidebar_filters.py`
- `rg -n "st\\.dataframe\\(|render_saedas_aggrid\\(|render_table_toolbar\\(" app/app_pages/<tela>.py app/utils/page_helpers.py`
- `streamlit run app/app.py`
