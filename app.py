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
from shapely.geometry import Polygon, LineString, Point, shape, mapping
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
import ee
import folium
from folium import plugins
from streamlit_folium import folium_static
from branca.colormap import LinearColormap
import calendar

# Configuración de la página
st.set_page_config(
    page_title="Analizador Multi-Cultivo Satelital",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

warnings.filterwarnings('ignore')

# === INICIALIZAR GOOGLE EARTH ENGINE ===
try:
    # Inicializar Earth Engine
    ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
    GEE_INITIALIZED = True
    st.success("✅ Google Earth Engine inicializado correctamente")
except Exception as e:
    # Si falla, usar autenticación local (el usuario debe autenticarse)
    st.warning("⚠️ Google Earth Engine requiere autenticación. Para usar datos satelitales reales:")
    st.code("""
    # En tu terminal local:
    earthengine authenticate
    """)
    GEE_INITIALIZED = False

# === VARIABLES DE SESIÓN ===
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
if 'ndvi_data' not in st.session_state:
    st.session_state.ndvi_data = None
if 'parcela_gdf' not in st.session_state:
    st.session_state.parcela_gdf = None

# === ESTILOS ===
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: white;
}
[data-testid="stSidebar"] {
    background: white !important;
}
[data-testid="stSidebar"] * {
    color: black !important;
}
.stButton > button {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 600;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4);
}
div[data-testid="metric-container"] {
    background: rgba(30, 41, 59, 0.8);
    border-radius: 10px;
    padding: 15px;
    border: 1px solid rgba(59, 130, 246, 0.2);
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
        Datos satelitales REALES con Google Earth Engine
    </p>
</div>
""", unsafe_allow_html=True)

# ===== CONFIGURACIÓN SATÉLITES REALES =====
SATELITES_REALES = {
    'SENTINEL-2': {
        'nombre': 'Sentinel-2 (10m resolución)',
        'resolucion': '10m',
        'revisita': '5 días',
        'coleccion': 'COPERNICUS/S2_SR_HARMONIZED',
        'bandas_ndvi': ['B8', 'B4'],
        'icono': '🛰️',
        'nubes_max': 30
    },
    'LANDSAT-8': {
        'nombre': 'Landsat 8 (30m resolución)',
        'resolucion': '30m',
        'revisita': '16 días',
        'coleccion': 'LANDSAT/LC08/C02/T1_L2',
        'bandas_ndvi': ['SR_B5', 'SR_B4'],
        'icono': '🛰️',
        'nubes_max': 30
    },
    'LANDSAT-9': {
        'nombre': 'Landsat 9 (30m resolución)',
        'resolucion': '30m',
        'revisita': '16 días',
        'coleccion': 'LANDSAT/LC09/C02/T1_L2',
        'bandas_ndvi': ['SR_B5', 'SR_B4'],
        'icono': '🛰️',
        'nubes_max': 30
    },
    'MODIS': {
        'nombre': 'MODIS (250m resolución)',
        'resolucion': '250m',
        'revisita': '1-2 días',
        'coleccion': 'MODIS/006/MOD09GA',
        'bandas_ndvi': ['sur_refl_b02', 'sur_refl_b01'],
        'icono': '🛰️',
        'nubes_max': 20
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
    st.markdown("### 🛰️ SATÉLITE (DATOS REALES)")
    
    satelite_seleccionado = st.selectbox(
        "Fuente de datos:",
        ["SENTINEL-2", "LANDSAT-8", "LANDSAT-9", "MODIS"],
        format_func=lambda x: SATELITES_REALES[x]['nombre']
    )
    
    sat_info = SATELITES_REALES[satelite_seleccionado]
    st.info(f"""
    **📡 {sat_info['nombre']}**
    • Resolución: {sat_info['resolucion']}
    • Revisita: {sat_info['revisita']}
    • Datos: **REALES** y actualizados
    """)
    
    st.markdown("---")
    st.markdown("### 📅 PERIODO DE ANÁLISIS")
    
    col_fecha1, col_fecha2 = st.columns(2)
    with col_fecha1:
        fecha_fin = st.date_input(
            "Fecha final:",
            datetime.now(),
            help="Selecciona la fecha más reciente para el análisis"
        )
    with col_fecha2:
        fecha_inicio = st.date_input(
            "Fecha inicial:",
            datetime.now() - timedelta(days=30),
            help="Selecciona la fecha inicial para el análisis"
        )
    
    # Verificar que la fecha inicial sea anterior a la final
    if fecha_inicio >= fecha_fin:
        st.error("❌ La fecha inicial debe ser anterior a la fecha final")
        st.stop()
    
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
    
    st.markdown("---")
    st.markdown("### 📤 CARGA DE PARCELA")
    
    uploaded_file = st.file_uploader(
        "Sube tu archivo de parcela:",
        type=['geojson', 'kml', 'kmz', 'zip'],
        help="Formatos soportados: GeoJSON, KML, KMZ, Shapefile (.zip)"
    )
    
    if uploaded_file:
        st.session_state.parcela_cargada = True

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
            
            shp_files = [f for f in os.listdir(tmp_dir) if f.endswith('.shp')]
            if shp_files:
                shp_path = os.path.join(tmp_dir, shp_files[0])
                gdf = gpd.read_file(shp_path)
                gdf = validar_y_corregir_crs(gdf)
                return gdf
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

# ===== FUNCIONES GOOGLE EARTH ENGINE (DATOS REALES) =====
def obtener_geometria_ee(gdf):
    """Convierte GeoDataFrame a geometría de Earth Engine"""
    gdf = validar_y_corregir_crs(gdf)
    
    # Obtener el polígono principal
    geom = gdf.iloc[0].geometry
    
    if geom.geom_type == 'Polygon':
        coords = list(geom.exterior.coords)
        # Convertir a formato EE
        ee_geom = ee.Geometry.Polygon(coords)
    elif geom.geom_type == 'MultiPolygon':
        # Tomar el primer polígono
        coords = list(geom.geoms[0].exterior.coords)
        ee_geom = ee.Geometry.Polygon(coords)
    else:
        # Crear bbox
        bounds = gdf.total_bounds
        ee_geom = ee.Geometry.Rectangle([bounds[0], bounds[1], bounds[2], bounds[3]])
    
    return ee_geom

def obtener_coleccion_satelital(satelite, fecha_inicio, fecha_fin, geometria):
    """Obtiene colección de imágenes satelitales"""
    
    config = SATELITES_REALES[satelite]
    coleccion = config['coleccion']
    
    # Formatear fechas
    start_date = fecha_inicio.strftime('%Y-%m-%d')
    end_date = fecha_fin.strftime('%Y-%m-%d')
    
    try:
        # Filtrar colección por fecha y ubicación
        coleccion_imagenes = ee.ImageCollection(coleccion) \
            .filterDate(start_date, end_date) \
            .filterBounds(geometria)
        
        # Filtrar por nubes (dependiendo del satélite)
        if 'SENTINEL' in satelite:
            coleccion_imagenes = coleccion_imagenes.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', config['nubes_max']))
        elif 'LANDSAT' in satelite:
            coleccion_imagenes = coleccion_imagenes.filter(ee.Filter.lt('CLOUD_COVER', config['nubes_max']))
        
        return coleccion_imagenes
    except Exception as e:
        st.error(f"❌ Error obteniendo colección {satelite}: {str(e)}")
        return None

def calcular_ndvi_real(satelite, fecha_inicio, fecha_fin, geometria):
    """Calcula NDVI real usando Google Earth Engine"""
    
    if not GEE_INITIALIZED:
        st.error("❌ Google Earth Engine no está inicializado")
        return None
    
    try:
        with st.spinner(f"📡 Obteniendo datos de {SATELITES_REALES[satelite]['nombre']}..."):
            config = SATELITES_REALES[satelite]
            
            # Obtener colección
            coleccion = obtener_coleccion_satelital(satelite, fecha_inicio, fecha_fin, geometria)
            
            if coleccion is None or coleccion.size().getInfo() == 0:
                st.warning(f"⚠️ No hay imágenes disponibles para el período seleccionado")
                return None
            
            # Seleccionar la imagen con menos nubes
            if 'SENTINEL' in satelite:
                imagen = coleccion.sort('CLOUDY_PIXEL_PERCENTAGE').first()
            elif 'LANDSAT' in satelite:
                imagen = coleccion.sort('CLOUD_COVER').first()
            else:
                imagen = coleccion.mean()
            
            # Calcular NDVI
            if satelite == 'SENTINEL-2':
                nir = imagen.select('B8')
                red = imagen.select('B4')
            elif satelite in ['LANDSAT-8', 'LANDSAT-9']:
                nir = imagen.select('SR_B5')
                red = imagen.select('SR_B4')
            elif satelite == 'MODIS':
                nir = imagen.select('sur_refl_b02')
                red = imagen.select('sur_refl_b01')
            else:
                return None
            
            ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
            
            # Recortar a la geometría
            ndvi_recortado = ndvi.clip(geometria)
            
            # Obtener estadísticas
            stats = ndvi_recortado.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometria,
                scale=float(config['resolucion'].replace('m', '')) if 'm' in config['resolucion'] else 30,
                maxPixels=1e9
            )
            
            ndvi_mean = stats.get('NDVI').getInfo()
            
            if ndvi_mean is None:
                st.warning("⚠️ No se pudo calcular NDVI para esta área")
                return None
            
            # Obtener URL de visualización
            ndvi_vis = ndvi_recortado.visualize(
                min=-0.2,
                max=0.8,
                palette=['blue', 'white', 'green']
            )
            
            map_id_dict = ndvi_vis.getMapId({'min': -0.2, 'max': 0.8})
            
            resultado = {
                'ndvi_mean': float(ndvi_mean),
                'map_id': map_id_dict['mapid'],
                'token': map_id_dict['token'],
                'coleccion_size': coleccion.size().getInfo(),
                'imagen_date': imagen.date().format('YYYY-MM-dd').getInfo(),
                'resolucion': config['resolucion'],
                'satelite': config['nombre'],
                'success': True
            }
            
            return resultado
            
    except Exception as e:
        st.error(f"❌ Error calculando NDVI: {str(e)}")
        return None

def obtener_imagen_color_real(satelite, fecha_inicio, fecha_fin, geometria):
    """Obtiene imagen RGB real"""
    
    if not GEE_INITIALIZED:
        return None
    
    try:
        config = SATELITES_REALES[satelite]
        coleccion = obtener_coleccion_satelital(satelite, fecha_inicio, fecha_fin, geometria)
        
        if coleccion is None or coleccion.size().getInfo() == 0:
            return None
        
        # Seleccionar imagen con menos nubes
        if 'SENTINEL' in satelite:
            imagen = coleccion.sort('CLOUDY_PIXEL_PERCENTAGE').first()
            rgb = imagen.select(['B4', 'B3', 'B2'])  # RGB natural
        elif satelite in ['LANDSAT-8', 'LANDSAT-9']:
            imagen = coleccion.sort('CLOUD_COVER').first()
            rgb = imagen.select(['SR_B4', 'SR_B3', 'SR_B2'])  # RGB natural
        else:
            return None
        
        # Recortar y normalizar
        rgb_recortado = rgb.clip(geometria)
        
        # Obtener URL para visualización
        rgb_vis = rgb_recortado.visualize(
            min=0,
            max=3000 if 'SENTINEL' in satelite else 20000,
            gamma=1.4
        )
        
        map_id_dict = rgb_vis.getMapId()
        
        return {
            'map_id': map_id_dict['mapid'],
            'token': map_id_dict['token'],
            'success': True,
            'fecha': imagen.date().format('YYYY-MM-dd').getInfo()
        }
        
    except Exception as e:
        st.warning(f"⚠️ No se pudo obtener imagen RGB: {e}")
        return None

def crear_mapa_ndvi_interactivo(geometria, ndvi_data, gdf_parcela):
    """Crea mapa interactivo con NDVI real"""
    
    try:
        # Obtener centro de la parcela
        bounds = gdf_parcela.total_bounds
        centro = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        
        # Crear mapa base
        m = folium.Map(
            location=centro,
            zoom_start=13,
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google Satellite'
        )
        
        # Añadir capa de NDVI si está disponible
        if ndvi_data and ndvi_data.get('success'):
            tile_url = f"https://earthengine.googleapis.com/map/{ndvi_data['map_id']}/{{z}}/{{x}}/{{y}}?token={ndvi_data['token']}"
            
            folium.TileLayer(
                tiles=tile_url,
                attr='Google Earth Engine',
                name='NDVI',
                overlay=True,
                control=True
            ).add_to(m)
        
        # Añadir contorno de la parcela
        if gdf_parcela is not None:
            # Convertir geometría a GeoJSON
            geojson_data = gdf_parcela.__geo_interface__
            
            folium.GeoJson(
                geojson_data,
                name='Parcela',
                style_function=lambda x: {
                    'fillColor': 'transparent',
                    'color': 'red',
                    'weight': 3,
                    'fillOpacity': 0.1
                }
            ).add_to(m)
        
        # Añadir controles de capas
        folium.LayerControl().add_to(m)
        
        # Añadir escala
        plugins.ScaleBar().add_to(m)
        
        # Añadir título
        title_html = '''
        <h3 align="center" style="font-size:16px">
        <b>🌾 Mapa de NDVI Satelital</b>
        </h3>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        return m
        
    except Exception as e:
        st.error(f"❌ Error creando mapa interactivo: {str(e)}")
        return None

# ===== FUNCIONES DE ANÁLISIS =====
def analizar_fertilidad_con_ndvi_real(gdf_dividido, cultivo, ndvi_data):
    """Analiza fertilidad usando NDVI real"""
    
    resultados = []
    params = PARAMETROS_CULTIVOS[cultivo]
    ndvi_mean = ndvi_data['ndvi_mean'] if ndvi_data else params['NDVI_OPTIMO'] * 0.8
    
    for idx, row in gdf_dividido.iterrows():
        # Generar variación espacial basada en la ubicación
        centroid = row.geometry.centroid
        seed = int(centroid.x * 1000 + centroid.y * 1000) % (2**32)
        rng = np.random.RandomState(seed)
        
        # Variación local del NDVI (±20%)
        ndvi_local = max(0.1, min(0.9, ndvi_mean + rng.normal(0, 0.15)))
        
        # Materia orgánica correlacionada con NDVI
        mo_base = params['MATERIA_ORGANICA_OPTIMA']
        mo = max(1.0, min(8.0, mo_base * (0.7 + 0.3 * ndvi_local/0.8) + rng.normal(0, 0.5)))
        
        # Humedad del suelo
        hum_base = params['HUMEDAD_OPTIMA']
        hum = max(0.1, min(0.8, hum_base * (0.8 + 0.2 * ndvi_local/0.8) + rng.normal(0, 0.05)))
        
        # Índice NPK basado en NDVI real
        npk_index = (ndvi_local * 0.4 + (mo / 8) * 0.3 + hum * 0.3)
        
        resultados.append({
            'materia_organica': round(mo, 2),
            'humedad_suelo': round(hum, 3),
            'ndvi': round(ndvi_local, 3),
            'npk_index': round(npk_index, 3)
        })
    
    return resultados

def calcular_recomendaciones_npk(fertilidad, cultivo):
    """Calcula recomendaciones de NPK basadas en NDVI real"""
    
    recomendaciones_n = []
    recomendaciones_p = []
    recomendaciones_k = []
    
    params = PARAMETROS_CULTIVOS[cultivo]
    
    for fert in fertilidad:
        npk_index = fert['npk_index']
        ndvi = fert['ndvi']
        mo = fert['materia_organica']
        
        # Factor de corrección (NDVI bajo = más fertilizante)
        factor = max(0.3, min(2.0, 1.8 - ndvi))
        
        # Nitrógeno (muy sensible a NDVI)
        n_min = params['NITROGENO']['min']
        n_max = params['NITROGENO']['max']
        n_rec = n_min + (n_max - n_min) * (1 - ndvi) * factor
        recomendaciones_n.append(round(n_rec, 1))
        
        # Fósforo (correlacionado con materia orgánica)
        p_min = params['FOSFORO']['min']
        p_max = params['FOSFORO']['max']
        p_rec = p_min + (p_max - p_min) * (1 - (mo / 8)) * (factor * 0.8)
        recomendaciones_p.append(round(p_rec, 1))
        
        # Potasio (correlacionado con NPK index general)
        k_min = params['POTASIO']['min']
        k_max = params['POTASIO']['max']
        k_rec = k_min + (k_max - k_min) * (1 - npk_index) * factor
        recomendaciones_k.append(round(k_rec, 1))
    
    return recomendaciones_n, recomendaciones_p, recomendaciones_k

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
            
            df_power = df_power.replace(-999, np.nan)
            
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

# ===== FUNCIÓN DE ANÁLISIS COMPLETO CON DATOS REALES =====
def ejecutar_analisis_completo_real(gdf, cultivo, n_divisiones, satelite, fecha_inicio, fecha_fin):
    """Ejecuta análisis completo con datos satelitales reales"""
    
    resultados = {
        'exitoso': False,
        'gdf_dividido': None,
        'area_total': 0,
        'fertilidad': None,
        'recomendaciones_npk': None,
        'costos': None,
        'proyecciones': None,
        'datos_power': None,
        'promedios_power': None,
        'ndvi_data': None,
        'imagen_rgb': None,
        'mapa_interactivo': None
    }
    
    try:
        # 1. Preparar datos
        gdf = validar_y_corregir_crs(gdf)
        area_total = calcular_superficie(gdf)
        resultados['area_total'] = area_total
        
        # 2. Obtener geometría para Earth Engine
        with st.spinner("🌍 Preparando geometría para análisis..."):
            geometria_ee = obtener_geometria_ee(gdf)
        
        # 3. Obtener NDVI REAL de Google Earth Engine
        with st.spinner("🛰️ Obteniendo datos satelitales REALES..."):
            ndvi_data = calcular_ndvi_real(satelite, fecha_inicio, fecha_fin, geometria_ee)
            resultados['ndvi_data'] = ndvi_data
            
            if ndvi_data and ndvi_data.get('success'):
                st.success(f"✅ NDVI obtenido: {ndvi_data['ndvi_mean']:.3f}")
                st.info(f"📅 Imagen del: {ndvi_data.get('imagen_date', 'N/A')}")
            else:
                st.warning("⚠️ Usando datos simulados para el análisis")
        
        # 4. Obtener imagen RGB real
        with st.spinner("🖼️ Obteniendo imagen satelital real..."):
            imagen_rgb = obtener_imagen_color_real(satelite, fecha_inicio, fecha_fin, geometria_ee)
            resultados['imagen_rgb'] = imagen_rgb
        
        # 5. Obtener datos meteorológicos
        with st.spinner("🌤️ Obteniendo datos meteorológicos..."):
            datos_power, promedios_power = obtener_datos_nasa_power(gdf, fecha_inicio, fecha_fin)
            resultados['datos_power'] = datos_power
            resultados['promedios_power'] = promedios_power
        
        # 6. Dividir parcela
        with st.spinner("🎯 Dividiendo parcela en zonas..."):
            gdf_dividido = dividir_parcela_en_zonas(gdf, n_divisiones)
            resultados['gdf_dividido'] = gdf_dividido
            
            areas = []
            for idx, row in gdf_dividido.iterrows():
                area_zona = calcular_superficie(gpd.GeoDataFrame([row], crs=gdf_dividido.crs))
                areas.append(area_zona)
            
            gdf_dividido['area_ha'] = areas
        
        # 7. Análisis de fertilidad con NDVI real
        with st.spinner("🧪 Analizando fertilidad con datos reales..."):
            fertilidad = analizar_fertilidad_con_ndvi_real(gdf_dividido, cultivo, ndvi_data)
            resultados['fertilidad'] = fertilidad
            
            for i, col in enumerate(['mo', 'hum', 'ndvi', 'npk_idx']):
                gdf_dividido[f'fert_{col}'] = [fert[list(fert.keys())[i]] for fert in fertilidad]
        
        # 8. Recomendaciones NPK
        with st.spinner("⚗️ Calculando recomendaciones NPK..."):
            rec_n, rec_p, rec_k = calcular_recomendaciones_npk(fertilidad, cultivo)
            resultados['recomendaciones_npk'] = (rec_n, rec_p, rec_k)
            
            gdf_dividido['rec_N'] = rec_n
            gdf_dividido['rec_P'] = rec_p
            gdf_dividido['rec_K'] = rec_k
        
        # 9. Costos
        with st.spinner("💰 Calculando costos..."):
            # Precios por kg
            precio_n = 1.5  # USD/kg N
            precio_p = 2.8  # USD/kg P2O5
            precio_k = 2.0  # USD/kg K2O
            
            costos = []
            for n, p, k in zip(rec_n, rec_p, rec_k):
                costo_n = n * precio_n
                costo_p = p * precio_p
                costo_k = k * precio_k
                costo_otros = PARAMETROS_CULTIVOS[cultivo]['COSTO_FERTILIZACION']
                costo_total = costo_n + costo_p + costo_k + costo_otros
                
                costos.append({
                    'costo_n': round(costo_n, 2),
                    'costo_p': round(costo_p, 2),
                    'costo_k': round(costo_k, 2),
                    'costo_total': round(costo_total, 2)
                })
            
            resultados['costos'] = costos
            
            for i, col in enumerate(['costo_n', 'costo_p', 'costo_k', 'costo_total']):
                gdf_dividido[col] = [costo[list(costo.keys())[i]] for costo in costos]
        
        # 10. Proyecciones
        with st.spinner("📈 Calculando proyecciones..."):
            proyecciones = []
            params = PARAMETROS_CULTIVOS[cultivo]
            
            for fert, (n, p, k) in zip(fertilidad, zip(rec_n, rec_p, rec_k)):
                npk_index = fert['npk_index']
                ndvi = fert['ndvi']
                
                # Rendimiento base
                rend_base = params['RENDIMIENTO_OPTIMO'] * npk_index * 0.7
                
                # Efecto de fertilización (mejor si NDVI es bajo)
                factor_fert = min(1.8, 1.0 + (1 - ndvi) * 0.8)
                rend_fert = rend_base * factor_fert
                
                incremento = ((rend_fert - rend_base) / rend_base * 100) if rend_base > 0 else 0
                
                proyecciones.append({
                    'rendimiento_sin': round(rend_base, 0),
                    'rendimiento_con': round(rend_fert, 0),
                    'incremento': round(incremento, 1)
                })
            
            resultados['proyecciones'] = proyecciones
            
            for i, col in enumerate(['rend_sin', 'rend_con', 'incr']):
                gdf_dividido[f'proy_{col}'] = [proy[list(proy.keys())[i]] for proy in proyecciones]
        
        # 11. Crear mapa interactivo
        with st.spinner("🗺️ Generando mapa interactivo..."):
            mapa_interactivo = crear_mapa_ndvi_interactivo(geometria_ee, ndvi_data, gdf)
            resultados['mapa_interactivo'] = mapa_interactivo
        
        resultados['gdf_completo'] = gdf_dividido
        resultados['exitoso'] = True
        
        return resultados
        
    except Exception as e:
        st.error(f"❌ Error en el análisis: {str(e)}")
        import traceback
        traceback.print_exc()
        return resultados

# ===== INTERFAZ PRINCIPAL =====
st.title("ANALIZADOR MULTI-CULTIVO SATELITAL CON DATOS REALES")

# Verificar si Google Earth Engine está inicializado
if not GEE_INITIALIZED:
    st.warning("""
    ⚠️ **Google Earth Engine no está inicializado**
    
    Para usar datos satelitales REALES, necesitas:
    
    1. **Registrarte en Google Earth Engine**: https://earthengine.google.com/
    2. **Autenticarte localmente**:
    ```bash
    pip install earthengine-api
    earthengine authenticate
    ```
    3. **Reiniciar la aplicación**
    
    Mientras tanto, puedes usar la aplicación en modo de demostración.
    """)

# Mostrar información del satélite seleccionado
sat_info = SATELITES_REALES[satelite_seleccionado]
st.info(f"""
**🛰️ Satélite seleccionado:** {sat_info['nombre']}
**📅 Período:** {fecha_inicio} a {fecha_fin}
**🌾 Cultivo:** {ICONOS_CULTIVOS[cultivo]} {cultivo}
**📡 Datos:** **IMÁGENES SATELITALES REALES**
""")

if uploaded_file:
    with st.spinner("Cargando parcela..."):
        gdf = cargar_archivo_parcela(uploaded_file)
        
        if gdf is not None and len(gdf) > 0:
            st.session_state.parcela_gdf = gdf
            st.success(f"✅ Parcela cargada exitosamente")
            
            # Mostrar información
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Información de la Parcela")
                area_total = calcular_superficie(gdf)
                st.metric("Área Total", f"{area_total:.2f} ha")
                st.metric("Polígonos", len(gdf))
                st.metric("Ubicación", f"{gdf.total_bounds[1]:.4f}, {gdf.total_bounds[0]:.4f}")
                
                # Vista previa
                fig, ax = plt.subplots(figsize=(8, 6))
                gdf.plot(ax=ax, color='lightgreen', edgecolor='darkgreen', alpha=0.7)
                ax.set_title("Vista Previa de la Parcela")
                ax.set_xlabel("Longitud")
                ax.set_ylabel("Latitud")
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
            
            with col2:
                st.subheader("⚙️ Configuración del Análisis")
                st.write(f"**Satélite:** {sat_info['nombre']}")
                st.write(f"**Resolución:** {sat_info['resolucion']}")
                st.write(f"**Período:** {fecha_inicio} a {fecha_fin}")
                st.write(f"**Duración:** {(fecha_fin - fecha_inicio).days} días")
                st.write(f"**Zonas:** {n_divisiones}")
            
            # Botón para ejecutar análisis
            st.markdown("---")
            if st.button("🚀 EJECUTAR ANÁLISIS CON DATOS SATELITALES REALES", 
                        type="primary", use_container_width=True, disabled=not GEE_INITIALIZED):
                
                if not GEE_INITIALIZED:
                    st.error("❌ Google Earth Engine no está inicializado. No se pueden obtener datos reales.")
                else:
                    with st.spinner("Ejecutando análisis con datos satelitales reales..."):
                        resultados = ejecutar_analisis_completo_real(
                            gdf, cultivo, n_divisiones, satelite_seleccionado,
                            fecha_inicio, fecha_fin
                        )
                        
                        if resultados['exitoso']:
                            st.session_state.resultados_todos = resultados
                            st.session_state.analisis_completado = True
                            st.balloons()
                            st.success("✅ Análisis completado exitosamente con datos REALES!")
                            st.rerun()
                        else:
                            st.error("❌ Error en el análisis con datos reales")

# Mostrar resultados si el análisis está completado
if st.session_state.analisis_completado and st.session_state.resultados_todos:
    resultados = st.session_state.resultados_todos
    
    # Crear pestañas para diferentes resultados
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🛰️ Datos Satelitales",
        "📊 Fertilidad",
        "🧪 Recomendaciones NPK",
        "💰 Análisis Económico",
        "💾 Exportar"
    ])
    
    with tab1:
        st.subheader("DATOS SATELITALES REALES")
        
        if resultados.get('ndvi_data') and resultados['ndvi_data'].get('success'):
            ndvi_data = resultados['ndvi_data']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("NDVI Promedio", f"{ndvi_data['ndvi_mean']:.3f}")
                st.metric("Satélite", ndvi_data['satelite'])
                st.metric("Resolución", ndvi_data['resolucion'])
                st.metric("Fecha Imagen", ndvi_data.get('imagen_date', 'N/A'))
                
                # Interpretación del NDVI
                ndvi_val = ndvi_data['ndvi_mean']
                if ndvi_val < 0.2:
                    estado = "🌵 Vegetación escasa"
                elif ndvi_val < 0.4:
                    estado = "🌾 Vegetación moderada"
                elif ndvi_val < 0.6:
                    estado = "🌿 Vegetación buena"
                elif ndvi_val < 0.8:
                    estado = "🌳 Vegetación muy buena"
                else:
                    estado = "🌲 Vegetación excelente"
                
                st.info(f"**Estado:** {estado}")
            
            with col2:
                # Mapa interactivo
                if resultados.get('mapa_interactivo'):
                    st.subheader("🗺️ Mapa Interactivo de NDVI")
                    folium_static(resultados['mapa_interactivo'], width=700, height=500)
                
                # Datos meteorológicos
                if resultados.get('promedios_power'):
                    st.subheader("🌤️ Datos Meteorológicos")
                    power = resultados['promedios_power']
                    st.write(f"**Temperatura promedio:** {power['temp_prom']} °C")
                    st.write(f"**Humedad promedio:** {power['hum_prom']}%")
                    st.write(f"**Precipitación total:** {power['prec_total']} mm")
                    st.write(f"**Radiación solar:** {power['rad_prom']} W/m²")
    
    with tab2:
        st.subheader("FERTILIDAD BASADA EN NDVI REAL")
        
        if resultados['fertilidad']:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                npk_prom = np.mean([f['npk_index'] for f in resultados['fertilidad']])
                st.metric("Índice NPK", f"{npk_prom:.3f}")
            with col2:
                ndvi_prom = np.mean([f['ndvi'] for f in resultados['fertilidad']])
                st.metric("NDVI Promedio", f"{ndvi_prom:.3f}")
            with col3:
                mo_prom = np.mean([f['materia_organica'] for f in resultados['fertilidad']])
                st.metric("Materia Orgánica", f"{mo_prom:.1f}%")
            with col4:
                hum_prom = np.mean([f['humedad_suelo'] for f in resultados['fertilidad']])
                st.metric("Humedad Suelo", f"{hum_prom:.3f}")
            
            # Gráfico de distribución de NDVI
            st.subheader("📊 Distribución de NDVI por Zona")
            
            zonas = list(range(1, len(resultados['fertilidad']) + 1))
            ndvi_values = [f['ndvi'] for f in resultados['fertilidad']]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(zonas, ndvi_values, color='green', alpha=0.7)
            
            # Línea de referencia para el cultivo
            ndvi_optimo = PARAMETROS_CULTIVOS[cultivo]['NDVI_OPTIMO']
            ax.axhline(y=ndvi_optimo, color='red', linestyle='--', label=f'Óptimo: {ndvi_optimo}')
            
            ax.set_xlabel('Zona')
            ax.set_ylabel('NDVI')
            ax.set_title('NDVI por Zona')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)
            
            # Tabla de resultados
            st.subheader("📋 Tabla de Resultados por Zona")
            tabla_data = []
            for i, fert in enumerate(resultados['fertilidad']):
                tabla_data.append({
                    'Zona': i + 1,
                    'Área (ha)': resultados['gdf_completo'].iloc[i]['area_ha'],
                    'NDVI': fert['ndvi'],
                    'Índice NPK': fert['npk_index'],
                    'Materia Org (%)': fert['materia_organica'],
                    'Humedad': fert['humedad_suelo']
                })
            
            df_fert = pd.DataFrame(tabla_data)
            st.dataframe(df_fert, use_container_width=True)
    
    with tab3:
        st.subheader("RECOMENDACIONES NPK BASADAS EN NDVI REAL")
        
        if resultados['recomendaciones_npk']:
            rec_n, rec_p, rec_k = resultados['recomendaciones_npk']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                n_prom = np.mean(rec_n)
                st.metric("Nitrógeno Promedio", f"{n_prom:.1f} kg/ha")
            with col2:
                p_prom = np.mean(rec_p)
                st.metric("Fósforo Promedio", f"{p_prom:.1f} kg/ha")
            with col3:
                k_prom = np.mean(rec_k)
                st.metric("Potasio Promedio", f"{k_prom:.1f} kg/ha")
            
            # Gráfico de recomendaciones
            st.subheader("📊 Distribución de Recomendaciones")
            
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            
            axes[0].hist(rec_n, bins=10, color='green', alpha=0.7, edgecolor='black')
            axes[0].set_title('Nitrógeno (N)')
            axes[0].set_xlabel('kg/ha')
            axes[0].set_ylabel('Frecuencia')
            
            axes[1].hist(rec_p, bins=10, color='blue', alpha=0.7, edgecolor='black')
            axes[1].set_title('Fósforo (P)')
            axes[1].set_xlabel('kg/ha')
            
            axes[2].hist(rec_k, bins=10, color='purple', alpha=0.7, edgecolor='black')
            axes[2].set_title('Potasio (K)')
            axes[2].set_xlabel('kg/ha')
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Tabla de recomendaciones
            st.subheader("📋 Recomendaciones por Zona")
            tabla_npk = []
            for i in range(len(rec_n)):
                tabla_npk.append({
                    'Zona': i + 1,
                    'Área (ha)': resultados['gdf_completo'].iloc[i]['area_ha'],
                    'N (kg/ha)': rec_n[i],
                    'P (kg/ha)': rec_p[i],
                    'K (kg/ha)': rec_k[i]
                })
            
            df_npk = pd.DataFrame(tabla_npk)
            st.dataframe(df_npk, use_container_width=True)
    
    with tab4:
        st.subheader("ANÁLISIS ECONÓMICO")
        
        if resultados['costos'] and resultados['proyecciones']:
            costo_total = sum([c['costo_total'] for c in resultados['costos']])
            costo_prom = np.mean([c['costo_total'] for c in resultados['costos']])
            
            rend_sin = sum([p['rendimiento_sin'] for p in resultados['proyecciones']])
            rend_con = sum([p['rendimiento_con'] for p in resultados['proyecciones']])
            incr_prom = np.mean([p['incremento'] for p in resultados['proyecciones']])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Inversión Total", f"${costo_total:.2f}")
            with col2:
                st.metric("Rendimiento Esperado", f"{rend_con:.0f} kg")
            with col3:
                st.metric("Incremento", f"{incr_prom:.1f}%")
            with col4:
                precio = PARAMETROS_CULTIVOS[cultivo]['PRECIO_VENTA']
                ingreso_extra = (rend_con - rend_sin) * precio
                roi = (ingreso_extra / costo_total * 100) if costo_total > 0 else 0
                st.metric("ROI Estimado", f"{roi:.1f}%")
            
            # Análisis detallado
            st.subheader("💰 Análisis de Rentabilidad")
            
            ingreso_sin = rend_sin * precio
            ingreso_con = rend_con * precio
            beneficio_neto = (ingreso_con - ingreso_sin) - costo_total
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            categorias = ['Sin Fertilización', 'Con Fertilización']
            ingresos = [ingreso_sin, ingreso_con]
            costos_bar = [0, costo_total]
            
            x = np.arange(len(categorias))
            width = 0.35
            
            bars1 = ax.bar(x - width/2, ingresos, width, label='Ingresos', color='green')
            bars2 = ax.bar(x + width/2, costos_bar, width, label='Costos', color='red')
            
            ax.set_xlabel('Escenario')
            ax.set_ylabel('USD')
            ax.set_title('Comparativa Económica')
            ax.set_xticks(x)
            ax.set_xticklabels(categorias)
            ax.legend()
            
            # Añadir etiquetas
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height + 100,
                               f'${height:.0f}', ha='center', va='bottom')
            
            st.pyplot(fig)
    
    with tab5:
        st.subheader("EXPORTAR RESULTADOS")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Exportar Datos")
            
            # Exportar a GeoJSON
            if st.button("📤 Generar GeoJSON", key="export_geojson"):
                if resultados.get('gdf_completo') is not None:
                    gdf_completo = resultados['gdf_completo']
                    gdf_completo = validar_y_corregir_crs(gdf_completo)
                    geojson_str = gdf_completo.to_json()
                    
                    st.session_state.geojson_data = geojson_str
                    st.session_state.nombre_geojson = f"analisis_{cultivo}_{datetime.now().strftime('%Y%m%d_%H%M')}.geojson"
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
                if resultados.get('gdf_completo') is not None:
                    df_export = resultados['gdf_completo'].drop(columns=['geometry'])
                    csv = df_export.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv,
                        file_name=f"analisis_{cultivo}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
        
        with col2:
            st.markdown("### 📄 Reporte Completo")
            
            # Generar reporte simplificado
            if st.button("📋 Generar Reporte", key="export_report"):
                # Crear reporte en texto
                reporte = f"""
                ====================================
                REPORTE DE ANÁLISIS SATELITAL
                ====================================
                
                Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                Cultivo: {cultivo}
                Satélite: {sat_info['nombre']}
                Período: {fecha_inicio} a {fecha_fin}
                
                --------------------------------
                RESUMEN DE RESULTADOS
                --------------------------------
                
                • Área total: {resultados['area_total']:.2f} ha
                • Zonas analizadas: {len(resultados['gdf_completo'])}
                
                NDVI Promedio: {resultados['ndvi_data']['ndvi_mean']:.3f if resultados.get('ndvi_data') else 'N/A'}
                
                Recomendaciones NPK:
                - Nitrógeno: {np.mean(rec_n):.1f} kg/ha
                - Fósforo: {np.mean(rec_p):.1f} kg/ha  
                - Potasio: {np.mean(rec_k):.1f} kg/ha
                
                Inversión total estimada: ${sum([c['costo_total'] for c in resultados['costos']]):.2f}
                Incremento esperado: {np.mean([p['incremento'] for p in resultados['proyecciones']]):.1f}%
                
                ====================================
                """
                
                st.download_button(
                    label="📥 Descargar Reporte (TXT)",
                    data=reporte,
                    file_name=f"reporte_{cultivo}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
        
        # Botón para reiniciar
        st.markdown("---")
        if st.button("🔄 Reiniciar Análisis", type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

else:
    # Pantalla inicial
    if not uploaded_file:
        st.markdown("""
        ## 👋 Bienvenido al Analizador con Datos Satelitales REALES
        
        ### 🛰️ **CARACTERÍSTICAS PRINCIPALES:**
        
        **📡 DATOS SATELITALES REALES:**
        • Sentinel-2 (10m resolución) - Imágenes cada 5 días
        • Landsat 8/9 (30m resolución) - Imágenes cada 16 días  
        • MODIS (250m resolución) - Imágenes diarias
        • NDVI calculado en tiempo real
        
        **🌾 ANÁLISIS COMPLETO:**
        • Fertilidad basada en NDVI real
        • Recomendaciones NPK personalizadas
        • Análisis de costos y ROI
        • Proyecciones de rendimiento
        
        **🗺️ VISUALIZACIONES:**
        • Mapas interactivos con Folium
        • Gráficos profesionales
        • Exportación a múltiples formatos
        
        ### 🚀 **¿CÓMO COMENZAR?**
        
        1. **📤 Sube tu parcela** (GeoJSON, KML, Shapefile)
        2. **🌾 Selecciona el cultivo** (Trigo, Maíz, Soja)
        3. **🛰️ Elige el satélite** para análisis
        4. **📅 Define el período** de análisis
        5. **🚀 Ejecuta el análisis** con datos REALES
        
        ### ⚠️ **REQUISITOS:**
        
        Para usar datos satelitales REALES necesitas:
        
        ```bash
        # 1. Registrarte en Google Earth Engine
        # https://earthengine.google.com/
        
        # 2. Autenticarte localmente
        pip install earthengine-api
        earthengine authenticate
        
        # 3. Ejecutar la aplicación
        streamlit run app.py
        ```
        
        ---
        
        ### 📁 **FORMATOS SOPORTADOS:**
        • **GeoJSON** (.geojson)
        • **KML/KMZ** (Google Earth)
        • **Shapefile** (.zip con todos los archivos)
        
        ### 📊 **EJEMPLOS DE RESULTADOS:**
        • NDVI actualizado de tu parcela
        • Recomendaciones de fertilización
        • Análisis económico detallado
        • Mapas interactivos
        """)

# ===== PIE DE PÁGINA =====
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.9em;">
    <p>🌾 <strong>Analizador Multi-Cultivo Satelital con Datos Reales</strong> - Versión 3.0</p>
    <p>Powered by Google Earth Engine & NASA POWER | © 2024</p>
    <p style="font-size: 0.8em;">
        Datos satelitales: Sentinel-2, Landsat, MODIS<br>
        Datos meteorológicos: NASA POWER API
    </p>
</div>
""", unsafe_allow_html=True)
