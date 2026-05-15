# Padrões Técnicos e de Design: Página Home (Início)

Este documento define os padrões de interface (UI), experiência do usuário (UX) e lógica de dados aplicados na **Página Home**, que servem como referência obrigatória para todas as outras páginas do sistema SAEDAS.

---

## 1. Arquitetura de KPIs (Metric Cards Interativos)

A Home introduziu o padrão de **Cards de Indicadores Clicáveis**, transformando métricas estáticas em atalhos de navegação.

### 1.1 Design e Estética (Bordas Iluminadas)
- **Superfície:** Fundo sólido Profundo (`#0f172a`) para destacar os contornos.
- **Bordas Gradientes:**
    - **Silver (Prata):** Para métricas totais estáticas.
    - **Blue (Azul) + Glow:** Para indicadores interativos que levam a outros módulos.
- **Ícones:** Inclusão do símbolo `↗` ao lado do rótulo para indicar navegabilidade.
- **Interatividade (Hover):**
    - Elevação visual: `transform: translateY(-3px)`.
    - Feedback de brilho: Intensificação do `box-shadow` azulado.
    - Transição: `0.25s cubic-bezier(0.4, 0, 0.2, 1)` para suavidade premium.
- **Reset de Link:** Uso de seletores de alta especificidade para remover decorações de texto e bordas padrão do Streamlit.

### 1.2 Implementação (Python/CSS)
```python
# O link deve envolver todo o container do card
st.markdown(f"""
    <a href="/?menu={link_target}" class="home-metric-link-wrapper">
        <div class="home-metric-card home-metric-plain metric-card-link">
            <div class="home-metric-label">{label}</div>
            <div class="home-metric-value">{value}</div>
        </div>
    </a>
""", unsafe_allow_html=True)
```

---

## 2. Sincronismo de Filtros (Two-Way Binding)

A Home é o hub central de filtragem temporal e regional.

### 2.1 Seletor de Ano Mestre
Componente central de filtragem temporal. Para especificações técnicas e visuais, consulte o padrão de [Seletor Temporal Mestre](specs/shared_components_spec.md#2-seletor-temporal-mestre-botoes-de-ano).

### 2.2 Sincronismo Sidebar/Página
- **Fonte de Verdade:** `st.session_state["global_years"]` e `st.session_state["global_urgs"]`.
- **Callback:** Uso obrigatório de callbacks no `state_manager.py` para evitar loops de re-renderização.

---

## 3. Visualização de Dados (Grid de Comparação)

O padrão de visualização evoluiu de gráficos únicos para **Gráficos de Comparação em Grid**.

### 3.1 Layout de Colunas
- **Regra:** Máximo de 3 colunas por linha para manter a legibilidade.
- **Implementação:** Iteração sobre os anos selecionados usando `st.columns(3)`.

### 3.2 Consistência de Cores
- **Mapeamento Fixo:** Uso obrigatório de `color_discrete_map` no Plotly Express.
- **Objetivo:** Garantir que a mesma categoria (ex: "Médico") mantenha a mesma cor (ex: Vermelho) em todos os gráficos de todos os anos, permitindo comparação visual rápida.

---

## 4. Hierarquia Visual e Estrutura de Página

A estrutura de layout da Home segue uma pirâmide de detalhamento:
1.  **Camada 1 (KPI Cards):** Visão executiva imediata com links de navegação.
2.  **Camada 2 (Performance por ANO):** Visão de tendência histórica e cobertura (Tabela Geral).
3.  **Camada 3 (Performance por URG):** Visão regional e hub de cross-filtering (AgGrid Mestra).
4.  **Camada 4 (Detalhamento por Escola):** Visão tática final.

### 4.1 Cabeçalho Dinâmico (filtro_titulo)
- **Padrão:** Cada seção de indicadores deve ser precedida por um título `###` que descreve dinamicamente os filtros aplicados (ex: `Indicadores Gerais (Anos: 2026 / URGs: Todos)`).
- **Design:** Texto em branco brilhante (`#f1f5f9`), negrito massivo (`800`) e espaçamento entre letras reduzido para uma estética moderna e impactante.

### 4.2 Separadores Visuais
- Use `st.markdown("---")` precedido de um pequeno espaço (`st.markdown(" ")`) entre as camadas de resumo (Cards) e as tabelas analíticas para reduzir a carga cognitiva.

---

## 5. Padrão Analítico: Taxa de Cobertura

As tabelas de performance por ano não devem usar o somatório total da coluna como base para percentuais.
- **Base de Cálculo:** O denominador deve ser obrigatoriamente o indicador **"TOTAL DE ALUNOS (ESCOLA)"** do respectivo ano.
- **Rótulo:** O cabeçalho da coluna deve ser renomeado de "% Total" para **"% Cobertura"**.
- **Objetivo:** Transformar dados brutos em indicadores de impacto e alcance social.

---

## 6. Sincronização Semântica (Rótulos e Ordem)

Para garantir que o usuário não se perca ao transitar entre os indicadores rápidos (Cards) e a tabela analítica:
- **Ordem:** As linhas da tabela devem seguir rigorosamente a mesma ordem visual dos cards de métricas.
- **Nomenclatura:** Os nomes das métricas (rótulos) devem ser idênticos em ambos os componentes (ex: se o card diz "ATEND. MÉDICO", a tabela não deve dizer "Consulta Médica").
- **Agregados:** Se um card apresenta uma métrica calculada (ex: soma de especialidades), a tabela deve conter uma linha equivalente com o mesmo nome para facilitar o "bate" de valores.

## 7. Tabelas AgGrid e Toolbars

### 7.1 Formatação de Dados
- **Índices:** Linhas numeradas começando em 1 (via `JsCode` no AgGrid).
- **Alinhamento:** Colunas de texto à esquerda, colunas numéricas centralizadas.
- **Zebra Striping:** Habilitado por padrão para facilitar a leitura de linhas longas.

### 7.2 Toolbar de Ações
- **Posicionamento:** Sempre no topo direito da tabela.
- **Agrupamento:** Botões (`Copiar`, `CSV`) colados uns aos outros, sem espaços internos.
- **Estilo:** Borda `#334155`, fundo transparente, altura fixa de `34px`.

---

## 8. Regras de Estilo CSS (Global vs Local)

### 8.1 CSS Injetado
A página Home utiliza injeção direta de `<style>` para componentes que exigem alta especificidade ou que são exclusivos daquela view.
- **Keys Estáveis:** Sempre use `st.container(key="...")` para ancorar o CSS em seletores `.st-key-...`.

### 8.2 Reset de Componentes Streamlit
- Remoção de margens excessivas em containers verticais/horizontais para criar uma interface mais densa e profissional ("tighter UI").

---

## 9. Checklist de Aplicação de Padrão (Nova Tela)

Ao criar uma nova tela baseada na Home, verifique:
- [ ] Os KPIs são interativos e usam o reset de link?
- [ ] Os filtros de ano/URG estão sincronizados com a Sidebar?
- [ ] A tabela de performance segue a **Taxa de Cobertura** (Denominador: Total Alunos)?
- [ ] Os rótulos da tabela são idênticos aos dos cards superiores?
- [ ] Tabelas numéricas começam o índice em 1?
- [ ] Gráficos múltiplos usam mapeamento de cores fixo e layout de grid?
- [ ] Toolbars de AgGrid estão no topo direito e agrupadas?

---
*Documentação atualizada em: 04/05/2026 (Revisão: Taxa de Cobertura e Hierarquia de Componentes)*
