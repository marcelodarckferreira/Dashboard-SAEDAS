#!/bin/bash

# ======================
# Configurações de acesso
# ======================
USER="admexport"
PASSWORD="@Suporte0102"
DATABASE="semug"
SERVER="172.15.2.2,1041"

# ======================
# Arquivos CSV
# ======================
ARQUIVO_CSV01="/media/db/saedas/app/data/DashboardHome.csv"
ARQUIVO_CSV11="/media/db/saedas/app/data/DashboardHomeURGAno.csv"
ARQUIVO_CSV12="/media/db/saedas/app/data/DashboardHomeEscolaAno.csv"
ARQUIVO_CSV13="/media/db/saedas/app/data/DashboardHomeAno.csv"

ARQUIVO_CSV02="/media/db/saedas/app/data/DashboardConsulta.csv"
ARQUIVO_CSV021="/media/db/saedas/app/data/DashboardConsultaAno.csv"
ARQUIVO_CSV022="/media/db/saedas/app/data/DashboardConsultaAluno.csv"

ARQUIVO_CSV03="/media/db/saedas/app/data/DashboardExame.csv"
ARQUIVO_CSV031="/media/db/saedas/app/data/DashboardExameAno.csv"
ARQUIVO_CSV032="/media/db/saedas/app/data/DashboardExameAluno.csv"

ARQUIVO_CSV04="/media/db/saedas/app/data/DashboardVacinacao.csv"
ARQUIVO_CSV041="/media/db/saedas/app/data/DashboardVacinacaoAno.csv"
ARQUIVO_CSV042="/media/db/saedas/app/data/DashboardVacinacaoAluno.csv"

ARQUIVO_CSV05="/media/db/saedas/app/data/DashboardNutricao.csv"
ARQUIVO_CSV051="/media/db/saedas/app/data/DashboardNutricaoAno.csv"
ARQUIVO_CSV052="/media/db/saedas/app/data/DashboardNutricaoAluno.csv"

# ======================
# Stored Procedures
# ======================
QUERY01="EXEC usp_Exportar_DashboardHome"
QUERY11="EXEC usp_Exportar_DashboardHomeURGAno"
QUERY12="EXEC usp_Exportar_DashboardHomeEscolaAno"
QUERY13="EXEC usp_Exportar_DashboardHomeAno"

QUERY02="EXEC usp_Exportar_DashboardConsulta"
QUERY021="EXEC usp_Exportar_DashboardConsultaAno"
QUERY022="EXEC usp_Exportar_DashboardConsultaAluno"

QUERY03="EXEC usp_Exportar_DashboardExame"
QUERY031="EXEC usp_Exportar_DashboardExameAno"
QUERY032="EXEC usp_Exportar_DashboardExameAluno"

QUERY04="EXEC usp_Exportar_DashboardVacinacao"
QUERY041="EXEC usp_Exportar_DashboardVacinacaoAno"
QUERY042="EXEC usp_Exportar_DashboardVacinacaoAluno"

QUERY05="EXEC usp_Exportar_DashboardNutricao"
QUERY051="EXEC usp_Exportar_DashboardNutricaoAno"
QUERY052="EXEC usp_Exportar_DashboardNutricaoAluno"

# ======================
# Cabeçalhos CSV corretos
# ======================
CABECALHO01="Ano;IdUrg;URG;Escola;DtInicio;DtFechamento;QtdAlunoEscola;QtdAluno;QtdProfessor;QtdPsicologo;QtdAssistSocial;QtdEnfermagem;QtdMedico;QtdVacinacao;QtdVacina;QtdEncaminhamento;QtdExame"
CABECALHO11="URG;Descricao;2022;2023;2024;2025;Total"
CABECALHO12="URG;Escola;Descricao;2022;2023;2024;2025;Total"
CABECALHO13="Descricao;2022;2023;2024;2025;Total"

CABECALHO02="Ano;IdUrg;URG;Escola;Tipo;Consulta;Qtd"
CABECALHO021="URG;Escola;Consulta;2022;2023;2024;2025;Total"
CABECALHO022="Ano;Aluno;DtNasc;Sexo;Consulta;IdUrg;URG;Escola;Tipo;Serie;Turma"

CABECALHO03="Ano;IdUrg;URG;Escola;Tipo;Exame;Qtd"
CABECALHO031="URG;Escola;Exame;2022;2023;2024;2025;Total"
CABECALHO032="Ano;Aluno;DtNasc;Sexo;Exame;IdUrg;URG;Escola;Tipo;Serie;Turma"

CABECALHO04="Ano;IdUrg;URG;Escola;Tipo;Vacina;Qtd"
CABECALHO041="URG;Escola;Vacina;2022;2023;2024;2025;Total"
CABECALHO042="Ano;Aluno;DtNasc;Sexo;Vacina;Dose;Lote;IdUrg;URG;Escola;Tipo;Serie;Turma"

CABECALHO05="Ano;IdUrg;URG;Escola;Tipo;Nutricao;Qtd"
CABECALHO051="URG;Escola;Nutricao;2022;2023;2024;2025;Total"
CABECALHO052="Ano;Aluno;DtNasc;Sexo;Peso;Altura;IMC;Nutricao;IdUrg;URG;Escola;Tipo;Serie;Turma"

# ======================
# Log
# ======================
LOGFILE="/media/db/saedas/app/exportar_dados.log"

# ======================
# Função de exportação com cabeçalho e uso de arquivo temporário
# ======================
exportar_csv() {
    local query="$1"
    local arquivo="$2"
    local cabecalho="$3"
    local titulo="$4"
    local temp_arquivo="/tmp/tmp_export_$(basename "$arquivo")"

    echo "--------------------------------------------------" >> "$LOGFILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando exportação: $titulo" >> "$LOGFILE"

    # Escreve cabeçalho no arquivo final
    echo "$cabecalho" > "$arquivo"

    # Executa bcp no arquivo temporário
    /opt/mssql-tools/bin/bcp "$query" queryout "$temp_arquivo" -S "$SERVER" -U "$USER" -P "$PASSWORD" -d "$DATABASE" -c -t";" -r"\n" >> "$LOGFILE" 2>&1

    if [ $? -eq 0 ]; then
        # Anexa conteúdo ao arquivo final
        cat "$temp_arquivo" >> "$arquivo"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Sucesso: $arquivo" >> "$LOGFILE"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ ERRO: $titulo" >> "$LOGFILE"
    fi

    # Remove arquivo temporário
    rm -f "$temp_arquivo"
}

# ======================
# Execuções
# ======================
exportar_csv "$QUERY01" "$ARQUIVO_CSV01" "$CABECALHO01" "DashboardHome"
exportar_csv "$QUERY11" "$ARQUIVO_CSV11" "$CABECALHO11" "DashboardHomeURGAno"
exportar_csv "$QUERY12" "$ARQUIVO_CSV12" "$CABECALHO12" "DashboardHomeEscolaAno"
exportar_csv "$QUERY13" "$ARQUIVO_CSV13" "$CABECALHO13" "DashboardHomeAno"

exportar_csv "$QUERY02" "$ARQUIVO_CSV02" "$CABECALHO02" "DashboardConsulta"
exportar_csv "$QUERY021" "$ARQUIVO_CSV021" "$CABECALHO021" "DashboardConsultaAno"
exportar_csv "$QUERY022" "$ARQUIVO_CSV022" "$CABECALHO022" "DashboardConsultaAluno"

exportar_csv "$QUERY03" "$ARQUIVO_CSV03" "$CABECALHO03" "DashboardExame"
exportar_csv "$QUERY031" "$ARQUIVO_CSV031" "$CABECALHO031" "DashboardExameAno"
exportar_csv "$QUERY032" "$ARQUIVO_CSV032" "$CABECALHO032" "DashboardExameAluno"

exportar_csv "$QUERY04" "$ARQUIVO_CSV04" "$CABECALHO04" "DashboardVacinacao"
exportar_csv "$QUERY041" "$ARQUIVO_CSV041" "$CABECALHO041" "DashboardVacinacaoAno"
exportar_csv "$QUERY042" "$ARQUIVO_CSV042" "$CABECALHO042" "DashboardVacinacaoAluno"

exportar_csv "$QUERY05" "$ARQUIVO_CSV05" "$CABECALHO05" "DashboardNutricao"
exportar_csv "$QUERY051" "$ARQUIVO_CSV051" "$CABECALHO051" "DashboardNutricaoAno"
exportar_csv "$QUERY052" "$ARQUIVO_CSV052" "$CABECALHO052" "DashboardNutricaoAluno"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Final da execução do script" >> "$LOGFILE"
echo "" >> "$LOGFILE"
