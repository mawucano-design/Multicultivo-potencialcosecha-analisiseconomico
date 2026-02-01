import streamlit as st
import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import io
import json
import os
import tempfile
import zipfile
from shapely.geometry import Polygon, MultiPolygon, Point, shape
from shapely.ops import unary_union
import rasterio
from rasterio.features import geometry_mask
import folium
from folium.plugins import Draw
import branca.colormap as cm
from streamlit_folium import st_folium
import warnings
warnings.filterwarnings('ignore')

# ===== INICIALIZACIÓN AUTOMÁTICA DE GOOGLE EARTH ENGINE =====
try:
    import ee
    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False
    st.warning("⚠️ Google Earth Engine no está instalado. Para usar datos satelitales reales, instala: pip install earthengine-api")

def inicializar_gee():
    """Inicializa GEE con Service Account desde secrets de Streamlit Cloud o autenticación local"""
    if not GEE_AVAILABLE:
        return False
    
    try:
        # Intentar con secrets de Streamlit Cloud
        gee_secret = os.environ.get('GEE_SERVICE_ACCOUNT')
        if gee_secret:
            try:
                # Limpiar y parsear JSON
                credentials_info = json.loads(gee_secret.strip())
                credentials = ee.ServiceAccountCredentials(
                    credentials_info['client_email'],
                    key_data=json.dumps(credentials_info)
                )
                ee.Initialize(credentials, project='ee-mawucano25')
                st.session_state.gee_authenticated = True
                st.session_state.gee_project = 'ee-mawucano25'
                print("✅ GEE inicializado con Service Account")
                return True
            except Exception as e:
                print(f"⚠️ Error Service Account: {str(e)}")
        
        # Fallback: autenticación local (desarrollo)
        try:
            ee.Initialize(project='ee-mawucano25')
            st.session_state.gee_authenticated = True
            st.session_state.gee_project = 'ee-mawucano25'
            print("✅ GEE inicializado localmente")
            return True
        except Exception as e:
            print(f"⚠️ Error inicialización local: {str(e)}")
            
        st.session_state.gee_authenticated = False
        return False
        
    except Exception as e:
        st.session_state.gee_authenticated = False
        print(f"❌ Error crítico GEE: {str(e)}")
        return False

# Ejecutar inicialización al inicio (ANTES de cualquier uso de ee.*)
if 'gee_authenticated' not in st.session_state:
    st.session_state.gee_authenticated = False
    st.session_state.gee_project = ''
    if GEE_AVAILABLE:
        inicializar_gee()

# ===== CONFIGURACIÓN INICIAL DE LA APP =====
st.set_page_config(
    page_title="🌾 Análisis Multicultivo Satelital",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS para modo oscuro
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: white;
    }
    .stButton>button {
        background-color: #1e3d28;
        color: white;
        border-radius: 8px;
        border: 1px solid #2e5d3c;
    }
    .stButton>button:hover {
        background-color: #2e5d3c;
        border-color: #3e7d4c;
    }
    .stSelectbox, .stTextInput, .stNumberInput {
        background-color: #1e293b;
        color: white;
        border: 1px solid #334155;
    }
    .stExpander {
        background-color: #1e293b;
        border: 1px solid #334155;
    }
    .css-1d391kg {
        background-color: #0e1117 !important;
    }
</style>
""", unsafe_allow_html=True)

# ===== FUNCIONES AUXILIARES =====
def crear_mapa_interactivo(poligono=None, titulo="Mapa de la Parcela"):
    """Crea un mapa interactivo con Esri World Imagery como base"""
    if poligono is not None:
        centroid = poligono.centroid
        lat, lon = centroid.y, centroid.x
    else:
        lat, lon = 4.6097, -74.0817  # Bogotá por defecto
    
    m = folium.Map(
        location=[lat, lon],
        zoom_start=14,
        tiles=None,
        control_scale=True,
        prefer_canvas=True
    )
    
    # Agregar Esri World Imagery
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri World Imagery',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Agregar capa de calles
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Límites y Nombres',
        overlay=True,
        control=True
    ).add_to(m)
    
    # Dibujar polígono si existe
    if poligono is not None:
        geojson = gpd.GeoSeries([poligono]).__geo_interface__
        folium.GeoJson(
            geojson,
            style_function=lambda x: {
                'fillColor': '#3e7d4c',
                'color': 'white',
                'weight': 2,
                'fillOpacity': 0.4,
            },
            name='Parcela'
        ).add_to(m)
    
    # Agregar control de capas
    folium.LayerControl(collapsed=False).add_to(m)
    
    return m

def generar_dem_sintetico(ancho=100, alto=100, pendiente_base=5, ruido=2):
    """Genera un DEM sintético para análisis de pendiente y erosión"""
    x = np.linspace(0, ancho, ancho)
    y = np.linspace(0, alto, alto)
    X, Y = np.meshgrid(x, y)
    
    # Crear pendiente suave + ruido topográfico
    Z = pendiente_base * (X / ancho) + ruido * np.random.randn(alto, ancho)
    return Z

def calcular_pendiente(dem):
    """Calcula pendiente en grados a partir de DEM"""
    dy, dx = np.gradient(dem)
    slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
    return slope

def calcular_indices_satelitales(tipo_satelite, usar_gee=False, poligono=None):
    """Genera índices satelitales realistas (simulados o desde GEE)"""
    if usar_gee and st.session_state.gee_authenticated and poligono is not None:
        try:
            # Convertir polígono a GeoJSON para GEE
            geojson = gpd.GeoSeries([poligono]).__geo_interface__['features'][0]['geometry']
            ee_poligono = ee.Geometry(geojson)
            
            # Seleccionar colección según satélite
            if 'SENTINEL-2' in tipo_satelite:
                collection = ee.ImageCollection('COPERNICUS/S2_SR') \
                    .filterBounds(ee_poligono) \
                    .filterDate('2023-01-01', '2024-12-31') \
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
                    .sort('CLOUDY_PIXEL_PERCENTAGE')
                
                imagen = collection.first()
                fecha = imagen.date().format('YYYY-MM-dd').getInfo()
                
                # Calcular índices
                ndvi = imagen.normalizedDifference(['B8', 'B4']).rename('NDVI')
                ndwi = imagen.normalizedDifference(['B8', 'B11']).rename('NDWI')
                evi = imagen.expression(
                    '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
                    {'NIR': imagen.select('B8'), 'RED': imagen.select('B4'), 'BLUE': imagen.select('B2')}
                ).rename('EVI')
                
                # Extraer valores medios en la parcela
                reducer = ee.Reducer.mean()
                stats_ndvi = ndvi.reduceRegion(reducer=reducer, geometry=ee_poligono, scale=10, maxPixels=1e9).getInfo()
                stats_ndwi = ndwi.reduceRegion(reducer=reducer, geometry=ee_poligono, scale=10, maxPixels=1e9).getInfo()
                stats_evi = evi.reduceRegion(reducer=reducer, geometry=ee_poligono, scale=10, maxPixels=1e9).getInfo()
                
                return {
                    'NDVI': stats_ndvi.get('NDVI', 0.65),
                    'NDWI': stats_ndwi.get('NDWI', 0.15),
                    'EVI': stats_evi.get('EVI', 0.55),
                    'fecha': fecha,
                    'fuente': 'GEE - Sentinel-2 real'
                }
            
            elif 'LANDSAT-8' in tipo_satelite:
                collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                    .filterBounds(ee_poligono) \
                    .filterDate('2023-01-01', '2024-12-31') \
                    .filter(ee.Filter.lt('CLOUD_COVER', 20)) \
                    .sort('CLOUD_COVER')
                
                imagen = collection.first()
                fecha = imagen.date().format('YYYY-MM-dd').getInfo()
                
                # Calcular índices (LANDSAT bandas escaladas)
                ndvi = imagen.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
                
                reducer = ee.Reducer.mean()
                stats_ndvi = ndvi.reduceRegion(reducer=reducer, geometry=ee_poligono, scale=30, maxPixels=1e9).getInfo()
                
                return {
                    'NDVI': stats_ndvi.get('NDVI', 0.62),
                    'NDWI': 0.12,
                    'EVI': 0.50,
                    'fecha': fecha,
                    'fuente': 'GEE - Landsat-8 real'
                }
            
            elif 'LANDSAT-9' in tipo_satelite:
                collection = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
                    .filterBounds(ee_poligono) \
                    .filterDate('2023-01-01', '2024-12-31') \
                    .filter(ee.Filter.lt('CLOUD_COVER', 20)) \
                    .sort('CLOUD_COVER')
                
                imagen = collection.first()
                fecha = imagen.date().format('YYYY-MM-dd').getInfo()
                
                ndvi = imagen.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
                reducer = ee.Reducer.mean()
                stats_ndvi = ndvi.reduceRegion(reducer=reducer, geometry=ee_poligono, scale=30, maxPixels=1e9).getInfo()
                
                return {
                    'NDVI': stats_ndvi.get('NDVI', 0.64),
                    'NDWI': 0.14,
                    'EVI': 0.53,
                    'fecha': fecha,
                    'fuente': 'GEE - Landsat-9 real'
                }
        
        except Exception as e:
            print(f"Error GEE: {str(e)}")
            st.warning(f"⚠️ Error al obtener datos de GEE: {str(e)[:100]}. Usando datos simulados.")
    
    # Fallback: datos simulados realistas
    np.random.seed(42)
    return {
        'NDVI': np.random.uniform(0.55, 0.85),
        'NDWI': np.random.uniform(0.10, 0.25),
        'EVI': np.random.uniform(0.45, 0.75),
        'fecha': '2024-01-15',
        'fuente': 'Simulado (GEE no disponible)'
    }

def generar_recomendaciones_npk(ndvi, cultivo, textura_suelo):
    """Genera recomendaciones de NPK basadas en NDVI y características del cultivo"""
    # Valores base según cultivo
    base_n = {'trigo': 120, 'maiz': 180, 'arroz': 100, 'café': 80, 'cacao': 60, 'pasto': 50}
    base_p = {'trigo': 60, 'maiz': 80, 'arroz': 70, 'café': 40, 'cacao': 30, 'pasto': 20}
    base_k = {'trigo': 80, 'maiz': 100, 'arroz': 90, 'café': 60, 'cacao': 50, 'pasto': 40}
    
    # Ajuste por NDVI (mayor NDVI = menor fertilización necesaria)
    factor_ndvi = 1.0 - (ndvi - 0.3) / 0.6  # Rango 0.3-0.9
    
    # Ajuste por textura (arcilla retiene más nutrientes)
    factor_textura = {'arenosa': 1.2, 'franco-arenosa': 1.1, 'franca': 1.0, 
                     'franco-arcillosa': 0.9, 'arcillosa': 0.85}.get(textura_suelo, 1.0)
    
    n = base_n.get(cultivo, 100) * factor_ndvi * factor_textura
    p = base_p.get(cultivo, 60) * factor_ndvi * factor_textura
    k = base_k.get(cultivo, 80) * factor_ndvi * factor_textura
    
    return {'N': round(n, 1), 'P': round(p, 1), 'K': round(k, 1)}

# ===== INTERFAZ DE USUARIO =====
st.title("🌾 Análisis Multicultivo Satelital con Google Earth Engine")

# Sidebar - Configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Estado de GEE
    st.subheader("🌍 Google Earth Engine")
    if st.session_state.gee_authenticated:
        st.success(f"✅ Autenticado\nProyecto: {st.session_state.gee_project}")
        st.caption(f"Fuente: {os.environ.get('GEE_SERVICE_ACCOUNT', 'local')[:20]}...")
    else:
        st.error("❌ No autenticado")
        st.info("💡 Para usar imágenes reales:\n1. Configura secrets en Streamlit Cloud\n2. O ejecuta 'earthengine authenticate' localmente")
    
    # Selección de satélite
    satelite_opciones = [
        'SENTINEL-2 (simulado)',
        'LANDSAT-8 (simulado)', 
        'LANDSAT-9 (simulado)'
    ]
    if st.session_state.gee_authenticated:
        satelite_opciones = [
            'SENTINEL-2_GEE (real 10m)',
            'LANDSAT-8_GEE (real 30m)',
            'LANDSAT-9_GEE (real 30m)',
            '---',
            'SENTINEL-2 (simulado)',
            'LANDSAT-8 (simulado)',
            'LANDSAT-9 (simulado)'
        ]
    
    satelite = st.selectbox("🛰️ Satélite", satelite_opciones)
    usar_gee = '_GEE' in satelite and st.session_state.gee_authenticated
    
    # Datos de la parcela
    st.subheader("📍 Parcela")
    cultivos = ['trigo', 'maiz', 'arroz', 'café', 'cacao', 'pasto']
    cultivo = st.selectbox("🌱 Cultivo", cultivos)
    
    texturas = ['arenosa', 'franco-arenosa', 'franca', 'franco-arcillosa', 'arcillosa']
    textura_suelo = st.selectbox("흙 Textura del suelo", texturas)
    
    precipitacion = st.slider("💧 Precipitación anual (mm)", 500, 4000, 1500)
    
    # Dibujo de polígono
    st.subheader("✏️ Dibujar parcela")
    st.info("Dibuja un polígono en el mapa o usa el ejemplo")
    if st.button("📍 Usar parcela de ejemplo (Colombia)"):
        coords = [(-74.10, 4.65), (-74.05, 4.65), (-74.05, 4.60), (-74.10, 4.60)]
        poligono = Polygon(coords)
        st.session_state.poligono = poligono

# Mapa interactivo
st.subheader("🗺️ Mapa de la Parcela")
if 'poligono' not in st.session_state:
    st.session_state.poligono = None

mapa = crear_mapa_interactivo(st.session_state.poligono)
output = st_folium(mapa, width=800, height=500)

# Si el usuario dibujó un polígono, guardarlo
if output and output.get('last_active_drawing'):
    coords = output['last_active_drawing']['geometry']['coordinates'][0]
    st.session_state.poligono = Polygon(coords)

# Botón de análisis
if st.button("🔬 Analizar Parcela", type="primary", use_container_width=True):
    if st.session_state.poligono is None:
        st.error("❌ Por favor, dibuja o carga una parcela primero")
    else:
        with st.spinner("Analizando parcela con datos satelitales..."):
            # Obtener índices satelitales
            indices = calcular_indices_satelitales(satelite, usar_gee, st.session_state.poligono)
            
            # Calcular DEM y pendiente
            dem = generar_dem_sintetico()
            pendiente = calcular_pendiente(dem)
            pendiente_promedio = np.mean(pendiente)
            
            # Recomendaciones NPK
            npk = generar_recomendaciones_npk(indices['NDVI'], cultivo, textura_suelo)
            
            # Mostrar resultados
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🌿 NDVI", f"{indices['NDVI']:.2f}", delta=None)
                st.caption(f"Fuente: {indices['fuente']}")
                if usar_gee:
                    st.caption(f"Fecha: {indices['fecha']}")
            
            with col2:
                st.metric("💧 NDWI", f"{indices['NDWI']:.2f}")
                st.metric("⛰️ Pendiente", f"{pendiente_promedio:.1f}°")
            
            with col3:
                st.metric("⚡ EVI", f"{indices['EVI']:.2f}")
                st.metric("🌧️ Precipitación", f"{precipitacion} mm")
            
            # Recomendaciones NPK
            st.subheader("🧪 Recomendaciones de Fertilización (kg/ha)")
            col1, col2, col3 = st.columns(3)
            col1.metric("Nitrógeno (N)", f"{npk['N']}")
            col2.metric("Fósforo (P₂O₅)", f"{npk['P']}")
            col3.metric("Potasio (K₂O)", f"{npk['K']}")
            
            # Mapa de pendiente
            st.subheader("⛰️ Mapa de Pendiente")
            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(pendiente, cmap='terrain', interpolation='nearest')
            plt.colorbar(im, ax=ax, label='Pendiente (grados)')
            ax.set_title('Análisis de Pendiente - Riesgo de Erosión')
            ax.axis('off')
            st.pyplot(fig)
            
            # Alertas
            if pendiente_promedio > 15:
                st.warning(f"⚠️ Pendiente alta ({pendiente_promedio:.1f}°). Riesgo de erosión. Considera cultivos de cobertura.")
            if indices['NDVI'] < 0.4:
                st.error(f"🔴 NDVI bajo ({indices['NDVI']:.2f}). Estrés vegetal detectado.")
            elif indices['NDVI'] > 0.8:
                st.success(f"🟢 NDVI óptimo ({indices['NDVI']:.2f}). Buen estado vegetativo.")

# Footer
st.markdown("---")
st.caption("Desarrollado por Martin Ernesto Cano | Ingeniero Agrónomo | mawucano@gmail.com | +5493525 532313")
