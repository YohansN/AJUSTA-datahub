from collections import defaultdict

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

@st.cache_data(ttl=300)
def load_sheet_data(worksheet, force_refresh=False):
    """Carrega dados de uma planilha específica"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet=worksheet)
    return df

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