import streamlit as st
import pandas as pd
import plotly.express as px

import utils.auth as auth
from utils.colors import (
    AJUSTA_COLORS,
    apply_plotly_style,
    discrete_color_map,
    discrete_colors_list,
)
from utils.dashboard_data import (
    LABEL_NULO,
    apply_dashboard_filtros,
    count_projetos_explodidos,
    n_projetos_distintos,
    ordenar_faixas_etarias,
    prepare_beneficiarios_dashboard,
    projetos_opcoes_filtro,
)
from utils.data import load_sheet_data

auth.check_auth()

st.set_page_config(
    page_title="Dashboard - AJUSTA",
    page_icon=None,
    layout="wide",
)

df_raw = load_sheet_data("Dados")
df_prep_full = prepare_beneficiarios_dashboard(df_raw)

if "dash_filter_gen" not in st.session_state:
    st.session_state.dash_filter_gen = 0

st.sidebar.header("Filtros")
st.sidebar.caption(
    "Os filtros abaixo restringem **todos** os números e gráficos da página. "
    "Deixe vazio para não filtrar por aquele critério."
)
fg = st.session_state.dash_filter_gen

opts_proj = projetos_opcoes_filtro(df_prep_full)
opts_bairro = sorted(df_prep_full["bairro"].dropna().unique().tolist()) if "bairro" in df_prep_full.columns else []
opts_sexo = sorted(df_prep_full["sexo"].dropna().unique().tolist()) if "sexo" in df_prep_full.columns else []
opts_tipo = (
    sorted(df_prep_full["tipo_residencia"].dropna().unique().tolist())
    if "tipo_residencia" in df_prep_full.columns
    else []
)
opts_hans = (
    sorted(df_prep_full["categoria_hanseniase"].dropna().unique().tolist())
    if "categoria_hanseniase" in df_prep_full.columns
    else []
)

sel_proj = st.sidebar.multiselect("Projeto (qualquer vínculo na linha)", opts_proj, key=f"fproj_{fg}")
sel_bairro = st.sidebar.multiselect("Bairro", opts_bairro, key=f"fbairro_{fg}")
sel_sexo = st.sidebar.multiselect("Sexo", opts_sexo, key=f"fsexo_{fg}")
sel_tipo = st.sidebar.multiselect("Tipo de residência", opts_tipo, key=f"ftipo_{fg}")
sel_hans = st.sidebar.multiselect("Situação de hanseníase", opts_hans, key=f"fhans_{fg}")

if st.sidebar.button("Limpar filtros"):
    st.session_state.dash_filter_gen += 1
    st.rerun()

df_vis = apply_dashboard_filtros(
    df_prep_full,
    projetos=sel_proj or None,
    bairros=sel_bairro or None,
    sexos=sel_sexo or None,
    tipos_residencia=sel_tipo or None,
    categorias_hanseniase=sel_hans or None,
)

st.title("Dashboard — AJUSTA Data Hub")
st.markdown("---")

if df_vis.empty:
    st.warning("Nenhum beneficiário corresponde aos filtros selecionados.")
    st.stop()


def pie_chart(counts: pd.Series, title: str) -> None:
    if counts.empty:
        st.info("Sem dados para este gráfico.")
        return
    cmap = discrete_color_map(counts.index, label_nulo=LABEL_NULO)
    fig = px.pie(
        values=counts.values,
        names=counts.index.astype(str),
        title=title,
        color=counts.index.astype(str),
        color_discrete_map={str(k): v for k, v in cmap.items()},
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        marker=dict(line=dict(color="#FFFFFF", width=2)),
    )
    fig = apply_plotly_style(fig)
    st.plotly_chart(fig, use_container_width=True)


def matriz_acesso(df: pd.DataFrame) -> pd.DataFrame:
    mapping = [
        ("Água", "acesso_agua"),
        ("Esgoto", "acesso_esgoto"),
        ("Energia", "acesso_energia"),
    ]
    series_list = {}
    all_idx = set()
    for label, col in mapping:
        if col not in df.columns:
            continue
        vc = df[col].value_counts()
        series_list[label] = vc
        all_idx.update(vc.index.tolist())
    if not series_list:
        return pd.DataFrame()
    pref = ["Sim", "Não", "Parcial", LABEL_NULO]
    cols_ordered = [x for x in pref if x in all_idx] + sorted(x for x in all_idx if x not in pref)
    return pd.DataFrame(
        {k: v.reindex(cols_ordered).fillna(0).astype(int) for k, v in series_list.items()}
    ).T


tab_visao, tab_demo, tab_moradia, tab_proj_saude, tab_renda = st.tabs(
    [
        "Visão geral",
        "Demografia e localização",
        "Moradia e serviços",
        "Projetos e saúde",
        "Renda e perfil",
    ]
)

with tab_visao:
    st.subheader("Visão geral")
    st.caption(
        "Indicadores calculados sobre o conjunto **já filtrado** (sidebar). "
        "Útil para comparar subgrupos sem alterar a base inteira."
    )
    c1, c2, c3, c4 = st.columns(4)
    n_total = len(df_vis)
    with c1:
        st.metric("Total de beneficiários", n_total)
    with c2:
        r = df_vis["renda_per_capita_num"]
        if r.notna().any():
            st.metric("Renda per capita média", f"R$ {r.mean():.2f}")
        else:
            st.metric("Renda per capita média", "—")
    with c3:
        memb = df_vis["numero_membros_familia_num"]
        if memb.notna().any():
            st.metric("Soma de membros no domicílio (registros)", f"{int(memb.sum(skipna=True))}")
        else:
            st.metric("Soma de membros no domicílio (registros)", "—")
    with c4:
        st.metric("Projetos distintos (citados)", n_projetos_distintos(df_vis))

with tab_demo:
    st.subheader("Demografia")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Sexo")
        s_counts = df_vis["sexo"].value_counts() if "sexo" in df_vis.columns else pd.Series()
        pie_chart(s_counts, "Distribuição por sexo")
        st.caption(
            "Proporção de cadastros por sexo informado. "
            f"“{LABEL_NULO}” inclui campo em branco ou não preenchido na planilha."
        )
    with c2:
        st.markdown("#### Gênero")
        g_counts = df_vis["genero"].value_counts() if "genero" in df_vis.columns else pd.Series()
        pie_chart(g_counts, "Distribuição por gênero")
        st.caption(
            "Autodeclaração de gênero quando informada; valores vazios aparecem como não respondido."
        )

    st.markdown("#### Faixa etária")
    faixa_counts = df_vis["faixa_etaria"].value_counts() if "faixa_etaria" in df_vis.columns else pd.Series()
    order = ordenar_faixas_etarias(faixa_counts.index)
    faixa_ord = faixa_counts.reindex(order).fillna(0).astype(int)
    cmap_faixa = discrete_color_map(faixa_ord.index, label_nulo=LABEL_NULO)
    fig_idade = px.bar(
        x=faixa_ord.index.astype(str),
        y=faixa_ord.values,
        title="Distribuição por faixa etária",
        labels={"x": "Faixa etária", "y": "Quantidade"},
        color=faixa_ord.index.astype(str),
        color_discrete_map={str(k): v for k, v in cmap_faixa.items()},
    )
    fig_idade.update_traces(marker=dict(line=dict(color=AJUSTA_COLORS["dark"], width=1)))
    fig_idade = apply_plotly_style(fig_idade, showlegend=False)
    st.plotly_chart(fig_idade, use_container_width=True)
    st.caption(
        "Idade calculada a partir da data de nascimento quando válida. "
        f"Sem data utilizável, o cadastro entra em “{LABEL_NULO}” (não é imputado como criança)."
    )

    st.subheader("Localização")
    st.markdown("#### Bairro")
    b_counts = df_vis["bairro"].value_counts() if "bairro" in df_vis.columns else pd.Series()
    if b_counts.empty:
        st.info("Sem dados de bairro.")
    else:
        fig_b = px.bar(
            x=b_counts.values,
            y=b_counts.index.astype(str),
            orientation="h",
            title="Beneficiários por bairro",
            labels={"x": "Quantidade", "y": "Bairro"},
        )
        colors_b = discrete_colors_list(b_counts.index, label_nulo=LABEL_NULO)
        fig_b.update_traces(
            marker=dict(color=colors_b, line=dict(color=AJUSTA_COLORS["dark"], width=0.5))
        )
        fig_b = apply_plotly_style(fig_b, showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)
        st.caption(
            "Contagem de cadastros por bairro informado; bairro em branco aparece como não informado."
        )

with tab_moradia:
    st.subheader("Moradia")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Tipo de residência")
        m_counts = (
            df_vis["tipo_residencia"].value_counts() if "tipo_residencia" in df_vis.columns else pd.Series()
        )
        pie_chart(m_counts, "Tipo de residência")
        st.caption("Situação da moradia (própria, alugada, etc.) conforme preenchimento do formulário.")

    with c2:
        st.markdown("#### Acesso a serviços básicos")
        acc_df = matriz_acesso(df_vis)
        if acc_df.empty:
            st.info("Sem colunas de acesso (água, esgoto, energia).")
        else:
            fig_a = px.bar(
                acc_df,
                barmode="group",
                title="Acesso a água, esgoto e energia",
                color_discrete_sequence=discrete_colors_list(acc_df.columns, label_nulo=LABEL_NULO),
            )
            fig_a.update_layout(legend_title_text="Resposta")
            fig_a = apply_plotly_style(fig_a)
            st.plotly_chart(fig_a, use_container_width=True)
            st.caption(
                "Para cada serviço, barras por resposta (Sim, Não, Parcial ou não informado). "
                "Compara condições entre dimensões."
            )

with tab_proj_saude:
    st.subheader("Projetos")
    p_counts = count_projetos_explodidos(df_vis)
    if p_counts.empty:
        st.info("Sem dados de projeto/ação.")
    else:
        fig_p = px.bar(
            x=p_counts.index.astype(str),
            y=p_counts.values,
            title="Participação por projeto (linhas podem citar vários projetos)",
            labels={"x": "Projeto", "y": "Menções"},
            color=p_counts.index.astype(str),
            color_discrete_map={
                str(k): v for k, v in discrete_color_map(p_counts.index, label_nulo=LABEL_NULO).items()
            },
        )
        fig_p.update_traces(marker=dict(line=dict(color=AJUSTA_COLORS["dark"], width=1)))
        fig_p = apply_plotly_style(fig_p, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig_p, use_container_width=True)
        st.caption(
            "Cada menção conta uma vez: um beneficiário em três projetos soma três. "
            f"“{LABEL_NULO}” indica cadastro sem projeto associado."
        )

    st.subheader("Hanseníase")
    h_c1, h_c2 = st.columns(2)
    with h_c1:
        st.markdown("#### Visão geral")
        h_counts = (
            df_vis["categoria_hanseniase"].value_counts()
            if "categoria_hanseniase" in df_vis.columns
            else pd.Series()
        )
        if h_counts.empty:
            st.info("Nenhum dado de hanseníase disponível.")
        else:
            pie_chart(h_counts, "Situação referente à hanseníase")
            st.caption(
                "Com base em “já teve hanseníase?” ou, em cadastros antigos, na coluna de situação clínica."
            )
    with h_c2:
        st.markdown("#### Estatísticas")
        h_tab = (
            df_vis["categoria_hanseniase"].value_counts()
            if "categoria_hanseniase" in df_vis.columns
            else pd.Series(dtype=int)
        )
        if h_tab.empty:
            st.info("Nenhum dado agregado de hanseníase.")
        else:
            nc = min(3, len(h_tab))
            cols_m = st.columns(nc)
            for i, (lab, val) in enumerate(h_tab.items()):
                cols_m[i % nc].metric(str(lab), int(val))

with tab_renda:
    st.subheader("Renda e perfil")
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("#### Renda per capita")
        n_sem = int(df_vis["renda_per_capita_num"].isna().sum())
        st.metric("Cadastros sem renda informada", n_sem)
        if df_vis["renda_per_capita_num"].notna().any():
            fig_r = px.histogram(
                df_vis,
                x="renda_per_capita_num",
                nbins=20,
                title="Distribuição de renda per capita (R$)",
                labels={"renda_per_capita_num": "Renda (R$)", "count": "Quantidade"},
            )
            fig_r.update_traces(
                marker_color=AJUSTA_COLORS["primary"],
                marker=dict(line=dict(color=AJUSTA_COLORS["dark"], width=1)),
            )
            fig_r = apply_plotly_style(fig_r)
            st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.info("Não há valores numéricos de renda para histograma.")
        st.caption(
            "Histograma usa apenas registros com renda numérica válida. "
            "O indicador acima mostra quantos ficaram de fora por valor ausente ou inválido."
        )
    with r2:
        st.markdown("#### Cor / raça / etnia")
        raca_counts = (
            df_vis["cor_raca_etnia"].value_counts() if "cor_raca_etnia" in df_vis.columns else pd.Series()
        )
        if raca_counts.empty:
            st.info("Sem dados de cor/raça/etnia.")
        else:
            cmap_r = discrete_color_map(raca_counts.index, label_nulo=LABEL_NULO)
            fig_ra = px.bar(
                x=raca_counts.index.astype(str),
                y=raca_counts.values,
                title="Distribuição por cor, raça ou etnia",
                labels={"x": "Categoria", "y": "Quantidade"},
                color=raca_counts.index.astype(str),
                color_discrete_map={str(k): v for k, v in cmap_r.items()},
            )
            fig_ra.update_traces(marker=dict(line=dict(color=AJUSTA_COLORS["dark"], width=1)))
            fig_ra = apply_plotly_style(fig_ra, showlegend=False)
            st.plotly_chart(fig_ra, use_container_width=True)
        st.caption("Autodeclaração conforme opções do cadastro; vazios agregados em não informado.")

st.markdown("---")
st.subheader("Resumo dos dados (filtrado)")
with st.expander("Ver tabela completa"):
    st.dataframe(df_vis, use_container_width=True)
