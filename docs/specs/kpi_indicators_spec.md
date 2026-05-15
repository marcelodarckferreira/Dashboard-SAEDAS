# Especificação Técnica — Engenharia de Indicadores (KPIs)

Este documento define os padrões de cálculo, formatação e comportamento dos indicadores gerais (KPI Cards) do SAEDAS, garantindo integridade das regras de negócio em todo o sistema.

---

## 1. Anatomia do Indicador
Todo KPI no sistema deve seguir estas regras visuais e de processamento:
- **Rótulo (Label):** Sempre em CAIXA ALTA (Upper Case).
- **Valor (Value):** Formatado com separador de milhar por ponto (ex: `1.234`).
- **Grid:** Layout fixo de 5 colunas por linha (conforme `render_metric_cards`).

---

## 2. Categorias de Indicadores e Fontes de Dados

### 2.1 KPIs Demográficos (Estáticos/Âncoras)
Devem ser os primeiros cards de qualquer dashboard (exceto Início).
- **TOTAL DE ALUNOS:** Soma de `QtdAlunoEscola` do dataset `DashboardHome.csv`.
- **ALUNOS ATENDIDOS:** Soma de `QtdAluno` do dataset `DashboardHome.csv`.
- **Regra de Ouro:** Estes indicadores **ignoram filtros de categoria específica** (ex: filtro de vacina) para servir de base demográfica constante.

### 2.2 KPIs de Domínio (Interativos/Toggle)
Representam a volumetria específica de cada módulo.
- **Cálculo:** Agrupamento (`groupby`) por categoria (Exame, Vacina, Atendimento) e soma da coluna `Quantidade`.
- **Interatividade:** Devem usar `is_toggle=True`. O clique deve disparar a sincronização com o multiselect da sidebar.
- **Visual:** O card "aceso" (Primary) indica que aquela categoria está filtrando o restante da tela.

### 2.3 KPIs Compostos (Relacionais)
Usados para mostrar eficiência ou cobertura.
- **Formato:** `{Valor A} / {Valor B}`.
- **Exemplo (Vacinação):** `Alunos Únicos Vacinados / Total de Doses Aplicadas`.
- **Regra de Negócio:** Se o valor for uma string composta, o `render_metric_cards` detecta e evita a formatação numérica automática para não quebrar a string.

---

## 3. Padrão de Sincronização de Estado
Para garantir que o KPI card funcione como um filtro:
1.  **Session State:** O estado da seleção deve ser armazenado em uma chave previsível (ex: `nutricao_situacao_multiselect`).
2.  **Callback:** A função `toggle_multiselect_value` em `page_helpers.py` deve ser usada para adicionar/remover o item da seleção ao clicar.
3.  **Rerun:** O clique em um card deve forçar um `st.rerun()` para que todos os gráficos e tabelas reajam instantaneamente ao novo filtro.

---

## 4. Checklist de Correção de Regras
Ao identificar uma divergência de números entre telas, verifique:
- [ ] O filtro de `Ano` está sendo aplicado à base antes da soma do KPI?
- [ ] O KPI Demográfico está filtrado por `Escola` e `URG` corretamente (conforme seleções da sidebar)?
- [ ] O KPI de Domínio está excluindo valores zero ou nulos do agrupamento?
- [ ] A ordenação dos cards segue a volumetria decrescente (mais importantes primeiro)?

---

## 5. Implementação Técnica (`render_metric_cards`)
O componente central em `app/utils/styles.py` abstrai a complexidade do CSS (WOW factor), mas a lógica de negócio **reside no módulo da página**.
- **Input:** Lista de dicionários `[{'label': 'NOME', 'value': 123, 'link': '...'}]`.
- **Responsive:** O componente gerencia automaticamente a quebra de linhas para manter o grid de 5 colunas.
