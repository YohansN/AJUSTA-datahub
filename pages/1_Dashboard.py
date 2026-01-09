import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import utils.auth as auth
from utils.colors import AJUSTA_COLORS, AJUSTA_PALETTE, PALETTE_HANSENIASE, apply_plotly_style

# Verificar autenticação
auth.check_auth()

# Configuração da página
st.set_page_config(
    page_title="Dashboard - AJUSTA",
    page_icon="📊",
    layout="wide"
)

# Carregar dados
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Dados")

st.title("📊 Dashboard - AJUSTA Data Hub")
st.markdown("---")

# Processar dados
def processar_dados(df):
    """Processa e prepara os dados para visualização"""
    df_processed = df.copy()
    
    # Converter data_nascimento para calcular idade
    df_processed['data_nascimento'] = pd.to_datetime(df_processed['data_nascimento'], format='%d/%m/%Y', errors='coerce')
    
    # Calcular idade
    hoje = datetime.now()
    df_processed['idade'] = (hoje - df_processed['data_nascimento']).dt.days / 365.25
    df_processed['idade'] = df_processed['idade'].fillna(0).astype(int)
    
    # Criar faixas etárias
    def categorizar_idade(idade):
        if idade <= 12:
            return '0-12 anos'
        elif idade <= 18:
            return '13-18 anos'
        elif idade <= 30:
            return '19-30 anos'
        elif idade <= 50:
            return '31-50 anos'
        else:
            return '51+ anos'
    
    df_processed['faixa_etaria'] = df_processed['idade'].apply(categorizar_idade)
    
    # Converter renda_per_capita para numérico
    df_processed['renda_per_capita_num'] = pd.to_numeric(df_processed['renda_per_capita'], errors='coerce')
    
    return df_processed

df_processed = processar_dados(df)

# ============================================
# 1. TOTAL DE BENEFICIÁRIOS CADASTRADOS
# ============================================
st.markdown("## 📈 Visão Geral")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total = len(df_processed)
    st.metric("Total de Beneficiários", total)

with col2:
    renda_media = df_processed['renda_per_capita_num'].mean()
    st.metric("Renda Per Capita Média", f"R$ {renda_media:.2f}")

with col3:
    familias = df_processed['numero_membros_familia'].sum()
    st.metric("Pessoas Beneficiadas", familias)

with col4:
    projetos = df_processed['projeto_acao'].nunique()
    st.metric("Projetos Ativos", projetos)

st.markdown("---")

# ============================================
# 2. DISTRIBUIÇÃO POR SEXO/GÊNERO
# ============================================
st.markdown("## 👥 Distribuição Demográfica")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Por Sexo")
    sexo_counts = df_processed['sexo'].value_counts()
    
    fig_sexo = px.pie(
        values=sexo_counts.values,
        names=sexo_counts.index,
        title="Distribuição por Sexo",
        color_discrete_sequence=AJUSTA_PALETTE
    )
    fig_sexo.update_traces(
        textposition='inside',
        textinfo='percent+label',
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )
    fig_sexo = apply_plotly_style(fig_sexo)
    st.plotly_chart(fig_sexo, use_container_width=True)

with col2:
    st.markdown("### Por Gênero")
    genero_counts = df_processed['genero'].value_counts()
    
    fig_genero = px.pie(
        values=genero_counts.values,
        names=genero_counts.index,
        title="Distribuição por Gênero",
        color_discrete_sequence=AJUSTA_PALETTE
    )
    fig_genero.update_traces(
        textposition='inside',
        textinfo='percent+label',
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )
    fig_genero = apply_plotly_style(fig_genero)
    st.plotly_chart(fig_genero, use_container_width=True)

# ============================================
# 3. DISTRIBUIÇÃO POR FAIXA ETÁRIA
# ============================================
st.markdown("### Por Faixa Etária")
faixa_counts = df_processed['faixa_etaria'].value_counts().sort_index()

fig_idade = px.bar(
    x=faixa_counts.index,
    y=faixa_counts.values,
    title="Distribuição por Faixa Etária",
    labels={'x': 'Faixa Etária', 'y': 'Quantidade'}
)
fig_idade.update_traces(
    marker=dict(line=dict(color=AJUSTA_COLORS['dark'], width=1)),
    marker_color=AJUSTA_COLORS['primary']
)
fig_idade = apply_plotly_style(fig_idade, showlegend=False)
st.plotly_chart(fig_idade, use_container_width=True)

st.markdown("---")

# ============================================
# 4. DISTRIBUIÇÃO POR BAIRRO
# ============================================
st.markdown("## 🏘️ Distribuição Geográfica")
bairro_counts = df_processed['bairro'].value_counts()

fig_bairro = px.bar(
    x=bairro_counts.values,
    y=bairro_counts.index,
    orientation='h',
    title="Beneficiários por Bairro",
    labels={'x': 'Quantidade', 'y': 'Bairro'}
)
fig_bairro.update_traces(
    marker_color=AJUSTA_COLORS['secondary'],
    marker=dict(line=dict(color=AJUSTA_COLORS['dark'], width=0.5))
)
fig_bairro = apply_plotly_style(fig_bairro, showlegend=False)
st.plotly_chart(fig_bairro, use_container_width=True)

st.markdown("---")

# ============================================
# 5. SITUAÇÃO DE MORADIA
# ============================================
st.markdown("## 🏠 Situação de Moradia")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Tipo de Residência")
    moradia_counts = df_processed['tipo_residencia'].value_counts()
    
    fig_moradia = px.pie(
        values=moradia_counts.values,
        names=moradia_counts.index,
        title="Distribuição por Tipo de Residência",
        color_discrete_sequence=AJUSTA_PALETTE
    )
    fig_moradia.update_traces(
        textposition='inside',
        textinfo='percent+label',
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )
    fig_moradia = apply_plotly_style(fig_moradia)
    st.plotly_chart(fig_moradia, use_container_width=True)

with col2:
    st.markdown("### Acesso a Serviços Básicos")
    
    # Preparar dados para gráfico de barras agrupadas
    acesso_agua_counts = df_processed['acesso_agua'].value_counts().to_dict()
    acesso_esgoto_counts = df_processed['acesso_esgoto'].value_counts().to_dict()
    acesso_energia_counts = df_processed['acesso_energia'].value_counts().to_dict()
    
    acesso_df = pd.DataFrame({
        'Água': acesso_agua_counts,
        'Esgoto': acesso_esgoto_counts,
        'Energia': acesso_energia_counts
    }).T
    
    fig_acesso = px.bar(
        acesso_df,
        title="Acesso a Serviços Básicos",
        barmode='group',
        color_discrete_sequence=[AJUSTA_COLORS['primary'], AJUSTA_COLORS['secondary'], AJUSTA_COLORS['accent']]
    )
    fig_acesso = apply_plotly_style(fig_acesso)
    st.plotly_chart(fig_acesso, use_container_width=True)

st.markdown("---")

# ============================================
# 6. PARTICIPAÇÃO EM PROGRAMAS SOCIAIS
# ============================================
st.markdown("## 💼 Programas e Projetos")
projeto_counts = df_processed['projeto_acao'].value_counts()

fig_projeto = px.bar(
    x=projeto_counts.index,
    y=projeto_counts.values,
    title="Distribuição de Beneficiários por Projeto",
    labels={'x': 'Projeto', 'y': 'Quantidade'}
)
fig_projeto.update_traces(
    marker_color=AJUSTA_COLORS['accent'],
    marker=dict(line=dict(color=AJUSTA_COLORS['dark'], width=1))
)
fig_projeto = apply_plotly_style(fig_projeto, showlegend=False, xaxis_tickangle=-45)
st.plotly_chart(fig_projeto, use_container_width=True)

st.markdown("---")

# ============================================
# 7. HISTÓRICO DE HANSENÍASE
# ============================================
st.markdown("## 🏥 Situação de Hanseníase")
col1, col2 = st.columns(2)

with col1:
    # Usar ja_teve_hanseniase para criar categorias
    if 'ja_teve_hanseniase' in df_processed.columns:
        # Mapear valores para categorias mais descritivas
        def categorizar_hanseniase(valor):
            if pd.isna(valor) or valor == "":
                return "Não informado"
            elif valor == "Sim":
                return "Já teve hanseníase"
            elif valor == "Não":
                return "Não possui"
            else:
                return "Não informado"
        
        df_processed['categoria_hanseniase'] = df_processed['ja_teve_hanseniase'].apply(categorizar_hanseniase)
        hanseniase_counts = df_processed['categoria_hanseniase'].value_counts()
    else:
        # Fallback para dados antigos que ainda podem ter situacao_hanseniase
        if 'situacao_hanseniase' in df_processed.columns:
            hanseniase_counts = df_processed['situacao_hanseniase'].value_counts()
        else:
            hanseniase_counts = pd.Series()
    
    if not hanseniase_counts.empty:
        fig_hansen = px.pie(
            values=hanseniase_counts.values,
            names=hanseniase_counts.index,
            title="Situação de Hanseníase",
            color_discrete_sequence=PALETTE_HANSENIASE
        )
        fig_hansen.update_traces(
            textposition='inside',
            textinfo='percent+label',
            marker=dict(line=dict(color='#FFFFFF', width=2))
        )
        fig_hansen = apply_plotly_style(fig_hansen)
        st.plotly_chart(fig_hansen, use_container_width=True)
    else:
        st.info("Nenhum dado de hanseníase disponível.")

with col2:
    st.markdown("### Estatísticas")
    
    if 'ja_teve_hanseniase' in df_processed.columns:
        ja_teve = df_processed[df_processed['ja_teve_hanseniase'] == 'Sim'].shape[0]
        nao_teve = df_processed[df_processed['ja_teve_hanseniase'] == 'Não'].shape[0]
        nao_informado = df_processed[(df_processed['ja_teve_hanseniase'].isna()) | (df_processed['ja_teve_hanseniase'] == '')].shape[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Já teve hanseníase", ja_teve)
            st.metric("Não informado", nao_informado)
        
        with col2:
            st.metric("Não possui", nao_teve)
    else:
        # Fallback para dados antigos
        if 'situacao_hanseniase' in df_processed.columns:
            em_tratamento = df_processed[df_processed['situacao_hanseniase'] == 'Em tratamento'].shape[0]
            curados = df_processed[df_processed['situacao_hanseniase'] == 'Curado'].shape[0]
            sem_registro = df_processed[df_processed['situacao_hanseniase'] == 'Não possui'].shape[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Em Tratamento", em_tratamento)
                st.metric("Sem Registro", sem_registro)
            
            with col2:
                st.metric("Curados", curados)
        else:
            st.info("Nenhum dado disponível.")

st.markdown("---")

# ============================================
# 8. DISTRIBUIÇÃO DE RENDA
# ============================================
st.markdown("## 💰 Distribuição de Renda")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Renda Per Capita")
    
    fig_renda = px.histogram(
        df_processed,
        x='renda_per_capita_num',
        nbins=20,
        title="Distribuição de Renda Per Capita",
        labels={'x': 'Renda (R$)', 'y': 'Quantidade'},
        color_discrete_sequence=[AJUSTA_COLORS['primary']]
    )
    fig_renda.update_traces(
        marker_color=AJUSTA_COLORS['primary'],
        marker=dict(line=dict(color=AJUSTA_COLORS['dark'], width=1))
    )
    fig_renda = apply_plotly_style(fig_renda)
    st.plotly_chart(fig_renda, use_container_width=True)

with col2:
    st.markdown("### Cor/Raça/Etnia")
    raca_counts = df_processed['cor_raca_etnia'].value_counts()
    
    fig_raca = px.bar(
        x=raca_counts.index,
        y=raca_counts.values,
        title="Distribuição por Cor/Raça/Etnia",
        color=raca_counts.values,
        color_continuous_scale='Viridis'
    )
    fig_raca.update_traces(
        marker_color=AJUSTA_COLORS['secondary'],
        marker=dict(line=dict(color=AJUSTA_COLORS['dark'], width=1))
    )
    fig_raca = apply_plotly_style(fig_raca, showlegend=False)
    st.plotly_chart(fig_raca, use_container_width=True)

st.markdown("---")

# ============================================
# 9. Tabela Resumo
# ============================================
st.markdown("## 📋 Resumo dos Dados")

with st.expander("Ver tabela completa de dados"):
    st.dataframe(df_processed, use_container_width=True)