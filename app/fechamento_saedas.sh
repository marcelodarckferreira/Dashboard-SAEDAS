#!/bin/bash

# Carregamento de Configurações (.env)
ENV_FILE="$(dirname "$0")/.env"
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "Erro: Arquivo .env não encontrado em $ENV_FILE"
    exit 1
fi

USER="$DB_USER"
PASSWORD="$DB_PASSWORD"
DATABASE="$DB_NAME"
SERVER="$DB_SERVER"

# Log
LOGFILE="${LOG_PATH}fechamento_saedas.log"

echo "----------------------------------------" >> "$LOGFILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando execução do fechamento" >> "$LOGFILE"

# Executa a stored procedure (sem saída esperada)
/opt/mssql-tools/bin/sqlcmd -S "$SERVER" -U "$USER" -P "$PASSWORD" -d "$DATABASE" -Q "EXEC usp_Fechamento_Saedas" >> "$LOGFILE" 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Fechamento executado com sucesso" >> "$LOGFILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ ERRO na execução do fechamento" >> "$LOGFILE"
fi
