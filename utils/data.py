from collections import defaultdict
import math
import numbers

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd


def _display_str_cell(v):
    """Converte célula de planilha para string segura para exibição (evita tipos mistos int/str)."""
    if v is None:
        return pd.NA
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, numbers.Integral):
        return str(int(v))
    if isinstance(v, float):
        if math.isnan(v):
            return pd.NA
        if v == math.floor(v):
            return str(int(v))
        return str(v)
    if isinstance(v, str):
        s = v.strip()
        return s if s else pd.NA
    try:
        if pd.isna(v):
            return pd.NA
    except (TypeError, ValueError):
        pass
    return str(v).strip()


# Colunas de texto na aba Dados (cadastro); evita Arrow misturando int/str sem forçar numéricas para string.
_DADOS_COERCE_TO_STRING = frozenset({
    "nome_completo", "cpf", "rg", "data_nascimento", "sexo", "genero",
    "cor_raca_etnia", "escolaridade", "ocupacao", "endereco", "bairro",
    "telefone", "tipo_residencia", "acesso_agua", "acesso_esgoto",
    "acesso_energia", "estado_civil", "ja_teve_hanseniase",
    "classificacao_operacional", "forma_clinica", "numero_lesoes",
    "nervos_afetados", "grau_incapacidade", "projeto_acao",
    "responsavel_preenchimento", "responsavel_entrevista",
    "situacao_hanseniase",
})


def normalize_sheet_columns(df, worksheet):
    """
    Na aba ``Dados``, campos de texto vindos do Sheets podem misturar int e str (ex.: ``endereco``,
    ``cpf``); o PyArrow do ``st.dataframe`` falha. Colunas numéricas não entram na lista. Em outras
    abas, só ``cpf``.
    """
    if df is None or df.empty:
        return df
    out = df.copy()
    if worksheet == "Dados":
        for name in list(out.columns):
            key = str(name).lower()
            if key in _DADOS_COERCE_TO_STRING:
                out[name] = out[name].map(_display_str_cell).astype("string")
    else:
        for name in list(out.columns):
            if str(name).lower() == "cpf":
                out[name] = out[name].map(_display_str_cell).astype("string")
    return out


@st.cache_data(ttl=300)
def load_sheet_data(worksheet, force_refresh=False):
    """Carrega dados de uma planilha específica"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet=worksheet)
    return normalize_sheet_columns(df, worksheet)

def clear_data_cache():
    """Remove entradas do ``st.cache_data`` (ex.: leituras de planilha). Não atualiza a UI sozinha."""
    st.cache_data.clear()


def refresh_after_sheet_mutation(*, toast_message=None):
    """
    Limpa o cache de leitura das planilhas e executa ``st.rerun()`` para a interface
    refletir inserções, atualizações ou exclusões.

    Use após mutações bem-sucedidas no Google Sheets. Em páginas com ``@st.dialog``,
    chame esta função **dentro** do fluxo que grava na planilha: após o primeiro clique
    no botão que abre o modal, ``if st.button(...)`` deixa de ser verdadeiro nos runs
    seguintes, então ``st.rerun()`` colocado só no final desse ``if`` nunca dispara.
    """
    if toast_message:
        st.toast(toast_message)
    clear_data_cache()
    st.rerun()

def update_sheet_data(worksheet, new_data):
    """Anexa as linhas de ``new_data`` ao final da aba. Para regravar a aba inteira, use ``overwrite_sheet_data``."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = load_sheet_data(worksheet)
        updated_df = pd.concat([df, new_data], ignore_index=True)
        conn.update(data=updated_df, worksheet=worksheet)
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar planilha: {str(e)}")
        return False


def overwrite_sheet_data(worksheet, df):
    """Substitui todo o conteúdo da aba pelo DataFrame (sem concatenar linhas)."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(data=df, worksheet=worksheet)
        return True
    except Exception as e:
        st.error(f"Erro ao gravar planilha: {str(e)}")
        return False


def get_beneficiarios_por_projeto():
    """
    Lê a aba ``Dados`` e retorna ``dict`` nome_do_projeto -> lista de ``nome_completo``.

    Cada linha de beneficiário pode citar vários projetos na coluna ``projeto_acao``,
    separados por vírgula (mesmo formato do cadastro em Novo Cadastro).
    """
    df = load_sheet_data("Dados")
    if df.empty:
        return {}

    nome_col, proj_col = "nome_completo", "projeto_acao"
    if nome_col not in df.columns or proj_col not in df.columns:
        return {}

    por_projeto = defaultdict(list)
    for _, row in df.iterrows():
        nome = row.get(nome_col)
        if pd.isna(nome):
            continue
        nome = str(nome).strip()
        if not nome:
            continue
        celula = row.get(proj_col)
        if pd.isna(celula):
            continue
        texto = str(celula).strip()
        if not texto:
            continue
        for parte in texto.split(","):
            pn = parte.strip()
            if pn:
                por_projeto[pn].append(nome)

    out = {}
    for projeto, nomes in por_projeto.items():
        vistos = set()
        ordenados = []
        for n in nomes:
            if n not in vistos:
                vistos.add(n)
                ordenados.append(n)
        out[projeto] = ordenados
    return out