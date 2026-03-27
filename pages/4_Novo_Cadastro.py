import streamlit as st
import pandas as pd
from datetime import date
import utils.auth as auth

from utils.data import load_sheet_data, clear_data_cache, update_sheet_data, overwrite_sheet_data

auth.check_auth()

def get_projetos_ativos():
    try:
        df_projetos = load_sheet_data("Projetos")
        if df_projetos.empty or "esta_ativo" not in df_projetos.columns:
            return pd.DataFrame()
        projetos_ativos = df_projetos[df_projetos["esta_ativo"].str.strip().str.lower() == "sim"]
        return projetos_ativos
    except Exception:
        return pd.DataFrame()

def get_administradores():
    return load_sheet_data("Autenticação")

def increase_beneficiados_projetos(projetos_selecionados):
    """Incrementa quantidade_beneficiados em 1 para cada projeto selecionado"""
    if not projetos_selecionados:
        return
    
    try:
        df_projetos = load_sheet_data("Projetos")
        
        if df_projetos.empty or "projeto" not in df_projetos.columns:
            return
        
        # Para cada projeto selecionado, incrementar quantidade_beneficiados
        for projeto_nome in projetos_selecionados:
            # Encontrar o índice do projeto pelo nome
            projeto_index = df_projetos[df_projetos["projeto"].str.strip() == projeto_nome.strip()].index
            
            if not projeto_index.empty:
                if "quantidade_beneficiados" in df_projetos.columns:
                    # Converter para numérico se necessário
                    current_value = df_projetos.loc[projeto_index[0], "quantidade_beneficiados"]
                    try:
                        current_value = int(current_value) if pd.notna(current_value) else 0
                    except (ValueError, TypeError):
                        current_value = 0
                    
                    df_projetos.loc[projeto_index[0], "quantidade_beneficiados"] = current_value + 1
        
        if not overwrite_sheet_data("Projetos", df_projetos):
            return
        clear_data_cache()
    except Exception as e:
        st.error(f"Erro ao atualizar quantidade de beneficiados: {str(e)}")

@st.dialog("Beneficiário cadastrado com sucesso!")
def dialog_after_success_save_data(nome_completo):
    st.success(f"Beneficiário **{nome_completo}** cadastrado com sucesso!")
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("Voltar para o dashboard", url="http://localhost:8501/Dashboard")  
    with col2:
        if st.button("Cadastrar outro beneficiário"):
            st.session_state[form_reset_key] += 1
            st.rerun()

#FORMULARIO
st.title("Novo Cadastro de Beneficiário")
st.write("Preencha todos os campos abaixo para cadastrar um novo beneficiário.")

# Chave para controlar quando limpar o formulário
form_reset_key = "form_novo_cadastro_reset"
if form_reset_key not in st.session_state:
    st.session_state[form_reset_key] = 0

form_key = f"novo_cadastro_{st.session_state[form_reset_key]}"

with st.form(key=form_key, clear_on_submit=False):

    st.subheader("Dados Pessoais")
    col1, col2 = st.columns(2)
    
    with col1:
        nome_completo = st.text_input("Nome Completo *", placeholder="Digite o nome completo")
        cpf = st.text_input("CPF *", placeholder="000.000.000-00", max_chars=14)
        rg = st.text_input("RG", placeholder="Digite o RG")
        data_nascimento = st.date_input("Data de Nascimento *", value=None, max_value=date.today(), min_value=date(1900, 1, 1))
        escolaridade = st.selectbox("Escolaridade", ["", "Sem escolaridade / Analfabeto", "Fundamental incompleto", "Fundamental completo", "Médio incompleto", "Médio completo", "Superior incompleto", "Superior completo", "Pós-graduação", "Não informado"])

    with col2:
        sexo = st.selectbox("Sexo *", ["", "Masculino", "Feminino", "Outro"])
        genero = st.selectbox("Gênero", ["", "Cisgênero", "Transgênero", "Não-binário", "Outro"])
        cor_raca_etnia = st.selectbox("Cor/Raça/Etnia", ["", "Branca", "Parda", "Preta", "Amarela", "Indígena", "Não informado"])
        telefone = st.text_input("Telefone", placeholder="(00) 00000-0000", max_chars=15)
        ocupacao = st.selectbox("Ocupação", ["", "Sem ocupação / Desempregado", "Agricultor / Trabalhador rural", "Operário / Trabalhador industrial", "Comerciante / Vendedor", "Prestador de serviços", "Profissional liberal", "Funcionário público", "Estudante", "Aposentado", "Do lar / Dona de casa", "Outro", "Não informado"])

    st.divider()

    st.subheader("Dados Residenciais")
    col1, col2 = st.columns(2)
    
    with col1:
        endereco = st.text_input("Endereço *", placeholder="Rua, Avenida, etc.")
        bairro = st.text_input("Bairro *", placeholder="Nome do bairro")
        anos_residencia = st.number_input("Anos de Residência", min_value=0, max_value=100, value=0)
        tipo_residencia = st.selectbox("Tipo de Residência", ["", "Própria", "Alugada", "Cedida", "Invadida", "Outro"])
    
    with col2:
        acesso_agua = st.selectbox("Acesso à Água", ["", "Sim", "Não", "Parcial"])
        acesso_esgoto = st.selectbox("Acesso ao Esgoto", ["", "Sim", "Não", "Parcial"])
        acesso_energia = st.selectbox("Acesso à Energia Elétrica", ["", "Sim", "Não", "Parcial"])
    
    st.divider()

    st.subheader("Dados Familiares")
    col1, col2 = st.columns(2)
    
    with col1:
        estado_civil = st.selectbox("Estado Civil", ["", "Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"])
        numero_filhos = st.number_input("Número de Filhos", min_value=0, max_value=20, value=0)
    
    with col2:
        numero_membros_familia = st.number_input("Número de Membros da Família", min_value=1, max_value=30, value=1)
        renda_bruta_total = st.number_input("Renda Bruta Total (R$)", min_value=0.0)
        # Calcular renda per capita automaticamente
        if numero_membros_familia > 0:
            renda_per_capita = renda_bruta_total / numero_membros_familia
        else:
            renda_per_capita = 0.0
    st.divider()

    st.subheader("Histórico de Hanseníase")
    col1, col2 = st.columns(2)
    
    with col1:
        ja_teve_hanseniase = st.selectbox("Já teve hanseníase?", ["", "Sim", "Não"])
        ano_diagnostico_hanseniase = st.number_input("Ano aproximado do diagnóstico", min_value=1900, max_value=date.today().year, value=None)
        classificacao_operacional = st.selectbox("Classificação operacional no diagnóstico", ["", "Paucibacilar (PB)", "Multibacilar (MB)", "Não sabe", "Não informado"])
        forma_clinica = st.selectbox("Forma clínica", ["", "Indeterminada", "Tuberculoide", "Dimorfa", "Virchowiana", "Não sabe"])
    
    with col2:
        numero_lesoes = st.selectbox("Número aproximado de lesões na época", ["", "1", "2–5", "6–10", "10+", "Não sabe"])
        nervos_afetados = st.selectbox("Teve nervos afetados?", ["", "Nenhum", "1–2", "3 ou mais", "Não sabe"])
        grau_incapacidade = st.selectbox("Grau de incapacidade após o tratamento", ["", "Grau 0 – sem incapacidade", "Grau 1 – perda de sensibilidade", "Grau 2 – deformidades visíveis", "Não avaliado", "Não sabe"])

    st.divider()

    st.subheader("Relacionamento com o Instituto")
    projetos_ativos_df = get_projetos_ativos()
    projetos_disponiveis = projetos_ativos_df["projeto"].tolist() if not projetos_ativos_df.empty else []
    
    if projetos_disponiveis:
        projeto_acao = st.multiselect(
            "Projeto/Ação",
            options=projetos_disponiveis,
            placeholder="Selecione o(s) projeto(s) ou ação(ões)",
        )
    else:
        st.info("Nenhum projeto ativo disponível no momento.")
        projeto_acao = []

    st.divider()

    st.subheader("Dados do responsável pelo preenchimento")

    st.write(f"Responsável pelo Preenchimento: {st.user.name}")
    responsavel_preenchimento = st.user.name
    responsavel_entrevista = st.text_input("Responsável pela Entrevista", placeholder="Nome do entrevistador")
    
    st.divider()

    submitted = st.form_submit_button("Cadastrar Beneficiário", width='stretch')


def validate_form():
    if submitted:
        # Validação dos campos obrigatórios
        # TODO: Definir campos obrigatórios
        campos_obrigatorios = {
            "Nome Completo": nome_completo,
            "CPF": cpf,
            "Data de Nascimento": data_nascimento,
            "Sexo": sexo,
            "Endereço": endereco,
            "Bairro": bairro,
            "Responsável pelo Preenchimento": responsavel_preenchimento
        }
        
        campos_vazios = [campo for campo, valor in campos_obrigatorios.items() if not valor]
        
        if campos_vazios:
            st.warning(f"Por favor, preencha os seguintes campos obrigatórios: {', '.join(campos_vazios)}")
        else:
            return True

def save_data():
    # Converter lista de projetos para string separada por vírgulas
    projeto_acao_str = ", ".join(projeto_acao) if projeto_acao else ""
    
    dados_beneficiario = pd.DataFrame([{
        "nome_completo": nome_completo,
        "cpf": cpf,
        "rg": rg,
        "data_nascimento": data_nascimento.strftime("%d/%m/%Y") if data_nascimento else "",
        "sexo": sexo,
        "genero": genero,
        "cor_raca_etnia": cor_raca_etnia,
        "escolaridade": escolaridade,
        "ocupacao": ocupacao,
        "endereco": endereco,
        "bairro": bairro,
        "telefone": telefone,
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
        "projeto_acao": projeto_acao_str,
        "ja_teve_hanseniase": ja_teve_hanseniase,
        "ano_diagnostico_hanseniase": ano_diagnostico_hanseniase if ano_diagnostico_hanseniase else "",
        "classificacao_operacional": classificacao_operacional,
        "forma_clinica": forma_clinica,
        "numero_lesoes": numero_lesoes,
        "nervos_afetados": nervos_afetados,
        "grau_incapacidade": grau_incapacidade,
        "responsavel_preenchimento": responsavel_preenchimento,
        "responsavel_entrevista": responsavel_entrevista
    }])

    if not update_sheet_data("Dados", dados_beneficiario):
        st.error("Erro ao salvar dados do beneficiário na planilha.")
        return

    if projeto_acao:
        increase_beneficiados_projetos(projeto_acao)

    dialog_after_success_save_data(nome_completo)

if submitted:
    if validate_form():
        save_data()