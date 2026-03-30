import streamlit as st

import utils.auth as auth
from utils.beneficiario_view import (
    NA_EXIBICAO,
    SECOES_CAMPOS,
    filtrar_por_busca,
    idade_para_metric,
    LABELS_PT,
    rotulo_linha_select,
    valor_exibicao,
)
from utils.dashboard_data import prepare_beneficiarios_dashboard
from utils.data import load_sheet_data

st.set_page_config(
    page_title="Beneficiário — AJUSTA Data Hub",
    page_icon="👤",
    layout="wide",
)

auth.check_auth()

st.title("Consulta de beneficiário")
st.caption(
    "Dados da aba **Dados** da planilha. Use a busca para filtrar por nome ou CPF e selecione a pessoa na lista."
)

df_raw = load_sheet_data("Dados")
if df_raw is None or df_raw.empty:
    st.warning("Não há registros na planilha ou a aba **Dados** está vazia.")
    st.stop()

df_prep = prepare_beneficiarios_dashboard(df_raw)

busca = st.text_input(
    "Buscar por nome ou CPF",
    placeholder="Ex.: Maria ou 12345678901",
    help="Busca por parte do nome (sem diferenciar maiúsculas) ou por sequência numérica do CPF.",
)

if not busca.strip():
    st.info(
        "Digite um termo para filtrar, ou deixe vazio e use a lista abaixo — "
        "todos os beneficiários aparecerão no seletor (pode ser longa em bases grandes)."
    )

filtrado = filtrar_por_busca(df_prep, busca)

if filtrado.empty:
    st.warning("Nenhum beneficiário encontrado para esse termo. Tente outro nome ou CPF.")
    st.stop()

filtrado = filtrado.reset_index(drop=True)
opcoes = list(range(len(filtrado)))
idx = st.selectbox(
    "Selecione o beneficiário",
    options=opcoes,
    format_func=lambda i: rotulo_linha_select(filtrado.iloc[i]),
)

row = filtrado.iloc[idx]

st.divider()
nome_topo = valor_exibicao(row.get("nome_completo"), col="nome_completo")
if nome_topo == NA_EXIBICAO:
    st.subheader("Detalhes")
else:
    st.subheader(nome_topo)

idade_m = idade_para_metric(row)
if idade_m is not None:
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.metric("Idade (anos)", f"{idade_m:.0f}")
    with c2:
        st.metric(
            "Faixa etária",
            valor_exibicao(row.get("faixa_etaria"), col="faixa_etaria"),
        )

for titulo_secao, colunas in SECOES_CAMPOS:
    presentes = [c for c in colunas if c in row.index]
    if not presentes:
        continue

    st.subheader(titulo_secao)
    pares: list[tuple[str, str]] = []
    for col in presentes:
        if titulo_secao == "Identificação" and col == "idade" and idade_m is not None:
            continue
        if titulo_secao == "Identificação" and col == "faixa_etaria" and idade_m is not None:
            continue
        label = LABELS_PT.get(col, col.replace("_", " ").title())
        val = valor_exibicao(row[col], col=col)
        pares.append((label, val))

    if not pares:
        continue

    for i in range(0, len(pares), 2):
        left, right = st.columns(2)
        with left:
            lab, val = pares[i]
            st.markdown(f"**{lab}**")
            st.write(val)
        with right:
            if i + 1 < len(pares):
                lab, val = pares[i + 1]
                st.markdown(f"**{lab}**")
                st.write(val)
