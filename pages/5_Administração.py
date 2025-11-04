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
            nome = st.text_input("Nome *", placeholder="Digite o nome...")
            email = st.text_input("E-mail *", placeholder="Digite o e-mail...")
            telefone = st.text_input("Telefone *", placeholder="(00) 00000-0000")
            
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

# Usar o componente
expandable_form_component_simple("Adicionar Novo Usuário Administrador", icon="➕")