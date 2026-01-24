"""
Utilitário de leitura de CSV com fallback de encoding e validação opcional de schema.

Uso básico:
    from app.utils.data_loader import load_csv
    df = load_csv("data/DashboardHome.csv", expected_cols={"Ano", "URG"})
Retorna um tuple (df, info), onde info traz encoding usado e mensagens de alerta/erro.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence

import pandas as pd


DEFAULT_ENCODINGS: Sequence[str] = ("utf-8",)


def load_csv(
    file_path: str | Path,
    *,
    sep: str = ";",
    encodings: Sequence[str] = DEFAULT_ENCODINGS,
    expected_cols: Optional[Iterable[str]] = None,
) -> tuple[pd.DataFrame, dict]:
    """
    Lê um CSV tentando múltiplos encodings e valida colunas esperadas (se fornecidas).

    Retorno:
        (df, info) onde info contém:
            - encoding_usado: str | None
            - erros: lista de mensagens de erro
            - alertas: lista de mensagens de alerta (ex.: colunas faltantes)
    Em caso de falha total na leitura, df será um DataFrame vazio e info.erros trará o motivo.
    """
    info = {"encoding_usado": None, "erros": [], "alertas": []}
    path = Path(file_path)
    if not path.exists():
        info["erros"].append(f"Arquivo '{path}' não encontrado.")
        return pd.DataFrame(), info

    df = pd.DataFrame()
    last_exc: Exception | None = None
    for enc in encodings:
        try:
            df = pd.read_csv(path, sep=sep, encoding=enc)
            info["encoding_usado"] = enc
            break
        except Exception as exc:  # Captura qualquer erro de leitura
            last_exc = exc
            continue

    # Fallback final com substituição de caracteres caso todos encodings falhem
    if info["encoding_usado"] is None:
        try:
            df = pd.read_csv(
                path,
                sep=sep,
                encoding=encodings[-1],
                encoding_errors="replace",
                on_bad_lines="skip",
                engine="python",  # parser mais tolerante para linhas quebradas
                usecols=list(expected_cols) if expected_cols else None,
            )
            info["encoding_usado"] = f"{encodings[-1]} (errors=replace, skip bad lines, engine=python)"
        except Exception as exc:
            last_exc = exc

    if info["encoding_usado"] is None:
        info["erros"].append(
            f"Não foi possível ler o arquivo '{path}' com encodings testados: {encodings}. "
            f"Último erro: {last_exc}"
        )
        return pd.DataFrame(), info

    if df.empty:
        info["alertas"].append(f"O arquivo '{path.name}' foi lido mas está vazio.")

    if expected_cols:
        missing = set(expected_cols) - set(df.columns)
        if missing:
            info["alertas"].append(
                f"Colunas ausentes em '{path.name}': {', '.join(sorted(missing))}"
            )

    return df, info
