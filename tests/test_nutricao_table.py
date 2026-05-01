import pandas as pd

from app.utils.page_helpers import prepare_nutricao_aluno_table


def test_prepare_nutricao_aluno_table_flattens_columns_for_streamlit():
    df = pd.DataFrame(
        [
            {
                "Aluno": "Ana",
                "DataNascimento": "2014-05-10",
                "Sexo": "F",
                "URG": "Centro",
                "Escola": "EMEF 1",
                "Ano": 2024,
                "Peso": "30,5",
                "Altura": "130",
                "IMC": "18,04",
            },
            {
                "Aluno": "Ana",
                "DataNascimento": "2014-05-10",
                "Sexo": "F",
                "URG": "Centro",
                "Escola": "EMEF 1",
                "Ano": 2025,
                "Peso": "32",
                "Altura": "132",
                "IMC": "18,37",
            },
        ]
    )

    def build_perfil_link(row: pd.Series) -> str:
        return f"?menu=Aluno&aluno={row['Aluno']}"

    result = prepare_nutricao_aluno_table(df, build_perfil_link)

    assert list(result.columns[:6]) == [
        "Aluno",
        "DataNascimento",
        "Sexo",
        "URG",
        "Escola",
        "Menu",
    ]
    assert all(isinstance(column, str) for column in result.columns)
    assert result.loc[0, "Menu"] == "?menu=Aluno&aluno=Ana"
    assert result.loc[0, "DataNascimento"] == "10/05/2014"
    assert result.loc[0, "2024 | Peso (kg)"] == "30,50"
    assert result.loc[0, "2025 | Alt (cm)"] == "132"
