import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D
import io
from shapely.geometry import Polygon, LineString, Point
import math
import warnings
import xml.etree.ElementTree as ET
import base64
import json
from io import BytesIO
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import geojson
import requests
import contextily as ctx

# Configuración de la página
st.set_page_config(
    page_title="Analizador Multi-Cultivo Satelital",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

warnings.filterwarnings('ignore')

# === INICIALIZACIÓN DE VARIABLES DE SESIÓN ===
if 'reporte_completo' not in st.session_state:
    st.session_state.reporte_completo = None
if 'geojson_data' not in st.session_state:
    st.session_state.geojson_data = None
if 'nombre_geojson' not in st.session_state:
    st.session_state.nombre_geojson = ""
if 'nombre_reporte' not in st.session_state:
    st.session_state.nombre_reporte = ""
if 'resultados_todos' not in st.session_state:
    st.session_state.resultados_todos = {}
if 'analisis_completado' not in st.session_state:
    st.session_state.analisis_completado = False
if 'mapas_generados' not in st.session_state:
    st.session_state.mapas_generados = {}
if 'dem_data' not in st.session_state:
    st.session_state.dem_data = {}
if 'imagen_satelital' not in st.session_state:
    st.session_state.imagen_satelital = None

# === ESTILOS PERSONALIZADOS ===
st.markdown("""
<style>
/* Fondo general */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
    color: #ffffff !important;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 2px solid #e5e7eb !important;
}

[data-testid="stSidebar"] * {
    color: #000000 !important;
}

/* Botones */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
    color: white !important;
    border: none !important;
    padding: 10px 20px !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4) !important;
}

/* Métricas */
div[data-testid="metric-container"] {
    background: rgba(30, 41, 59, 0.8) !important;
    border-radius: 10px !important;
    padding: 15px !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 4px 4px 0px 0px;
    gap: 1px;
    padding-top: 10px;
    padding-bottom: 10px;
}

.stTabs [aria-selected="true"] {
    background-color: #3b82f6 !important;
    color: white !important;
}

/* Dataframes */
.dataframe {
    background: rgba(30, 41, 59, 0.8) !important;
    border-radius: 10px !important;
}

.dataframe th {
    background: #3b82f6 !important;
    color: white !important;
}

/* Alertas */
.stAlert {
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ===== HERO BANNER =====
st.markdown("""
<div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);">
    <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 800;">
        🌾 ANALIZADOR MULTI-CULTIVO SATELITAL
    </h1>
    <p style="color: #cbd5e1; font-size: 1.2rem; margin-top: 0.5rem;">
        Agricultura de precisión con datos satelitales y análisis avanzado
    </p>
</div>
""", unsafe_allow_html=True)

# ===== CONFIGURACIÓN DE SATÉLITES =====
SATELITES_DISPONIBLES = {
    'SENTINEL-2': {
        'nombre': 'Sentinel-2 (ESA)',
        'resolucion': '10m',
        'revisita': '5 días',
        'bandas': ['B2', 'B3', 'B4', 'B8'],
        'indices': ['NDVI', 'NDWI', 'EVI'],
        'icono': '🛰️'
    },
    'LANDSAT-8': {
        'nombre': 'Landsat 8 (NASA)',
        'resolucion': '30m',
        'revisita': '16 días',
        'bandas': ['B2', 'B3', 'B4', 'B5'],
        'indices': ['NDVI', 'NDWI', 'SAVI'],
        'icono': '🛰️'
    },
    'DATOS_SIMULADOS': {
        'nombre': 'Datos Simulados',
        'resolucion': '10m',
        'revisita': '5 días',
        'bandas': ['B2', 'B3', 'B4'],
        'indices': ['NDVI', 'NDRE'],
        'icono': '🔬'
    }
}

# ===== PARÁMETROS DE CULTIVOS =====
PARAMETROS_CULTIVOS = {
    'TRIGO': {
        'NITROGENO': {'min': 100, 'max': 180},
        'FOSFORO': {'min': 40, 'max': 80},
        'POTASIO': {'min': 90, 'max': 150},
        'MATERIA_ORGANICA_OPTIMA': 3.5,
        'HUMEDAD_OPTIMA': 0.28,
        'NDVI_OPTIMO': 0.75,
        'RENDIMIENTO_OPTIMO': 4500,
        'COSTO_FERTILIZACION': 350,
        'PRECIO_VENTA': 0.25
    },
    'MAIZ': {
        'NITROGENO': {'min': 150, 'max': 250},
        'FOSFORO': {'min': 50, 'max': 90},
        'POTASIO': {'min': 120, 'max': 200},
        'MATERIA_ORGANICA_OPTIMA': 3.8,
        'HUMEDAD_OPTIMA': 0.32,
        'NDVI_OPTIMO': 0.80,
        'RENDIMIENTO_OPTIMO': 8500,
        'COSTO_FERTILIZACION': 550,
        'PRECIO_VENTA': 0.20
    },
    'SOJA': {
        'NITROGENO': {'min': 20, 'max': 40},
        'FOSFORO': {'min': 45, 'max': 85},
        'POTASIO': {'min': 140, 'max': 220},
        'MATERIA_ORGANICA_OPTIMA': 3.5,
        'HUMEDAD_OPTIMA': 0.30,
        'NDVI_OPTIMO': 0.78,
        'RENDIMIENTO_OPTIMO': 3200,
        'COSTO_FERTILIZACION': 400,
        'PRECIO_VENTA': 0.45
    }
}

ICONOS_CULTIVOS = {
    'TRIGO': '🌾',
    'MAIZ': '🌽',
    'SOJA': '🫘'
}

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("### ⚙️ CONFIGURACIÓN")
    
    cultivo = st.selectbox(
        "Selecciona el cultivo:",
        ["TRIGO", "MAIZ", "SOJA"],
        format_func=lambda x: f"{ICONOS_CULTIVOS[x]} {x}"
    )
    
    st.markdown("---")
    st.markdown("### 🛰️ FUENTE DE DATOS")
    
    satelite_seleccionado = st.selectbox(
        "Satélite:",
        ["SENTINEL-2", "LANDSAT-8", "DATOS_SIMULADOS"],
        format_func=lambda x: SATELITES_DISPONIBLES[x]['nombre']
    )
    
    st.markdown("---")
    st.markdown("### 📅 PERIODO DE ANÁLISIS")
    
    fecha_fin = st.date_input(
        "Fecha final:",
        datetime.now(),
        help="Selecciona la fecha más reciente para el análisis"
    )
    
    fecha_inicio = st.date_input(
        "Fecha inicial:",
        datetime.now() - timedelta(days=30),
        help="Selecciona la fecha inicial para el análisis"
    )
    
    st.markdown("---")
    st.markdown("### 🎯 DIVISIÓN DE PARCELA")
    
    n_divisiones = st.slider(
        "Número de zonas:",
        min_value=4,
        max_value=36,
        value=16,
        step=4,
        help="Divide la parcela en zonas de manejo diferenciado"
    )
    
    st.markdown("---")
    st.markdown("### 🏔️ CONFIGURACIÓN TOPOGRÁFICA")
    
    intervalo_curvas = st.slider(
        "Intervalo curvas (m):",
        min_value=1.0,
        max_value=20.0,
        value=5.0,
        step=1.0
    )
    
    resolucion_dem = st.slider(
        "Resolución DEM (m):",
        min_value=5.0,
        max_value=50.0,
        value=10.0,
        step=5.0
    )
    
    st.markdown("---")
    st.markdown("### 📤 CARGA DE PARCELA")
    
    uploaded_file = st.file_uploader(
        "Sube tu archivo de parcela:",
        type=['zip', 'kml', 'geojson', 'shp'],
        help="Formatos soportados: Shapefile (.zip), KML, GeoJSON"
    )

# ===== FUNCIONES AUXILIARES =====
def validar_y_corregir_crs(gdf):
    """Valida y corrige el sistema de coordenadas"""
    if gdf is None or len(gdf) == 0:
        return gdf
    
    try:
        if gdf.crs is None:
            gdf = gdf.set_crs('EPSG:4326', inplace=False)
        elif str(gdf.crs).upper() != 'EPSG:4326':
            gdf = gdf.to_crs('EPSG:4326')
        return gdf
    except Exception as e:
        st.warning(f"⚠️ Error al corregir CRS: {e}")
        return gdf

def calcular_superficie(gdf):
    """Calcula la superficie en hectáreas"""
    try:
        if gdf is None or len(gdf) == 0:
            return 0.0
        
        gdf = validar_y_corregir_crs(gdf)
        
        # Proyectar a un CRS métrico para cálculo de área
        gdf_projected = gdf.to_crs('EPSG:3857')
        area_m2 = gdf_projected.geometry.area.sum()
        
        return area_m2 / 10000  # Convertir a hectáreas
    except Exception as e:
        # Método alternativo aproximado
        try:
            bounds = gdf.total_bounds
            area_grados = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
            area_m2 = area_grados * 111000 * 111000  # Aproximación
            return area_m2 / 10000
        except:
            return 0.0

def dividir_parcela_en_zonas(gdf, n_zonas):
    """Divide la parcela en zonas de manejo"""
    if len(gdf) == 0:
        return gdf
    
    gdf = validar_y_corregir_crs(gdf)
    parcela_principal = gdf.iloc[0].geometry
    bounds = parcela_principal.bounds
    
    minx, miny, maxx, maxy = bounds
    sub_poligonos = []
    
    # Calcular número de filas y columnas
    n_cols = math.ceil(math.sqrt(n_zonas))
    n_rows = math.ceil(n_zonas / n_cols)
    
    width = (maxx - minx) / n_cols
    height = (maxy - miny) / n_rows
    
    for i in range(n_rows):
        for j in range(n_cols):
            if len(sub_poligonos) >= n_zonas:
                break
            
            cell_minx = minx + (j * width)
            cell_maxx = minx + ((j + 1) * width)
            cell_miny = miny + (i * height)
            cell_maxy = miny + ((i + 1) * height)
            
            cell_poly = Polygon([
                (cell_minx, cell_miny),
                (cell_maxx, cell_miny),
                (cell_maxx, cell_maxy),
                (cell_minx, cell_maxy)
            ])
            
            intersection = parcela_principal.intersection(cell_poly)
            if not intersection.is_empty and intersection.area > 0:
                sub_poligonos.append(intersection)
    
    if sub_poligonos:
        nuevo_gdf = gpd.GeoDataFrame({
            'id_zona': range(1, len(sub_poligonos) + 1),
            'geometry': sub_poligonos
        }, crs='EPSG:4326')
        return nuevo_gdf
    else:
        return gdf

# ===== FUNCIONES DE CARGA DE ARCHIVOS =====
def cargar_shapefile_desde_zip(zip_file):
    """Carga un shapefile desde archivo ZIP"""
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)
            
            # Buscar archivo .shp
            shp_files = [f for f in os.listdir(tmp_dir) if f.endswith('.shp')]
            if shp_files:
                shp_path = os.path.join(tmp_dir, shp_files[0])
                gdf = gpd.read_file(shp_path)
                gdf = validar_y_corregir_crs(gdf)
                return gdf
            else:
                st.error("❌ No se encontró archivo .shp en el ZIP")
                return None
    except Exception as e:
        st.error(f"❌ Error cargando shapefile: {str(e)}")
        return None

def cargar_kml(kml_file):
    """Carga archivo KML o KMZ"""
    try:
        if kml_file.name.endswith('.kmz'):
            with tempfile.TemporaryDirectory() as tmp_dir:
                with zipfile.ZipFile(kml_file, 'r') as zip_ref:
                    zip_ref.extractall(tmp_dir)
                
                kml_files = [f for f in os.listdir(tmp_dir) if f.endswith('.kml')]
                if kml_files:
                    kml_path = os.path.join(tmp_dir, kml_files[0])
                    gdf = gpd.read_file(kml_path)
                    gdf = validar_y_corregir_crs(gdf)
                    return gdf
                else:
                    st.error("❌ No se encontró archivo .kml en el KMZ")
                    return None
        else:
            gdf = gpd.read_file(kml_file)
            gdf = validar_y_corregir_crs(gdf)
            return gdf
    except Exception as e:
        st.error(f"❌ Error cargando KML/KMZ: {str(e)}")
        return None

def cargar_archivo_parcela(uploaded_file):
    """Carga cualquier tipo de archivo de parcela"""
    try:
        if uploaded_file.name.endswith('.zip'):
            return cargar_shapefile_desde_zip(uploaded_file)
        elif uploaded_file.name.endswith(('.kml', '.kmz')):
            return cargar_kml(uploaded_file)
        elif uploaded_file.name.endswith('.geojson'):
            gdf = gpd.read_file(uploaded_file)
            return validar_y_corregir_crs(gdf)
        else:
            st.error("❌ Formato no soportado")
            return None
    except Exception as e:
        st.error(f"❌ Error cargando archivo: {str(e)}")
        return None

# ===== FUNCIONES DE ANÁLISIS SATELITAL =====
def obtener_datos_satelitales(gdf, cultivo, satelite, fecha_inicio, fecha_fin):
    """Obtiene datos satelitales según la fuente seleccionada"""
    
    if satelite == "SENTINEL-2":
        # Datos simulados para Sentinel-2
        ndvi_base = PARAMETROS_CULTIVOS[cultivo]['NDVI_OPTIMO']
        ndvi_variacion = np.random.normal(0, 0.1)
        ndvi = max(0.1, min(0.9, ndvi_base + ndvi_variacion))
        
        return {
            'indice': 'NDVI',
            'valor_promedio': ndvi,
            'fuente': 'Sentinel-2 (Simulado)',
            'fecha': fecha_fin.strftime('%Y-%m-%d'),
            'resolucion': '10m',
            'cobertura_nubes': f"{np.random.randint(0, 20)}%"
        }
    
    elif satelite == "LANDSAT-8":
        # Datos simulados para Landsat-8
        ndvi_base = PARAMETROS_CULTIVOS[cultivo]['NDVI_OPTIMO'] * 0.9
        ndvi_variacion = np.random.normal(0, 0.12)
        ndvi = max(0.1, min(0.9, ndvi_base + ndvi_variacion))
        
        return {
            'indice': 'NDVI',
            'valor_promedio': ndvi,
            'fuente': 'Landsat-8 (Simulado)',
            'fecha': fecha_fin.strftime('%Y-%m-%d'),
            'resolucion': '30m',
            'cobertura_nubes': f"{np.random.randint(0, 30)}%"
        }
    
    else:  # DATOS_SIMULADOS
        ndvi_base = PARAMETROS_CULTIVOS[cultivo]['NDVI_OPTIMO'] * 0.85
        ndvi_variacion = np.random.normal(0, 0.08)
        ndvi = max(0.1, min(0.9, ndvi_base + ndvi_variacion))
        
        return {
            'indice': 'NDVI',
            'valor_promedio': ndvi,
            'fuente': 'Datos Simulados',
            'fecha': fecha_fin.strftime('%Y-%m-%d'),
            'resolucion': '10m'
        }

def obtener_datos_nasa_power(gdf, fecha_inicio, fecha_fin):
    """Obtiene datos meteorológicos de NASA POWER"""
    try:
        centroid = gdf.geometry.unary_union.centroid
        lat = round(centroid.y, 4)
        lon = round(centroid.x, 4)
        
        start = fecha_inicio.strftime("%Y%m%d")
        end = fecha_fin.strftime("%Y%m%d")
        
        params = {
            'parameters': 'T2M,RH2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN',
            'community': 'AG',
            'longitude': lon,
            'latitude': lat,
            'start': start,
            'end': end,
            'format': 'JSON'
        }
        
        url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'properties' in data and 'parameter' in data['properties']:
            series = data['properties']['parameter']
            
            df_power = pd.DataFrame({
                'fecha': pd.to_datetime(list(series['T2M'].keys())),
                'temperatura': list(series['T2M'].values()),
                'humedad': list(series['RH2M'].values()),
                'precipitacion': list(series['PRECTOTCORR'].values()),
                'radiacion': list(series['ALLSKY_SFC_SW_DWN'].values())
            })
            
            # Reemplazar valores -999 por NaN
            df_power = df_power.replace(-999, np.nan)
            
            # Calcular promedios
            promedios = {
                'temp_prom': round(df_power['temperatura'].mean(), 1),
                'hum_prom': round(df_power['humedad'].mean(), 0),
                'prec_total': round(df_power['precipitacion'].sum(), 1),
                'rad_prom': round(df_power['radiacion'].mean(), 1)
            }
            
            return df_power, promedios
        
        return None, None
    except Exception as e:
        st.warning(f"⚠️ No se pudieron obtener datos de NASA POWER: {e}")
        return None, None

# ===== FUNCIONES DEM =====
def generar_dem_sintetico(gdf, resolucion=10.0):
    """Genera un DEM sintético para análisis topográfico"""
    gdf = validar_y_corregir_crs(gdf)
    bounds = gdf.total_bounds
    
    minx, miny, maxx, maxy = bounds
    
    # Crear grid
    num_cells_x = int((maxx - minx) * 111000 / resolucion)
    num_cells_y = int((maxy - miny) * 111000 / resolucion)
    
    num_cells_x = max(20, min(num_cells_x, 100))
    num_cells_y = max(20, min(num_cells_y, 100))
    
    x = np.linspace(minx, maxx, num_cells_x)
    y = np.linspace(miny, maxy, num_cells_y)
    X, Y = np.meshgrid(x, y)
    
    # Generar terreno sintético
    seed = int((minx + miny) * 10000) % (2**32)
    rng = np.random.RandomState(seed)
    
    # Elevación base
    Z_base = rng.uniform(100, 300)
    
    # Pendiente
    slope_x = rng.uniform(-0.001, 0.001)
    slope_y = rng.uniform(-0.001, 0.001)
    
    # Relieve
    Z = Z_base + slope_x * (X - minx) + slope_y * (Y - miny)
    
    # Añadir colinas
    n_hills = rng.randint(2, 5)
    for _ in range(n_hills):
        center_x = rng.uniform(minx, maxx)
        center_y = rng.uniform(miny, maxy)
        radius = rng.uniform(0.001, 0.003)
        height = rng.uniform(20, 60)
        
        dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        Z += height * np.exp(-dist**2 / (2 * radius**2))
    
    # Ruido
    noise = rng.randn(*X.shape) * 5
    Z += noise
    
    # Aplicar máscara
    points = np.vstack([X.flatten(), Y.flatten()]).T
    mask = gdf.geometry.unary_union.contains([Point(p) for p in points])
    mask = mask.reshape(X.shape)
    
    Z[~mask] = np.nan
    
    return X, Y, Z, bounds

def calcular_pendiente(X, Y, Z, resolucion):
    """Calcula pendiente a partir del DEM"""
    try:
        dy, dx = np.gradient(Z, edge_order=2)
        
        # Convertir a metros (aproximado)
        dy_m = dy * 111000
        dx_m = dx * 111000
        
        # Calcular pendiente en porcentaje
        pendiente = np.sqrt(dx_m**2 + dy_m**2) / resolucion * 100
        pendiente = np.clip(pendiente, 0, 100)
        
        return pendiente
    except:
        return np.zeros_like(Z)

def generar_curvas_nivel(X, Y, Z, intervalo=5.0):
    """Genera curvas de nivel"""
    curvas = []
    elevaciones = []
    
    try:
        z_min = np.nanmin(Z)
        z_max = np.nanmax(Z)
        
        if np.isnan(z_min) or np.isnan(z_max):
            return curvas, elevaciones
        
        niveles = np.arange(
            np.ceil(z_min / intervalo) * intervalo,
            np.floor(z_max / intervalo) * intervalo + intervalo,
            intervalo
        )
        
        # Crear curvas de nivel simples
        for nivel in niveles:
            mask = np.abs(Z - nivel) < (intervalo / 2)
            if np.any(mask):
                # Encontrar contornos
                from scipy import ndimage
                labeled, num_features = ndimage.label(mask)
                
                for i in range(1, num_features + 1):
                    if np.sum(labeled == i) > 10:
                        y_idx, x_idx = np.where(labeled == i)
                        if len(x_idx) > 2:
                            puntos = np.column_stack([X[mask].flatten(), Y[mask].flatten()])
                            if len(puntos) >= 3:
                                linea = LineString(puntos)
                                curvas.append(linea)
                                elevaciones.append(nivel)
        
        return curvas, elevaciones
    except:
        return [], []

# ===== FUNCIONES DE ANÁLISIS =====
def analizar_fertilidad(gdf_dividido, cultivo, datos_satelitales):
    """Analiza la fertilidad actual"""
    resultados = []
    params = PARAMETROS_CULTIVOS[cultivo]
    
    for idx, row in gdf_dividido.iterrows():
        # Simular valores basados en el NDVI satelital
        ndvi_base = datos_satelitales['valor_promedio']
        
        # Variación espacial
        centroid = row.geometry.centroid
        seed = int(centroid.x * 1000 + centroid.y * 1000) % (2**32)
        rng = np.random.RandomState(seed)
        
        # Materia orgánica
        mo_base = params['MATERIA_ORGANICA_OPTIMA']
        mo = max(1.0, min(8.0, rng.normal(mo_base * 0.8, mo_base * 0.2)))
        
        # Humedad
        hum_base = params['HUMEDAD_OPTIMA']
        hum = max(0.1, min(0.8, rng.normal(hum_base * 0.9, hum_base * 0.1)))
        
        # NDVI local
        ndvi_local = max(0.1, min(0.9, rng.normal(ndvi_base, 0.1)))
        
        # Índice NPK
        npk_index = (ndvi_local * 0.4 + (mo / 8) * 0.3 + hum * 0.3)
        
        resultados.append({
            'materia_organica': round(mo, 2),
            'humedad_suelo': round(hum, 3),
            'ndvi': round(ndvi_local, 3),
            'npk_index': round(npk_index, 3)
        })
    
    return resultados

def calcular_recomendaciones_npk(fertilidad, cultivo):
    """Calcula recomendaciones de NPK"""
    recomendaciones_n = []
    recomendaciones_p = []
    recomendaciones_k = []
    
    params = PARAMETROS_CULTIVOS[cultivo]
    
    for fert in fertilidad:
        npk_index = fert['npk_index']
        ndvi = fert['ndvi']
        mo = fert['materia_organica']
        
        # Factor de corrección basado en NPK index
        factor = max(0.3, min(1.5, 1.5 - npk_index))
        
        # Nitrógeno
        n_min = params['NITROGENO']['min']
        n_max = params['NITROGENO']['max']
        n_rec = n_min + (n_max - n_min) * (1 - ndvi) * factor
        recomendaciones_n.append(round(n_rec, 1))
        
        # Fósforo
        p_min = params['FOSFORO']['min']
        p_max = params['FOSFORO']['max']
        p_rec = p_min + (p_max - p_min) * (1 - (mo / 8)) * factor
        recomendaciones_p.append(round(p_rec, 1))
        
        # Potasio
        k_min = params['POTASIO']['min']
        k_max = params['POTASIO']['max']
        k_rec = k_min + (k_max - k_min) * (1 - npk_index) * factor
        recomendaciones_k.append(round(k_rec, 1))
    
    return recomendaciones_n, recomendaciones_p, recomendaciones_k

def calcular_costos_fertilizacion(recomendaciones_n, recomendaciones_p, recomendaciones_k, cultivo):
    """Calcula costos de fertilización"""
    costos = []
    params = PARAMETROS_CULTIVOS[cultivo]
    
    # Precios por kg
    precio_n = 1.5  # USD/kg N
    precio_p = 2.8  # USD/kg P2O5
    precio_k = 2.0  # USD/kg K2O
    
    for n, p, k in zip(recomendaciones_n, recomendaciones_p, recomendaciones_k):
        costo_n = n * precio_n
        costo_p = p * precio_p
        costo_k = k * precio_k
        
        costo_otros = params['COSTO_FERTILIZACION']
        costo_total = costo_n + costo_p + costo_k + costo_otros
        
        costos.append({
            'costo_n': round(costo_n, 2),
            'costo_p': round(costo_p, 2),
            'costo_k': round(costo_k, 2),
            'costo_otros': round(costo_otros, 2),
            'costo_total': round(costo_total, 2)
        })
    
    return costos

def calcular_proyecciones_cosecha(fertilidad, recomendaciones_npk, cultivo):
    """Calcula proyecciones de cosecha"""
    proyecciones = []
    params = PARAMETROS_CULTIVOS[cultivo]
    
    for fert, (n, p, k) in zip(fertilidad, zip(*recomendaciones_npk)):
        npk_index = fert['npk_index']
        ndvi = fert['ndvi']
        
        # Rendimiento base sin fertilización
        rend_base = params['RENDIMIENTO_OPTIMO'] * npk_index * 0.7
        
        # Efecto de la fertilización
        factor_fert = min(1.5, 1.0 + (1 - npk_index) * 0.5)
        
        # Rendimiento con fertilización
        rend_fert = rend_base * factor_fert
        
        # Incremento porcentual
        incremento = ((rend_fert - rend_base) / rend_base * 100) if rend_base > 0 else 0
        
        proyecciones.append({
            'rendimiento_sin': round(rend_base, 0),
            'rendimiento_con': round(rend_fert, 0),
            'incremento': round(incremento, 1)
        })
    
    return proyecciones

def analizar_textura_suelo(gdf_dividido, cultivo):
    """Analiza textura del suelo"""
    gdf_resultado = gdf_dividido.copy()
    
    texturas = ['Franco', 'Franco arcilloso', 'Franco arenoso']
    colores = ['#c7eae5', '#5ab4ac', '#f6e8c3']
    
    for idx, row in gdf_resultado.iterrows():
        centroid = row.geometry.centroid
        seed = int(centroid.x * 1000 + centroid.y * 1000) % (2**32)
        rng = np.random.RandomState(seed)
        
        # Distribución granulométrica
        arena = rng.uniform(30, 70)
        limo = rng.uniform(20, 50)
        arcilla = 100 - arena - limo
        
        # Clasificar textura
        if arcilla > 35:
            textura = 'Franco arcilloso'
            color = colores[1]
        elif arena > 60:
            textura = 'Franco arenoso'
            color = colores[2]
        else:
            textura = 'Franco'
            color = colores[0]
        
        gdf_resultado.at[idx, 'textura'] = textura
        gdf_resultado.at[idx, 'color'] = color
        gdf_resultado.at[idx, 'arena'] = round(arena, 1)
        gdf_resultado.at[idx, 'limo'] = round(limo, 1)
        gdf_resultado.at[idx, 'arcilla'] = round(arcilla, 1)
    
    return gdf_resultado

# ===== FUNCIÓN DE ANÁLISIS COMPLETO =====
def ejecutar_analisis_completo(gdf, cultivo, n_divisiones, satelite, fecha_inicio, fecha_fin, intervalo_curvas, resolucion_dem):
    """Ejecuta todos los análisis"""
    
    resultados = {
        'exitoso': False,
        'gdf_dividido': None,
        'area_total': 0,
        'fertilidad': None,
        'recomendaciones_npk': None,
        'costos': None,
        'proyecciones': None,
        'textura': None,
        'datos_power': None,
        'promedios_power': None,
        'dem_data': None
    }
    
    try:
        # 1. Preparar datos
        gdf = validar_y_corregir_crs(gdf)
        area_total = calcular_superficie(gdf)
        resultados['area_total'] = area_total
        
        # 2. Obtener datos satelitales
        with st.spinner("📡 Obteniendo datos satelitales..."):
            datos_satelitales = obtener_datos_satelitales(
                gdf, cultivo, satelite, fecha_inicio, fecha_fin
            )
        
        # 3. Obtener datos meteorológicos
        with st.spinner("🌤️ Obteniendo datos meteorológicos..."):
            datos_power, promedios_power = obtener_datos_nasa_power(gdf, fecha_inicio, fecha_fin)
            resultados['datos_power'] = datos_power
            resultados['promedios_power'] = promedios_power
        
        # 4. Dividir parcela
        with st.spinner("🎯 Dividiendo parcela en zonas..."):
            gdf_dividido = dividir_parcela_en_zonas(gdf, n_divisiones)
            resultados['gdf_dividido'] = gdf_dividido
            
            # Calcular áreas por zona
            areas = []
            for idx, row in gdf_dividido.iterrows():
                area_zona = calcular_superficie(gpd.GeoDataFrame([row], crs=gdf_dividido.crs))
                areas.append(area_zona)
            
            gdf_dividido['area_ha'] = areas
        
        # 5. Análisis de fertilidad
        with st.spinner("🧪 Analizando fertilidad..."):
            fertilidad = analizar_fertilidad(gdf_dividido, cultivo, datos_satelitales)
            resultados['fertilidad'] = fertilidad
            
            # Añadir resultados al GeoDataFrame
            for i, col in enumerate(['mo', 'hum', 'ndvi', 'npk_idx']):
                gdf_dividido[f'fert_{col}'] = [fert[list(fert.keys())[i]] for fert in fertilidad]
        
        # 6. Recomendaciones NPK
        with st.spinner("⚗️ Calculando recomendaciones NPK..."):
            rec_n, rec_p, rec_k = calcular_recomendaciones_npk(fertilidad, cultivo)
            resultados['recomendaciones_npk'] = (rec_n, rec_p, rec_k)
            
            gdf_dividido['rec_N'] = rec_n
            gdf_dividido['rec_P'] = rec_p
            gdf_dividido['rec_K'] = rec_k
        
        # 7. Costos
        with st.spinner("💰 Calculando costos..."):
            costos = calcular_costos_fertilizacion(rec_n, rec_p, rec_k, cultivo)
            resultados['costos'] = costos
            
            for i, col in enumerate(['costo_n', 'costo_p', 'costo_k', 'costo_total']):
                gdf_dividido[col] = [costo[list(costo.keys())[i]] for costo in costos]
        
        # 8. Proyecciones
        with st.spinner("📈 Calculando proyecciones..."):
            proyecciones = calcular_proyecciones_cosecha(fertilidad, (rec_n, rec_p, rec_k), cultivo)
            resultados['proyecciones'] = proyecciones
            
            for i, col in enumerate(['rend_sin', 'rend_con', 'incr']):
                gdf_dividido[f'proy_{col}'] = [proy[list(proy.keys())[i]] for proy in proyecciones]
        
        # 9. Textura del suelo
        with st.spinner("🏗️ Analizando textura del suelo..."):
            textura = analizar_textura_suelo(gdf_dividido, cultivo)
            resultados['textura'] = textura
        
        # 10. Análisis DEM
        with st.spinner("🏔️ Generando modelo digital de elevación..."):
            try:
                X, Y, Z, bounds = generar_dem_sintetico(gdf, resolucion_dem)
                pendientes = calcular_pendiente(X, Y, Z, resolucion_dem)
                curvas, elevaciones = generar_curvas_nivel(X, Y, Z, intervalo_curvas)
                
                resultados['dem_data'] = {
                    'X': X,
                    'Y': Y,
                    'Z': Z,
                    'bounds': bounds,
                    'pendientes': pendientes,
                    'curvas': curvas,
                    'elevaciones': elevaciones
                }
            except Exception as e:
                st.warning(f"⚠️ Error generando DEM: {e}")
                resultados['dem_data'] = None
        
        resultados['gdf_completo'] = gdf_dividido
        resultados['exitoso'] = True
        
        return resultados
        
    except Exception as e:
        st.error(f"❌ Error en el análisis: {str(e)}")
        return resultados

# ===== FUNCIONES DE VISUALIZACIÓN =====
def crear_mapa_fertilidad(gdf_completo, cultivo):
    """Crea mapa de fertilidad"""
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Normalizar valores para colormap
        valores = gdf_completo['fert_npk_idx'].values
        norm = plt.Normalize(vmin=0, vmax=1)
        cmap = plt.cm.RdYlGn
        
        # Plotear zonas
        for idx, row in gdf_completo.iterrows():
            color = cmap(norm(row['fert_npk_idx']))
            gdf_completo.iloc[[idx]].plot(
                ax=ax,
                color=color,
                edgecolor='black',
                linewidth=1,
                alpha=0.7
            )
            
            # Etiqueta
            centroid = row.geometry.centroid
            ax.text(
                centroid.x, centroid.y,
                f"Z{row['id_zona']}\n{row['fert_npk_idx']:.2f}",
                fontsize=8,
                ha='center',
                va='center',
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8)
            )
        
        # Configurar mapa
        ax.set_title(f'Mapa de Fertilidad - {cultivo}', fontsize=16, fontweight='bold')
        ax.set_xlabel('Longitud')
        ax.set_ylabel('Latitud')
        ax.grid(True, alpha=0.3)
        
        # Barra de colores
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.8)
        cbar.set_label('Índice de Fertilidad (0-1)')
        
        plt.tight_layout()
        
        # Guardar en buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf
    except Exception as e:
        st.error(f"Error creando mapa: {e}")
        return None

def crear_mapa_npk(gdf_completo, cultivo, nutriente='N'):
    """Crea mapa de recomendaciones NPK"""
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Seleccionar columna y parámetros
        if nutriente == 'N':
            columna = 'rec_N'
            titulo = 'Nitrógeno (kg/ha)'
            cmap = plt.cm.Greens
            vmin = PARAMETROS_CULTIVOS[cultivo]['NITROGENO']['min'] * 0.5
            vmax = PARAMETROS_CULTIVOS[cultivo]['NITROGENO']['max'] * 1.5
        elif nutriente == 'P':
            columna = 'rec_P'
            titulo = 'Fósforo (kg/ha)'
            cmap = plt.cm.Blues
            vmin = PARAMETROS_CULTIVOS[cultivo]['FOSFORO']['min'] * 0.5
            vmax = PARAMETROS_CULTIVOS[cultivo]['FOSFORO']['max'] * 1.5
        else:  # 'K'
            columna = 'rec_K'
            titulo = 'Potasio (kg/ha)'
            cmap = plt.cm.Purples
            vmin = PARAMETROS_CULTIVOS[cultivo]['POTASIO']['min'] * 0.5
            vmax = PARAMETROS_CULTIVOS[cultivo]['POTASIO']['max'] * 1.5
        
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        
        # Plotear zonas
        for idx, row in gdf_completo.iterrows():
            color = cmap(norm(row[columna]))
            gdf_completo.iloc[[idx]].plot(
                ax=ax,
                color=color,
                edgecolor='black',
                linewidth=1,
                alpha=0.7
            )
            
            # Etiqueta
            centroid = row.geometry.centroid
            ax.text(
                centroid.x, centroid.y,
                f"Z{row['id_zona']}\n{row[columna]:.0f}",
                fontsize=8,
                ha='center',
                va='center',
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8)
            )
        
        ax.set_title(f'Recomendaciones de {titulo} - {cultivo}', fontsize=16, fontweight='bold')
        ax.set_xlabel('Longitud')
        ax.set_ylabel('Latitud')
        ax.grid(True, alpha=0.3)
        
        # Barra de colores
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.8)
        cbar.set_label(titulo)
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf
    except Exception as e:
        st.error(f"Error creando mapa NPK: {e}")
        return None

def crear_visualizacion_3d(X, Y, Z):
    """Crea visualización 3D del terreno"""
    try:
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot superficie
        surf = ax.plot_surface(X, Y, Z, cmap='terrain', alpha=0.8, linewidth=0.5)
        
        ax.set_xlabel('Longitud')
        ax.set_ylabel('Latitud')
        ax.set_zlabel('Elevación (m)')
        ax.set_title('Modelo 3D del Terreno', fontsize=14, fontweight='bold')
        
        # Colorbar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Elevación (m)')
        
        ax.view_init(elev=30, azim=45)
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf
    except Exception as e:
        st.error(f"Error creando visualización 3D: {e}")
        return None

# ===== FUNCIONES DE EXPORTACIÓN =====
def exportar_a_geojson(gdf):
    """Exporta resultados a GeoJSON"""
    try:
        gdf = validar_y_corregir_crs(gdf)
        geojson_str = gdf.to_json()
        return geojson_str
    except Exception as e:
        st.error(f"Error exportando a GeoJSON: {e}")
        return None

def generar_reporte_docx(resultados, cultivo, satelite, fecha_inicio, fecha_fin):
    """Genera reporte en formato DOCX"""
    try:
        doc = Document()
        
        # Título
        doc.add_heading(f'Reporte de Análisis - {cultivo}', 0)
        
        # Información general
        doc.add_heading('Información General', level=1)
        doc.add_paragraph(f'Cultivo: {cultivo}')
        doc.add_paragraph(f'Satélite: {SATELITES_DISPONIBLES[satelite]["nombre"]}')
        doc.add_paragraph(f'Período: {fecha_inicio} a {fecha_fin}')
        doc.add_paragraph(f'Área total: {resultados["area_total"]:.2f} ha')
        doc.add_paragraph(f'Zonas analizadas: {len(resultados["gdf_completo"])}')
        
        # Fertilidad
        doc.add_heading('Fertilidad Promedio', level=1)
        if resultados['fertilidad']:
            fert_prom = np.mean([f['npk_index'] for f in resultados['fertilidad']])
            doc.add_paragraph(f'Índice NPK promedio: {fert_prom:.3f}')
        
        # Recomendaciones NPK
        doc.add_heading('Recomendaciones NPK', level=1)
        if resultados['recomendaciones_npk']:
            rec_n, rec_p, rec_k = resultados['recomendaciones_npk']
            doc.add_paragraph(f'Nitrógeno promedio: {np.mean(rec_n):.1f} kg/ha')
            doc.add_paragraph(f'Fósforo promedio: {np.mean(rec_p):.1f} kg/ha')
            doc.add_paragraph(f'Potasio promedio: {np.mean(rec_k):.1f} kg/ha')
        
        # Costos
        doc.add_heading('Costos Estimados', level=1)
        if resultados['costos']:
            costo_total = sum([c['costo_total'] for c in resultados['costos']])
            doc.add_paragraph(f'Costo total estimado: ${costo_total:.2f} USD')
        
        # Proyecciones
        doc.add_heading('Proyecciones de Cosecha', level=1)
        if resultados['proyecciones']:
            rend_sin = sum([p['rendimiento_sin'] for p in resultados['proyecciones']])
            rend_con = sum([p['rendimiento_con'] for p in resultados['proyecciones']])
            incr_prom = np.mean([p['incremento'] for p in resultados['proyecciones']])
            
            doc.add_paragraph(f'Rendimiento sin fertilización: {rend_sin:.0f} kg')
            doc.add_paragraph(f'Rendimiento con fertilización: {rend_con:.0f} kg')
            doc.add_paragraph(f'Incremento promedio: {incr_prom:.1f}%')
        
        # Datos meteorológicos
        if resultados['promedios_power']:
            doc.add_heading('Datos Meteorológicos', level=1)
            for key, value in resultados['promedios_power'].items():
                doc.add_paragraph(f'{key}: {value}')
        
        # Guardar documento
        docx_buffer = BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)
        
        return docx_buffer
        
    except Exception as e:
        st.error(f"Error generando reporte DOCX: {e}")
        return None

# ===== INTERFAZ PRINCIPAL =====
st.title("ANALIZADOR MULTI-CULTIVO SATELITAL")

if uploaded_file:
    with st.spinner("Cargando parcela..."):
        gdf = cargar_archivo_parcela(uploaded_file)
        
        if gdf is not None and len(gdf) > 0:
            st.success(f"✅ Parcela cargada exitosamente")
            
            # Mostrar información de la parcela
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Información de la Parcela")
                area_total = calcular_superficie(gdf)
                st.metric("Área Total", f"{area_total:.2f} ha")
                st.metric("Polígonos", len(gdf))
                st.metric("Cultivo", f"{ICONOS_CULTIVOS[cultivo]} {cultivo}")
                
                # Vista previa de la parcela
                fig, ax = plt.subplots(figsize=(8, 6))
                gdf.plot(ax=ax, color='lightgreen', edgecolor='darkgreen', alpha=0.7)
                ax.set_title("Vista Previa de la Parcela")
                ax.set_xlabel("Longitud")
                ax.set_ylabel("Latitud")
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
            
            with col2:
                st.subheader("⚙️ Configuración del Análisis")
                st.write(f"**Satélite:** {SATELITES_DISPONIBLES[satelite_seleccionado]['nombre']}")
                st.write(f"**Período:** {fecha_inicio} a {fecha_fin}")
                st.write(f"**Zonas:** {n_divisiones}")
                st.write(f"**Resolución DEM:** {resolucion_dem} m")
                st.write(f"**Intervalo curvas:** {intervalo_curvas} m")
            
            # Botón para ejecutar análisis
            st.markdown("---")
            if st.button("🚀 EJECUTAR ANÁLISIS COMPLETO", type="primary", use_container_width=True):
                with st.spinner("Ejecutando análisis completo..."):
                    resultados = ejecutar_analisis_completo(
                        gdf, cultivo, n_divisiones, satelite_seleccionado,
                        fecha_inicio, fecha_fin, intervalo_curvas, resolucion_dem
                    )
                    
                    if resultados['exitoso']:
                        st.session_state.resultados_todos = resultados
                        st.session_state.analisis_completado = True
                        st.success("✅ Análisis completado exitosamente!")
                        st.rerun()
                    else:
                        st.error("❌ Error en el análisis")

# Mostrar resultados si el análisis está completado
if st.session_state.analisis_completado and st.session_state.resultados_todos:
    resultados = st.session_state.resultados_todos
    
    # Crear pestañas para diferentes resultados
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Fertilidad Actual",
        "🧪 Recomendaciones NPK",
        "💰 Análisis de Costos",
        "📈 Proyecciones",
        "🏔️ Topografía",
        "💾 Exportar"
    ])
    
    with tab1:
        st.subheader("FERTILIDAD ACTUAL")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            npk_prom = np.mean([f['npk_index'] for f in resultados['fertilidad']])
            st.metric("Índice NPK Promedio", f"{npk_prom:.3f}")
        with col2:
            ndvi_prom = np.mean([f['ndvi'] for f in resultados['fertilidad']])
            st.metric("NDVI Promedio", f"{ndvi_prom:.3f}")
        with col3:
            mo_prom = np.mean([f['materia_organica'] for f in resultados['fertilidad']])
            st.metric("Materia Orgánica", f"{mo_prom:.1f}%")
        with col4:
            hum_prom = np.mean([f['humedad_suelo'] for f in resultados['fertilidad']])
            st.metric("Humedad Suelo", f"{hum_prom:.3f}")
        
        # Mapa de fertilidad
        st.subheader("🗺️ Mapa de Fertilidad")
        mapa_fert = crear_mapa_fertilidad(resultados['gdf_completo'], cultivo)
        if mapa_fert:
            st.image(mapa_fert, use_container_width=True)
            
            # Botón de descarga
            st.download_button(
                label="📥 Descargar Mapa de Fertilidad",
                data=mapa_fert,
                file_name=f"mapa_fertilidad_{cultivo}.png",
                mime="image/png"
            )
        
        # Tabla de resultados
        st.subheader("📋 Tabla de Resultados por Zona")
        tabla_data = []
        for i, fert in enumerate(resultados['fertilidad']):
            tabla_data.append({
                'Zona': i + 1,
                'Área (ha)': resultados['gdf_completo'].iloc[i]['area_ha'],
                'Índice NPK': fert['npk_index'],
                'NDVI': fert['ndvi'],
                'Materia Org (%)': fert['materia_organica'],
                'Humedad': fert['humedad_suelo']
            })
        
        df_fert = pd.DataFrame(tabla_data)
        st.dataframe(df_fert, use_container_width=True)
    
    with tab2:
        st.subheader("RECOMENDACIONES NPK")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            rec_n, rec_p, rec_k = resultados['recomendaciones_npk']
            n_prom = np.mean(rec_n)
            st.metric("Nitrógeno Promedio", f"{n_prom:.1f} kg/ha")
        with col2:
            p_prom = np.mean(rec_p)
            st.metric("Fósforo Promedio", f"{p_prom:.1f} kg/ha")
        with col3:
            k_prom = np.mean(rec_k)
            st.metric("Potasio Promedio", f"{k_prom:.1f} kg/ha")
        
        # Mapas NPK
        st.subheader("🗺️ Mapas de Recomendaciones")
        
        col_n, col_p, col_k = st.columns(3)
        with col_n:
            mapa_n = crear_mapa_npk(resultados['gdf_completo'], cultivo, 'N')
            if mapa_n:
                st.image(mapa_n, use_container_width=True)
                st.caption("Nitrógeno (N)")
        with col_p:
            mapa_p = crear_mapa_npk(resultados['gdf_completo'], cultivo, 'P')
            if mapa_p:
                st.image(mapa_p, use_container_width=True)
                st.caption("Fósforo (P)")
        with col_k:
            mapa_k = crear_mapa_npk(resultados['gdf_completo'], cultivo, 'K')
            if mapa_k:
                st.image(mapa_k, use_container_width=True)
                st.caption("Potasio (K)")
        
        # Tabla de recomendaciones
        st.subheader("📋 Recomendaciones por Zona")
        tabla_npk = []
        for i in range(len(rec_n)):
            tabla_npk.append({
                'Zona': i + 1,
                'N (kg/ha)': rec_n[i],
                'P (kg/ha)': rec_p[i],
                'K (kg/ha)': rec_k[i]
            })
        
        df_npk = pd.DataFrame(tabla_npk)
        st.dataframe(df_npk, use_container_width=True)
    
    with tab3:
        st.subheader("ANÁLISIS DE COSTOS")
        
        if resultados['costos']:
            costo_total = sum([c['costo_total'] for c in resultados['costos']])
            costo_prom = np.mean([c['costo_total'] for c in resultados['costos']])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Costo Total Estimado", f"${costo_total:.2f}")
            with col2:
                st.metric("Costo Promedio por ha", f"${costo_prom:.2f}")
            with col3:
                inversion_ha = costo_total / resultados['area_total'] if resultados['area_total'] > 0 else 0
                st.metric("Inversión por ha", f"${inversion_ha:.2f}")
            
            # Gráfico de distribución de costos
            st.subheader("📊 Distribución de Costos")
            
            costos_n = sum([c['costo_n'] for c in resultados['costos']])
            costos_p = sum([c['costo_p'] for c in resultados['costos']])
            costos_k = sum([c['costo_k'] for c in resultados['costos']])
            costos_otros = sum([c['costo_otros'] for c in resultados['costos']])
            
            fig, ax = plt.subplots(figsize=(8, 6))
            labels = ['Nitrógeno', 'Fósforo', 'Potasio', 'Otros']
            valores = [costos_n, costos_p, costos_k, costos_otros]
            colores = ['#4CAF50', '#2196F3', '#9C27B0', '#FF9800']
            
            ax.pie(valores, labels=labels, colors=colores, autopct='%1.1f%%', startangle=90)
            ax.set_title('Distribución de Costos de Fertilización')
            
            st.pyplot(fig)
            
            # Tabla de costos
            st.subheader("📋 Costos por Zona")
            tabla_costos = []
            for i, costo in enumerate(resultados['costos']):
                tabla_costos.append({
                    'Zona': i + 1,
                    'Costo N (USD)': costo['costo_n'],
                    'Costo P (USD)': costo['costo_p'],
                    'Costo K (USD)': costo['costo_k'],
                    'Total (USD)': costo['costo_total']
                })
            
            df_costos = pd.DataFrame(tabla_costos)
            st.dataframe(df_costos, use_container_width=True)
    
    with tab4:
        st.subheader("PROYECCIONES DE COSECHA")
        
        if resultados['proyecciones']:
            rend_sin = sum([p['rendimiento_sin'] for p in resultados['proyecciones']])
            rend_con = sum([p['rendimiento_con'] for p in resultados['proyecciones']])
            incr_prom = np.mean([p['incremento'] for p in resultados['proyecciones']])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rendimiento sin Fertilización", f"{rend_sin:.0f} kg")
            with col2:
                st.metric("Rendimiento con Fertilización", f"{rend_con:.0f} kg")
            with col3:
                st.metric("Incremento Esperado", f"{incr_prom:.1f}%")
            
            # Análisis económico
            st.subheader("💰 Análisis Económico")
            
            precio = PARAMETROS_CULTIVOS[cultivo]['PRECIO_VENTA']
            ingreso_sin = rend_sin * precio
            ingreso_con = rend_con * precio
            costo_fert = sum([c['costo_total'] for c in resultados['costos']])
            beneficio_neto = (ingreso_con - ingreso_sin) - costo_fert
            roi = (beneficio_neto / costo_fert * 100) if costo_fert > 0 else 0
            
            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                st.metric("Ingreso Adicional", f"${ingreso_con - ingreso_sin:.2f}")
            with col_e2:
                st.metric("Beneficio Neto", f"${beneficio_neto:.2f}")
            with col_e3:
                st.metric("ROI Estimado", f"{roi:.1f}%")
            
            # Tabla de proyecciones
            st.subheader("📋 Proyecciones por Zona")
            tabla_proy = []
            for i, proy in enumerate(resultados['proyecciones']):
                tabla_proy.append({
                    'Zona': i + 1,
                    'Sin Fertilización (kg)': proy['rendimiento_sin'],
                    'Con Fertilización (kg)': proy['rendimiento_con'],
                    'Incremento (%)': proy['incremento']
                })
            
            df_proy = pd.DataFrame(tabla_proy)
            st.dataframe(df_proy, use_container_width=True)
    
    with tab5:
        st.subheader("ANÁLISIS TOPOGRÁFICO")
        
        if resultados.get('dem_data'):
            dem_data = resultados['dem_data']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                elev_min = np.nanmin(dem_data['Z'])
                st.metric("Elevación Mínima", f"{elev_min:.1f} m")
            with col2:
                elev_max = np.nanmax(dem_data['Z'])
                st.metric("Elevación Máxima", f"{elev_max:.1f} m")
            with col3:
                elev_prom = np.nanmean(dem_data['Z'])
                st.metric("Elevación Promedio", f"{elev_prom:.1f} m")
            with col4:
                if 'pendientes' in dem_data:
                    pend_prom = np.nanmean(dem_data['pendientes'])
                    st.metric("Pendiente Promedio", f"{pend_prom:.1f}%")
            
            # Visualización 3D
            st.subheader("🎨 Visualización 3D del Terreno")
            vis_3d = crear_visualizacion_3d(dem_data['X'], dem_data['Y'], dem_data['Z'])
            if vis_3d:
                st.image(vis_3d, use_container_width=True)
                
                st.download_button(
                    label="📥 Descargar Visualización 3D",
                    data=vis_3d,
                    file_name=f"visualizacion_3d_{cultivo}.png",
                    mime="image/png"
                )
    
    with tab6:
        st.subheader("EXPORTAR RESULTADOS")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Exportar Datos")
            
            # Exportar a GeoJSON
            if st.button("📤 Generar GeoJSON", key="export_geojson"):
                geojson_data = exportar_a_geojson(resultados['gdf_completo'])
                if geojson_data:
                    st.session_state.geojson_data = geojson_data
                    st.session_state.nombre_geojson = f"analisis_{cultivo}_{datetime.now().strftime('%Y%m%d')}.geojson"
                    st.success("✅ GeoJSON generado correctamente")
            
            if st.session_state.geojson_data:
                st.download_button(
                    label="📥 Descargar GeoJSON",
                    data=st.session_state.geojson_data,
                    file_name=st.session_state.nombre_geojson,
                    mime="application/json"
                )
            
            # Exportar a CSV
            if st.button("📊 Generar CSV", key="export_csv"):
                # Crear DataFrame con todos los datos
                df_export = resultados['gdf_completo'].drop(columns=['geometry', 'color'])
                csv = df_export.to_csv(index=False)
                
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv,
                    file_name=f"analisis_{cultivo}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            st.markdown("### 📄 Exportar Reporte")
            
            # Generar reporte DOCX
            if st.button("📝 Generar Reporte DOCX", key="export_docx"):
                docx_buffer = generar_reporte_docx(
                    resultados, cultivo, satelite_seleccionado, fecha_inicio, fecha_fin
                )
                if docx_buffer:
                    st.session_state.reporte_completo = docx_buffer
                    st.session_state.nombre_reporte = f"reporte_{cultivo}_{datetime.now().strftime('%Y%m%d')}.docx"
                    st.success("✅ Reporte generado correctamente")
            
            if st.session_state.reporte_completo is not None:
                st.download_button(
                    label="📥 Descargar Reporte DOCX",
                    data=st.session_state.reporte_completo,
                    file_name=st.session_state.nombre_reporte,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        
        # Limpiar estado
        st.markdown("---")
        if st.button("🔄 Reiniciar Análisis", type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

else:
    # Pantalla inicial
    st.markdown("""
    ## 👋 Bienvenido al Analizador Multi-Cultivo Satelital
    
    Esta aplicación te permite:
    
    ### 🌾 **ANÁLISIS DE CULTIVOS**
    - Evaluar fertilidad del suelo
    - Calcular recomendaciones de NPK
    - Proyectar rendimientos
    - Analizar costos y ROI
    
    ### 🛰️ **DATOS SATELITALES**
    - Índices de vegetación (NDVI)
    - Datos meteorológicos de NASA POWER
    - Modelos digitales de elevación
    
    ### 📊 **REPORTES COMPLETOS**
    - Mapas interactivos
    - Tablas de resultados
    - Exportación a múltiples formatos
    
    ### 🚀 **¿CÓMO COMENZAR?**
    1. Sube tu archivo de parcela (KML, Shapefile, GeoJSON)
    2. Selecciona el cultivo y configuración
    3. Ejecuta el análisis completo
    4. Explora los resultados y descarga reportes
    
    ---
    
    ### 📁 **FORMATOS SOPORTADOS**
    - **Shapefile** (.zip con .shp, .shx, .dbf, .prj)
    - **KML/KMZ** (Google Earth)
    - **GeoJSON** (.geojson)
    
    ### 🌍 **FUENTES DE DATOS**
    - **Sentinel-2** (ESA) - 10m resolución
    - **Landsat-8** (NASA) - 30m resolución
    - **NASA POWER** - Datos meteorológicos
    """)

# ===== PIE DE PÁGINA =====
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.9em;">
    <p>🌾 <strong>Analizador Multi-Cultivo Satelital</strong> - Versión 2.0</p>
    <p>Desarrollado para agricultura de precisión | © 2024</p>
</div>
""", unsafe_allow_html=True)
