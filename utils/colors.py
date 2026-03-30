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

# Paleta coesa para o dashboard (contraste sem cores destoantes)
DASHBOARD_CATEGORICAL = [
    '#1a5f7a',
    '#2d8f6f',
    '#0d9488',
    '#c2410c',
    '#4c1d95',
    '#0369a1',
    '#15803d',
]

COR_NAO_INFORMADO = '#6c757d'

DEFAULT_LABEL_NULO = 'Não informado'


def discrete_color_map(
    categories,
    label_nulo: str = DEFAULT_LABEL_NULO,
    palette: list | None = None,
) -> dict:
    """Mapeia cada categoria a uma cor; ``label_nulo`` usa cinza fixo."""
    pal = palette or DASHBOARD_CATEGORICAL
    out = {}
    pi = 0
    for cat in categories:
        key = str(cat)
        if key == label_nulo:
            out[cat] = COR_NAO_INFORMADO
        else:
            out[cat] = pal[pi % len(pal)]
            pi += 1
    return out


def discrete_colors_list(
    categories,
    label_nulo: str = DEFAULT_LABEL_NULO,
    palette: list | None = None,
) -> list:
    """Lista de cores na mesma ordem de ``categories``."""
    m = discrete_color_map(categories, label_nulo=label_nulo, palette=palette)
    return [m[c] for c in categories]

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