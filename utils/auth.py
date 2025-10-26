import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

def get_allowed_emails():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Autenticação")
    return df["e-mail"].dropna().tolist()

def validate_login_authorization():
    """Verifica se o usuário está autorizado a acessar o sistema"""
    return st.user.email in get_allowed_emails()

def show_login_page():
    """Exibe a página de login quando usuário não está logado"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 🏠 AJUSTA - Data Hub")
        st.markdown("---")
        
        # Card de login
        with st.container():
            
            st.markdown("### 🔐 Acesso Restrito")
            st.markdown("Faça login com sua conta Google para acessar o sistema.")
            
            # Botão de login
            if st.button("🔑 Entrar com Google", use_container_width=True, type="primary"):
                st.login()
            
            st.markdown("---")
            st.info("💡 Apenas usuários autorizados podem acessar este sistema.")
            st.caption("Desenvolvido com 💛 por Yohans Nascimento - IFCE Maracanaú")

def show_access_denied():
    """Exibe página de acesso negado"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 🚫 Acesso Negado")
        st.markdown("---")
        
        with st.container():
            st.error("❌ Seu email não está na lista de usuários autorizados.")
            st.warning("💡 Entre em contato com o administrador para solicitar acesso.")
            
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🚪 Fazer Logout", use_container_width=True):
                    st.logout()

def check_auth():
    """Verifica autenticação e exibe mensagens apropriadas"""
    # Verificar se o usuário está logado
    if not st.user.is_logged_in:
        show_login_page()
        st.stop()
    
    # Verificar se o usuário está autorizado
    if not validate_login_authorization():
        show_access_denied()
        st.stop()