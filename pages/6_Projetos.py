import streamlit as st
import utils.auth as auth
import uuid
import pandas as pd
from datetime import datetime
import time

from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="AJUSTA - Projetos",
    page_icon="🏠",
    layout="wide"
)

auth.check_auth()

conn = st.connection("gsheets", type=GSheetsConnection)

# Funções para gerenciar os projetos
def get_projects():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Projetos")
    return df

def validate_form(projeto, esta_ativo):
    campos_obrigatorios = {
        "projeto": projeto,
        "esta_ativo": esta_ativo
    }
    
    campos_vazios = [campo for campo, valor in campos_obrigatorios.items() if not valor]
    
    if campos_vazios:
        st.warning(f"❌ Por favor, preencha os seguintes campos obrigatórios: {', '.join(campos_vazios)}")
    else:
        return True

def save_project(projeto, esta_ativo, descricao, principal_responsavel):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        dados_projeto = pd.DataFrame([{
            "id": str(uuid.uuid4()),
            "projeto": projeto,
            "esta_ativo": esta_ativo,
            "descricao": descricao,
            "quantidade_beneficiados": 0,
            "principal_responsavel": principal_responsavel,
            "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "cadastrado_por": st.user.email
        }])

        df = conn.read(worksheet="Projetos")
        updated_df = pd.concat([df, dados_projeto], ignore_index=True)
        conn.update(data = updated_df, worksheet="Projetos")
        st.success(f"✅ Projeto '{projeto}' cadastrado com sucesso!")
        time.sleep(3)
    except Exception as e:
        st.error(f"❌ Erro ao salvar projeto: {str(e)}")
    return False

# Tela principal
st.title("🏠 Projetos")
st.write("Gerencie os projetos do instituto.")
st.caption("Os projetos cadastrados aparecerão como opção para preenchimento no cadastro de beneficiários.")

st.dataframe(get_projects())

with st.expander("🔍 Adicionar Projeto"):
    # Chave única para controlar o estado do formulário
    form_key_base = f"form_add_project"
    reset_key = f"reset_{form_key_base}"
    
    # Inicializar contador de reset para forçar limpeza do form
    if reset_key not in st.session_state:
        st.session_state[reset_key] = 0
    
    # Criar chave única do form baseada no contador de reset
    # Isso força o Streamlit a recriar o formulário quando resetado
    form_key = f"{form_key_base}_{st.session_state[reset_key]}"

    with st.form(key=form_key, clear_on_submit=False):
        st.markdown("#### Preencha os dados abaixo:")
        st.caption("Campos obrigatórios estão marcados com *")
        
        projeto = st.text_input("Nome do projeto *", placeholder="Nome do projeto", help="Digite o nome do projeto que deseja adicionar.")
        esta_ativo = st.selectbox("O projeto está ativo? *", ["Sim", "Não"], placeholder="Sim", help="Selecione se o projeto está ativo no momento.")
        descricao = st.text_area("Descrição", placeholder="O que é o projeto?", help="Descreva o projeto, o que ele faz, quem são os beneficiários, etc.")
        principal_responsavel = st.text_input("Principal Responsável", placeholder="Nome do responsável pelo projeto", help="Digite o nome do responsável pelo projeto.")
            
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Salvar", width='stretch')
        with col2:
            cancel = st.form_submit_button("❌ Cancelar", width='stretch')
            
        if cancel:
            # Incrementar contador para forçar recriação do form limpo
            st.session_state[reset_key] += 1
            st.rerun()
            
        if submit:
            if validate_form(projeto, esta_ativo):
                save_project(projeto, esta_ativo, descricao, principal_responsavel)
                # Limpar formulário após salvar
                st.session_state[reset_key] += 1
                st.rerun()