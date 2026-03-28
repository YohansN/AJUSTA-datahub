import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import utils.auth as auth
from utils.colors import AJUSTA_PALETTE, apply_plotly_style
from utils.data import load_sheet_data
from utils.risco_clinico import beneficiarios_com_score

st.set_page_config(
    page_title="AJUSTA - Vulnerabilidades",
    page_icon="⚕️",
    layout="wide",
)

auth.check_auth()

st.title("Ranking de vulnerabilidade clínica")
st.caption(
    "O **score de risco clínico** é uma estimativa probabilística derivada de modelo treinado "
    "com dados públicos do SINAN (não com dados do instituto). **Não é diagnóstico** — serve para "
    "análises populacionais e priorização institucional."
)

df_raw = load_sheet_data("Dados")
df_full, stats = beneficiarios_com_score(df_raw)

total = stats["total"]
elegiveis = stats["elegiveis"]
com_score = stats["com_score"]
pct = round(100.0 * com_score / total, 1) if total else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("Beneficiários na base", str(total))
c2.metric("Com dados completos para o modelo", str(com_score))
c3.metric("Percentual elegível", f"{pct}%")

if com_score == 0:
    st.warning(
        "Nenhum beneficiário possui todos os campos clínicos preenchidos de forma compatível com o "
        "modelo (sexo M/F, raça, escolaridade, lesões, nervos, classificação PB/MB e forma clínica, "
        "sem “Não sabe”/“Não informado” onde exigido)."
    )
    st.stop()

mask_score = df_full["score_risco_clinico"].notna()
df_rank = df_full.loc[mask_score].copy()
df_rank = df_rank.sort_values("score_risco_clinico", ascending=False)

if "renda_per_capita" in df_rank.columns:
    df_rank["_renda_num"] = pd.to_numeric(df_rank["renda_per_capita"], errors="coerce")
else:
    df_rank["_renda_num"] = np.nan
try:
    df_rank["faixa_renda"] = pd.qcut(
        df_rank["_renda_num"],
        q=4,
        duplicates="drop",
    ).astype(str)
except (ValueError, TypeError):
    df_rank["faixa_renda"] = "—"

st.sidebar.header("Filtros")
cats = ["Todas", "Baixo", "Médio", "Alto"]
sel_cat = st.sidebar.selectbox("Categoria de risco", cats)
if "bairro" in df_rank.columns:
    bairros_opts = sorted(df_rank["bairro"].dropna().unique().tolist(), key=str)
else:
    bairros_opts = []
sel_bairros = st.sidebar.multiselect("Bairro", options=bairros_opts)
faixas_opts = sorted(df_rank["faixa_renda"].dropna().unique().tolist())
sel_faixa = st.sidebar.multiselect("Faixa de renda (quartis)", options=faixas_opts)

df_view = df_rank
if sel_cat != "Todas":
    df_view = df_view[df_view["categoria_risco"] == sel_cat]
if sel_bairros:
    df_view = df_view[df_view["bairro"].isin(sel_bairros)]
if sel_faixa:
    df_view = df_view[df_view["faixa_renda"].isin(sel_faixa)]

display_cols = [
    "nome_completo",
    "score_risco_clinico",
    "categoria_risco",
    "renda_per_capita",
    "escolaridade",
    "bairro",
    "tipo_residencia",
    "acesso_agua",
    "acesso_esgoto",
    "acesso_energia",
]
present = [c for c in display_cols if c in df_view.columns]
df_table = df_view[present].copy()
if "score_risco_clinico" in df_table.columns:
    df_table["score_risco_clinico"] = df_table["score_risco_clinico"].map(
        lambda x: round(float(x), 3) if pd.notna(x) else np.nan
    )

st.subheader("Ranking")
st.dataframe(df_table, use_container_width=True, hide_index=True)

st.subheader("Visualizações")
col_a, col_b = st.columns(2)

agg_renda = (
    df_rank.dropna(subset=["faixa_renda", "score_risco_clinico"])
    .groupby("faixa_renda", observed=True)["score_risco_clinico"]
    .mean()
    .reset_index()
)
agg_renda.columns = ["faixa_renda", "score_medio"]
fig_renda = px.bar(
    agg_renda,
    x="faixa_renda",
    y="score_medio",
    title="Score médio por faixa de renda (quartis)",
    labels={"faixa_renda": "Faixa de renda", "score_medio": "Score médio"},
    color="score_medio",
    color_continuous_scale=AJUSTA_PALETTE,
)
fig_renda = apply_plotly_style(fig_renda, showlegend=False)
col_a.plotly_chart(fig_renda, use_container_width=True)
col_a.caption(
    "**Legenda:** cada barra é a **média do score de risco clínico** entre os beneficiários "
    "com score, agrupados por **quartis da renda per capita** (divisão em quatro faixas com "
    "número parecido de pessoas). Eixo horizontal: intervalo de renda (valores em R$); eixo vertical: "
    "score médio (0 = menor risco estimado, 1 = maior). Ajuda a ver se o risco estimado pelo modelo "
    "varia entre faixas de renda na base elegível."
)

agg_esc = (
    df_rank.dropna(subset=["escolaridade", "score_risco_clinico"])
    .groupby("escolaridade", observed=True)["score_risco_clinico"]
    .mean()
    .reset_index()
)
agg_esc.columns = ["escolaridade", "score_medio"]
fig_esc = px.bar(
    agg_esc,
    x="escolaridade",
    y="score_medio",
    title="Score médio por escolaridade",
    labels={"escolaridade": "Escolaridade", "score_medio": "Score médio"},
    color="score_medio",
    color_continuous_scale=AJUSTA_PALETTE,
)
fig_esc.update_xaxes(tickangle=-35)
fig_esc = apply_plotly_style(fig_esc, showlegend=False)
col_b.plotly_chart(fig_esc, use_container_width=True)
col_b.caption(
    "**Legenda:** cada barra é a **média do score** entre beneficiários com score na mesma "
    "**escolaridade** informada no cadastro. Não é causalidade: mostra apenas como o modelo "
    "distribui probabilidades médias por grupo de escolaridade entre quem tem dados completos."
)

fig_hist = px.histogram(
    df_rank,
    x="score_risco_clinico",
    nbins=30,
    title="Distribuição do score de risco clínico",
    labels={"score_risco_clinico": "Score", "count": "Quantidade"},
)
fig_hist = apply_plotly_style(fig_hist)
st.plotly_chart(fig_hist, use_container_width=True)
st.caption(
    "**Legenda:** **histograma** da distribuição dos scores individuais (cada beneficiário elegível "
    "conta uma vez). O eixo horizontal é o score (0 a 1); a altura das barras é a **quantidade** de "
    "pessoas naquele intervalo. Permite ver se a base está concentrada em baixo, médio ou alto risco "
    "estimado pelo modelo."
)

excluidos = total - com_score
if excluidos > 0:
    st.info(
        f"{excluidos} beneficiário(s) sem score por falta de dados clínicos completos ou mapeáveis."
    )
