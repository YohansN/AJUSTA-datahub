from streamlit_gsheets import GSheetsConnection
import streamlit as st
import utils.auth as auth
import pandas as pd
from datetime import datetime
import time

st.set_page_config(
    page_title="AJUSTA - Admin",
    page_icon="⚙️",
    layout="wide"
)

auth.check_auth()

st.title("📊 Administração")
st.write("Gerencie os usuários autorizados do sistema.")

def get_admin_users():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Autenticação")
    return df

def validate_form(nome, email, telefone):
    campos_obrigatorios = {
        "nome": nome,
        "e-mail": email,
        "telefone": telefone
    }
    
    campos_vazios = [campo for campo, valor in campos_obrigatorios.items() if not valor]
    
    if campos_vazios:
        st.warning(f"❌ Por favor, preencha os seguintes campos obrigatórios: {', '.join(campos_vazios)}")
    else:
        return True


def save_admin_user(nome, email, telefone):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        dados_admin_user = pd.DataFrame([{
            "nome": nome,
            "e-mail": email,
            "telefone": telefone,
            "data cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "cadastrado por": st.user.email
        }])

        df = conn.read(worksheet="Autenticação")
        updated_df = pd.concat([df, dados_admin_user], ignore_index=True)
        conn.update(data = updated_df, worksheet="Autenticação")
        st.success(f"✅ Administrador(a) {nome} cadastrado com sucesso!")
        time.sleep(3)
    except Exception as e:
        st.error(f"❌ Erro ao salvar usuário: {str(e)}")
    return False

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
        st.error(f"❌ Erro ao buscar usuário: {str(e)}")
        return None

def delete_admin_user(email):
    """Remove usuário da planilha pelo email"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Autenticação")
        
        if "e-mail" not in df.columns:
            st.error("❌ Coluna 'e-mail' não encontrada na planilha.")
            return False
        
        # Buscar índice do usuário
        user_index = df[df["e-mail"].str.lower() == email.lower().strip()].index
        
        if user_index.empty:
            st.error(f"❌ Usuário com email {email} não encontrado.")
            return False
        
        # Remover o usuário
        df_updated = df.drop(user_index).reset_index(drop=True)
        
        # Escrever de volta para o Google Sheets
        conn.update(data = df_updated, worksheet="Autenticação")
        
        # Obter nome do usuário deletado para mensagem
        deleted_user = df.iloc[user_index[0]]
        nome_deletado = deleted_user.get("nome", email)
        
        st.success(f"✅ Usuário {nome_deletado} ({email}) removido com sucesso!")
        time.sleep(2)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao deletar usuário: {str(e)}")
        return False

def expandable_form_component_simple(title, icon="➕"):
    # Chave única para controlar o estado do formulário
    form_key_base = f"form_{title.lower().replace(' ', '_')}"
    reset_key = f"reset_{form_key_base}"
    
    # Inicializar contador de reset para forçar limpeza do form
    if reset_key not in st.session_state:
        st.session_state[reset_key] = 0
    
    # Criar chave única do form baseada no contador de reset
    # Isso força o Streamlit a recriar o formulário quando resetado
    form_key = f"{form_key_base}_{st.session_state[reset_key]}"
    
    with st.expander(f"{icon} {title}", expanded=False):
        st.markdown("#### Preencha os dados abaixo:")
        st.caption("Campos obrigatórios estão marcados com *")
        
        with st.form(key=form_key, clear_on_submit=False):
            nome = st.text_input("Nome *", placeholder="Nome do administrador", help="Digite o nome do usuário administrador que deseja adicionar como administrador.")
            email = st.text_input("E-mail *", placeholder="usuario@exemplo.com", help="Digite o e-mail do usuário administrador que deseja adicionar como administrador.",)
            telefone = st.text_input("Telefone *", placeholder="(00) 00000-0000", help="Digite o telefone do usuário administrador que deseja adicionar como administrador.")
            
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
                if validate_form(nome, email, telefone):
                    save_admin_user(nome, email, telefone)
                    # Limpar formulário após salvar
                    st.session_state[reset_key] += 1
                    st.rerun()

st.subheader("Usuários autorizados")
st.dataframe(get_admin_users())

st.markdown("---")
st.markdown("## Gerenciar Usuários")

# Componente para adicionar usuário
expandable_form_component_simple("Adicionar Novo Usuário Administrador", icon="➕")

# st.markdown("---")

# Componente para excluir usuário
def expandable_delete_form_component(title, icon="🗑️"):
    """Componente para excluir usuário por email"""
    # Chave única para controlar o estado do formulário
    form_key_base = f"delete_form_{title.lower().replace(' ', '_')}"
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
    
    # Chave para email (baseada no título, não no form_key, para persistir entre resets)
    email_state_key = f"email_{form_key_base}"
    if email_state_key not in st.session_state:
        st.session_state[email_state_key] = ""
    
    with st.expander(f"{icon} {title}", expanded=False):
        st.markdown("#### Buscar usuário por e-mail:")
        st.caption("Digite o e-mail do usuário que deseja remover")
        
        with st.form(key=form_key, clear_on_submit=False):
            email = st.text_input(
                "E-mail do usuário *", 
                placeholder="usuario@exemplo.com",
                help="Digite o e-mail do usuário que deseja remover",
                value=st.session_state[email_state_key]
            )
            
            col1, col2 = st.columns(2)
            with col1:
                search = st.form_submit_button("🔍 Buscar", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        # Processar busca após submit do form
        if search:
            if not email:
                st.warning("❌ Por favor, digite um e-mail para buscar.")
                st.session_state[email_state_key] = ""
            else:
                st.session_state[email_state_key] = email
                user = find_user_by_email(email)
                if user is not None:
                    st.session_state[search_key] = user
                    st.session_state[confirm_key] = True
                else:
                    st.error(f"❌ Nenhum usuário encontrado com o e-mail: {email}")
                    st.session_state[search_key] = None
                    st.session_state[confirm_key] = False
        
        # Mostrar informações do usuário encontrado
        if st.session_state[search_key] is not None:
            user = st.session_state[search_key]
            st.markdown("---")
            st.markdown("#### 👤 Usuário encontrado:")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Nome:** {user.get('nome', 'N/A')}")
                st.info(f"**E-mail:** {user.get('e-mail', 'N/A')}")
            with col2:
                st.info(f"**Telefone:** {user.get('telefone', 'N/A')}")
                if "data cadastro" in user:
                    st.info(f"**Cadastrado em:** {user.get('data cadastro', 'N/A')}")
        
        # Mostrar confirmação de exclusão
        if st.session_state[confirm_key] and st.session_state[search_key] is not None:
            st.markdown("---")
            st.warning("⚠️ **ATENÇÃO:** Esta ação não pode ser desfeita!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Exclusão", use_container_width=True, type="primary"):
                    email_to_delete = st.session_state[search_key].get('e-mail')
                    if delete_admin_user(email_to_delete):
                        # Limpar estados
                        st.session_state[reset_key] += 1
                        st.session_state[confirm_key] = False
                        st.session_state[search_key] = None
                        st.session_state[email_state_key] = ""
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar Exclusão", use_container_width=True):
                    st.session_state[confirm_key] = False
                    st.session_state[search_key] = None
                    st.session_state[email_state_key] = ""
                    st.session_state[reset_key] += 1
                    st.rerun()
        
        # Processar cancelamento do formulário
        if cancel:
            st.session_state[reset_key] += 1
            st.session_state[confirm_key] = False
            st.session_state[search_key] = None
            st.session_state[email_state_key] = ""
            st.rerun()

# Usar o componente de exclusão
expandable_delete_form_component("Remover Usuário Administrador", icon="🗑️")