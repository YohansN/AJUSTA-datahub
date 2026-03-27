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

auth.check_auth()

# Bloco 1: Cabeçalho do usuário (saudação + ações em uma linha compacta)
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### Bem-vindo, {st.user.name}!")
        st.markdown(f"E-mail: {st.user.email}")
    with col2:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col2:
            if st.button("Sair"):
                st.logout()

st.markdown("---")

# Bloco 2: Navegação em grid para melhor escaneabilidade
with st.container():
    st.markdown("## Acesso rápido")
    row1_c1, row1_c2, row1_c3 = st.columns(3)
    with row1_c1:
        st.page_link("pages/1_Dashboard.py", label="Dashboard", width='stretch')
    with row1_c2:
        st.page_link("pages/2_Beneficiarios.py", label="Beneficiários ativos", width='stretch')
    with row1_c3:
        st.page_link("pages/3_Detalhes.py", label="Detalhes beneficiários", width='stretch')
    row2_c1, row2_c2, row2_c3 = st.columns(3)
    with row2_c1:
        st.page_link("pages/4_Novo_Cadastro.py", label="Cadastro de beneficiários", width='stretch')
    with row2_c2:
        st.page_link("pages/5_Administração.py", label="Administração", width='stretch')
    with row2_c3:
        st.page_link("pages/6_Projetos.py", label="Projetos", width='stretch')

st.markdown("---")

# Bloco 3: Mensagem de confirmação de login
with st.container():
    st.info("Login realizado com sucesso! Você tem acesso ao sistema.")
