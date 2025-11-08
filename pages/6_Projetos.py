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
        time.sleep(2)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar projeto: {str(e)}")
        return False

def find_project_by_id(project_id):
    """Busca projeto pelo ID na planilha"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Projetos")
        
        if "id" not in df.columns:
            return None
        
        # Buscar projeto pelo ID
        project_row = df[df["id"].str.strip() == project_id.strip()]
        
        if project_row.empty:
            return None
        
        return project_row.iloc[0]
    except Exception as e:
        st.error(f"❌ Erro ao buscar projeto: {str(e)}")
        return None

def delete_project(project_id):
    """Remove projeto da planilha pelo ID"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Projetos")
        
        if "id" not in df.columns:
            st.error("❌ Coluna 'id' não encontrada na planilha.")
            return False
        
        # Buscar índice do projeto
        project_index = df[df["id"].str.strip() == project_id.strip()].index
        
        if project_index.empty:
            st.error(f"❌ Projeto com ID {project_id} não encontrado.")
            return False
        
        # Remover o projeto
        df_updated = df.drop(project_index).reset_index(drop=True)
        
        # Escrever de volta para o Google Sheets
        conn.update(data = df_updated, worksheet="Projetos")
        
        # Obter nome do projeto deletado para mensagem
        deleted_project = df.iloc[project_index[0]]
        nome_deletado = deleted_project.get("projeto", project_id)
        
        st.success(f"✅ Projeto '{nome_deletado}' (ID: {project_id}) removido com sucesso!")
        time.sleep(2)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao deletar projeto: {str(e)}")
        return False

def update_project_status(project_id):
    """Alterna o status do projeto entre Ativo e Inativo"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Projetos")
        
        if "id" not in df.columns or "esta_ativo" not in df.columns:
            st.error("❌ Colunas necessárias não encontradas na planilha.")
            return False
        
        # Buscar índice do projeto
        project_index = df[df["id"].str.strip() == project_id.strip()].index
        
        if project_index.empty:
            st.error(f"❌ Projeto com ID {project_id} não encontrado.")
            return False
        
        # Obter status atual
        current_status = df.iloc[project_index[0]]["esta_ativo"]
        
        # Alternar status
        new_status = "Não" if current_status == "Sim" else "Sim"
        
        # Atualizar o status
        df.loc[project_index[0], "esta_ativo"] = new_status
        
        # Escrever de volta para o Google Sheets
        conn.update(data = df, worksheet="Projetos")
        
        # Obter nome do projeto para mensagem
        project_name = df.iloc[project_index[0]].get("projeto", project_id)
        
        status_text = "ativado" if new_status == "Sim" else "desativado"
        st.success(f"✅ Projeto '{project_name}' foi {status_text} com sucesso!")
        time.sleep(2)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao atualizar status do projeto: {str(e)}")
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


with st.expander("🗑️ Excluir Projeto"):
    # Chave única para controlar o estado do formulário
    form_key_base = f"form_delete_project"
    reset_key = f"reset_{form_key_base}"
    confirm_key = f"confirm_{form_key_base}"
    search_key = f"search_{form_key_base}"
    
    # Inicializar estados
    if reset_key not in st.session_state:
        st.session_state[reset_key] = 0
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False
    if search_key not in st.session_state:
        st.session_state[search_key] = None
    
    # Criar chave única do form baseada no contador de reset
    form_key = f"{form_key_base}_{st.session_state[reset_key]}"
    
    # Chave para ID (baseada no título, não no form_key, para persistir entre resets)
    id_state_key = f"id_{form_key_base}"
    if id_state_key not in st.session_state:
        st.session_state[id_state_key] = ""
    
    st.markdown("#### Buscar projeto por ID:")
    st.caption("Digite o ID do projeto que deseja remover")
    
    # Chave para rastrear cancelamento
    cancel_key_state = f"cancel_{form_key_base}"
    
    with st.form(key=form_key, clear_on_submit=False):
        project_id = st.text_input(
            "ID do projeto *", 
            placeholder="Digite o ID do projeto...",
            help="Digite o ID único do projeto que deseja remover",
            value=st.session_state[id_state_key]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            search = st.form_submit_button("🔍 Buscar", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        # Processar cancelamento dentro do form
        if cancel:
            st.session_state[cancel_key_state] = True
    
    # Processar cancelamento após submit do form
    if st.session_state.get(cancel_key_state, False):
        st.session_state[reset_key] += 1
        st.session_state[confirm_key] = False
        st.session_state[search_key] = None
        st.session_state[id_state_key] = ""
        st.session_state[cancel_key_state] = False
        st.rerun()
    
    # Processar busca após submit do form
    if search:
        if not project_id:
            st.warning("❌ Por favor, digite um ID para buscar.")
            st.session_state[id_state_key] = ""
        else:
            st.session_state[id_state_key] = project_id
            project = find_project_by_id(project_id)
            if project is not None:
                st.session_state[search_key] = project
                st.session_state[confirm_key] = True
            else:
                st.error(f"❌ Nenhum projeto encontrado com o ID: {project_id}")
                st.session_state[search_key] = None
                st.session_state[confirm_key] = False
    
    # Mostrar informações do projeto encontrado
    if st.session_state[search_key] is not None:
        project = st.session_state[search_key]
        st.markdown("---")
        st.markdown("#### 📋 Projeto encontrado:")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**ID:** {project.get('id', 'N/A')}")
            st.info(f"**Nome:** {project.get('projeto', 'N/A')}")
            st.info(f"**Status:** {project.get('esta_ativo', 'N/A')}")
        with col2:
            st.info(f"**Responsável:** {project.get('principal_responsavel', 'N/A')}")
            st.info(f"**Beneficiados:** {project.get('quantidade_beneficiados', 'N/A')}")
            if "data_cadastro" in project:
                st.info(f"**Cadastrado em:** {project.get('data_cadastro', 'N/A')}")
        
        if "descricao" in project and pd.notna(project.get('descricao')):
            st.markdown("---")
            st.markdown(f"**Descrição:** {project.get('descricao', 'N/A')}")
    
    # Mostrar confirmação de exclusão
    if st.session_state[confirm_key] and st.session_state[search_key] is not None:
        st.markdown("---")
        st.warning("⚠️ **ATENÇÃO:** Esta ação não pode ser desfeita!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar Exclusão", use_container_width=True, type="primary"):
                project_id_to_delete = st.session_state[search_key].get('id')
                if delete_project(project_id_to_delete):
                    # Limpar estados
                    st.session_state[reset_key] += 1
                    st.session_state[confirm_key] = False
                    st.session_state[search_key] = None
                    st.session_state[id_state_key] = ""
                    st.rerun()
        with col2:
            if st.button("❌ Cancelar Exclusão", use_container_width=True):
                st.session_state[confirm_key] = False
                st.session_state[search_key] = None
                st.session_state[id_state_key] = ""
                st.session_state[reset_key] += 1
                st.rerun()

with st.expander("🔄 Alterar Status do Projeto"):
    # Chave única para controlar o estado do formulário
    form_key_base = f"form_toggle_status_project"
    reset_key = f"reset_{form_key_base}"
    confirm_key = f"confirm_{form_key_base}"
    search_key = f"search_{form_key_base}"
    
    # Inicializar estados
    if reset_key not in st.session_state:
        st.session_state[reset_key] = 0
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False
    if search_key not in st.session_state:
        st.session_state[search_key] = None
    
    # Criar chave única do form baseada no contador de reset
    form_key = f"{form_key_base}_{st.session_state[reset_key]}"
    
    # Chave para ID (baseada no título, não no form_key, para persistir entre resets)
    id_state_key = f"id_{form_key_base}"
    if id_state_key not in st.session_state:
        st.session_state[id_state_key] = ""
    
    st.markdown("#### Buscar projeto por ID:")
    st.caption("Digite o ID do projeto para alterar seu status (Ativo/Inativo)")
    
    # Chave para rastrear cancelamento
    cancel_key_state = f"cancel_{form_key_base}"
    
    with st.form(key=form_key, clear_on_submit=False):
        project_id = st.text_input(
            "ID do projeto *", 
            placeholder="Digite o ID do projeto...",
            help="Digite o ID único do projeto que deseja alterar o status",
            value=st.session_state[id_state_key]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            search = st.form_submit_button("🔍 Buscar", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        # Processar cancelamento dentro do form
        if cancel:
            st.session_state[cancel_key_state] = True
    
    # Processar cancelamento após submit do form
    if st.session_state.get(cancel_key_state, False):
        st.session_state[reset_key] += 1
        st.session_state[confirm_key] = False
        st.session_state[search_key] = None
        st.session_state[id_state_key] = ""
        st.session_state[cancel_key_state] = False
        st.rerun()
    
    # Processar busca após submit do form
    if search:
        if not project_id:
            st.warning("❌ Por favor, digite um ID para buscar.")
            st.session_state[id_state_key] = ""
        else:
            st.session_state[id_state_key] = project_id
            project = find_project_by_id(project_id)
            if project is not None:
                st.session_state[search_key] = project
                st.session_state[confirm_key] = True
            else:
                st.error(f"❌ Nenhum projeto encontrado com o ID: {project_id}")
                st.session_state[search_key] = None
                st.session_state[confirm_key] = False
    
    # Mostrar informações do projeto encontrado
    if st.session_state[search_key] is not None:
        project = st.session_state[search_key]
        current_status = project.get('esta_ativo', 'N/A')
        new_status = "Não" if current_status == "Sim" else "Sim"
        
        st.markdown("---")
        st.markdown("#### 📋 Projeto encontrado:")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**ID:** {project.get('id', 'N/A')}")
            st.info(f"**Nome:** {project.get('projeto', 'N/A')}")
            # Mostrar status atual com destaque
            if current_status == "Sim":
                st.success(f"**Status Atual:** 🟢 Ativo")
            else:
                st.warning(f"**Status Atual:** 🔴 Inativo")
        with col2:
            st.info(f"**Responsável:** {project.get('principal_responsavel', 'N/A')}")
            st.info(f"**Beneficiados:** {project.get('quantidade_beneficiados', 'N/A')}")
            if "data_cadastro" in project:
                st.info(f"**Cadastrado em:** {project.get('data_cadastro', 'N/A')}")
        
        # Mostrar mudança de status
        st.markdown("---")
        if new_status == "Sim":
            st.info(f"📝 **Novo Status:** 🟢 Ativo (o projeto será ativado)")
        else:
            st.info(f"📝 **Novo Status:** 🔴 Inativo (o projeto será desativado)")
    
    # Mostrar confirmação de alteração
    if st.session_state[confirm_key] and st.session_state[search_key] is not None:
        project = st.session_state[search_key]
        current_status = project.get('esta_ativo', 'N/A')
        new_status = "Não" if current_status == "Sim" else "Sim"
        
        st.markdown("---")
        st.warning("⚠️ **Confirmação de Alteração de Status**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar Alteração", use_container_width=True, type="primary"):
                project_id_to_update = st.session_state[search_key].get('id')
                if update_project_status(project_id_to_update):
                    # Limpar estados
                    st.session_state[reset_key] += 1
                    st.session_state[confirm_key] = False
                    st.session_state[search_key] = None
                    st.session_state[id_state_key] = ""
                    st.rerun()
        with col2:
            if st.button("❌ Cancelar Alteração", use_container_width=True):
                st.session_state[confirm_key] = False
                st.session_state[search_key] = None
                st.session_state[id_state_key] = ""
                st.session_state[reset_key] += 1
                st.rerun()
    
