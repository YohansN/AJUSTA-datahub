import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

@st.cache_data(ttl=300)
def load_sheet_data(worksheet, force_refresh=False):
    """Carrega dados de uma planilha específica"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet=worksheet)
    return df

def clear_data_cache():
    st.cache_data.clear()

def update_sheet_data(worksheet, new_data):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = load_sheet_data(worksheet)
    updated_df = pd.concat([df, new_data], ignore_index=True)
    conn.update(data = updated_df, worksheet=worksheet)    