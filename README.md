# SAEDAS - Sistema de Análise Estatística e Dados de Assistência à Saúde

## Descrição
O **SAEDAS** é uma plataforma analítica desenvolvida para centralizar, processar e visualizar dados críticos de saúde escolar e assistência social. Atuando como um *Dashboard* tático-operacional, o sistema permite o monitoramento em tempo real de indicadores de encaminhamentos médicos, exames, vacinação, nutrição e perfis individuais de alunos.

Projetado para ambientes de alta disponibilidade, o core da aplicação utiliza **Streamlit** para renderização reativa de dados, permitindo que gestores e profissionais de saúde tomem decisões baseadas em evidências (Data-Driven Decision Making). A interface é otimizada para usabilidade, garantindo acesso rápido a métricas consolidadas e detalhamento granular por indivíduo.

## Arquitetura
A arquitetura do SAEDAS segue o padrão **Microservices-ready**, desacoplada e containerizada para garantir escalabilidade e portabilidade.

### Componentes Principais:
1.  **Frontend/Application Layer (Streamlit)**:
    *   **Engine**: Python 3.12+ com Streamlit Framework.
    *   **Responsabilidade**: Gerenciamento de estado de sessão (`st.session_state`), roteamento de páginas (`option_menu`) e renderização de componentes visuais.
    *   **Modularidade**: O código é segmentado em módulos funcionais (`app_pages/`) para manutenção isolada de cada domínio (Home, Consulta, Exame, Vacinação, Nutrição, Aluno).

2.  **Data Processing Layer (Pandas/NumPy)**:
    *   Camada interna responsável pela ingestão, limpeza e transformação de *dataframes*. Otimizada para operações vetoriais, minimizando o *overhead* de CPU durante o processamento de grandes volumes de dados.

3.  **Containerization (Docker)**:
    *   O ambiente é encapsulado em uma imagem **Docker** baseada no `python:3.12.6-slim`, garantindo um *footprint* reduzido e consistência entre ambientes de desenvolvimento e produção.

4.  **Entry Points**:
    *   `app.py`: Gateway principal da aplicação. Gerencia o ciclo de vida da aplicação, injeção de dependências e roteamento global.
    *   `Dockerfile`: Definição imutável da infraestrutura de execução.
    *   `docker-compose.yml`: Orquestração simplificada para *deploy* local e *hot-reloading*.

## Instalação
Siga os passos abaixo para preparar o ambiente de execução.

### Pré-requisitos
*   **Docker Engine** (v20.10+)
*   **Docker Compose** (v2.0+)
*   **Git**

### Procedimento de Setup
1.  Clone o repositório para o seu ambiente local:
    ```bash
    git clone https://usuario@repositorio.com/saedas.git
    cd SAEDAS
    ```

2.  (Opcional) Se optar por execução sem Docker (Virtual Environment):
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    
    pip install -r requirements.txt
    ```

3.  Build e execução via Docker (Recomendado):
    ```bash
    docker-compose up --build -d
    ```

O sistema estará acessível em `http://localhost:8501`.

## Configuração de Segurança
A segurança do SAEDAS é projetada em camadas (Defense in Depth). Abaixo estão as diretrizes implementadas e recomendadas:

### Nível de Aplicação
*   **Input Sanitization**: O Streamlit abstrai a renderização direta de HTML, mitigando riscos de XSS (Cross-Site Scripting), exceto onde `unsafe_allow_html=True` é explicitamente utilizado. Nestes pontos, o código foi auditado para garantir que apenas conteúdo estático e confiável seja injetado.
*   **Session Management**: O gerenciamento de estado é isolado por instância de usuário, prevenindo *Session Hijacking* básico em ambientes compartilhados.

### Nível de Infraestrutura (Rede/Linux)
*   **Container Isolation**: O `Dockerfile` utiliza um usuário não-root (prática recomendada para produção - *to be implemented*) para limitar o vetor de ataque em caso de compromisso do container.
*   **Network Segmentation**: No `docker-compose.yml`, a aplicação expõe a porta `8501` apenas para o *host*. Em produção, recomenda-se o uso de um **Reverse Proxy** (Nginx/Traefik) com terminação SSL/TLS (HTTPS) à frente do container.
*   **Firewall Rules**:
    *   Bloquear acesso externo direto à porta 8501.
    *   Permitir tráfego apenas via porta 443 (HTTPS) através do Load Balancer/Proxy.

## Uso
O sistema é intuitivo e dividido em seções funcionais na barra lateral (Sidebar).

### Execução Local (Dev Mode)
Para iniciar o servidor de desenvolvimento com *hot-reload* ativado:
```bash
streamlit run app/app.py
```

### Navegação e Funcionalidades
1.  **Dashboard Geral (Início)**: Visão macro dos indicadores de desempenho (KPIs) de saúde.
2.  **Módulos Específicos**:
    *   **Encaminhamentos**: Gestão de fluxo de pacientes para especialistas.
    *   **Exames & Vacinação**: Controle de prontuários e cobertura vacinal.
    *   **Nutrição**: Monitoramento antropométrico e dietético.
3.  **Deep Linking**: O sistema suporta parâmetros de URL para acesso direto a perfis de alunos.
    *   Exemplo: `http://localhost:8501/?menu=Aluno&aluno=NomeDoAluno&nasc=2010-01-01`
    *   Essa funcionalidade permite integração com sistemas externos para redirecionamento rápido.

### Exportação de Dados
Scripts auxiliares em `bash` estão disponíveis na raiz para operações de dados (ex: `app/exportar_dados_csv.sh`), permitindo dumps controlados da base de dados para análise externa. Executar via terminal dentro do container:
```bash
docker exec -it <container_id> /bin/bash /app/exportar_dados_csv.sh
```
