"""
Schemas esperados por página para validação na carga de dados.
Usado pelo utilitário load_csv.
"""

# Dashboard Home (visão geral)
SCHEMA_HOME = {
    "Ano",
    "URG",
    "Escola",
    "DtInicio",
    "DtFechamento",
    "QtdAluno",
    "QtdProfessor",
    "QtdPsicologo",
    "QtdAssistSocial",
    "QtdEnfermagem",
    "QtdMedico",
    "QtdVacinacao",
    "QtdVacina",
    "QtdEncaminhamento",
    "QtdExame",
    "QtdAlunoEscola",
}

# Encaminhamentos (consulta)
SCHEMA_CONSULTA = {
    "Ano",
    "URG",
    "Escola",
    "Consulta",
    "Qtd",
    "Tipo",
}

# Encaminhamentos por aluno (consulta detalhada)
SCHEMA_CONSULTA_ALUNO = {
    "Ano",
    "Aluno",
    "DtNasc",
    "Sexo",
    "Consulta",
    "IdUrg",
    "URG",
    "Escola",
    "Tipo",
    "Serie",
    "Turma",
}

# Consulta por ano (agregado)
SCHEMA_CONSULTA_ANO = {
    "URG",
    "Escola",
    "Consulta",
    "2022",
    "2023",
    "2024",
    "2025",
    "2026",
    "Total",
}

# Exames
SCHEMA_EXAME = {
    "Ano",
    "URG",
    "Escola",
    "Exame",
    "Qtd",
    "Tipo",
}

# Exames por aluno
SCHEMA_EXAME_ALUNO = {
    "Ano",
    "Aluno",
    "DtNasc",
    "Sexo",
    "Exame",
    "IdUrg",
    "URG",
    "Escola",
    "Tipo",
    "Serie",
    "Turma",
}

# Exames por ano (agregado)
SCHEMA_EXAME_ANO = {
    "URG",
    "Escola",
    "Exame",
    "2022",
    "2023",
    "2024",
    "2025",
    "2026",
    "Total",
}

# Vacinação
SCHEMA_VACINACAO = {
    "Ano",
    "URG",
    "Escola",
    "Vacina",
    "Qtd",
    "Tipo",
}

# Vacinação por aluno
SCHEMA_VACINACAO_ALUNO = {
    "Ano",
    "Aluno",
    "DtNasc",
    "Sexo",
    "Vacina",
    "Dose",
    "Lote",
    "IdUrg",
    "URG",
    "Escola",
    "Tipo",
    "Serie",
    "Turma",
}

# Vacinação por ano (agregado)
SCHEMA_VACINACAO_ANO = {
    "URG",
    "Escola",
    "Vacina",
    "2022",
    "2023",
    "2024",
    "2025",
    "2026",
    "Total",
}

# Vacinação por ano (agregado)
SCHEMA_VACINACAO_ANO = {
    "URG",
    "Escola",
    "Vacina",
    "2022",
    "2023",
    "2024",
    "2025",
    "2026",
    "Total",
}

# Nutrição
SCHEMA_NUTRICAO = {
    "Ano",
    "URG",
    "Escola",
    "Tipo",
    "Nutricao",
    "Qtd",
    "IdUrg",
}

# Nutrição por aluno
SCHEMA_NUTRICAO_ALUNO = {
    "Ano",
    "Aluno",
    "DtNasc",
    "Sexo",
    "Peso",
    "Altura",
    "IMC",
    "Nutricao",
    "IdUrg",
    "URG",
    "Escola",
    "Tipo",
    "Serie",
    "Turma",
}

# Nutrição por ano (agregado)
SCHEMA_NUTRICAO_ANO = {
    "URG",
    "Escola",
    "Nutricao",
    "2022",
    "2023",
    "2024",
    "2025",
    "2026",
    "Total",
}

# Home por Escola/Ano (agregado)
SCHEMA_HOME_ESCOLA_ANO = {
    "URG",
    "Escola",
    "Descricao",
    "2022",
    "2023",
    "2024",
    "2025",
    "2026",
    "Total",
}

# Home por URG/Ano (agregado)
SCHEMA_HOME_URG_ANO = {
    "URG",
    "Descricao",
    "2022",
    "2023",
    "2024",
    "2025",
    "2026",
    "Total",
}

# Home por Ano (agregado geral)
SCHEMA_HOME_ANO = {
    "Descricao",
    "2022",
    "2023",
    "2024",
    "2025",
    "2026",
    "Total",
}
