# Especificação Técnica — Página Perfil do Aluno

A página Perfil do Aluno é a visão 360° individual, consolidando o histórico de saúde e educação de um único estudante a partir de múltiplos datasets do sistema.

---

## 1. Visão Geral e Propósito
- **Objetivo:** Oferecer um prontuário unificado do aluno.
- **Integração:** Recebe tráfego de todas as tabelas de "Detalhamento por Aluno" do sistema via deep-links.

---

## 2. Fontes de Dados e Schemas
Datasets carregados em `carregar_dados_aluno()`:
- **Encaminhamentos:** `DashboardConsultaAluno.csv`
- **Exames:** `DashboardExameAluno.csv`
- **Vacinação:** `DashboardVacinacaoAluno.csv`
- **Nutrição:** `DashboardNutricaoAluno.csv`

---

## 3. Navegação e Seleção
### 3.1 Deep-Linking
- **Query Params:** Suporta `?menu=Aluno&aluno=Nome+Do+Aluno&nasc=YYYY-MM-DD`.
- **Pre-selection:** Lógica de `aluno_preselect` no session state para carregar o aluno correto vindo de outra página.

### 3.2 Busca e Filtro
- **Busca Sidebar:** Texto para filtrar nome ou data de nascimento na lista de alunos únicos.
- **Selectbox:** Seletor final do aluno a ser exibido.

---

## 4. Componentes de Interface

### 4.1 Cabeçalho e Indicadores
- **Card de Total:** Volume total de registros.
- **Cards de Especialidade:** Contagem específica de Psicólogo e Médico.
- **Cards de Categoria:** Totais por Encaminhamento, Exame, Vacinação e Nutrição.

### 4.2 Evolução Nutricional
- **Gráfico de Linha:** Evolução de Peso, Altura e IMC ao longo dos anos.
- **Tabela Comparativa:** Dados numéricos e classificações (Normal, Sobrepeso, etc.) por ano.

### 4.3 Histórico Detalhado (Seções)
Exibição de tabelas específicas para cada categoria:
- **Encaminhamentos:** Ano, URG, Escola, Evento, Série/Turma.
- **Exames:** Detalhamento dos procedimentos realizados.
- **Vacinação:** Controle de Doses e Lotes por ano.
- **Nutrição:** Histórico de medidas antropométricas.

---

## 5. Regras de Negócio e Tratamento de Dados
- **Unificação:** O sistema realiza o `concat` de todos os dataframes de aluno para gerar a lista mestre de busca.
- **Data de Nascimento:** Usada como chave secundária obrigatória junto ao Nome para diferenciar homônimos.
- **Formatação:** Converte datas e números para o padrão regional (PT-BR) na exibição.

---

## 6. Observações Técnicas
- **Performance:** Carregamento seletivo de dados baseado na busca para otimizar o uso de memória.
- **Estilo:** Segue o padrão de `metric_cards` e tabelas zebra do Design System SAEDAS.
