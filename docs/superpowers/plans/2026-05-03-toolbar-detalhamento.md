# Toolbar Unificada — Tabela de Detalhamento

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir os controles dispersos da tabela de detalhamento (botão Colunas à esquerda + Copiar/CSV abaixo) por um grupo unificado de três botões posicionado à direita acima da tabela.

**Architecture:** Modificação única em `home.py` — troca o CSS `.home-toolbar-row` pelo novo `.saedas-toolbar-right`, substitui o `toolbar_container` pelo novo grupo e remove os botões abaixo da tabela. Todos os dados (`df_display_for_copy`, `csv_visible_data`) já estão computados antes do ponto de inserção.

**Tech Stack:** Streamlit, st-aggrid, Python, CSS injection via `st.markdown(unsafe_allow_html=True)`

---

## Mapa de Arquivos

| Arquivo | Operação |
|---------|----------|
| `app/app_pages/home.py` | Modificar — único arquivo afetado |

---

## Task 1: Substituir CSS `.home-toolbar-row` pelo novo `.saedas-toolbar-right`

**Files:**
- Modify: `app/app_pages/home.py:2303-2334`

- [ ] **Step 1: Localizar o bloco CSS antigo**

  Abrir `app/app_pages/home.py`. Confirmar que as linhas 2303–2334 contêm o bloco:
  ```python
  st.markdown(
      """
  <style>
      .home-toolbar-row { ... }
      .home-toolbar-row div[data-testid="stHorizontalBlock"] { ... }
      .home-toolbar-row div[data-testid="column"] { ... }
      .home-toolbar-status { ... }
  </style>
  """,
      unsafe_allow_html=True,
  )
  ```

- [ ] **Step 2: Substituir o bloco CSS pelo novo**

  Substituir todo o bloco `st.markdown(...)` de linhas 2303–2334 por:

  ```python
  st.markdown(
      """
  <style>
      .saedas-toolbar-right {
          display: flex;
          justify-content: flex-end;
          margin-bottom: 4px;
      }
      .saedas-toolbar-right div[data-testid="stHorizontalBlock"] {
          gap: 0 !important;
          justify-content: flex-end !important;
          align-items: center !important;
          flex-wrap: nowrap !important;
          width: auto !important;
      }
      .saedas-toolbar-right div[data-testid="column"] {
          flex: 0 0 auto !important;
          padding: 0 !important;
          min-width: unset !important;
          width: auto !important;
      }
      .saedas-toolbar-right div[data-testid="column"] button {
          background: transparent !important;
          border: 1px solid #334155 !important;
          border-radius: 0 !important;
          border-right: none !important;
          color: #94a3b8 !important;
          height: 34px !important;
          padding: 0 12px !important;
          font-size: 0.78rem !important;
          min-height: unset !important;
          transition: background 0.15s, color 0.15s !important;
          white-space: nowrap !important;
      }
      .saedas-toolbar-right div[data-testid="column"]:first-of-type button {
          border-radius: 6px 0 0 6px !important;
      }
      .saedas-toolbar-right div[data-testid="column"]:last-of-type button {
          border-radius: 0 6px 6px 0 !important;
          border-right: 1px solid #334155 !important;
      }
      .saedas-toolbar-right div[data-testid="column"] button:hover {
          background: #1e293b !important;
          color: #e2e8f0 !important;
      }
  </style>
  """,
      unsafe_allow_html=True,
  )
  ```

- [ ] **Step 3: Verificar visualmente no Streamlit**

  Rodar o app (`streamlit run app/app.py`). Navegar até a tabela de detalhamento. Confirmar que não há erros de CSS e que a área ainda carrega corretamente (a toolbar antiga ainda existe neste ponto — será trocada na Task 2).

- [ ] **Step 4: Commit**

  ```bash
  git add app/app_pages/home.py
  git commit -m "style: replace home-toolbar-row CSS with saedas-toolbar-right"
  ```

---

## Task 2: Substituir toolbar container pelo grupo unificado à direita

**Files:**
- Modify: `app/app_pages/home.py:2461-2494`

- [ ] **Step 1: Localizar o bloco do toolbar container antigo (linhas 2461–2494)**

  Confirmar que o bloco a ser substituído é exatamente:

  ```python
  toolbar_container = st.container()

  with toolbar_container:
      st.markdown('<div class="home-toolbar-row">', unsafe_allow_html=True)

      column_col, export_col = st.columns([1, 1], gap="small")

      with column_col:
          column_toggle_clicked = st.button(
              "Colunas",
              key="home_toolbar_column_toggle",
              help="Mostrar/ocultar colunas da tabela",
          )

          if column_toggle_clicked:
              st.session_state["home_show_column_selector"] = (
                  not st.session_state["home_show_column_selector"]
              )

      st.markdown("</div>", unsafe_allow_html=True)

  if st.session_state["home_show_column_selector"]:
      selected_hidden_columns = st.multiselect(
          "Colunas a ocultar",
          options=available_columns,
          default=selected_hidden_columns,
          key="home_hidden_columns_selector",
          help="Selecione as colunas que deseja ocultar na tabela",
      )

      st.session_state["home_hidden_columns"] = selected_hidden_columns

  else:
      st.session_state["home_hidden_columns"] = selected_hidden_columns
  ```

- [ ] **Step 2: Substituir pelo novo grupo unificado**

  Substituir o bloco inteiro por:

  ```python
  _colunas_ativo = st.session_state["home_show_column_selector"]

  _active_css = (
      """
  <style>
  .saedas-toolbar-right div[data-testid="column"]:first-of-type button {
      background: #1e3a5f !important;
      color: #60a5fa !important;
  }
  </style>
  """
      if _colunas_ativo
      else ""
  )
  st.markdown(_active_css, unsafe_allow_html=True)

  st.markdown('<div class="saedas-toolbar-right">', unsafe_allow_html=True)
  _col_colunas, _col_copiar, _col_csv = st.columns([1, 1, 1], gap="small")

  with _col_colunas:
      if st.button(
          "⚙️ Colunas",
          key="home_toolbar_column_toggle",
          help="Mostrar/ocultar colunas da tabela",
      ):
          st.session_state["home_show_column_selector"] = not _colunas_ativo

  with _col_copiar:
      if st.button(
          "📋 Copiar",
          key="home_toolbar_copy",
          help="Copiar tabela para área de transferência (Excel)",
      ):
          try:
              df_display_for_copy.to_clipboard(index=False, excel=True)
              st.toast("Tabela copiada. Cole no Excel com Ctrl+V.")
          except Exception as _copy_exc:
              st.toast(f"Não foi possível copiar: {_copy_exc}", icon="❌")

  with _col_csv:
      st.download_button(
          label="⬇️ CSV",
          data=csv_visible_data,
          file_name="detalhamento_home.csv",
          mime="text/csv",
          key="download_csv_home_toolbar",
          help="Exportar tabela como CSV",
      )

  st.markdown("</div>", unsafe_allow_html=True)

  if st.session_state["home_show_column_selector"]:
      selected_hidden_columns = st.multiselect(
          "Colunas a ocultar",
          options=available_columns,
          default=selected_hidden_columns,
          key="home_hidden_columns_selector",
          help="Selecione as colunas que deseja ocultar na tabela",
      )
      st.session_state["home_hidden_columns"] = selected_hidden_columns
  else:
      st.session_state["home_hidden_columns"] = selected_hidden_columns
  ```

- [ ] **Step 3: Verificar visualmente — toolbar nova**

  Recarregar o app. Confirmar:
  - Grupo de três botões aparece à **direita** acima da tabela
  - Botões têm bordas unificadas (sem gap entre eles)
  - Clicar em **⚙️ Colunas** abre o multiselect e o botão fica azul
  - Clicar novamente fecha o multiselect e o botão volta ao normal
  - **📋 Copiar** copia a tabela e exibe o toast de confirmação
  - **⬇️ CSV** inicia o download do arquivo `detalhamento_home.csv`

- [ ] **Step 4: Commit**

  ```bash
  git add app/app_pages/home.py
  git commit -m "feat: add unified right-aligned toolbar above detalhamento table"
  ```

---

## Task 3: Remover botões abaixo da tabela

**Files:**
- Modify: `app/app_pages/home.py:2517-2542` (números de linha após Task 2 serão ligeiramente diferentes — localizar pelo conteúdo)

- [ ] **Step 1: Localizar o bloco a remover**

  Após a chamada `AgGrid(...)`, confirmar que existem estas linhas:

  ```python
  copy_feedback_placeholder = st.empty()
  copy_row = st.columns([1.4, 1.2, 4.4])
  with copy_row[0]:
      if st.button(
          "Copiar tabela (Detalhamento)",
          key="copy_home_detail_table_aggrid",
          help="Copiar tabela (Detalhamento dos Dados) para a área de transferência",
      ):
          try:
              df_display_for_copy.to_clipboard(index=False, excel=True)
              copy_feedback_placeholder.success(
                  "Tabela copiada. Cole no Excel usando Ctrl+V."
              )
          except Exception as clipboard_exc:
              copy_feedback_placeholder.error(
                  f"Não foi possível copiar automaticamente: {clipboard_exc}"
              )
  with copy_row[1]:
      st.download_button(
          label="Exportar CSV",
          data=csv_visible_data,
          file_name="detalhamento_home.csv",
          mime="text/csv",
          key="download_csv_home_visible_aggrid_bottom",
          help="Exportar tabela (CSV)",
      )
  ```

- [ ] **Step 2: Remover o bloco inteiro**

  Deletar todas as linhas acima (de `copy_feedback_placeholder = st.empty()` até o fim do bloco `with copy_row[1]:`), inclusive.

- [ ] **Step 3: Verificar visualmente — remoção confirmada**

  Recarregar o app. Confirmar:
  - Abaixo da tabela AgGrid **não há mais** os botões "Copiar tabela (Detalhamento)" e "Exportar CSV"
  - A seção seguinte (sidebar export ou próximo conteúdo) aparece diretamente após a tabela
  - Nenhum erro no console do Streamlit

- [ ] **Step 4: Commit**

  ```bash
  git add app/app_pages/home.py
  git commit -m "refactor: remove redundant copy/export buttons below detalhamento table"
  ```

---

## Verificação Final

- [ ] Clicar em **⚙️ Colunas**: multiselect abre, botão fica azul; clicar novamente fecha
- [ ] Ocultar uma coluna via multiselect: coluna some da tabela imediatamente
- [ ] Clicar em **📋 Copiar**: toast "Tabela copiada..." aparece; colar no Excel funciona
- [ ] Clicar em **⬇️ CSV**: arquivo `detalhamento_home.csv` é baixado com separador `;`
- [ ] Abaixo da tabela: nenhum botão residual
- [ ] Dark mode: grupo de botões tem bordas `#334155`, hover `#1e293b`
- [ ] `st.session_state["home_show_column_selector"]` e `home_hidden_columns` persistem entre reruns normalmente
