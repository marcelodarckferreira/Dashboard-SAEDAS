# SAEDAS — Sistema de Análise Estatística e Dados de Assistência à Saúde

## Visão Geral

O **SAEDAS** é um dashboard analítico para monitoramento de indicadores de saúde escolar e assistência social. A plataforma centraliza dados de encaminhamentos médicos, exames, vacinação, nutrição e perfis individuais de alunos, permitindo análise por Unidade Regional de Governo (URG), escola e período.

Construído com **Streamlit**, o sistema consome dados extraídos de um banco SQL Server (via stored procedures) e exportados como CSVs. A interface oferece filtros interativos, gráficos dinâmicos e deep linking para perfis de alunos.

---

## Objetivo

Fornecer aos gestores e profissionais de saúde um painel tático-operacional com:

- Visão consolidada de KPIs (alunos atendidos, profissionais, encaminhamentos, exames, vacinas)
- Drill-down por URG, escola, tipo de unidade, ano e aluno
- Acompanhamento longitudinal (2022–2025) com comparação por período
- Acesso direto a perfis individuais via deep link

---

## Stack Tecnológica

| Camada           | Tecnologia                                   |
|------------------|----------------------------------------------|
| **Aplicação**    | Python 3.12 · Streamlit 1.49                 |
| **Dados**        | Pandas 2.3 · NumPy 2.3 · PyArrow 21         |
| **Visualização** | Plotly 6.3 · Altair 5.5                      |
| **Estatística**  | SciPy 1.16 · Statsmodels 0.14               |
| **UI**           | streamlit-option-menu · streamlit-aggrid     |
| **Container**    | Docker (python:3.12.6-slim)                  |
| **Banco de dados** | SQL Server (externo, via `bcp`/`sqlcmd`)   |

---

## Estrutura do Projeto

```text
app/
├── app.py                    # Entrypoint principal (Streamlit)
├── app_pages/                # Páginas do dashboard
│   ├── home.py               #   Dashboard Geral (KPIs)
│   ├── consulta.py           #   Encaminhamentos médicos
│   ├── exame.py              #   Exames
│   ├── vacinacao.py          #   Vacinação
│   ├── nutricao.py           #   Nutrição
│   └── aluno.py              #   Perfil individual do aluno
├── components/               # Componentes reutilizáveis da UI
│   ├── sidebar_filters.py    #   Filtros dinâmicos (Ano, URG, Escola, Tipo)
│   └── footer_personal.py    #   Rodapé
├── utils/                    # Utilitários
│   ├── data_loader.py        #   Leitura de CSV com fallback de encoding
│   ├── schemas.py            #   Schemas esperados por página
│   ├── page_helpers.py       #   Helpers compartilhados entre páginas
│   └── styles.py             #   Injeção de CSS global
├── data/                     # CSVs de dados (não versionados — .gitignore)
├── assets/                   # Arquivos estáticos (CSS, logo, favicon)
├── .streamlit/config.toml    # Configuração do Streamlit
├── exportar_dados_csv.sh     # Script de extração de dados via bcp
└── fechamento_saedas.sh      # Script de fechamento de período via sqlcmd
Dockerfile                    # Imagem Docker (python:3.12.6-slim)
docker-compose.yml            # Orquestração local
requirements.txt              # Dependências Python
```

---

## Pré-requisitos

| Requisito              | Versão mínima     |
|------------------------|--------------------|
| Python                 | 3.12+              |
| Docker Engine          | 20.10+             |
| Docker Compose         | 2.0+               |
| Git                    | qualquer recente   |

> **Nota:** No ambiente de produção (Linux), os scripts `.sh` requerem `mssql-tools` (`bcp` e `sqlcmd`) para comunicação com o SQL Server.

---

## Instalação

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd SAEDAS
```

### 2. Ambiente local (desenvolvimento)

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Via Docker (recomendado para produção)

```bash
docker compose up --build -d
```

---

## Configuração

### Streamlit

O arquivo `app/.streamlit/config.toml` define a configuração do servidor:

```toml
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false
```

### Dados

Os CSVs da pasta `app/data/` são gerados externamente pelo script `exportar_dados_csv.sh`, que executa stored procedures no SQL Server e exporta os resultados via `bcp`.

> ⚠️ **Os arquivos CSV não são versionados** (`.gitignore`). No primeiro setup, é necessário executar o script de extração ou obter os CSVs de outra fonte.

### Variáveis de Ambiente

Atualmente, as credenciais de banco estão hardcoded nos scripts `.sh`. **Recomenda-se** migrá-las para variáveis de ambiente:

```bash
export SAEDAS_DB_USER="usuario"
export SAEDAS_DB_PASSWORD="senha"
export SAEDAS_DB_SERVER="host,porta"
export SAEDAS_DB_NAME="database"
```

---

## Uso

### Execução local (dev mode com hot-reload)

```bash
streamlit run app/app.py
```

Acesse: `http://localhost:8501`

### Execução via Docker

```bash
docker compose up --build -d
docker compose logs -f streamlit    # Acompanhar logs
docker compose down                  # Parar
```

### Navegação

| Página               | Função                                                   |
|-----------------------|----------------------------------------------------------|
| **Início**            | Dashboard geral com KPIs e visão macro                  |
| **Encaminhamentos**   | Análise de encaminhamentos médicos por URG/escola       |
| **Exames**            | Controle de exames realizados                            |
| **Vacinação**         | Cobertura vacinal e acompanhamento por aluno            |
| **Nutrição**          | Monitoramento antropométrico (peso, altura, IMC)        |
| **Aluno**             | Perfil individual com histórico completo                |

### Deep Linking

O sistema suporta acesso direto a um perfil de aluno via parâmetros de URL:

```
http://localhost:8501/?menu=Aluno&aluno=NomeDoAluno&nasc=2010-01-01
```

Isso permite integração com sistemas externos para redirecionamento rápido.

---

## Comandos Disponíveis

| Comando                                | Descrição                             |
|----------------------------------------|---------------------------------------|
| `streamlit run app/app.py`             | Inicia o servidor de desenvolvimento  |
| `docker compose up --build -d`         | Build e execução em container         |
| `docker compose logs -f streamlit`     | Acompanhar logs em tempo real         |
| `docker compose down`                  | Parar os serviços                     |
| `bash app/exportar_dados_csv.sh`       | Extrair dados do SQL Server           |
| `bash app/fechamento_saedas.sh`        | Executar fechamento de período        |

---

## Build / Deploy

### Docker em produção

```bash
docker compose up --build -d
```

A imagem `dashboard-saedas:latest` é construída a partir do `Dockerfile` utilizando `python:3.12.6-slim`. O volume `./app:/app` no `docker-compose.yml` mapeia o código para hot-reload.

### Extração de dados (crontab)

No servidor de produção, os scripts de exportação são agendados via `crontab` para atualização periódica dos CSVs:

```bash
crontab -e
# Adicionar agenda, ex:
# 0 6 * * * /media/db/saedas/app/exportar_dados_csv.sh
# 0 5 * * 1 /media/db/saedas/app/fechamento_saedas.sh
```

---

## Testes

Atualmente não há suíte de testes automatizados. Para validação:

1. Execute `streamlit run app/app.py` e verifique as páginas afetadas
2. Valide deep links: `/?menu=Aluno&aluno=Nome&nasc=2010-01-01`
3. Para novas funcionalidades, crie testes em `tests/` usando `pytest` com convenção `test_*.py`

---

## Segurança e Notas Operacionais

### Dados Sensíveis

- Os CSVs contêm **dados de saúde e dados pessoais de alunos** (LGPD). Não devem ser versionados nem compartilhados externamente sem sanitização.
- Os arquivos `.env` e `.streamlit/secrets.toml` são ignorados pelo Git.

### Credenciais

- Os scripts `.sh` contêm credenciais hardcoded de banco de dados. **Migre para variáveis de ambiente** antes de publicar o repositório.

### Produção

- Utilize um **reverse proxy** (Nginx/Traefik) com terminação SSL/TLS à frente do container.
- Bloqueie acesso externo direto à porta `8501`; exponha apenas via HTTPS (443).
- O `Dockerfile` executa como root — considere adicionar um usuário não-root para produção.
- A flag `enableXsrfProtection = false` no `config.toml` deve ser reavaliada para ambientes expostos à internet.

---

## Contribuição

1. Crie uma branch a partir de `main`
2. Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`
3. Inclua resumo, módulos afetados e passos de validação manual no PR
4. Adicione screenshots para mudanças visuais

---

## Licença

Nenhuma licença definida. Projeto de uso interno.
