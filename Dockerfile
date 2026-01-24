FROM python:3.12.6-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para bibliotecas como Pillow
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de dependências e instala as bibliotecas Python necessárias
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Expõe a porta padrão do Streamlit
EXPOSE 8501

# Comando para iniciar o aplicativo Streamlit
CMD ["streamlit", "run", "app.py", "--server.enableCORS=false", "--server.port=8501", "--server.address=0.0.0.0"]
