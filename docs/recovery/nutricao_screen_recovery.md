# Runbook de Recuperação: Tela Nutrição

## Objetivo
Documento operacional para restaurar e alinhar a tela `Nutrição` (`app/app_pages/nutricao.py`, função `page_nutricao()`) ao blueprint oficial em caso de regressão visual/funcional.

> Referências obrigatórias:
> - `docs/similar_screens_blueprint.md`
> - `docs/specs/nutricao_page_spec.md`
> - `docs/specs/state_interaction_spec.md`

---

## 1. Escopo Funcional
- Seletor temporal mestre (container `massive_year_selector`, widget `home_year_buttons`).
- Filtros sidebar: Ano, URG, Escola, Tipo, Situação Nutricional.
- Cards demográficos estáticos (Total de Alunos, Alunos Atendidos, Total de Registros).
- KPI toggle de Situação Nutricional (chunks de 5).
- Tabela Comparativa de Performance por ANO (Nutrição).
- Tabela Performance por URG (mestre de cross-filter).
- Top Escolas por URG (mestre de cross-filter de Escola).
- Gráficos: Comparativo Anual por URG e Distribuição por Situação.
- Detalhamento por aluno com pivot anual de Peso, Altura, IMC, Idade e Situação.

---

## 2. Fontes de Dados
| Dataset | CSV | Schema | Redis Key |
|---|---|---|---|
| Principal | `data/DashboardNutricao.csv` | `SCHEMA_NUTRICAO` | `saedas:nutricao:dataset:main` |
| Aluno | `data/DashboardNutricaoAluno.csv` | `SCHEMA_NUTRICAO_ALUNO` | `saedas:nutricao:dataset:aluno` |
| Ano (agregado) | `data/DashboardNutricaoAno.csv` | `SCHEMA_NUTRICAO_ANO` | `saedas:nutricao:dataset:ano` |
| Home (demografia) | `data/DashboardHome.csv` | `SCHEMA_HOME` | `saedas:home:dataset:main` |

Renomeações: `Qtd → Quantidade`, `DtNasc → DataNascimento`, `Peso → Peso (kg)`, `Altura → Altura (m)`.

---

## 3. Fonte de Verdade de Estado
- Globais: `global_years`, `global_urgs`.
- Sidebar: `sidebar_year_filter`, `sidebar_urg_filter`, `sidebar_escola_filter`.
- Pendências: `pending_sidebar_urg_filter`, `pending_sidebar_escola_filter`.
- Controle de origem: `last_interaction_source` (`sidebar` | `table` | `table_escola`).
- Filtro local Nutrição: `nutricao_situacao_multiselect` ↔ `persistent_nutricao_situacao`.
- Tabela Escola: `escola_table_selection_nutricao`, `escola_table_selection_nutricao__selected_values`.
- Guarda da chave AgGrid URG: `_prev_urg_table_key_nutricao`, `_is_page_first_run`.

---

## 4. Contrato de Sincronismo
- Two-way binding entre sidebar e tabelas mestre (URG e Escola).
- Fluxos:
  - Sidebar → `global_*` → `onFirstDataRendered` reflete na tabela.
  - Tabela → `global_*` → `pending_sidebar_*` → `apply_pending_table_filters` → `rerun`.
- Anti-loop: respeitar `last_interaction_source`; nunca usar widget como fonte de verdade.
- Callback de Situação Nutricional: `sync_local_nutricao_situacao` mantém `persistent_nutricao_situacao` em sincronia.

---

## 5. Regras de Filtro (pipeline)
1. `df_base_sem_escola` = `df` + `Tipo` + `Ano` (se `selected_years_comp` vazio → DataFrame vazio).
2. `df_base_final` = `df_base_sem_escola` + `Escola`.
3. `df_master_no_nut` = `df_base_final` + `URG`.
4. `df_master_filtrado` (`df_filt`) = `df_master_no_nut` + `Nutricao`.
5. `df_filt_no_escola` = `df_base_sem_escola` + `URG` (Top Escolas).
6. `df_filt_no_nut` = `df_master_no_nut` (cards/tabela comparativa).

---

## 6. Exceções Intencionais
- Tabela URG (mestre): sensível a Ano, Tipo e `Nutricao`; imune a URG e Escola.
- Tabela Escola (mestre): sensível a Ano e `Nutricao`; imune ao próprio filtro de Escola.
- Cards de Situação Nutricional: usam `df_filt_no_nut` para preservar o catálogo.
- Card "TOTAL DE REGISTROS DE NUTRIÇÃO": soma `df_master_no_nut["Quantidade"]`.
- Cards demográficos: `df_home_filt = filter_by_sidebar_selections(df_home, selections)`.

---

## 7. Regras Obrigatórias de UI
- Seletor temporal: padrão Home (`massive_year_selector` + `home_year_buttons` + callback `sync_home_to_sidebar`).
- Indicadores em grid de 5 colunas por linha.
- Tabela comparativa por ANO: respeita ordem dos KPIs, `TOTAL` na última linha.
- Toolbars com `render_table_toolbar` (botões `Copiar` + `CSV`).
- Wrappers obrigatórios:
  - `.selection-master-table` → tabela URG e Top Escolas.
  - `.st-table-with-total` → tabela comparativa por ANO.
- Containers de toolbar (CSS escopado): `nutricao_urg_actions_toolbar`, `nutricao_ano_actions_toolbar`, `escola_table_selection_nutricao_actions_toolbar`, `nutricao_aluno_actions_toolbar`, `nutricao_simple_actions_toolbar`.
- Classes de card/KPI: `.home-metric-card`, `.metric-card-static`, `.home-metric-label`, `.home-metric-value`, `div[class*="st-key-btn_kpi_"] button`.

---

## 8. Padrão Técnico de Tabelas
- Sempre `render_saedas_aggrid(...)`; nunca `st.dataframe(...)`.
- Sempre `split_aggrid_footer(...)` quando houver linha TOTAL.
- AgGrid URG: chave dinâmica `urg_table_nutricao_{years}_{nuts}_{urgs}`.
- AgGrid Detalhamento Aluno: `render_aluno_detalhamento_aggrid(..., key="aluno_table_nutricao", csv_name="detalhes_alunos_nutricao.csv", toolbar_key="nutricao_aluno_actions_toolbar")`.
- Exportação CSV: separador `;`, codificação `utf-8-sig`.
- TOTAL: última posição, não selecionável (`TOTAL` filtrado em `new_selected_urgs`).

---

## 9. Detalhamento por Aluno
- Pipeline: `filter_by_sidebar_selections` → filtro `Ano in selected_years_comp` → filtro `Nutricao` → filtros locais (Aluno, Série, Turma) → `prepare_nutricao_aluno_table`.
- Pivot anual de `Peso (kg)`, `Altura (m)`, `IMC`, `Idade`, `Nutricao` (`Idade = Ano - year(DataNascimento)`).
- Formatação BR (vírgula decimal) para Peso/Altura/IMC; inteiro para Idade.
- Coluna `Nutricao` em UPPERCASE para itens selecionados; demais capitalizados.
- Coluna `Menu` → renomeada para `Perfil`, com URL `?menu=Aluno&aluno={nome}[&nasc=YYYY-MM-DD]`.
- Render via `render_profile_click_bridge()` (link `Ver Perfil`).

---

## 10. Checklist de Recuperação
1. Validar carga dos 4 datasets (principal, aluno, ano, home) com Redis e fallback de disco.
2. Validar seletor de ano `home_year_buttons` no padrão da Home.
3. Validar pipeline `df_base_sem_escola → df_base_final → df_master_no_nut → df_filt`.
4. Validar sync URG tabela ↔ sidebar (seleção, remoção, `pending_sidebar_urg_filter`).
5. Validar sync Escola tabela ↔ sidebar (seleção, remoção, `pending_sidebar_escola_filter`).
6. Validar proteção anti-loop com `last_interaction_source` e `_prev_urg_table_key_nutricao`.
7. Validar toggle dos cards Situação Nutricional + persistência (`persistent_nutricao_situacao`).
8. Validar ordem da tabela ANO igual aos KPIs gerais com TOTAL ao final.
9. Validar imunidade dos cards demográficos ao filtro de Situação.
10. Validar toolbars (`Copiar` + `CSV`) em todas as tabelas.
11. Validar wrappers `.selection-master-table` e `.st-table-with-total`.
12. Validar detalhamento por aluno: filtros cruzados, pivot anual, link de Perfil.

---

## 11. Comandos Úteis
- `streamlit run app/main.py`
- `python -m py_compile app/app_pages/nutricao.py app/utils/page_helpers.py app/utils/state_manager.py app/components/sidebar_filters.py`
- `rg -n "render_saedas_aggrid\\(|render_table_toolbar\\(|split_aggrid_footer\\(|nutricao_situacao_multiselect|persistent_nutricao_situacao" app/app_pages/nutricao.py app/utils/page_helpers.py`
- `rg -n "st\\.dataframe\\(|last_interaction_source|pending_sidebar_|selection-master-table|st-table-with-total|_prev_urg_table_key_nutricao" app/app_pages/nutricao.py app/utils/page_helpers.py app/utils/state_manager.py`
- `rg -n "saedas:nutricao:dataset" app/app_pages/nutricao.py app/utils/redis_client.py`
