import streamlit as st
import pandas as pd
from datetime import date
import time
import utils.auth as auth

from utils.data import load_sheet_data, clear_data_cache, update_sheet_data
from streamlit_gsheets import GSheetsConnection

auth.check_auth()

st.title("📝 Novo Cadastro de Beneficiário")
st.write("Preencha todos os campos abaixo para cadastrar um novo beneficiário.")

with st.form(key="novo_cadastro", clear_on_submit=True):

    st.subheader("👤 Dados Pessoais")
    col1, col2 = st.columns(2)
    
    with col1:
        nome_completo = st.text_input("Nome Completo *", placeholder="Digite o nome completo")
        cpf = st.text_input("CPF *", placeholder="000.000.000-00", max_chars=14)
        rg = st.text_input("RG", placeholder="Digite o RG")
        data_nascimento = st.date_input("Data de Nascimento *", value=None, max_value=date.today(), min_value=date(1900, 1, 1))

    with col2:
        sexo = st.selectbox("Sexo *", ["", "Masculino", "Feminino", "Outro"])
        genero = st.selectbox("Gênero", ["", "Cisgênero", "Transgênero", "Não-binário", "Outro"])
        cor_raca_etnia = st.selectbox("Cor/Raça/Etnia", ["", "Branca", "Parda", "Preta", "Amarela", "Indígena", "Não informado"])
        telefone = st.text_input("Telefone", placeholder="(00) 00000-0000")

    st.divider()

    st.subheader("🏠 Dados Residenciais")
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

    st.subheader("👨‍👩‍👧‍👦 Dados Familiares")
    col1, col2 = st.columns(2)
    
    with col1:
        estado_civil = st.selectbox("Estado Civil", ["", "Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"])
        numero_filhos = st.number_input("Número de Filhos", min_value=0, max_value=20, value=0)
        numero_membros_familia = st.number_input("Número de Membros da Família", min_value=1, max_value=20, value=1)
        responsavel_familiar = st.text_input("Responsável Familiar", placeholder="Nome do responsável")
    
    with col2:
        renda_bruta_total = st.number_input("Renda Bruta Total (R$)", min_value=0.0, value=0.0, step=1.0)
        renda_per_capita = st.number_input("Renda Per Capita (R$)", min_value=0.0, value=0.0, step=1.0)
    
    st.divider()

    st.subheader("🏥 Dados de Saúde")
    col1, col2 = st.columns(2)
    
    with col1:
        situacao_hanseniase = st.selectbox("Situação Hanseníase", ["", "Não possui", "Em tratamento", "Curado", "Não informado"])
        ano_tratamento_hanseniase = st.number_input("Ano de Tratamento Hanseníase", min_value=1900, max_value=date.today().year, value=None) # VALIDAR
    
    with col2:
        projeto_acao = st.text_input("Projeto/Ação", placeholder="Nome do projeto ou ação") #TODO: Buscar de planilha de projetos e fazer selectbox
    
    st.divider()

    st.subheader("📋 Dados do Responsável")
    col1, col2 = st.columns(2)
    
    with col1:
        responsavel_preenchimento = st.text_input("Responsável pelo Preenchimento *", placeholder="Nome do responsável")
    
    with col2:
        responsavel_entrevista = st.text_input("Responsável pela Entrevista", placeholder="Nome do entrevistador")
    
    st.divider()

    submitted = st.form_submit_button("💾 Cadastrar Beneficiário", use_container_width=True)


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
            st.warning(f"❌ Por favor, preencha os seguintes campos obrigatórios: {', '.join(campos_vazios)}")
        else:
            return True

def save_data():
    dados_beneficiario = pd.DataFrame([{
        "nome_completo": nome_completo,
        "cpf": cpf,
        "rg": rg,
        "data_nascimento": data_nascimento.strftime("%d/%m/%Y") if data_nascimento else "",
        "sexo": sexo,
        "genero": genero,
        "cor_raca_etnia": cor_raca_etnia,
        "endereco": endereco,
        "bairro": bairro,
        "telefone": telefone,
        "anos_residencia": anos_residencia,
        "estado_civil": estado_civil,
        "numero_filhos": numero_filhos,
        "numero_membros_familia": numero_membros_familia,
        "responsavel_familiar": responsavel_familiar,
        "renda_bruta_total": renda_bruta_total,
        "renda_per_capita": renda_per_capita,
        "tipo_residencia": tipo_residencia,
        "acesso_agua": acesso_agua,
        "acesso_esgoto": acesso_esgoto,
        "acesso_energia": acesso_energia,
        "situacao_hanseniase": situacao_hanseniase,
        "ano_tratamento_hanseniase": ano_tratamento_hanseniase if ano_tratamento_hanseniase else "",
        "projeto_acao": projeto_acao,
        "responsavel_preenchimento": responsavel_preenchimento,
        "responsavel_entrevista": responsavel_entrevista
    }])

    # Envio de dados para o Google Sheets
    update_sheet_data("Dados", dados_beneficiario)

    st.success(f"✅ Beneficiário {nome_completo} cadastrado com sucesso!")
    time.sleep(3)
    clear_data_cache()

if submitted:
    if validate_form():
        save_data()