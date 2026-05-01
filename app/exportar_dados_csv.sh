#!/bin/bash

# ======================
# Carregamento de Configurações (.env)
# ======================
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

ARQUIVO_CSV06="/media/db/saedas/app/data/DashboardMedico.csv"
ARQUIVO_CSV061="/media/db/saedas/app/data/DashboardMedicoAno.csv"
ARQUIVO_CSV062="/media/db/saedas/app/data/DashboardMedicoAluno.csv"

ARQUIVO_CSV07="/media/db/saedas/app/data/DashboardEnfermagem.csv"
ARQUIVO_CSV071="/media/db/saedas/app/data/DashboardEnfermagemAno.csv"
ARQUIVO_CSV072="/media/db/saedas/app/data/DashboardEnfermagemAluno.csv"

ARQUIVO_CSV08="/media/db/saedas/app/data/DashboardAssistenciaSocial.csv"
ARQUIVO_CSV081="/media/db/saedas/app/data/DashboardAssistenciaSocialAno.csv"
ARQUIVO_CSV082="/media/db/saedas/app/data/DashboardAssistenciaSocialAluno.csv"

ARQUIVO_CSV09="/media/db/saedas/app/data/DashboardProfessor.csv"
ARQUIVO_CSV091="/media/db/saedas/app/data/DashboardProfessorAno.csv"
ARQUIVO_CSV092="/media/db/saedas/app/data/DashboardProfessorAluno.csv"

ARQUIVO_CSV10="/media/db/saedas/app/data/DashboardProfissional.csv"

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

QUERY06="EXEC usp_Exportar_DashboardMedico"
QUERY061="EXEC usp_Exportar_DashboardMedicoAno"
QUERY062="EXEC usp_Exportar_DashboardMedicoAluno"

QUERY07="EXEC usp_Exportar_DashboardEnfermagem"
QUERY071="EXEC usp_Exportar_DashboardEnfermagemAno"
QUERY072="EXEC usp_Exportar_DashboardEnfermagemAluno"

QUERY08="EXEC usp_Exportar_DashboardAssistenciaSocial"
QUERY081="EXEC usp_Exportar_DashboardAssistenciaSocialAno"
QUERY082="EXEC usp_Exportar_DashboardAssistenciaSocialAluno"

QUERY09="EXEC usp_Exportar_DashboardProfessor"
QUERY091="EXEC usp_Exportar_DashboardProfessorAno"
QUERY092="EXEC usp_Exportar_DashboardProfessorAluno"

QUERY10="EXEC usp_Exportar_DashboardProfissional"

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

CABECALHO06="Ano;IdUrg;URG;Escola;Tipo;Descricao;Qtd"
CABECALHO061="URG;Escola;Atendimento;2022;2023;2024;2025;2026;Total"
CABECALHO062="Ano;ID;Aluno;DtNasc;Sexo;Profissional;IdUrg;URG;Escola;Tipo;Serie;Turma"

CABECALHO07="Ano;IdUrg;URG;Escola;Tipo;Descricao;Qtd"
CABECALHO071="URG;Escola;Atendimento;2022;2023;2024;2025;2026;Total"
CABECALHO072="Ano;ID;Aluno;DtNasc;Sexo;Profissional;IdUrg;URG;Escola;Tipo;Serie;Turma"

CABECALHO08="Ano;IdUrg;URG;Escola;Tipo;Descricao;Qtd"
CABECALHO081="URG;Escola;Atendimento;2022;2023;2024;2025;2026;Total"
CABECALHO082="Ano;ID;Aluno;DtNasc;Sexo;Profissional;IdUrg;URG;Escola;Tipo;Serie;Turma"

CABECALHO09="Ano;IdUrg;URG;Escola;Tipo;Descricao;Qtd"
CABECALHO091="URG;Escola;Atendimento;2022;2023;2024;2025;2026;Total"
CABECALHO092="Ano;ID;Aluno;DtNasc;Sexo;Profissional;IdUrg;URG;Escola;Tipo;Serie;Turma"

CABECALHO10="Ano;IdUrg;URG;Escola;Tipo;Descricao;Qtd"

# ======================
# Log
# ======================
LOGFILE="${LOG_PATH}exportar_dados.log"

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

exportar_csv "$QUERY06" "$ARQUIVO_CSV06" "$CABECALHO06" "DashboardMedico"
exportar_csv "$QUERY061" "$ARQUIVO_CSV061" "$CABECALHO061" "DashboardMedicoAno"
exportar_csv "$QUERY062" "$ARQUIVO_CSV062" "$CABECALHO062" "DashboardMedicoAluno"

exportar_csv "$QUERY07" "$ARQUIVO_CSV07" "$CABECALHO07" "DashboardEnfermagem"
exportar_csv "$QUERY071" "$ARQUIVO_CSV071" "$CABECALHO071" "DashboardEnfermagemAno"
exportar_csv "$QUERY072" "$ARQUIVO_CSV072" "$CABECALHO072" "DashboardEnfermagemAluno"

exportar_csv "$QUERY08" "$ARQUIVO_CSV08" "$CABECALHO08" "DashboardAssistenciaSocial"
exportar_csv "$QUERY081" "$ARQUIVO_CSV081" "$CABECALHO081" "DashboardAssistenciaSocialAno"
exportar_csv "$QUERY082" "$ARQUIVO_CSV082" "$CABECALHO082" "DashboardAssistenciaSocialAluno"

exportar_csv "$QUERY09" "$ARQUIVO_CSV09" "$CABECALHO09" "DashboardProfessor"
exportar_csv "$QUERY091" "$ARQUIVO_CSV091" "$CABECALHO091" "DashboardProfessorAno"
exportar_csv "$QUERY092" "$ARQUIVO_CSV092" "$CABECALHO092" "DashboardProfessorAluno"

exportar_csv "$QUERY10" "$ARQUIVO_CSV10" "$CABECALHO10" "DashboardProfissional"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Final da execução do script" >> "$LOGFILE"
echo "" >> "$LOGFILE"
