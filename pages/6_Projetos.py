import streamlit as st
import utils.auth as auth
import uuid
import pandas as pd
from datetime import datetime

from utils.data import (
    load_sheet_data,
    update_sheet_data,
    refresh_after_sheet_mutation,
    get_beneficiarios_por_projeto,
)
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
    return load_sheet_data("Projetos")


def _beneficiarios_do_projeto(mapa, nome_projeto):
    """Associa o nome do projeto na planilha Projetos às chaves do mapa (strip, case-insensitive)."""
    if pd.isna(nome_projeto):
        return []
    np = str(nome_projeto).strip()
    if not np:
        return []
    if np in mapa:
        return mapa[np]
    npl = np.lower()
    for k, v in mapa.items():
        if str(k).strip().lower() == npl:
            return v
    return []

def validate_form(projeto, esta_ativo):
    campos_obrigatorios = {
        "projeto": projeto,
        "esta_ativo": esta_ativo
    }
    
    campos_vazios = [campo for campo, valor in campos_obrigatorios.items() if not valor]
    
    if campos_vazios:
        st.warning(f"Por favor, preencha os seguintes campos obrigatórios: {', '.join(campos_vazios)}")
    else:
        return True

def save_project(projeto, esta_ativo, descricao, principal_responsavel):
    try:
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

        if not update_sheet_data("Projetos", dados_projeto):
            return False
        refresh_after_sheet_mutation(
            toast_message=f"Projeto '{projeto}' cadastrado com sucesso!"
        )
        return True
    except Exception as e:
        st.error(f"Erro ao salvar projeto: {str(e)}")
        return False

def find_project_by_id(project_id):
    """Busca projeto pelo ID na planilha"""
    try:
        df = load_sheet_data("Projetos")
        
        if "id" not in df.columns:
            return None
        
        # Buscar projeto pelo ID
        project_row = df[df["id"].str.strip() == project_id.strip()]
        
        if project_row.empty:
            return None
        
        return project_row.iloc[0]
    except Exception as e:
        st.error(f"Erro ao buscar projeto: {str(e)}")
        return None

def delete_project(project_id):
    """Remove projeto da planilha pelo ID"""
    try:
        df = load_sheet_data("Projetos")
        
        if "id" not in df.columns:
            st.error("Coluna 'id' não encontrada na planilha.")
            return False
        
        # Buscar índice do projeto
        project_index = df[df["id"].str.strip() == project_id.strip()].index
        
        if project_index.empty:
            st.error(f"Projeto com ID {project_id} não encontrado.")
            return False
        
        # Remover o projeto
        df_updated = df.drop(project_index).reset_index(drop=True)
        
        # Escrever de volta para o Google Sheets
        conn.update(data = df_updated, worksheet="Projetos")
        
        # Obter nome do projeto deletado para mensagem
        deleted_project = df.iloc[project_index[0]]
        nome_deletado = deleted_project.get("projeto", project_id)
        
        refresh_after_sheet_mutation(
            toast_message=f"Projeto '{nome_deletado}' (ID: {project_id}) removido com sucesso!"
        )
        return True
    except Exception as e:
        st.error(f"Erro ao deletar projeto: {str(e)}")
        return False

def update_project_status(project_id):
    """Alterna o status do projeto entre Ativo e Inativo"""
    try:
        df = load_sheet_data("Projetos")
        
        if "id" not in df.columns or "esta_ativo" not in df.columns:
            st.error("Colunas necessárias não encontradas na planilha.")
            return False
        
        # Buscar índice do projeto
        project_index = df[df["id"].str.strip() == project_id.strip()].index
        
        if project_index.empty:
            st.error(f"Projeto com ID {project_id} não encontrado.")
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
        refresh_after_sheet_mutation(
            toast_message=f"Projeto '{project_name}' foi {status_text} com sucesso!"
        )
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar status do projeto: {str(e)}")
        return False


@st.dialog("Adicionar Projeto")
def add_project_dialog():
    """Modal com formulário para cadastro de novo projeto."""
    with st.container():
        st.markdown("#### Preencha os dados abaixo:")
        st.caption("Campos obrigatórios estão marcados com *")

        with st.form(key="add_project_dialog_form", clear_on_submit=False):
            projeto = st.text_input(
                "Nome do projeto *",
                placeholder="Nome do projeto",
                help="Digite o nome do projeto que deseja adicionar.",
            )
            esta_ativo = st.selectbox(
                "O projeto está ativo? *",
                ["Sim", "Não"],
                placeholder="Sim",
                help="Selecione se o projeto está ativo no momento.",
            )
            descricao = st.text_area(
                "Descrição",
                placeholder="O que é o projeto?",
                help="Descreva o projeto, o que ele faz, quem são os beneficiários, etc.",
            )
            principal_responsavel = st.text_input(
                "Principal Responsável",
                placeholder="Nome do responsável pelo projeto",
                help="Digite o nome do responsável pelo projeto.",
            )

            col1, col2 = st.columns(2)
            with col1:
                cancel = st.form_submit_button("Cancelar", width='stretch')
            with col2:
                submit = st.form_submit_button("Salvar", type="primary", width='stretch')

            if cancel:
                st.rerun()

            if submit:
                if validate_form(projeto, esta_ativo) and save_project(projeto, esta_ativo, descricao, principal_responsavel):
                    return "saved"


@st.dialog("Excluir Projeto")
def delete_project_dialog():
    """Modal para buscar e excluir projeto por ID."""
    for key in ("delete_project_dialog_project", "delete_project_dialog_confirm", "delete_project_dialog_id"):
        if key not in st.session_state:
            st.session_state[key] = None if "project" in key or "confirm" in key else ""

    with st.container():
        st.markdown("#### Buscar projeto por ID:")
        st.caption("Digite o ID do projeto que deseja remover")

        with st.form(key="delete_project_dialog_form", clear_on_submit=False):
            project_id = st.text_input(
                "ID do projeto *",
                placeholder="Digite o ID do projeto...",
                help="Digite o ID único do projeto que deseja remover",
                value=st.session_state.get("delete_project_dialog_id", ""),
            )

            col1, col2 = st.columns(2)
            with col1:
                cancel = st.form_submit_button("Cancelar", width='stretch')
            with col2:
                search = st.form_submit_button("Buscar", type="primary", width='stretch')

            if cancel:
                st.rerun()

            if search:
                if not project_id:
                    st.warning("Por favor, digite um ID para buscar.")
                    st.session_state["delete_project_dialog_id"] = ""
                else:
                    st.session_state["delete_project_dialog_id"] = project_id
                    project = find_project_by_id(project_id)
                    if project is not None:
                        st.session_state["delete_project_dialog_project"] = project
                        st.session_state["delete_project_dialog_confirm"] = True
                    else:
                        st.error(f"Nenhum projeto encontrado com o ID: {project_id}")
                        st.session_state["delete_project_dialog_project"] = None
                        st.session_state["delete_project_dialog_confirm"] = False

    project = st.session_state.get("delete_project_dialog_project")
    if project is not None:
        st.markdown("---")
        st.markdown("#### Projeto encontrado:")
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
        if "descricao" in project and pd.notna(project.get("descricao")):
            st.markdown("---")
            st.markdown(f"**Descrição:** {project.get('descricao', 'N/A')}")

    if st.session_state.get("delete_project_dialog_confirm") and st.session_state.get("delete_project_dialog_project") is not None:
        st.markdown("---")
        st.warning("**ATENÇÃO:** Esta ação não pode ser desfeita!")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cancelar Exclusão", width='stretch'):
                st.rerun()

        with col2:
            if st.button("Confirmar Exclusão", type="primary", width='stretch'):
                project_id_to_delete = st.session_state["delete_project_dialog_project"].get("id")
                if delete_project(project_id_to_delete):
                    for key in ("delete_project_dialog_project", "delete_project_dialog_confirm", "delete_project_dialog_id"):
                        st.session_state.pop(key, None)
                    return "deleted"


@st.dialog("Alterar Status do Projeto")
def toggle_status_project_dialog():
    """Modal para buscar projeto e alterar status (Ativo/Inativo)."""
    for key in ("toggle_status_dialog_project", "toggle_status_dialog_confirm", "toggle_status_dialog_id"):
        if key not in st.session_state:
            st.session_state[key] = None if "project" in key or "confirm" in key else ""

    with st.container():
        st.markdown("#### Buscar projeto por ID:")
        st.caption("Digite o ID do projeto para alterar seu status (Ativo/Inativo)")

        with st.form(key="toggle_status_project_dialog_form", clear_on_submit=False):
            project_id = st.text_input(
                "ID do projeto *",
                placeholder="Digite o ID do projeto...",
                help="Digite o ID único do projeto que deseja alterar o status",
                value=st.session_state.get("toggle_status_dialog_id", ""),
            )

            col1, col2 = st.columns(2)
            with col1:
                cancel = st.form_submit_button("Cancelar", width='stretch')
            with col2:
                search = st.form_submit_button("Buscar", type="primary", width='stretch')

            if cancel:
                st.rerun()

            if search:
                if not project_id:
                    st.warning("Por favor, digite um ID para buscar.")
                    st.session_state["toggle_status_dialog_id"] = ""
                else:
                    st.session_state["toggle_status_dialog_id"] = project_id
                    project = find_project_by_id(project_id)
                    if project is not None:
                        st.session_state["toggle_status_dialog_project"] = project
                        st.session_state["toggle_status_dialog_confirm"] = True
                    else:
                        st.error(f"Nenhum projeto encontrado com o ID: {project_id}")
                        st.session_state["toggle_status_dialog_project"] = None
                        st.session_state["toggle_status_dialog_confirm"] = False

    project = st.session_state.get("toggle_status_dialog_project")
    if project is not None:
        current_status = project.get("esta_ativo", "N/A")
        new_status = "Não" if current_status == "Sim" else "Sim"

        st.markdown("---")
        st.markdown("#### Projeto encontrado:")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**ID:** {project.get('id', 'N/A')}")
            st.info(f"**Nome:** {project.get('projeto', 'N/A')}")
            if current_status == "Sim":
                st.success(f"**Status Atual:** Ativo")
            else:
                st.warning(f"**Status Atual:** Inativo")
        with col2:
            st.info(f"**Responsável:** {project.get('principal_responsavel', 'N/A')}")
            st.info(f"**Beneficiados:** {project.get('quantidade_beneficiados', 'N/A')}")
            if "data_cadastro" in project:
                st.info(f"**Cadastrado em:** {project.get('data_cadastro', 'N/A')}")

        st.markdown("---")
        if new_status == "Sim":
            st.info(f"**Novo Status:** Ativo (o projeto será ativado)")
        else:
            st.info(f"**Novo Status:** Inativo (o projeto será desativado)")

    if st.session_state.get("toggle_status_dialog_confirm") and st.session_state.get("toggle_status_dialog_project") is not None:
        st.markdown("---")
        st.warning("**Confirmação de Alteração de Status**")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirmar Alteração", type="primary"):
                project_id_to_update = st.session_state["toggle_status_dialog_project"].get("id")
                if update_project_status(project_id_to_update):
                    for key in ("toggle_status_dialog_project", "toggle_status_dialog_confirm", "toggle_status_dialog_id"):
                        st.session_state.pop(key, None)
                    return "updated"
        with col2:
            if st.button("Cancelar Alteração"):
                st.rerun()


# Tela principal
st.title("Projetos")
st.write("Gerencie os projetos do instituto.")
st.caption("Os projetos cadastrados aparecerão como opção para preenchimento no cadastro de beneficiários.")

st.dataframe(get_projects())

st.markdown("---")
st.markdown("## Gerenciar Projetos")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Adicionar Projeto", type="primary", width='stretch'):
        add_project_dialog()

with col2:
    if st.button("Excluir Projeto", width='stretch'):
        for key in ("delete_project_dialog_project", "delete_project_dialog_confirm", "delete_project_dialog_id"):
            st.session_state.pop(key, None)
        delete_project_dialog()

with col3:
    if st.button("Alterar Status do Projeto", width='stretch'):
        for key in ("toggle_status_dialog_project", "toggle_status_dialog_confirm", "toggle_status_dialog_id"):
            st.session_state.pop(key, None)
        toggle_status_project_dialog()

st.markdown("---")
st.markdown("## Beneficiários por projeto")
st.caption(
    "Lista montada a partir da aba **Dados**: cada beneficiário entra nos projetos "
    "marcados no campo *Projeto/Ação* do cadastro (mesmos nomes da coluna *projeto*)."
)

_mapa_benef = get_beneficiarios_por_projeto()
_df_proj = get_projects()
if _df_proj.empty or "projeto" not in _df_proj.columns:
    st.info("Não há projetos cadastrados para exibir.")
else:
    for _, prow in _df_proj.iterrows():
        pn = prow.get("projeto")
        nomes = _beneficiarios_do_projeto(_mapa_benef, pn)
        label = str(pn).strip() if pd.notna(pn) else "(sem nome)"
        n_b = len(nomes)
        exp_title = f"{label} — {n_b} {'beneficiário' if n_b == 1 else 'beneficiários'}"
        with st.expander(exp_title, expanded=False):
            if nomes:
                st.markdown("\n".join(f"- {n}" for n in nomes))
            else:
                st.caption("Nenhum beneficiário vinculado a este projeto nos cadastros.")



