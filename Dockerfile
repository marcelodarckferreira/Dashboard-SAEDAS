FROM python:3.12-slim-bookworm

# Evita que o Python gere arquivos .pyc e garante log em tempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/SAEDAS \
    TZ=America/Sao_Paulo

WORKDIR /SAEDAS

# Instala dependências do sistema necessárias para bibliotecas científicas e Streamlit
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas o requirements primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Atualiza pip e instala dependências
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o restante do código (esta camada muda frequentemente)
COPY app/ app/

# Expõe a porta padrão do Streamlit
EXPOSE 8501

# Healthcheck para garantir que o container está saudável
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Comando para iniciar a aplicação
CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0"]