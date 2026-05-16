from streamlit_gsheets import GSheetsConnection
import streamlit as st
import utils.auth as auth
import pandas as pd
from datetime import datetime

from utils.data import load_sheet_data, update_sheet_data, refresh_after_sheet_mutation

st.set_page_config(
    page_title="AJUSTA - Admin",
    page_icon="⚙️",
    layout="wide"
)

auth.check_auth()

st.title("Administração")
st.write("Gerencie os usuários autorizados do sistema.")

def get_admin_users():
    return load_sheet_data("Autenticação")

def validate_form(nome, email, telefone):
    campos_obrigatorios = {
        "nome": nome,
        "e-mail": email,
        "telefone": telefone
    }
    
    campos_vazios = [campo for campo, valor in campos_obrigatorios.items() if not valor]
    
    if campos_vazios:
        st.warning(f"Por favor, preencha os seguintes campos obrigatórios: {', '.join(campos_vazios)}")
    else:
        return True


def save_admin_user(nome, email, telefone):
    try:
        dados_admin_user = pd.DataFrame([{
            "nome": nome,
            "e-mail": email,
            "telefone": telefone,
            "data cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "cadastrado por": st.user.email
        }])

        if not update_sheet_data("Autenticação", dados_admin_user):
            return False
        refresh_after_sheet_mutation(
            toast_message=f"Administrador(a) {nome} cadastrado com sucesso!"
        )
        return True
    except Exception as e:
        st.error(f"Erro ao salvar usuário: {str(e)}")
    return False


@st.dialog("Adicionar Novo Usuário Administrador")
def add_admin_user_dialog():
    """Modal com formulário para cadastro de novo administrador."""
    with st.container():
        st.markdown("#### Preencha os dados abaixo:")
        st.caption("Campos obrigatórios estão marcados com *")

        with st.form(key="add_admin_user_dialog_form", clear_on_submit=False):
            nome = st.text_input(
                "Nome *",
                placeholder="Nome do administrador",
                help="Digite o nome do usuário administrador que deseja adicionar.",
            )
            email = st.text_input(
                "E-mail *",
                placeholder="usuario@exemplo.com",
                help="Digite o e-mail do usuário administrador que deseja adicionar.",
            )
            telefone = st.text_input(
                "Telefone *",
                placeholder="(00) 00000-0000",
                help="Digite o telefone do usuário administrador que deseja adicionar.",
            )

            col1, col2 = st.columns(2)
            with col1:
                cancel = st.form_submit_button("Cancelar", width='stretch')
            with col2:
                submit = st.form_submit_button("Salvar", type="primary", width='stretch')

            if cancel:
                st.rerun()

            if submit:
                if not validate_form(nome, email, telefone):
                    pass
                elif find_user_by_email(email) is not None:
                    st.warning(
                        "Cada e-mail deve ser único no cadastro."
                    )
                elif save_admin_user(nome, email, telefone):
                    return "saved"


def find_user_by_email(email):
    """Busca usuário pelo email na planilha"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Autenticação")
        
        if "e-mail" not in df.columns:
            return None
        
        # Buscar usuário pelo email (case-insensitive)
        user_row = df[df["e-mail"].str.lower() == email.lower().strip()]
        
        if user_row.empty:
            return None
        
        return user_row.iloc[0]
    except Exception as e:
        st.error(f"Erro ao buscar usuário: {str(e)}")
        return None

def delete_admin_user(email):
    """Remove usuário da planilha pelo email"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Autenticação")
        
        if "e-mail" not in df.columns:
            st.error("Coluna 'e-mail' não encontrada na planilha.")
            return False
        
        # Buscar índice do usuário
        user_index = df[df["e-mail"].str.lower() == email.lower().strip()].index
        
        if user_index.empty:
            st.error(f"Usuário com email {email} não encontrado.")
            return False
        
        # Remover o usuário
        df_updated = df.drop(user_index).reset_index(drop=True)
        
        # Escrever de volta para o Google Sheets
        conn.update(data = df_updated, worksheet="Autenticação")
        
        # Obter nome do usuário deletado para mensagem
        deleted_user = df.iloc[user_index[0]]
        nome_deletado = deleted_user.get("nome", email)
        
        refresh_after_sheet_mutation(
            toast_message=f"Usuário {nome_deletado} ({email}) removido com sucesso!"
        )
        return True
    except Exception as e:
        st.error(f"Erro ao deletar usuário: {str(e)}")
        return False


@st.dialog("Remover Usuário Administrador")
def remove_admin_user_dialog():
    """Modal com formulário para buscar e remover administrador por e-mail."""
    if "delete_dialog_user" not in st.session_state:
        st.session_state["delete_dialog_user"] = None
    if "delete_dialog_confirm" not in st.session_state:
        st.session_state["delete_dialog_confirm"] = False
    if "delete_dialog_email" not in st.session_state:
        st.session_state["delete_dialog_email"] = ""

    with st.container():
        st.markdown("#### Buscar usuário por e-mail:")
        st.caption("Digite o e-mail do usuário que deseja remover")

        with st.form(key="remove_admin_user_dialog_form", clear_on_submit=False):
            email = st.text_input(
                "E-mail do usuário *",
                placeholder="usuario@exemplo.com",
                help="Digite o e-mail do usuário que deseja remover",
                value=st.session_state.get("delete_dialog_email", ""),
            )

            col1, col2 = st.columns(2)
            with col1:
                cancel = st.form_submit_button("Cancelar", width='stretch')
            with col2:
                search = st.form_submit_button("Buscar", type="primary", width='stretch')

            if cancel:
                st.rerun()

            if search:
                if not email:
                    st.warning("Por favor, digite um e-mail para buscar.")
                    st.session_state["delete_dialog_email"] = ""
                else:
                    st.session_state["delete_dialog_email"] = email
                    user = find_user_by_email(email)
                    if user is not None:
                        st.session_state["delete_dialog_user"] = user
                        st.session_state["delete_dialog_confirm"] = True
                    else:
                        st.error(f"Nenhum usuário encontrado com o e-mail: {email}")
                        st.session_state["delete_dialog_user"] = None
                        st.session_state["delete_dialog_confirm"] = False

    user = st.session_state.get("delete_dialog_user")
    if user is not None:
        st.markdown("---")
        st.markdown("#### Usuário encontrado:")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Nome:** {user.get('nome', 'N/A')}")
            st.info(f"**E-mail:** {user.get('e-mail', 'N/A')}")
        with col2:
            st.info(f"**Telefone:** {user.get('telefone', 'N/A')}")
            if "data cadastro" in user:
                st.info(f"**Cadastrado em:** {user.get('data cadastro', 'N/A')}")

    if st.session_state.get("delete_dialog_confirm") and st.session_state.get("delete_dialog_user") is not None:
        st.markdown("---")
        st.warning("**ATENÇÃO:** Esta ação não pode ser desfeita!")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirmar Exclusão", type="primary"):
                email_to_delete = st.session_state["delete_dialog_user"].get("e-mail")
                if delete_admin_user(email_to_delete):
                    for key in ("delete_dialog_user", "delete_dialog_confirm", "delete_dialog_email"):
                        st.session_state.pop(key, None)
                    return "deleted"
        with col2:
            if st.button("Cancelar Exclusão"):
                for key in ("delete_dialog_user", "delete_dialog_confirm", "delete_dialog_email"):
                    st.session_state.pop(key, None)
                return

# ----------- UI Components -----------

st.subheader("Usuários autorizados")
st.dataframe(get_admin_users())

st.markdown("---")
st.markdown("## Gerenciar Usuários")

if st.button("Adicionar Novo Usuário Administrador", type="primary", width='stretch'):
    add_admin_user_dialog()

if st.button("Remover Usuário Administrador", width='stretch'):
    for key in ("delete_dialog_user", "delete_dialog_confirm", "delete_dialog_email"):
        st.session_state.pop(key, None)
    remove_admin_user_dialog()