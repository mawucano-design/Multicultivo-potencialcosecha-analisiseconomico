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

# === DESACTIVAR ADVERTENCIAS ===
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

# === ESTILOS PERSONALIZADOS ===
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
    color: #ffffff !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e5e7eb !important;
}
[data-testid="stSidebar"] * {
    color: #000000 !important;
}
.stButton > button {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
    color: white !important;
    border: none !important;
    padding: 0.8em 1.5em !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    margin-top: 10px !important;
}
.hero-banner {
    background: linear-gradient(rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 0.95)),
                url('https://images.unsplash.com/photo-1597981309443-6e2d2a4d9c3f?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80') !important;
    background-size: cover !important;
    background-position: center 40% !important;
    padding: 3em 2em !important;
    border-radius: 24px !important;
    margin-bottom: 2em !important;
    text-align: center !important;
}
.hero-title {
    color: #ffffff !important;
    font-size: 2.8em !important;
    font-weight: 900 !important;
    margin-bottom: 0.5em !important;
}
.hero-subtitle {
    color: #cbd5e1 !important;
    font-size: 1.2em !important;
    max-width: 800px !important;
    margin: 0 auto !important;
}
.sidebar-title {
    font-size: 1.3em;
    font-weight: 800;
    margin: 1em 0;
    text-align: center;
    padding: 12px;
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    border-radius: 12px;
    color: #ffffff !important;
}
.metric-card {
    background: rgba(30, 41, 59, 0.8) !important;
    backdrop-filter: blur(10px) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    margin-bottom: 15px !important;
}
</style>
""", unsafe_allow_html=True)

# ===== HERO BANNER =====
st.markdown("""
<div class="hero-banner">
    <h1 class="hero-title">ANALIZADOR MULTI-CULTIVO SATELITAL</h1>
    <p class="hero-subtitle">Potenciado con NASA POWER para agricultura de precisión</p>
</div>
""", unsafe_allow_html=True)

# ===== CONFIGURACIÓN DE CULTIVOS =====
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
    st.markdown('<div class="sidebar-title">⚙️ CONFIGURACIÓN</div>', unsafe_allow_html=True)
    
    cultivo = st.selectbox("Selecciona el cultivo:", ["TRIGO", "MAIZ", "SOJA"])
    
    st.subheader("📅 Rango Temporal")
    fecha_fin = st.date_input("Fecha fin", datetime.now())
    fecha_inicio = st.date_input("Fecha inicio", datetime.now() - timedelta(days=30))
    
    st.subheader("🎯 División de Parcela")
    n_divisiones = st.slider("Número de zonas:", 4, 32, 16)
    
    st.subheader("📤 Subir Parcela")
    uploaded_file = st.file_uploader("Sube tu archivo", type=['zip', 'kml', 'geojson'],
                                     help="Formatos: Shapefile (.zip), KML (.kml), GeoJSON (.geojson)")

# ===== FUNCIONES AUXILIARES =====
def validar_y_corregir_crs(gdf):
    if gdf.crs is None:
        gdf = gdf.set_crs('EPSG:4326', inplace=False)
    elif str(gdf.crs).upper() != 'EPSG:4326':
        gdf = gdf.to_crs('EPSG:4326')
    return gdf

def calcular_superficie(gdf):
    try:
        gdf = validar_y_corregir_crs(gdf)
        gdf_projected = gdf.to_crs('EPSG:3857')
        area_m2 = gdf_projected.geometry.area.sum()
        return area_m2 / 10000
    except:
        try:
            return gdf.geometry.area.sum() / 10000
        except:
            return 0.0

def cargar_archivo_parcela(uploaded_file):
    try:
        if uploaded_file.name.endswith('.zip'):
            with tempfile.TemporaryDirectory() as tmp_dir:
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    zip_ref.extractall(tmp_dir)
                shp_files = [f for f in os.listdir(tmp_dir) if f.endswith('.shp')]
                if shp_files:
                    gdf = gpd.read_file(os.path.join(tmp_dir, shp_files[0]))
                    gdf = validar_y_corregir_crs(gdf)
                    return gdf
                else:
                    st.error("❌ No se encontró archivo .shp en el ZIP")
                    return None
                    
        elif uploaded_file.name.endswith('.geojson'):
            gdf = gpd.read_file(uploaded_file)
            gdf = validar_y_corregir_crs(gdf)
            return gdf
            
        elif uploaded_file.name.endswith('.kml'):
            gdf = gpd.read_file(uploaded_file, driver='KML')
            gdf = validar_y_corregir_crs(gdf)
            return gdf
            
    except Exception as e:
        st.error(f"❌ Error cargando archivo: {str(e)}")
        return None

def dividir_parcela_en_zonas(gdf, n_zonas):
    if len(gdf) == 0:
        return gdf
    
    gdf = validar_y_corregir_crs(gdf)
    parcela_principal = gdf.iloc[0].geometry
    bounds = parcela_principal.bounds
    minx, miny, maxx, maxy = bounds
    
    n_cols = math.ceil(math.sqrt(n_zonas))
    n_rows = math.ceil(n_zonas / n_cols)
    width = (maxx - minx) / n_cols
    height = (maxy - miny) / n_rows
    
    sub_poligonos = []
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
        return gpd.GeoDataFrame({
            'id_zona': range(1, len(sub_poligonos) + 1), 
            'geometry': sub_poligonos
        }, crs='EPSG:4326')
    else:
        return gdf

def analizar_fertilidad(gdf_dividido, cultivo):
    resultados = []
    params = PARAMETROS_CULTIVOS[cultivo]
    
    for idx, row in gdf_dividido.iterrows():
        # Simular datos basados en el cultivo
        materia_organica = np.random.uniform(
            params['MATERIA_ORGANICA_OPTIMA'] * 0.6,
            params['MATERIA_ORGANICA_OPTIMA'] * 1.2
        )
        humedad_suelo = np.random.uniform(
            params['HUMEDAD_OPTIMA'] * 0.5,
            params['HUMEDAD_OPTIMA'] * 1.1
        )
        ndvi = np.random.uniform(
            params['NDVI_OPTIMO'] * 0.6,
            params['NDVI_OPTIMO'] * 1.0
        )
        
        # Calcular NPK basado en NDVI y humedad
        npk_actual = (ndvi * 0.6 + (humedad_suelo / 0.5) * 0.4) / 2
        npk_actual = min(1.0, max(0.0, npk_actual))
        
        resultados.append({
            'materia_organica': round(materia_organica, 2),
            'humedad_suelo': round(humedad_suelo, 3),
            'ndvi': round(ndvi, 3),
            'npk_actual': round(npk_actual, 3)
        })
    
    return resultados

def calcular_recomendaciones_npk(resultados, cultivo):
    recomendaciones_n = []
    recomendaciones_p = []
    recomendaciones_k = []
    
    params = PARAMETROS_CULTIVOS[cultivo]
    
    for res in resultados:
        factor = 1 - res['npk_actual']
        
        n_rec = params['NITROGENO']['min'] + factor * (params['NITROGENO']['max'] - params['NITROGENO']['min'])
        p_rec = params['FOSFORO']['min'] + factor * (params['FOSFORO']['max'] - params['FOSFORO']['min'])
        k_rec = params['POTASIO']['min'] + factor * (params['POTASIO']['max'] - params['POTASIO']['min'])
        
        recomendaciones_n.append(round(n_rec, 1))
        recomendaciones_p.append(round(p_rec, 1))
        recomendaciones_k.append(round(k_rec, 1))
    
    return recomendaciones_n, recomendaciones_p, recomendaciones_k

def calcular_proyecciones(resultados, cultivo):
    proyecciones = []
    params = PARAMETROS_CULTIVOS[cultivo]
    
    for res in resultados:
        rendimiento_base = params['RENDIMIENTO_OPTIMO'] * res['npk_actual']
        
        # Con fertilización
        incremento = (1 - res['npk_actual']) * 0.4
        rendimiento_con_fert = rendimiento_base * (1 + incremento)
        
        proyecciones.append({
            'rendimiento_sin_fert': round(rendimiento_base, 0),
            'rendimiento_con_fert': round(rendimiento_con_fert, 0),
            'incremento_esperado': round(incremento * 100, 1)
        })
    
    return proyecciones

# ===== INTERFAZ PRINCIPAL =====
if uploaded_file:
    with st.spinner("Cargando parcela..."):
        gdf = cargar_archivo_parcela(uploaded_file)
        
        if gdf is not None:
            st.success(f"✅ **Parcela cargada exitosamente:** {len(gdf)} polígono(s)")
            area_total = calcular_superficie(gdf)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.write("**📊 INFORMACIÓN DE LA PARCELA:**")
                st.write(f"- Polígonos: {len(gdf)}")
                st.write(f"- Área total: {area_total:.1f} ha")
                st.write(f"- Formato: {uploaded_file.name.split('.')[-1].upper()}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Vista previa
                fig, ax = plt.subplots(figsize=(8, 6))
                gdf.plot(ax=ax, color='lightgreen', edgecolor='darkgreen', alpha=0.7)
                ax.set_title(f"Parcela: {uploaded_file.name[:30]}")
                ax.set_xlabel("Longitud")
                ax.set_ylabel("Latitud")
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
                
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.write("**🎯 CONFIGURACIÓN**")
                st.write(f"- Cultivo: {ICONOS_CULTIVOS[cultivo]} {cultivo}")
                st.write(f"- Zonas: {n_divisiones}")
                st.write(f"- Período: {fecha_inicio} a {fecha_fin}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("🚀 EJECUTAR ANÁLISIS COMPLETO", type="primary", use_container_width=True):
                with st.spinner("Ejecutando análisis..."):
                    # Dividir parcela
                    gdf_dividido = dividir_parcela_en_zonas(gdf, n_divisiones)
                    
                    if len(gdf_dividido) == 0:
                        st.error("No se pudo dividir la parcela")
                        st.stop()
                    
                    # Calcular áreas
                    areas_ha = []
                    for idx, row in gdf_dividido.iterrows():
                        area_gdf = gpd.GeoDataFrame({'geometry': [row.geometry]}, crs=gdf_dividido.crs)
                        area_ha = calcular_superficie(area_gdf)
                        areas_ha.append(area_ha)
                    
                    gdf_dividido['area_ha'] = areas_ha
                    
                    # 1. Análisis de fertilidad
                    fertilidad = analizar_fertilidad(gdf_dividido, cultivo)
                    
                    # 2. Recomendaciones NPK
                    rec_n, rec_p, rec_k = calcular_recomendaciones_npk(fertilidad, cultivo)
                    
                    # 3. Proyecciones de cosecha
                    proyecciones = calcular_proyecciones(fertilidad, cultivo)
                    
                    # Combinar resultados
                    gdf_completo = gdf_dividido.copy()
                    
                    # Añadir fertilidad
                    for i, fert in enumerate(fertilidad):
                        gdf_completo.at[gdf_completo.index[i], 'materia_organica'] = fert['materia_organica']
                        gdf_completo.at[gdf_completo.index[i], 'humedad_suelo'] = fert['humedad_suelo']
                        gdf_completo.at[gdf_completo.index[i], 'ndvi'] = fert['ndvi']
                        gdf_completo.at[gdf_completo.index[i], 'npk_actual'] = fert['npk_actual']
                    
                    # Añadir recomendaciones
                    gdf_completo['rec_N'] = rec_n
                    gdf_completo['rec_P'] = rec_p
                    gdf_completo['rec_K'] = rec_k
                    
                    # Añadir proyecciones
                    for i, proy in enumerate(proyecciones):
                        gdf_completo.at[gdf_completo.index[i], 'rendimiento_sin'] = proy['rendimiento_sin_fert']
                        gdf_completo.at[gdf_completo.index[i], 'rendimiento_con'] = proy['rendimiento_con_fert']
                        gdf_completo.at[gdf_completo.index[i], 'incremento'] = proy['incremento_esperado']
                    
                    # Guardar resultados
                    st.session_state.resultados_todos = {
                        'gdf_completo': gdf_completo,
                        'area_total': area_total,
                        'cultivo': cultivo
                    }
                    st.session_state.analisis_completado = True
                    
                    st.success("✅ Análisis completado exitosamente!")
                    st.rerun()

# Mostrar resultados si el análisis está completado
if st.session_state.analisis_completado and 'resultados_todos' in st.session_state:
    resultados = st.session_state.resultados_todos
    gdf_completo = resultados['gdf_completo']
    
    st.markdown("---")
    st.subheader("📊 RESULTADOS DEL ANÁLISIS")
    
    # Mostrar métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("NDVI Promedio", f"{gdf_completo['ndvi'].mean():.3f}")
    with col2:
        st.metric("Fertilidad NPK", f"{gdf_completo['npk_actual'].mean():.3f}")
    with col3:
        st.metric("N Promedio", f"{gdf_completo['rec_N'].mean():.1f} kg/ha")
    with col4:
        st.metric("Zonas Analizadas", len(gdf_completo))
    
    # Pestañas de resultados
    tab1, tab2, tab3 = st.tabs(["🗺️ Mapa de Zonas", "📋 Tabla de Datos", "💰 Análisis Económico"])
    
    with tab1:
        # Crear mapa
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Usar NDVI para colorear
        norm = plt.Normalize(gdf_completo['ndvi'].min(), gdf_completo['ndvi'].max())
        cmap = plt.cm.YlGn
        
        for idx, row in gdf_completo.iterrows():
            color = cmap(norm(row['ndvi']))
            gdf_completo.iloc[[idx]].plot(ax=ax, color=color, edgecolor='black', linewidth=1.5)
            
            # Etiqueta con ID de zona
            centroid = row.geometry.centroid
            ax.text(centroid.x, centroid.y, f"Z{row['id_zona']}", 
                   fontsize=8, ha='center', va='center',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        ax.set_title(f"Mapa de Zonas - {resultados['cultivo']}", fontsize=16, fontweight='bold')
        ax.set_xlabel("Longitud")
        ax.set_ylabel("Latitud")
        
        # Añadir barra de colores
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, shrink=0.8)
        cbar.set_label('NDVI', fontsize=12)
        
        st.pyplot(fig)
        
        # Descargar mapa
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        
        st.download_button(
            label="📥 Descargar Mapa PNG",
            data=buf,
            file_name=f"mapa_{resultados['cultivo']}_{datetime.now().strftime('%Y%m%d')}.png",
            mime="image/png"
        )
    
    with tab2:
        # Mostrar tabla de datos
        columnas_mostrar = ['id_zona', 'area_ha', 'ndvi', 'npk_actual', 
                          'materia_organica', 'rec_N', 'rec_P', 'rec_K',
                          'rendimiento_sin', 'rendimiento_con', 'incremento']
        
        df_display = gdf_completo[columnas_mostrar].copy()
        df_display.columns = ['Zona', 'Área (ha)', 'NDVI', 'Índice NPK', 
                             'Materia Org (%)', 'N (kg/ha)', 'P (kg/ha)', 'K (kg/ha)',
                             'Rend. sin fert (kg)', 'Rend. con fert (kg)', 'Incremento (%)']
        
        st.dataframe(df_display, use_container_width=True)
        
        # Estadísticas resumen
        st.subheader("📈 Estadísticas Resumen")
        col_stats1, col_stats2 = st.columns(2)
        
        with col_stats1:
            st.write("**Fertilidad:**")
            st.write(f"- NDVI mínimo: {gdf_completo['ndvi'].min():.3f}")
            st.write(f"- NDVI máximo: {gdf_completo['ndvi'].max():.3f}")
            st.write(f"- Materia orgánica promedio: {gdf_completo['materia_organica'].mean():.1f}%")
        
        with col_stats2:
            st.write("**Recomendaciones:**")
            st.write(f"- N total necesario: {gdf_completo['rec_N'].sum():.0f} kg")
            st.write(f"- P total necesario: {gdf_completo['rec_P'].sum():.0f} kg")
            st.write(f"- K total necesario: {gdf_completo['rec_K'].sum():.0f} kg")
    
    with tab3:
        # Análisis económico
        st.subheader("💰 ANÁLISIS ECONÓMICO")
        
        # Calcular costos
        precio_n = 1.2  # USD/kg
        precio_p = 2.5  # USD/kg
        precio_k = 1.8  # USD/kg
        
        costo_total_n = gdf_completo['rec_N'].sum() * precio_n
        costo_total_p = gdf_completo['rec_P'].sum() * precio_p
        costo_total_k = gdf_completo['rec_K'].sum() * precio_k
        costo_total_fertilizacion = costo_total_n + costo_total_p + costo_total_k
        
        # Rendimientos
        rendimiento_total_sin = gdf_completo['rendimiento_sin'].sum()
        rendimiento_total_con = gdf_completo['rendimiento_con'].sum()
        
        # Ingresos
        precio_venta = PARAMETROS_CULTIVOS[resultados['cultivo']]['PRECIO_VENTA']
        ingreso_sin = rendimiento_total_sin * precio_venta
        ingreso_con = rendimiento_total_con * precio_venta
        
        # Beneficios
        beneficio_neto = (ingreso_con - ingreso_sin) - costo_total_fertilizacion
        roi = (beneficio_neto / costo_total_fertilizacion * 100) if costo_total_fertilizacion > 0 else 0
        
        # Mostrar métricas económicas
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            st.metric("Inversión en Fertilización", f"${costo_total_fertilizacion:,.0f}")
        with col_e2:
            st.metric("Ingreso Adicional", f"${ingreso_con - ingreso_sin:,.0f}")
        with col_e3:
            st.metric("ROI Estimado", f"{roi:.1f}%")
        
        # Gráfico de distribución de costos
        fig_costos, ax_costos = plt.subplots(figsize=(10, 6))
        
        categorias = ['Nitrógeno', 'Fósforo', 'Potasio']
        valores = [costo_total_n, costo_total_p, costo_total_k]
        colores = ['#00ff00', '#0000ff', '#800080']
        
        bars = ax_costos.bar(categorias, valores, color=colores, edgecolor='black')
        ax_costos.set_title('Distribución de Costos de Fertilización', fontsize=14, fontweight='bold')
        ax_costos.set_ylabel('USD', fontsize=12)
        
        # Añadir valores en las barras
        for bar in bars:
            height = bar.get_height()
            ax_costos.text(bar.get_x() + bar.get_width()/2., height + 50,
                         f'${height:,.0f}', ha='center', va='bottom', fontweight='bold')
        
        st.pyplot(fig_costos)
        
        # Resumen de recomendaciones
        st.subheader("🎯 RECOMENDACIONES")
        
        zonas_bajas_ndvi = gdf_completo[gdf_completo['ndvi'] < gdf_completo['ndvi'].mean()]
        zonas_altas_ndvi = gdf_completo[gdf_completo['ndvi'] > gdf_completo['ndvi'].mean()]
        
        st.info(f"""
        **Recomendaciones específicas para {resultados['cultivo']}:**
        
        1. **Zonas prioritarias:** {len(zonas_bajas_ndvi)} zonas con NDVI bajo (< {gdf_completo['ndvi'].mean():.3f})
        2. **Fertilización diferenciada:** Aplicar más N en zonas con NDVI < 0.5
        3. **Riego suplementario:** Considerar en zonas con humedad < 0.2
        4. **Monitoreo continuo:** Seguir NDVI cada 15 días
        """)
        
        # Exportar resultados
        st.subheader("💾 EXPORTAR RESULTADOS")
        
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            if st.button("📤 Exportar a GeoJSON", key="export_geojson"):
                try:
                    geojson_data = gdf_completo.to_json()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nombre_archivo = f"resultados_{resultados['cultivo']}_{timestamp}.geojson"
                    
                    st.download_button(
                        label="📥 Descargar GeoJSON",
                        data=geojson_data,
                        file_name=nombre_archivo,
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Error exportando: {str(e)}")
        
        with col_exp2:
            if st.button("📄 Exportar a CSV", key="export_csv"):
                try:
                    csv_data = gdf_completo.drop(columns=['geometry']).to_csv(index=False)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nombre_archivo = f"resultados_{resultados['cultivo']}_{timestamp}.csv"
                    
                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv_data,
                        file_name=nombre_archivo,
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error exportando: {str(e)}")

else:
    st.info("👈 **Sube un archivo de parcela en el sidebar para comenzar**")
    
    st.markdown("""
    ### 📋 CÓMO USAR ESTA APLICACIÓN:
    
    1. **Configuración:**
       - Selecciona el cultivo en el sidebar
       - Define el rango de fechas para el análisis
       - Especifica el número de zonas de manejo
    
    2. **Sube tu parcela:**
       - Formato ZIP (Shapefile)
       - Formato KML (Google Earth)
       - Formato GeoJSON
    
    3. **Ejecuta el análisis:**
       - Presiona el botón "EJECUTAR ANÁLISIS COMPLETO"
       - Espera los resultados
    
    4. **Explora los resultados:**
       - Mapa de zonas de manejo
       - Tabla de datos detallados
       - Análisis económico
       - Exporta los resultados
    """)
    
    # Ejemplo de archivos
    with st.expander("📁 Ejemplo de estructura de archivos aceptados"):
        st.code("""
        # Shapefile (comprimido en ZIP)
        parcela.zip/
        ├── parcela.shp      # Geometrías
        ├── parcela.shx      # Índice
        ├── parcela.dbf      # Datos
        └── parcela.prj      # Sistema de coordenadas
        
        # GeoJSON
        parcela.geojson      # Un solo archivo
        
        # KML
        parcela.kml          # Archivo de Google Earth
        """)

# ===== PIE DE PÁGINA =====
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)
with col_footer1:
    st.markdown("""
    **📡 Fuentes de Datos:**
    - NASA POWER API
    - Datos simulados
    """)
with col_footer2:
    st.markdown("""
    **🛠️ Tecnologías:**
    - Streamlit
    - GeoPandas
    - Matplotlib
    """)
with col_footer3:
    st.markdown("""
    **📞 Soporte:**
    - Versión: 1.0
    - Última actualización: Enero 2024
    """)

st.markdown(
    '<div style="text-align: center; color: #94a3b8; font-size: 0.9em; margin-top: 2em;">'
    '© 2024 Analizador Multi-Cultivo Satelital. Todos los derechos reservados.'
    '</div>',
    unsafe_allow_html=True
)
