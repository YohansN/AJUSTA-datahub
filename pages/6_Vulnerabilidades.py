import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import utils.auth as auth
from utils.colors import AJUSTA_PALETTE, apply_plotly_style
from utils.data import load_sheet_data
from utils.risco_clinico import (
    FEATURE_COLS,
    beneficiarios_com_score,
    label_classopera,
    label_cs_escol_n,
    label_cs_raca,
    label_cs_sexo,
    label_formaclini,
)

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

st.sidebar.divider()
st.sidebar.subheader("Entradas do modelo")

idade_series = pd.to_numeric(df_rank["NU_IDADE_N"], errors="coerce").dropna()
idade_min = int(idade_series.min()) if not idade_series.empty else 0
idade_max = int(idade_series.max()) if not idade_series.empty else 100
if idade_min < idade_max:
    idade_lo, idade_hi = st.sidebar.slider(
        "Idade (anos, NU_IDADE_N)",
        min_value=idade_min,
        max_value=idade_max,
        value=(idade_min, idade_max),
    )
else:
    idade_lo = idade_hi = idade_min
    st.sidebar.caption(f"Idade fixa na base: {idade_min} anos (NU_IDADE_N).")

sexo_opts = sorted(df_rank["CS_SEXO"].dropna().astype(str).unique().tolist())
sel_sexo = st.sidebar.multiselect(
    "Sexo (CS_SEXO)",
    options=sexo_opts,
    format_func=label_cs_sexo,
)

raca_opts = sorted(
    df_rank["CS_RACA"].dropna().unique().tolist(),
    key=lambda x: float(x),
)
sel_raca = st.sidebar.multiselect(
    "Raça / cor (CS_RACA)",
    options=raca_opts,
    format_func=label_cs_raca,
)

esc_opts = sorted(
    df_rank["CS_ESCOL_N"].dropna().unique().tolist(),
    key=lambda x: float(x),
)
sel_escol = st.sidebar.multiselect(
    "Escolaridade codificada (CS_ESCOL_N)",
    options=esc_opts,
    format_func=label_cs_escol_n,
)

lesoes_opts = sorted(
    df_rank["NU_LESOES"].dropna().unique().tolist(),
    key=lambda x: float(x),
)
sel_lesoes = st.sidebar.multiselect("Lesões (NU_LESOES)", options=lesoes_opts)

nervos_opts = sorted(
    df_rank["NERVOSAFET"].dropna().unique().tolist(),
    key=lambda x: float(x),
)
sel_nervos = st.sidebar.multiselect("Nervos afetados (NERVOSAFET)", options=nervos_opts)

class_opts = sorted(
    df_rank["CLASSOPERA"].dropna().unique().tolist(),
    key=lambda x: float(x),
)
sel_class = st.sidebar.multiselect(
    "Classificação operacional (CLASSOPERA)",
    options=class_opts,
    format_func=label_classopera,
)

forma_opts = sorted(
    df_rank["FORMACLINI"].dropna().unique().tolist(),
    key=lambda x: float(x),
)
sel_forma = st.sidebar.multiselect(
    "Forma clínica (FORMACLINI)",
    options=forma_opts,
    format_func=label_formaclini,
)

df_view = df_rank
if sel_cat != "Todas":
    df_view = df_view[df_view["categoria_risco"] == sel_cat]
if sel_bairros:
    df_view = df_view[df_view["bairro"].isin(sel_bairros)]
if sel_faixa:
    df_view = df_view[df_view["faixa_renda"].isin(sel_faixa)]

nu_idade_num = pd.to_numeric(df_view["NU_IDADE_N"], errors="coerce")
df_view = df_view[(nu_idade_num >= idade_lo) & (nu_idade_num <= idade_hi)]
if sel_sexo:
    df_view = df_view[df_view["CS_SEXO"].astype(str).isin(sel_sexo)]
if sel_raca:
    df_view = df_view[df_view["CS_RACA"].isin(sel_raca)]
if sel_escol:
    df_view = df_view[df_view["CS_ESCOL_N"].isin(sel_escol)]
if sel_lesoes:
    df_view = df_view[df_view["NU_LESOES"].isin(sel_lesoes)]
if sel_nervos:
    df_view = df_view[df_view["NERVOSAFET"].isin(sel_nervos)]
if sel_class:
    df_view = df_view[df_view["CLASSOPERA"].isin(sel_class)]
if sel_forma:
    df_view = df_view[df_view["FORMACLINI"].isin(sel_forma)]

display_cols = (
    ["nome_completo", "score_risco_clinico", "categoria_risco"]
    + FEATURE_COLS
    + [
        "renda_per_capita",
        "bairro",
        "tipo_residencia",
        "acesso_agua",
        "acesso_esgoto",
        "acesso_energia",
    ]
)
present = [c for c in display_cols if c in df_view.columns]
df_table = df_view[present].copy()
if "score_risco_clinico" in df_table.columns:
    df_table["score_risco_clinico"] = df_table["score_risco_clinico"].map(
        lambda x: round(float(x), 3) if pd.notna(x) else np.nan
    )
for col in ("NU_IDADE_N", "NU_LESOES", "NERVOSAFET"):
    if col in df_table.columns:
        df_table[col] = pd.to_numeric(df_table[col], errors="coerce").map(
            lambda x: int(x) if pd.notna(x) and float(x) == int(float(x)) else x
        )
for col in ("CLASSOPERA", "CS_RACA", "CS_ESCOL_N", "FORMACLINI"):
    if col in df_table.columns:
        df_table[col] = pd.to_numeric(df_table[col], errors="coerce").map(
            lambda x: int(x) if pd.notna(x) and abs(float(x) - int(float(x))) < 1e-9 else round(float(x), 2)
        )

st.subheader("Ranking")
st.caption(
    "Colunas **NU_***, **CS_***, **CLASSOPERA** e **FORMACLINI** são as **entradas enviadas ao modelo** "
    "(padrão SINAN), derivadas do cadastro — não são os textos brutos de todos os campos da ficha."
)
st.dataframe(df_table, use_container_width=True, hide_index=True)

st.subheader("Visualizações")
st.caption(
    "Os gráficos abaixo consideram **todos** os beneficiários com score (base elegível), "
    "independentemente dos filtros da barra lateral — a tabela de ranking é que reflete os filtros."
)

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
