"""
Inferência do modelo de risco clínico (SINAN) sobre cadastro AJUSTA.

Mapeamentos AJUSTA → colunas do pipeline: NU_IDADE_N, CS_SEXO, CS_RACA,
CS_ESCOL_N, NU_LESOES, NERVOSAFET, CLASSOPERA, FORMACLINI.

CS_ESCOL_N segue faixas usuais da FIN SINAN (0–8 e 10, sem 9 no treino).
NERVOSAFET: contagem aproximada de nervos afetados (0, 2, 5 para faixas do formulário).
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

# Colunas exigidas pelo pickle (RandomForest + ColumnTransformer)
FEATURE_COLS = [
    "NU_IDADE_N",
    "CS_SEXO",
    "CS_RACA",
    "CS_ESCOL_N",
    "NU_LESOES",
    "NERVOSAFET",
    "CLASSOPERA",
    "FORMACLINI",
]

MODEL_REL_PATH = Path("ml_models") / "modelo_risco_clinico_v2.pkl"

# Classificação sugerida em contexts/implement_model.md
def classificar_risco(score: float) -> str:
    if score < 0.3:
        return "Baixo"
    if score < 0.7:
        return "Médio"
    return "Alto"


def _norm_label(val) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    try:
        if pd.isna(val):
            return ""
    except (TypeError, ValueError):
        pass
    t = str(val).strip()
    t = t.replace("\u2013", "-").replace("\u2014", "-")
    return t


# Classificação operacional (SINAN PB=1, MB=2)
_MAP_CLASSOPERA = {
    "Paucibacilar (PB)": 1.0,
    "Multibacilar (MB)": 2.0,
}

# Forma clínica (códigos FIN hanseníase usuais)
_MAP_FORMA = {
    "Indeterminada": 1.0,
    "Tuberculoide": 2.0,
    "Dimorfa": 3.0,
    "Virchowiana": 4.0,
}

# Sexo: pipeline treinado com 'M' / 'F'
_MAP_SEXO = {
    "Masculino": "M",
    "Feminino": "F",
}

# Cor/raça SINAN (1 Branca … 5 Indígena)
_MAP_RACA = {
    "Branca": 1.0,
    "Preta": 2.0,
    "Amarela": 3.0,
    "Parda": 4.0,
    "Indígena": 5.0,
}

# Escolaridade → CS_ESCOL_N (FIN SINAN hanseníase; categorias no treino: 0–8 e 10).
# Revisar com a planilha/tabulação oficial se houver divergência com o estado do Ceará no treino.
_MAP_ESCOL = {
    "Sem escolaridade / Analfabeto": 0.0,
    "Fundamental incompleto": 2.0,
    "Fundamental completo": 4.0,
    "Médio incompleto": 5.0,
    "Médio completo": 6.0,
    "Superior incompleto": 7.0,
    "Superior completo": 8.0,
    "Pós-graduação": 10.0,
}

# Número de lesões → inteiro representativo da faixa
_MAP_LESOES = {
    "1": 1,
    "2-5": 3,
    "6-10": 8,
    "10+": 12,
}

# Nervos afetados → contagem aproximada (NERVOSAFET numérico no SINAN).
# Ajustar 1–2 / 3+ se o dicionário de treino usar outra convenção.
_MAP_NERVOS = {
    "Nenhum": 0,
    "1-2": 2,
    "3 ou mais": 5,
}

_INV_RACA = {float(v): k for k, v in _MAP_RACA.items()}
_INV_ESCOL = {float(v): k for k, v in _MAP_ESCOL.items()}
_INV_FORMA = {float(v): k for k, v in _MAP_FORMA.items()}


def _fmt_code_num(val) -> str:
    try:
        v = float(val)
    except (TypeError, ValueError):
        return str(val)
    if np.isnan(v):
        return "—"
    if v == int(v):
        return str(int(v))
    return str(v).rstrip("0").rstrip(".")


def label_cs_raca(val) -> str:
    """Rótulo para multiselect / legenda (código SINAN + nome IBGE)."""
    try:
        v = float(val)
    except (TypeError, ValueError):
        return str(val) if val is not None and not (isinstance(val, float) and np.isnan(val)) else "—"
    if np.isnan(v):
        return "—"
    nome = _INV_RACA.get(v, "?")
    return f"{_fmt_code_num(v)} — {nome}"


def label_cs_escol_n(val) -> str:
    try:
        v = float(val)
    except (TypeError, ValueError):
        return str(val)
    if np.isnan(v):
        return "—"
    nome = _INV_ESCOL.get(v, "Código")
    return f"{_fmt_code_num(v)} — {nome}"


def label_classopera(val) -> str:
    try:
        v = float(val)
    except (TypeError, ValueError):
        return str(val)
    if np.isnan(v):
        return "—"
    if v == 1.0:
        return "1 — Paucibacilar (PB)"
    if v == 2.0:
        return "2 — Multibacilar (MB)"
    return f"{_fmt_code_num(v)} — Classificação"


def label_formaclini(val) -> str:
    try:
        v = float(val)
    except (TypeError, ValueError):
        return str(val)
    if np.isnan(v):
        return "—"
    nome = _INV_FORMA.get(v, "?")
    return f"{_fmt_code_num(v)} — {nome}"


def label_cs_sexo(val) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "—"
    s = str(val).strip().upper()
    if s == "M":
        return "M — Masculino"
    if s == "F":
        return "F — Feminino"
    return str(val)


@st.cache_resource
def get_clinical_risk_pipeline():
    """Carrega o joblib uma vez por sessão (sklearn==1.6.1)."""
    import joblib  # import tardio: evita falha ao importar o módulo se joblib/sklearn atrasarem no deploy

    root = Path(__file__).resolve().parents[1]
    path = root / MODEL_REL_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Modelo não encontrado: {path}")
    return joblib.load(path)


def _idade_anos_series(s_data_nasc: pd.Series) -> pd.Series:
    dt = pd.to_datetime(s_data_nasc, format="%d/%m/%Y", errors="coerce")
    hoje = datetime.now()
    dias = (hoje - dt).dt.days
    idade = (dias / 365.25).round().astype("Int64")
    return idade


def _build_feature_row_series(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna DataFrame com colunas FEATURE_COLS (object/float mistos)."""
    out = pd.DataFrame(index=df.index)

    out["NU_IDADE_N"] = _idade_anos_series(df["data_nascimento"])

    sexo_raw = df["sexo"].map(_norm_label)
    out["CS_SEXO"] = sexo_raw.map(_MAP_SEXO)

    raca_raw = df["cor_raca_etnia"].map(_norm_label)
    out["CS_RACA"] = raca_raw.map(lambda x: _MAP_RACA.get(x) if x else None)

    esc_raw = df["escolaridade"].map(_norm_label)
    out["CS_ESCOL_N"] = esc_raw.map(lambda x: _MAP_ESCOL.get(x) if x else None)

    le_raw = df["numero_lesoes"].map(_norm_label)
    out["NU_LESOES"] = le_raw.map(lambda x: _MAP_LESOES.get(x) if x else None)

    nv_raw = df["nervos_afetados"].map(_norm_label)
    out["NERVOSAFET"] = nv_raw.map(lambda x: _MAP_NERVOS.get(x) if x else None)

    co_raw = df["classificacao_operacional"].map(_norm_label)
    out["CLASSOPERA"] = co_raw.map(lambda x: _MAP_CLASSOPERA.get(x) if x else None)

    fc_raw = df["forma_clinica"].map(_norm_label)
    out["FORMACLINI"] = fc_raw.map(lambda x: _MAP_FORMA.get(x) if x else None)

    return out


def _elegivel_mask(features: pd.DataFrame) -> pd.Series:
    ok_idade = features["NU_IDADE_N"].notna() & (features["NU_IDADE_N"] >= 0) & (
        features["NU_IDADE_N"] <= 120
    )
    ok_rest = pd.Series(True, index=features.index)
    for c in FEATURE_COLS:
        if c == "NU_IDADE_N":
            continue
        ok_rest &= features[c].notna()
    return ok_idade & ok_rest


def beneficiarios_com_score(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Anexa score_risco_clinico e categoria_risco onde houver dados completos.

    Retorna (df_enriquecido, stats) com keys: total, elegiveis, com_score.
    """
    required = [
        "data_nascimento",
        "sexo",
        "cor_raca_etnia",
        "escolaridade",
        "numero_lesoes",
        "nervos_afetados",
        "classificacao_operacional",
        "forma_clinica",
    ]
    out = df.copy()
    stats = {"total": len(out), "elegiveis": 0, "com_score": 0}

    if out.empty or not all(c in out.columns for c in required):
        out["score_risco_clinico"] = np.nan
        out["categoria_risco"] = pd.NA
        for c in FEATURE_COLS:
            if c == "CS_SEXO":
                out[c] = pd.Series(pd.NA, index=out.index, dtype=object)
            else:
                out[c] = np.nan
        return out, stats

    feats = _build_feature_row_series(out)
    elig = _elegivel_mask(feats)
    stats["elegiveis"] = int(elig.sum())

    out["score_risco_clinico"] = np.nan
    out["categoria_risco"] = pd.Series(pd.NA, index=out.index, dtype="string")
    for c in FEATURE_COLS:
        if c == "CS_SEXO":
            out[c] = pd.Series(pd.NA, index=out.index, dtype=object)
        else:
            out[c] = np.nan

    if not elig.any():
        return out, stats

    pipeline = get_clinical_risk_pipeline()
    X = feats.loc[elig, FEATURE_COLS].copy()
    # Garantir dtypes esperados pelo sklearn
    X["NU_IDADE_N"] = X["NU_IDADE_N"].astype(float)
    X["NU_LESOES"] = X["NU_LESOES"].astype(float)
    X["NERVOSAFET"] = X["NERVOSAFET"].astype(float)
    for c in ("CLASSOPERA", "CS_ESCOL_N", "FORMACLINI", "CS_RACA"):
        X[c] = X[c].astype(float)

    proba = pipeline.predict_proba(X)[:, 1]
    out.loc[elig, "score_risco_clinico"] = proba
    out.loc[elig, "categoria_risco"] = [classificar_risco(float(s)) for s in proba]
    for c in FEATURE_COLS:
        out.loc[elig, c] = feats.loc[elig, c].values
    stats["com_score"] = int(elig.sum())

    return out, stats
