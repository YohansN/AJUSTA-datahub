import streamlit as st
import pandas as pd
import numpy as np

from streamlit_gsheets import GSheetsConnection

conn = st.connection("gsheets", type=GSheetsConnection)

df = conn.read()

st.subheader("Preview dos Dados")
st.dataframe(df)
