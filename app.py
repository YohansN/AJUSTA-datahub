import streamlit as st
import pandas as pd
import numpy as np
import time
from streamlit_gsheets import GSheetsConnection
import utils.auth as auth

st.set_page_config(
    page_title="AJUSTA - Data Hub",
    page_icon="🏠",
    layout="wide"
)
            
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
    auth.check_auth()
    show_main_app()

if __name__ == "__main__":
    main()