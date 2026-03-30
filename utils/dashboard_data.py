"""Padronização de dados da aba Dados para visualização no dashboard."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

LABEL_NULO = "Não informado"


def normalize_categoria(series: pd.Series, label_nulo: str = LABEL_NULO) -> pd.Series:
    """Trata vazio, NA e espaços como label_nulo; demais valores com strip."""

    def _one(v) -> str:
        if pd.isna(v):
            return label_nulo
        s = str(v).strip()
        if not s or s.lower() == "nan":
            return label_nulo
        return s

    return series.map(_one)


def _faixa_etaria(idade: float, label_nulo: str) -> str:
    if pd.isna(idade):
        return label_nulo
    if idade <= 12:
        return "0-12 anos"
    if idade <= 18:
        return "13-18 anos"
    if idade <= 30:
        return "19-30 anos"
    if idade <= 50:
        return "31-50 anos"
    return "51+ anos"


def prepare_beneficiarios_dashboard(
    df: pd.DataFrame,
    *,
    ref_date: datetime | None = None,
    label_nulo: str = LABEL_NULO,
) -> pd.DataFrame:
    """
    Copia o DataFrame e adiciona colunas padronizadas para gráficos e filtros.
    Idade e faixa etária não imputam valor falso quando falta data de nascimento.
    """
    if df is None:
        return pd.DataFrame()
    if df.empty:
        return df.copy()

    out = df.copy()
    ref = ref_date or datetime.now()

    cat_cols = [
        "sexo",
        "genero",
        "bairro",
        "tipo_residencia",
        "acesso_agua",
        "acesso_esgoto",
        "acesso_energia",
        "cor_raca_etnia",
        "ja_teve_hanseniase",
        "projeto_acao",
    ]
    for c in cat_cols:
        if c in out.columns:
            out[c] = normalize_categoria(out[c], label_nulo)

    if "data_nascimento" in out.columns:
        dt = pd.to_datetime(out["data_nascimento"], dayfirst=True, errors="coerce")
        out["data_nascimento_parsed"] = dt
        idade = (ref - dt).dt.days / 365.25
        idade = idade.where(dt.notna(), np.nan)
        out["idade"] = idade
    else:
        out["data_nascimento_parsed"] = pd.NaT
        out["idade"] = np.nan

    out["faixa_etaria"] = out["idade"].apply(lambda x: _faixa_etaria(x, label_nulo))

    if "renda_per_capita" in out.columns:
        out["renda_per_capita_num"] = pd.to_numeric(
            out["renda_per_capita"], errors="coerce"
        )
    else:
        out["renda_per_capita_num"] = np.nan

    if "numero_membros_familia" in out.columns:
        out["numero_membros_familia_num"] = pd.to_numeric(
            out["numero_membros_familia"], errors="coerce"
        )
    else:
        out["numero_membros_familia_num"] = np.nan

    if "ja_teve_hanseniase" in out.columns:

        def _cat_h(v: str) -> str:
            if v == "Sim":
                return "Já teve hanseníase"
            if v == "Não":
                return "Não possui"
            return label_nulo

        out["categoria_hanseniase"] = out["ja_teve_hanseniase"].map(_cat_h)
    elif "situacao_hanseniase" in out.columns:
        out["categoria_hanseniase"] = normalize_categoria(
            out["situacao_hanseniase"], label_nulo
        )
    else:
        out["categoria_hanseniase"] = label_nulo

    return out


def split_projetos_celula(val, label_nulo: str = LABEL_NULO) -> list[str]:
    if val is None:
        return []
    try:
        if pd.isna(val):
            return []
    except (TypeError, ValueError):
        pass
    s = str(val).strip()
    if not s or s == label_nulo or s == "<NA>":
        return []
    return [p.strip() for p in s.split(",") if p.strip()]


def explode_projetos_series(df: pd.DataFrame, col: str = "projeto_acao") -> pd.Series:
    """Uma entrada por projeto citado na linha (para contagens agregadas)."""
    if col not in df.columns or df.empty:
        return pd.Series(dtype=object)
    parts: list[str] = []
    for val in df[col]:
        ps = split_projetos_celula(val, LABEL_NULO)
        parts.extend(ps if ps else [LABEL_NULO])
    return pd.Series(parts, name="projeto")


def projetos_opcoes_filtro(df: pd.DataFrame) -> list[str]:
    s = explode_projetos_series(df)
    u = sorted({x for x in s.unique() if x != LABEL_NULO})
    return u


def count_projetos_explodidos(df: pd.DataFrame) -> pd.Series:
    return explode_projetos_series(df).value_counts()


def n_projetos_distintos(df: pd.DataFrame) -> int:
    s = explode_projetos_series(df)
    u = {x for x in s.unique() if x != LABEL_NULO}
    return len(u)


def apply_dashboard_filtros(
    df: pd.DataFrame,
    *,
    projetos: list[str] | None = None,
    bairros: list[str] | None = None,
    sexos: list[str] | None = None,
    tipos_residencia: list[str] | None = None,
    categorias_hanseniase: list[str] | None = None,
    label_nulo: str = LABEL_NULO,
) -> pd.DataFrame:
    """Filtra o DataFrame; listas vazias ou None não aplicam aquele critério."""
    if df is None or df.empty:
        return df.copy() if df is not None else pd.DataFrame()

    out = df

    if projetos:
        sel = set(projetos)

        def _match_proj(row) -> bool:
            ps = set(split_projetos_celula(row.get("projeto_acao"), label_nulo))
            return bool(ps & sel)

        out = out[out.apply(_match_proj, axis=1)]

    if bairros and "bairro" in out.columns:
        out = out[out["bairro"].isin(bairros)]
    if sexos and "sexo" in out.columns:
        out = out[out["sexo"].isin(sexos)]
    if tipos_residencia and "tipo_residencia" in out.columns:
        out = out[out["tipo_residencia"].isin(tipos_residencia)]
    if categorias_hanseniase and "categoria_hanseniase" in out.columns:
        out = out[out["categoria_hanseniase"].isin(categorias_hanseniase)]

    return out


# Ordem lógica para eixo X em faixa etária
ORDEM_FAIXA_ETARIA = [
    "0-12 anos",
    "13-18 anos",
    "19-30 anos",
    "31-50 anos",
    "51+ anos",
    LABEL_NULO,
]


def ordenar_faixas_etarias(index_like: pd.Index) -> list:
    ordem = {k: i for i, k in enumerate(ORDEM_FAIXA_ETARIA)}
    return sorted(index_like, key=lambda x: ordem.get(str(x), 999))
