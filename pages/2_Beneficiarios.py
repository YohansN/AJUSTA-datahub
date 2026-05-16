from datetime import date

import pandas as pd
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
from utils.data import load_sheet_data, overwrite_sheet_data, refresh_after_sheet_mutation

def _adjust_project_counts(old_str: str, new_str: str) -> None:
    def _parse(s):
        return {p.strip() for p in str(s).split(",") if p.strip() and p.strip() != "Não informado"}

    adicionados = _parse(new_str) - _parse(old_str)
    removidos = _parse(old_str) - _parse(new_str)
    if not adicionados and not removidos:
        return

    df_proj = load_sheet_data("Projetos")
    if df_proj.empty or "projeto" not in df_proj.columns or "quantidade_beneficiados" not in df_proj.columns:
        return

    for nome, delta in [(n, +1) for n in adicionados] + [(n, -1) for n in removidos]:
        idx = df_proj[df_proj["projeto"].str.strip() == nome].index
        if idx.empty:
            continue
        curr = df_proj.loc[idx[0], "quantidade_beneficiados"]
        try:
            curr = int(curr) if pd.notna(curr) else 0
        except (ValueError, TypeError):
            curr = 0
        df_proj.loc[idx[0], "quantidade_beneficiados"] = max(0, curr + delta)

    overwrite_sheet_data("Projetos", df_proj)


def _get_projetos_ativos() -> list[str]:
    try:
        df = load_sheet_data("Projetos")
        if df.empty or "esta_ativo" not in df.columns:
            return []
        ativos = df[df["esta_ativo"].str.strip().str.lower() == "sim"]
        return ativos["projeto"].tolist() if "projeto" in ativos.columns else []
    except Exception:
        return []


@st.dialog("Editar beneficiário", width="large")
def edit_beneficiario_dialog(row: pd.Series) -> None:
    def _str_val(v) -> str:
        try:
            if pd.isna(v):
                return ""
        except (TypeError, ValueError):
            pass
        s = str(v).strip()
        return "" if s.lower() in ("nan", "<na>") else s

    def _idx(opts: list, val) -> int:
        v = _str_val(val)
        return opts.index(v) if v in opts else 0

    def _int_val(v, default: int = 0) -> int:
        try:
            return int(float(v)) if pd.notna(v) and str(v).strip() not in ("", "nan") else default
        except (ValueError, TypeError):
            return default

    def _float_val(v, default: float = 0.0) -> float:
        try:
            return float(v) if pd.notna(v) and str(v).strip() not in ("", "nan") else default
        except (ValueError, TypeError):
            return default

    # parse data de nascimento
    data_nasc_value = None
    raw_dn = _str_val(row.get("data_nascimento"))
    if raw_dn:
        parsed_dt = pd.to_datetime(raw_dn, dayfirst=True, errors="coerce")
        if pd.notna(parsed_dt):
            data_nasc_value = parsed_dt.date()

    # parse projetos
    proj_raw = _str_val(row.get("projeto_acao"))
    projetos_atuais = [p.strip() for p in proj_raw.split(",") if p.strip() and p.strip() != "Não informado"]

    OPTS_SEXO = ["", "Masculino", "Feminino", "Outro"]
    OPTS_GENERO = ["", "Cisgênero", "Transgênero", "Não-binário", "Outro"]
    OPTS_COR = ["", "Branca", "Parda", "Preta", "Amarela", "Indígena", "Não informado"]
    OPTS_ESCOL = ["", "Sem escolaridade / Analfabeto", "Fundamental incompleto", "Fundamental completo",
                  "Médio incompleto", "Médio completo", "Superior incompleto", "Superior completo",
                  "Pós-graduação", "Não informado"]
    OPTS_OCUP = ["", "Sem ocupação / Desempregado", "Agricultor / Trabalhador rural",
                 "Operário / Trabalhador industrial", "Comerciante / Vendedor",
                 "Prestador de serviços", "Profissional liberal", "Funcionário público",
                 "Estudante", "Aposentado", "Do lar / Dona de casa", "Outro", "Não informado"]
    OPTS_TIPO_RES = ["", "Própria", "Alugada", "Cedida", "Invadida", "Outro"]
    OPTS_AGUA = ["", "Sim", "Não", "Parcial"]
    OPTS_ESGOTO = ["", "Sim", "Não", "Parcial"]
    OPTS_ENERGIA = ["", "Sim", "Não", "Parcial"]
    OPTS_EST_CIVIL = ["", "Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"]
    OPTS_HANSENIASE = ["", "Sim", "Não"]
    OPTS_CLASS_OP = ["", "Paucibacilar (PB)", "Multibacilar (MB)", "Não sabe", "Não informado"]
    OPTS_FORMA_CLIN = ["", "Indeterminada", "Tuberculoide", "Dimorfa", "Virchowiana", "Não sabe"]
    OPTS_LESOES = ["", "1", "2–5", "6–10", "10+", "Não sabe"]
    OPTS_NERVOS = ["", "Nenhum", "1–2", "3 ou mais", "Não sabe"]
    OPTS_GRAU = ["", "Grau 0 – sem incapacidade", "Grau 1 – perda de sensibilidade",
                 "Grau 2 – deformidades visíveis", "Não avaliado", "Não sabe"]

    st.subheader("Dados Pessoais")
    c1, c2 = st.columns(2)
    with c1:
        nome_completo = st.text_input("Nome Completo *", value=_str_val(row.get("nome_completo")))
        cpf = st.text_input(
            "CPF * (identificador — alterar com cuidado)",
            value=_str_val(row.get("cpf")),
            max_chars=14,
        )
        rg = st.text_input("RG", value=_str_val(row.get("rg")))
        data_nascimento = st.date_input(
            "Data de Nascimento *",
            value=data_nasc_value,
            max_value=date.today(),
            min_value=date(1900, 1, 1),
        )
        escolaridade = st.selectbox("Escolaridade", OPTS_ESCOL, index=_idx(OPTS_ESCOL, row.get("escolaridade")))
    with c2:
        sexo = st.selectbox("Sexo *", OPTS_SEXO, index=_idx(OPTS_SEXO, row.get("sexo")))
        genero = st.selectbox("Gênero", OPTS_GENERO, index=_idx(OPTS_GENERO, row.get("genero")))
        cor_raca_etnia = st.selectbox("Cor/Raça/Etnia", OPTS_COR, index=_idx(OPTS_COR, row.get("cor_raca_etnia")))
        telefone = st.text_input("Telefone", value=_str_val(row.get("telefone")), max_chars=15)
        ocupacao = st.selectbox("Ocupação", OPTS_OCUP, index=_idx(OPTS_OCUP, row.get("ocupacao")))

    st.divider()
    st.subheader("Dados Residenciais")
    c1, c2 = st.columns(2)
    with c1:
        endereco = st.text_input("Endereço *", value=_str_val(row.get("endereco")))
        bairro = st.text_input("Bairro *", value=_str_val(row.get("bairro")))
        anos_residencia = st.number_input("Anos de Residência", min_value=0, max_value=100,
                                          value=_int_val(row.get("anos_residencia")))
        tipo_residencia = st.selectbox("Tipo de Residência", OPTS_TIPO_RES,
                                       index=_idx(OPTS_TIPO_RES, row.get("tipo_residencia")))
    with c2:
        acesso_agua = st.selectbox("Acesso à Água", OPTS_AGUA, index=_idx(OPTS_AGUA, row.get("acesso_agua")))
        acesso_esgoto = st.selectbox("Acesso ao Esgoto", OPTS_ESGOTO,
                                     index=_idx(OPTS_ESGOTO, row.get("acesso_esgoto")))
        acesso_energia = st.selectbox("Acesso à Energia Elétrica", OPTS_ENERGIA,
                                      index=_idx(OPTS_ENERGIA, row.get("acesso_energia")))

    st.divider()
    st.subheader("Dados Familiares")
    c1, c2 = st.columns(2)
    with c1:
        estado_civil = st.selectbox("Estado Civil", OPTS_EST_CIVIL,
                                    index=_idx(OPTS_EST_CIVIL, row.get("estado_civil")))
        numero_filhos = st.number_input("Número de Filhos", min_value=0, max_value=20,
                                        value=_int_val(row.get("numero_filhos")))
    with c2:
        numero_membros_familia = st.number_input("Número de Membros da Família", min_value=1, max_value=30,
                                                 value=max(1, _int_val(row.get("numero_membros_familia"), 1)))
        renda_bruta_total = st.number_input("Renda Bruta Total (R$)", min_value=0.0,
                                            value=_float_val(row.get("renda_bruta_total")))

    st.divider()
    st.subheader("Histórico de Hanseníase")
    c1, c2 = st.columns(2)
    with c1:
        ja_teve_hanseniase = st.selectbox("Já teve hanseníase?", OPTS_HANSENIASE,
                                          index=_idx(OPTS_HANSENIASE, row.get("ja_teve_hanseniase")))
        situacao_hanseniase = st.text_input("Situação (hanseníase)",
                                            value=_str_val(row.get("situacao_hanseniase")))
        ano_raw = row.get("ano_diagnostico_hanseniase")
        try:
            ano_val = int(float(ano_raw)) if pd.notna(ano_raw) and str(ano_raw).strip() not in ("", "nan") else None
        except (ValueError, TypeError):
            ano_val = None
        ano_diagnostico_hanseniase = st.number_input(
            "Ano aproximado do diagnóstico",
            min_value=1900, max_value=date.today().year, value=ano_val,
        )
        classificacao_operacional = st.selectbox("Classificação operacional", OPTS_CLASS_OP,
                                                 index=_idx(OPTS_CLASS_OP, row.get("classificacao_operacional")))
        forma_clinica = st.selectbox("Forma clínica", OPTS_FORMA_CLIN,
                                     index=_idx(OPTS_FORMA_CLIN, row.get("forma_clinica")))
    with c2:
        numero_lesoes = st.selectbox("Número aproximado de lesões", OPTS_LESOES,
                                     index=_idx(OPTS_LESOES, row.get("numero_lesoes")))
        nervos_afetados = st.selectbox("Nervos afetados?", OPTS_NERVOS,
                                       index=_idx(OPTS_NERVOS, row.get("nervos_afetados")))
        grau_incapacidade = st.selectbox("Grau de incapacidade", OPTS_GRAU,
                                         index=_idx(OPTS_GRAU, row.get("grau_incapacidade")))

    st.divider()
    st.subheader("Relacionamento com o Instituto")
    projetos_disponiveis = _get_projetos_ativos()
    for p in projetos_atuais:
        if p not in projetos_disponiveis:
            projetos_disponiveis.append(p)
    if projetos_disponiveis:
        projeto_acao = st.multiselect("Projeto/Ação", options=projetos_disponiveis,
                                      default=[p for p in projetos_atuais if p in projetos_disponiveis])
    else:
        st.info("Nenhum projeto ativo disponível.")
        projeto_acao = []

    st.divider()
    st.subheader("Responsável")
    resp_orig = _str_val(row.get("responsavel_preenchimento"))
    st.info(f"Responsável pelo preenchimento: **{resp_orig or 'Não informado'}**")
    responsavel_entrevista = st.text_input("Responsável pela Entrevista",
                                           value=_str_val(row.get("responsavel_entrevista")))

    submitted = st.button("Salvar alterações", type="primary", use_container_width=True)

    if submitted:
        if not nome_completo.strip():
            st.error("Nome completo é obrigatório.")
            return
        if not cpf.strip():
            st.error("CPF é obrigatório para identificar o registro.")
            return

        df_raw = load_sheet_data("Dados")
        cpf_val = str(row.get("cpf", "")).strip()
        matches = df_raw[df_raw["cpf"].str.strip() == cpf_val]
        if matches.empty:
            st.error("CPF não encontrado na planilha. Recarregue a página e tente novamente.")
            return

        i = matches.index[0]
        old_proj = str(df_raw.loc[i, "projeto_acao"]) if "projeto_acao" in df_raw.columns else ""
        new_proj = ", ".join(projeto_acao) if projeto_acao else ""

        renda_per_capita = renda_bruta_total / numero_membros_familia if numero_membros_familia > 0 else 0.0

        updates = {
            "nome_completo": nome_completo.strip(),
            "cpf": cpf.strip(),
            "rg": rg.strip(),
            "data_nascimento": data_nascimento.strftime("%d/%m/%Y") if data_nascimento else "",
            "sexo": sexo,
            "genero": genero,
            "cor_raca_etnia": cor_raca_etnia,
            "escolaridade": escolaridade,
            "ocupacao": ocupacao,
            "endereco": endereco.strip(),
            "bairro": bairro.strip(),
            "telefone": telefone.strip(),
            "anos_residencia": anos_residencia,
            "estado_civil": estado_civil,
            "numero_filhos": numero_filhos,
            "numero_membros_familia": numero_membros_familia,
            "renda_bruta_total": renda_bruta_total,
            "renda_per_capita": renda_per_capita,
            "tipo_residencia": tipo_residencia,
            "acesso_agua": acesso_agua,
            "acesso_esgoto": acesso_esgoto,
            "acesso_energia": acesso_energia,
            "projeto_acao": new_proj,
            "ja_teve_hanseniase": ja_teve_hanseniase,
            "situacao_hanseniase": situacao_hanseniase.strip(),
            "ano_diagnostico_hanseniase": ano_diagnostico_hanseniase if ano_diagnostico_hanseniase else "",
            "classificacao_operacional": classificacao_operacional,
            "forma_clinica": forma_clinica,
            "numero_lesoes": numero_lesoes,
            "nervos_afetados": nervos_afetados,
            "grau_incapacidade": grau_incapacidade,
            "responsavel_preenchimento": resp_orig,
            "responsavel_entrevista": responsavel_entrevista.strip(),
        }
        for col, val in updates.items():
            if col in df_raw.columns:
                df_raw.loc[i, col] = val

        if overwrite_sheet_data("Dados", df_raw):
            _adjust_project_counts(old_proj, new_proj)
            refresh_after_sheet_mutation(toast_message=f"Beneficiário {nome_completo.strip()} atualizado com sucesso!")
        else:
            st.error("Erro ao salvar. Tente novamente.")


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

st.divider()
if st.button("Editar beneficiário", type="secondary"):
    edit_beneficiario_dialog(row)
