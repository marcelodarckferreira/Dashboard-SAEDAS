# Plano de Desenvolvimento SAEDAS

## Como usar (controle)
- Fonte única de tarefas: `planejamento/tasks.yaml` (id, status `todo|doing|done`, prioridade, owner, descrição).
- Relatórios gerados: `planejamento/status.md` (visão por status) e `planejamento/CHANGELOG.md` (concluídas).
- Atualização: após editar `tasks.yaml`, rodar `python planejamento/scripts/generate_status.py` para regenerar os relatórios.

## Objetivos
- Garantir base solida (encoding, dados, layout) antes de evoluir funcionalidades.
- Centralizar reutilizacao (load de CSV, filtros, estilos, graficos) para manutencao simples.
- Preparar trilha de IA focada em previsao, alertas e automacao de qualidade de dados.
- Documentar e testar fluxos criticos para reduzir regressao.

## Etapas (macro)
1) Fundacao tecnica: normalizar encoding UTF-8 em codigo/CSV, corrigir textos quebrados, alinhar requisitos de dependencias, README.
2) Reuso e arquitetura: utilitario de leitura/validacao de dados, helpers de filtro/titulo, tema unico de CSS/Plotly, componentes compartilhados (cabecalho, cards, secoes).
3) UX/Conteudo: padronizar labels/botoes, legendas claras, acessibilidade basica, copy em portugues sem caracteres corrompidos.
4) Observabilidade/Qualidade: logs leves, testes unitarios de utilitarios, smoke de paginas, lint/format.
5) Performance/Dados: cache com st.cache_data, tipagem de colunas, paginacao/limites em AgGrid, opcional migrar para parquet/DB.
6) Trilhas de IA: casos de uso, dados, modelos, etica/governanca; POC iterativa.

## Backlog detalhado
- Encoding e dados
  - Revisar/salvar fontes e CSVs em UTF-8; remover caracteres corrompidos nos textos e labels.
  - Criar util load_csv(dataset_name, expected_cols=None): tentativas de encoding, schema check, tipos (datas/numeros), log de erros.
  - Validar schemas por pagina (home, consulta, exame, vacinacao) com mensagens amigaveis.
  - Ingerir e validar novos CSVs: DashboardConsultaAluno, DashboardConsultaAno, DashboardExameAluno, DashboardExameAno, DashboardHomeEscolaAno, DashboardHomeURGAno, DashboardNutricao, DashboardNutricaoAluno, DashboardNutricaoAno, DashboardVacinacaoAluno, DashboardVacinacaoAno.
- Reuso de UI/tema
  - Extrair CSS global para assets/styles.css; aplicar em todas as paginas.
  - Helper unico para titulo de filtros e strings exibidas (anos/URGs/escolas/...).
  - Componente de cabecalho e toolbar (botoes: mostrar/ocultar colunas, exportar, copiar) com labels consistentes.
  - Configurar tema Plotly padrao (separadores, fontes, paleta) e wrappers para graficos comuns.
  - Padronizar AgGrid onde for necessário (mesmo padrão da home: toolbar, altura/rolagem, export/cópia).
- Organizacao de codigos
  - Mapear constantes (nomes de colunas, labels, icones do menu) em um modulo de config.
  - Remover duplicacao de CSS inline e helpers repetidos nas paginas; usar componentes comuns.
  - Estruturar scripts de export (CSV) reutilizando utilitario e nomenclatura padronizada.
- Observabilidade e qualidade
  - Adicionar logs: inicio/fim de carga de CSV, linhas apos filtros, erros de schema/encoding.
  - Adicionar testes: util de CSV (sucesso/falha), formata de filtros; smoke de Streamlit (streamlit.testing) por pagina.
  - Configurar lint (ruff/flake8) e format (black); CI leve opcional (pre-commit ou pipeline simples).
- Performance e dados
  - Habilitar st.cache_data no load_csv com chave pelo caminho/mtime.
  - Converter colunas de data/numero na carga; evitar object desnecessario.
  - Ajustar AgGrid: limite default de linhas, opcao "Todas" com aviso, ocultar auto colunas tecnicas.
  - Avaliar migracao de CSV -> parquet ou banco leve se volume crescer.
- Copy/UX
  - Corrigir textos com acentos e legendas (metricas, botoes, alertas); revisar icones do menu.
  - Adicionar legenda padrao para colunas percentuais e campos tecnicos.
  - Validar responsividade (colunas, charts) e contraste de cores.
  - Agrupar menu e filtros por contexto de dados; remover filtros redundantes (ex.: URG duplicado).
- IA: melhor forma de desenvolvimento
  - Casos de uso alvo: (1) previsao de demanda de exames/vacinacao por URG/ano, (2) deteccao de anomalias em series (quedas/subidas abruptas), (3) sugestao de alocacao de equipes/profissionais, (4) alerta de inconsistencias de dados.
  - Dados: avaliar historico disponivel, qualidade e granularidade; definir dicionario de dados e variaveis derivadas; tratar faltantes/outliers.
  - Modelagem: comecar com baseline classico (ARIMA/Prophet/regressao) antes de modelos complexos; pipeline reproducivel (notebooks + scripts); metricas (MAE/MAPE/Precision-Recall para alertas).
  - Ciclo seguro: separar ambiente de experimentacao; controlar versao de dados/modelos; registrar experimentos (MLflow leve ou planilha versionada); checklist de etica/privacidade (anonimizar/aggregar dados sensiveis).
  - Integracao: expor previsoes/alertas via CSV/JSON consumido pelo Streamlit; destacar que recomendacoes sao apoio e nao decisao final; incluir flag de confianca/intervalo.
  - POC inicial: previsao mensal de demanda por URG + dashboard com bandas de confianca; depois anomalias e alocacao.
- Documentacao/Entrega
  - Atualizar README: como rodar, dependencias, formato dos CSVs esperados, comandos (streamlit run app/app.py).
  - Registrar decisoes de arquitetura/IA em docs/ (ex.: ADRs curtas ou README de arquitetura).

## Proximos passos sugeridos (ordem)
1) Ingerir/validar os novos CSVs (Consulta/Exame/Home/Nutricao/Vacinacao por aluno/ano) usando `load_csv` + schemas.
2) Remover filtros redundantes e agrupar menu/filtros por contexto (ex.: URG duplicado em consulta).
3) Padronizar AgGrid onde for necessário (padrão do home: toolbar, altura/rolagem, export/cópia).
4) Adicionar logs/testes básicos e habilitar lint/format.
5) Iniciar POC de IA (previsão de demanda e anomalias) com pipeline rastreável.
