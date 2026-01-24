#!/bin/bash

# Configurações de acesso
USER="admexport"
PASSWORD="@Suporte0102"
DATABASE="semug"
SERVER="172.15.2.2,1041"

# Log
LOGFILE="/media/db/saedas/app/fechamento_saedas.log"

echo "----------------------------------------" >> "$LOGFILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando execução do fechamento" >> "$LOGFILE"

# Executa a stored procedure (sem saída esperada)
/opt/mssql-tools/bin/sqlcmd -S "$SERVER" -U "$USER" -P "$PASSWORD" -d "$DATABASE" -Q "EXEC usp_Fechamento_Saedas" >> "$LOGFILE" 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Fechamento executado com sucesso" >> "$LOGFILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ ERRO na execução do fechamento" >> "$LOGFILE"
fi
