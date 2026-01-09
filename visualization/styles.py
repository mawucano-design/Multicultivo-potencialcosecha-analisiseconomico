# visualization/styles.py
import streamlit as st

def aplicar_estilos():
    """Aplica los estilos CSS a la aplicación"""
    st.markdown("""
    <style>
    /* === FONDO GENERAL OSCURO ELEGANTE === */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #ffffff !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* === SIDEBAR: FONDO BLANCO CON TEXTO NEGRO === */
    [data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e5e7eb !important;
        box-shadow: 5px 0 25px rgba(0, 0, 0, 0.1) !important;
    }

    /* Texto general del sidebar en NEGRO */
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stText,
    [data-testid="stSidebar"] .stTitle,
    [data-testid="stSidebar"] .stSubheader {
        color: #000000 !important;
        text-shadow: none !important;
    }

    /* Título del sidebar elegante */
    .sidebar-title {
        font-size: 1.4em;
        font-weight: 800;
        margin: 1.5em 0 1em 0;
        text-align: center;
        padding: 14px;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 16px;
        color: #ffffff !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        letter-spacing: 0.5px;
    }

    /* Widgets del sidebar con estilo glassmorphism */
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stDateInput,
    [data-testid="stSidebar"] .stSlider {
        background: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
        border: 1px solid #d1d5db !important;
    }

    /* Labels de los widgets en negro */
    [data-testid="stSidebar"] .stSelectbox div,
    [data-testid="stSidebar"] .stDateInput div,
    [data-testid="stSidebar"] .stSlider label {
        color: #000000 !important;
        font-weight: 600;
        font-size: 0.95em;
    }

    /* Inputs y selects - fondo blanco con texto negro */
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
        color: #000000 !important;
        border-radius: 8px;
    }

    /* Slider - colores negro */
    [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] {
        color: #000000 !important;
    }

    /* Date Input - fondo blanco con texto negro */
    [data-testid="stSidebar"] .stDateInput [data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
        color: #000000 !important;
        border-radius: 8px;
    }

    /* Placeholder en gris */
    [data-testid="stSidebar"] .stDateInput [data-baseweb="input"]::placeholder {
        color: #6b7280 !important;
    }

    /* Botones premium */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.8em 1.5em !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1em !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.6) !important;
        background: linear-gradient(135deg, #4f8df8 0%, #2d5fe8 100%) !important;
    }

    /* === HERO BANNER PRINCIPAL CON IMAGEN === */
    .hero-banner {
        background: linear-gradient(rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 0.95)),
                    url('https://images.unsplash.com/photo-1597981309443-6e2d2a4d9c3f?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80') !important;
        background-size: cover !important;
        background-position: center 40% !important;
        padding: 3.5em 2em !important;
        border-radius: 24px !important;
        margin-bottom: 2.5em !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .hero-banner::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        background: linear-gradient(45deg, rgba(59, 130, 246, 0.1), rgba(29, 78, 216, 0.05)) !important;
        z-index: 1 !important;
    }

    .hero-content {
        position: relative !important;
        z-index: 2 !important;
        text-align: center !important;
    }

    .hero-title {
        color: #ffffff !important;
        font-size: 3.2em !important;
        font-weight: 900 !important;
        margin-bottom: 0.3em !important;
        text-shadow: 0 4px 12px rgba(0, 0, 0, 0.6) !important;
        letter-spacing: -0.5px !important;
        background: linear-gradient(135deg, #ffffff 0%, #93c5fd 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
    }

    .hero-subtitle {
        color: #cbd5e1 !important;
        font-size: 1.3em !important;
        font-weight: 400 !important;
        max-width: 800px !important;
        margin: 0 auto !important;
        line-height: 1.6 !important;
    }

    /* === PESTAÑAS PRINCIPALES (fuera del sidebar) - SIN CAMBIOS === */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        padding: 8px 16px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        margin-top: 1em !important;
        gap: 8px !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        border-radius: 12px !important;
        background: transparent !important;
        transition: all 0.3s ease !important;
        border: 1px solid transparent !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff !important;
        background: rgba(59, 130, 246, 0.2) !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
        transform: translateY(-2px) !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }

    /* === PESTAÑAS DEL SIDEBAR: FONDO BLANCO + TEXTO NEGRO === */
    [data-testid="stSidebar"] .stTabs [data-baseweb="tab-list"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        padding: 8px !important;
        border-radius: 12px !important;
        gap: 6px !important;
    }

    [data-testid="stSidebar"] .stTabs [data-baseweb="tab"] {
        color: #000000 !important;
        background: transparent !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        border: 1px solid transparent !important;
    }

    [data-testid="stSidebar"] .stTabs [data-baseweb="tab"]:hover {
        background: #f1f5f9 !important;
        color: #000000 !important;
        border-color: #cbd5e1 !important;
    }

    /* Pestaña activa en el sidebar: blanco con texto negro */
    [data-testid="stSidebar"] .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border: 1px solid #3b82f6 !important;
    }

    /* === MÉTRICAS PREMIUM === */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9)) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 20px !important;
        padding: 24px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        transition: all 0.3s ease !important;
    }

    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 15px 40px rgba(59, 130, 246, 0.2) !important;
        border-color: rgba(59, 130, 246, 0.4) !important;
    }

    div[data-testid="metric-container"] label,
    div[data-testid="metric-container"] div,
    div[data-testid="metric-container"] [data-testid="stMetricValue"],
    div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 2.5em !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
    }

    /* === GRÁFICOS CON ESTILO OSCURO === */
    .stPlotlyChart, .stPyplot {
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 20px !important;
        padding: 20px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
    }

    /* === EXPANDERS ELEGANTES === */
    .streamlit-expanderHeader {
        color: #ffffff !important;
        background: rgba(30, 41, 59, 0.8) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 16px !important;
        font-weight: 700 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 16px 20px !important;
        margin-bottom: 10px !important;
    }

    .streamlit-expanderContent {
        background: rgba(15, 23, 42, 0.6) !important;
        border-radius: 0 0 16px 16px !important;
        padding: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-top: none !important;
    }

    /* === TEXTOS GENERALES === */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 800 !important;
        margin-top: 1.5em !important;
    }

    p, div, span, label, li {
        color: #cbd5e1 !important;
        line-height: 1.7 !important;
    }

    /* === DATA FRAMES TABLAS ELEGANTES === */
    .dataframe {
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255,255, 0.1) !important;
        color: #ffffff !important;
    }

    .dataframe th {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        padding: 16px !important;
    }

    .dataframe td {
        color: #cbd5e1 !important;
        padding: 14px 16px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* === ALERTS Y MENSAJES === */
    .stAlert {
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
    }

    /* === SCROLLBAR PERSONALIZADA === */
    ::-webkit-scrollbar {
        width: 10px !important;
        height: 10px !important;
    }

    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.8) !important;
        border-radius: 10px !important;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        border-radius: 10px !important;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #4f8df8 0%, #2d5fe8 100%) !important;
    }

    /* === IMÁGENES DEL SIDEBAR === */
    [data-testid="stSidebar"] img {
        border-radius: 16px !important;
        border: 2px solid #d1d5db !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stSidebar"] img:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.2) !important;
        border-color: #3b82f6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def mostrar_hero_banner():
    """Muestra el banner principal de la aplicación"""
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-content">
            <h1 class="hero-title">ANALIZADOR MULTI-CULTIVO SATELITAL</h1>
            <p class="hero-subtitle">Potenciado con NASA POWER, GEE y tecnología avanzada para una agricultura de precisión</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
