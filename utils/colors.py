# Dicionário de cores principais
AJUSTA_COLORS = {
    'primary': '#1f77b4',      # Azul principal
    'secondary': '#2ca02c',    # Verde
    'accent': '#ff7f0e',        # Laranja
    'success': '#2ca02c',      # Verde sucesso
    'warning': '#ffbb00',      # Amarelo
    'danger': '#d62728',       # Vermelho
    'info': '#17a2b8',         # Azul claro
    'light': '#f8f9fa',        # Cinza claro
    'dark': '#343a40'          # Cinza escuro
}

# Paleta de cores para gráficos (array)
AJUSTA_PALETTE = [
    '#1f77b4',  # Azul
    '#2ca02c',  # Verde
    '#ff7f0e',  # Laranja
    '#d62728',  # Vermelho
    '#9467bd',  # Roxo
    '#8c564b',  # Marrom
    '#e377c2',  # Rosa
    '#7f7f7f',  # Cinza
    '#bcbd22',  # Amarelo esverdeado
    '#17becf'   # Ciano
]

# Paleta para gráficos categóricos específicos
PALETTE_MORADIA = ['#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd']
PALETTE_SEXO = ['#1f77b4', '#ff7f0e', '#9467bd']
PALETTE_HANSENIASE = ['#d62728', '#2ca02c', '#ffbb00', '#95a5a6']
PALETTE_RACA = ['#1f77b4', '#2ca02c', '#8c564b', '#9467bd', '#e377c2', '#7f7f7f']

# Configurações de estilo para gráficos Plotly
PLOTLY_STYLE = {
    'font_family': 'Arial',
    'font_size': 12,
    'plot_bgcolor': 'white',
    'paper_bgcolor': 'white',
    'margin': dict(l=50, r=50, t=50, b=50)
}

def apply_plotly_style(fig, **kwargs):
    """Aplica o estilo do AJUSTA a um gráfico Plotly"""
    fig.update_layout(
        font=dict(
            family=PLOTLY_STYLE['font_family'],
            size=PLOTLY_STYLE['font_size']
        ),
        plot_bgcolor=PLOTLY_STYLE['plot_bgcolor'],
        paper_bgcolor=PLOTLY_STYLE['paper_bgcolor'],
        margin=PLOTLY_STYLE['margin'],
        **kwargs
    )
    return fig