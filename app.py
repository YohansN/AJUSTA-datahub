import streamlit as st
import pandas as pd
import numpy as np
import time
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="AJUSTA - Data Hub",
    page_icon="🏠",
    layout="wide"
)

def get_allowed_emails():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Autenticação")
    return df["e-mail"].dropna().tolist()

def validate_login():
    return st.user.email in get_allowed_emails()

def show_login_page():
    """Exibe a página de login"""
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
            
def show_main_app():
    """Exibe a aplicação principal após login bem-sucedido"""
    # Barra superior com informações do usuário
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"### 👋 Bem-vindo, {st.user.name}!")
        st.markdown(f"📧  {st.user.email}")
    
    # TODO: Melhorar esse design
    with col2:
        if st.button("🔄 Atualizar"):
            st.rerun()
        if st.button("🚪 Sair"):
            st.logout()
    
    st.page_link("pages/1_Dashboard.py", label="Dashboard", icon="1️⃣")
    st.page_link("pages/2_Beneficiarios.py", label="Beneficiários ativos", icon="2️⃣")
    st.page_link("pages/3_Detalhes.py", label="Detalhes beneficiários", icon="3️⃣")
    st.page_link("pages/4_Novo_Cadastro.py", label="Cadastro de beneficiários", icon="4️⃣")
    st.page_link("pages/5_Usuarios.py", label="Administração", icon="5️⃣")
    
    st.markdown("---")
    st.info("🎉 Login realizado com sucesso! Você tem acesso ao sistema.")

def main():
    """Fluxo principal da aplicação"""

    if not st.user.is_logged_in:
        show_login_page()
        st.stop()

    if not validate_login():
        show_access_denied()
        st.stop()

    show_main_app()

if __name__ == "__main__":
    main()