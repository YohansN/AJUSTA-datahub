"""Helpers para exibir detalhes de um beneficiário (aba Dados) na interface."""

from __future__ import annotations

import math
import re

import pandas as pd

from utils.dashboard_data import LABEL_NULO

NA_EXIBICAO = "Não foi informado"

# (título da seção, colunas na ordem; omitir colunas ausentes no DataFrame)
SECOES_CAMPOS: list[tuple[str, list[str]]] = [
    (
        "Identificação",
        [
            "nome_completo",
            "cpf",
            "rg",
            "data_nascimento",
            "idade",
            "faixa_etaria",
            "sexo",
            "genero",
            "cor_raca_etnia",
            "escolaridade",
            "ocupacao",
            "estado_civil",
        ],
    ),
    (
        "Moradia e contato",
        [
            "endereco",
            "bairro",
            "telefone",
            "tipo_residencia",
            "anos_residencia",
            "acesso_agua",
            "acesso_esgoto",
            "acesso_energia",
        ],
    ),
    (
        "Família e renda",
        [
            "numero_filhos",
            "numero_membros_familia",
            "renda_bruta_total",
            "renda_per_capita",
        ],
    ),
    (
        "Hanseníase",
        [
            "ja_teve_hanseniase",
            "situacao_hanseniase",
            "ano_diagnostico_hanseniase",
            "classificacao_operacional",
            "forma_clinica",
            "numero_lesoes",
            "nervos_afetados",
            "grau_incapacidade",
        ],
    ),
    (
        "Institucional",
        [
            "projeto_acao",
            "responsavel_preenchimento",
            "responsavel_entrevista",
        ],
    ),
]

LABELS_PT: dict[str, str] = {
    "nome_completo": "Nome completo",
    "cpf": "CPF",
    "rg": "RG",
    "data_nascimento": "Data de nascimento",
    "idade": "Idade (anos)",
    "faixa_etaria": "Faixa etária",
    "sexo": "Sexo",
    "genero": "Gênero",
    "cor_raca_etnia": "Cor / raça / etnia",
    "escolaridade": "Escolaridade",
    "ocupacao": "Ocupação",
    "estado_civil": "Estado civil",
    "endereco": "Endereço",
    "bairro": "Bairro",
    "telefone": "Telefone",
    "tipo_residencia": "Tipo de residência",
    "anos_residencia": "Anos de residência",
    "acesso_agua": "Acesso à água",
    "acesso_esgoto": "Acesso ao esgoto",
    "acesso_energia": "Acesso à energia",
    "numero_filhos": "Número de filhos",
    "numero_membros_familia": "Membros da família",
    "renda_bruta_total": "Renda bruta total",
    "renda_per_capita": "Renda per capita",
    "ja_teve_hanseniase": "Já teve hanseníase",
    "situacao_hanseniase": "Situação (hanseníase)",
    "ano_diagnostico_hanseniase": "Ano do diagnóstico",
    "classificacao_operacional": "Classificação operacional",
    "forma_clinica": "Forma clínica",
    "numero_lesoes": "Número de lesões",
    "nervos_afetados": "Nervos afetados",
    "grau_incapacidade": "Grau de incapacidade",
    "projeto_acao": "Projeto / ação",
    "responsavel_preenchimento": "Responsável pelo preenchimento",
    "responsavel_entrevista": "Responsável pela entrevista",
}

_COLS_MOEDA = frozenset({"renda_bruta_total", "renda_per_capita"})


def _is_missing(v) -> bool:
    if v is None:
        return True
    try:
        if pd.isna(v):
            return True
    except (TypeError, ValueError):
        pass
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return True
    if isinstance(v, str):
        s = v.strip()
        if not s or s.lower() == "nan":
            return True
        if s == LABEL_NULO:
            return True
    return False


def _format_moeda(v: float) -> str:
    s = f"{abs(v):.2f}"
    partes = s.split(".")
    inteiro = partes[0]
    frac = partes[1] if len(partes) > 1 else "00"
    rev = inteiro[::-1]
    blocos = [rev[i : i + 3] for i in range(0, len(rev), 3)]
    inteiro_fmt = ".".join(b[::-1] for b in reversed(blocos))
    prefix = "-" if v < 0 else ""
    return f"{prefix}R$ {inteiro_fmt},{frac}"


def valor_exibicao(v, *, col: str | None = None) -> str:
    """Texto seguro para UI; ausentes viram NA_EXIBICAO."""
    if _is_missing(v):
        return NA_EXIBICAO
    if isinstance(v, pd.Timestamp):
        return v.strftime("%d/%m/%Y")
    if hasattr(v, "to_pydatetime") and callable(v.to_pydatetime):
        try:
            return v.to_pydatetime().strftime("%d/%m/%Y")
        except (AttributeError, ValueError, OSError):
            pass
    if isinstance(v, bool):
        return "Sim" if v else "Não"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if col in _COLS_MOEDA:
            return _format_moeda(float(v))
        if isinstance(v, float) and abs(v - round(v)) < 1e-6:
            return str(int(round(v)))
        if isinstance(v, float):
            return f"{v:.1f}".rstrip("0").rstrip(".")
        return str(int(v))
    s = str(v).strip()
    if s == LABEL_NULO:
        return NA_EXIBICAO
    if col == "data_nascimento":
        parsed = pd.to_datetime(s, dayfirst=True, errors="coerce")
        if pd.notna(parsed):
            return parsed.strftime("%d/%m/%Y")
        return s if s else NA_EXIBICAO
    return s


def filtrar_por_busca(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Substring no nome (sem case) e/ou no CPF (compara dígitos). Query vazia = sem filtro."""
    if df is None or df.empty:
        return df.copy() if df is not None else pd.DataFrame()

    q = (query or "").strip()
    if not q:
        return df.copy()

    q_lower = q.lower()
    q_digits = re.sub(r"\D", "", q)
    mask = pd.Series(False, index=df.index)

    if "nome_completo" in df.columns:
        nomes = df["nome_completo"].map(lambda x: str(x).lower() if pd.notna(x) else "")
        mask = mask | nomes.str.contains(q_lower, na=False, regex=False)

    if "cpf" in df.columns:
        cpfs_digits = df["cpf"].map(
            lambda x: re.sub(r"\D", "", str(x)) if pd.notna(x) else ""
        )
        if q_digits:
            mask = mask | cpfs_digits.str.contains(q_digits, na=False, regex=False)
        else:
            cpfs_raw = df["cpf"].map(lambda x: str(x).lower() if pd.notna(x) else "")
            mask = mask | cpfs_raw.str.contains(q_lower, na=False, regex=False)

    return df.loc[mask].copy()


def rotulo_linha_select(row: pd.Series) -> str:
    nome_raw = row.get("nome_completo")
    nome = str(nome_raw).strip() if pd.notna(nome_raw) else ""
    if not nome or nome.lower() == "nan":
        nome = NA_EXIBICAO
    cpf_raw = row.get("cpf")
    if pd.notna(cpf_raw) and str(cpf_raw).strip():
        return f"{nome} — CPF: {str(cpf_raw).strip()}"
    return f"{nome} — CPF não informado"


def idade_para_metric(row: pd.Series) -> float | None:
    """Idade numérica para st.metric, ou None se não houver."""
    if "idade" not in row.index:
        return None
    v = row["idade"]
    if _is_missing(v):
        return None
    try:
        f = float(v)
        if math.isnan(f):
            return None
        return f
    except (TypeError, ValueError):
        return None
