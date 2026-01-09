# analysis/soil_analysis.py
import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st

from config import TEXTURA_SUELO_OPTIMA, RECOMENDACIONES_TEXTURA
from utils.geoprocessing import validar_y_corregir_crs, calcular_superficie

def clasificar_textura_usda(arena, limo, arcilla):
    """
    Clasifica la textura del suelo según el sistema USDA
    """
    try:
        total = arena + limo + arcilla
        if total == 0:
            return "Sin datos"
        
        # Normalizar porcentajes
        arena_pct = (arena / total) * 100
        limo_pct = (limo / total) * 100
        arcilla_pct = (arcilla / total) * 100
        
        # Clasificación USDA según el triángulo de texturas
        if arcilla_pct > 40:
            if limo_pct >= 40:
                return "Arcilla limosa"
            elif arena_pct <= 45:
                return "Arcilla"
            else:
                return "Arcilla arenosa"
        elif arcilla_pct >= 27 and arcilla_pct <= 40:
            if limo_pct >= 40:
                return "Franco arcilloso limoso"
            elif arena_pct <= 20:
                return "Franco arcilloso"
            else:
                return "Franco arcilloso arenoso"
        elif arcilla_pct >= 20 and arcilla_pct < 27:
            if limo_pct < 28:
                if arena_pct >= 52:
                    return "Arena franca"
                else:
                    return "Franco arenoso"
            else:
                if arena_pct >= 52:
                    return "Franco limoso arenoso"
                else:
                    return "Franco limoso"
        elif arcilla_pct >= 10 and arcilla_pct < 20:
            if limo_pct >= 50:
                return "Limo"
            elif limo_pct >= 30:
                if arena_pct >= 50:
                    return "Franco limoso arenoso"
                else:
                    return "Franco limoso"
            else:
                if arena_pct >= 70:
                    return "Arena"
                elif arena_pct >= 50:
                    return "Arena franca"
                else:
                    return "Franco arenoso"
        else:  # arcilla_pct < 10
            if limo_pct >= 80:
                return "Limo"
            elif limo_pct >= 50:
                return "Limo arenoso"
            else:
                if arena_pct >= 85:
                    return "Arena"
                else:
                    return "Arena franca"
    except Exception as e:
        return "Sin datos"

def clasificar_textura_suelo(arena, limo, arcilla):
    """Función principal que ahora usa clasificación USDA"""
    return clasificar_textura_usda(arena, limo, arcilla)

def analizar_textura_suelo(gdf, cultivo):
    """Analiza la textura del suelo para un cultivo específico"""
    gdf = validar_y_corregir_crs(gdf)
    params_textura = TEXTURA_SUELO_OPTIMA[cultivo]
    
    # Crear una copia para no modificar el original
    zonas_gdf = gdf.copy()
    
    areas_ha_list = []
    arena_list = []
    limo_list = []
    arcilla_list = []
    textura_list = []
    
    for idx, row in zonas_gdf.iterrows():
        try:
            # Calcular área de la zona
            area_gdf = gpd.GeoDataFrame({'geometry': [row.geometry]}, crs=zonas_gdf.crs)
            area_ha = calcular_superficie(area_gdf)
            
            # Convertir a float si es necesario
            if hasattr(area_ha, 'iloc'):
                area_ha = float(area_ha.iloc[0])
            elif hasattr(area_ha, '__len__') and len(area_ha) > 0:
                area_ha = float(area_ha[0])
            else:
                area_ha = float(area_ha)
            
            # Generar datos simulados basados en la ubicación
            centroid = row.geometry.centroid if hasattr(row.geometry, 'centroid') else row.geometry.representative_point()
            seed_value = abs(hash(f"{centroid.x:.6f}_{centroid.y:.6f}_{cultivo}_textura")) % (2**32)
            rng = np.random.RandomState(seed_value)
            
            # Simular composición basada en textura óptima
            arena_optima = params_textura['arena_optima']
            limo_optima = params_textura['limo_optima']
            arcilla_optima = params_textura['arcilla_optima']
            
            # Variación alrededor del óptimo
            arena_val = max(5, min(95, rng.normal(arena_optima, 10)))
            limo_val = max(5, min(95, rng.normal(limo_optima, 8)))
            arcilla_val = max(5, min(95, rng.normal(arcilla_optima, 7)))
            
            # Normalizar a 100%
            total = arena_val + limo_val + arcilla_val
            arena_pct = (arena_val / total) * 100
            limo_pct = (limo_val / total) * 100
            arcilla_pct = (arcilla_val / total) * 100
            
            # Clasificar textura
            textura = clasificar_textura_suelo(arena_pct, limo_pct, arcilla_pct)
            
            # Guardar resultados
            areas_ha_list.append(area_ha)
            arena_list.append(float(arena_pct))
            limo_list.append(float(limo_pct))
            arcilla_list.append(float(arcilla_pct))
            textura_list.append(textura)
            
        except Exception as e:
            # Valores por defecto en caso de error
            areas_ha_list.append(0.0)
            arena_list.append(float(params_textura['arena_optima']))
            limo_list.append(float(params_textura['limo_optima']))
            arcilla_list.append(float(params_textura['arcilla_optima']))
            textura_list.append(params_textura['textura_optima'])
    
    # Agregar columnas al GeoDataFrame
    zonas_gdf['area_ha'] = areas_ha_list
    zonas_gdf['arena'] = arena_list
    zonas_gdf['limo'] = limo_list
    zonas_gdf['arcilla'] = arcilla_list
    zonas_gdf['textura_suelo'] = textura_list
    
    return zonas_gdf

def mostrar_resultados_textura(gdf_analizado, cultivo, area_total):
    """Muestra los resultados del análisis de textura en Streamlit"""
    st.subheader("📊 ESTADÍSTICAS DE TEXTURA (USDA)")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        textura_predominante = gdf_analizado['textura_suelo'].mode()[0] if len(gdf_analizado) > 0 else "Sin datos"
        st.metric("🏗️ Textura Predominante", textura_predominante)
    with col2:
        avg_arena = gdf_analizado['arena'].mean()
        st.metric("🏖️ Arena Promedio", f"{avg_arena:.1f}%")
    with col3:
        avg_limo = gdf_analizado['limo'].mean()
        st.metric("🌫️ Limo Promedio", f"{avg_limo:.1f}%")
    with col4:
        avg_arcilla = gdf_analizado['arcilla'].mean()
        st.metric("🧱 Arcilla Promedio", f"{avg_arcilla:.1f}%")
    
    # Gráfico de composición
    st.subheader("📈 COMPOSICIÓN GRANULOMÉTRICA (USDA)")
    
    import matplotlib.pyplot as plt
    from visualization.charts import crear_grafico_textura_triangulo
    
    fig_triangulo = crear_grafico_textura_triangulo(gdf_analizado)
    if fig_triangulo:
        st.pyplot(fig_triangulo)
    
    # Gráfico de distribución de texturas
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('#0f172a')
    ax1.set_facecolor('#0f172a')
    ax2.set_facecolor('#0f172a')
    
    # Gráfico de torta
    composicion = [gdf_analizado['arena'].mean(), 
                   gdf_analizado['limo'].mean(), 
                   gdf_analizado['arcilla'].mean()]
    labels = ['Arena', 'Limo', 'Arcilla']
    colors_pie = ['#d8b365', '#f6e8c3', '#01665e']
    ax1.pie(composicion, labels=labels, colors=colors_pie, 
            autopct='%1.1f%%', startangle=90, textprops={'color': 'white'})
    ax1.set_title('Composición Promedio USDA', color='white')
    
    # Gráfico de barras de distribución de texturas
    textura_dist = gdf_analizado['textura_suelo'].value_counts()
    from config import PALETAS_GEE
    colors_bar = [PALETAS_GEE['TEXTURA'][i % len(PALETAS_GEE['TEXTURA'])] 
                  for i in range(len(textura_dist))]
    ax2.bar(textura_dist.index, textura_dist.values, color=colors_bar)
    ax2.set_title('Distribución de Texturas USDA', color='white')
    ax2.set_xlabel('Clase Textural USDA', color='white')
    ax2.set_ylabel('Número de Zonas', color='white')
    ax2.tick_params(axis='x', rotation=45, colors='white')
    ax2.tick_params(axis='y', colors='white')
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Tabla de resultados
    st.subheader("📋 TABLA DE RESULTADOS POR ZONA (USDA)")
    columnas_textura = ['id_zona', 'area_ha', 'textura_suelo', 'arena', 'limo', 'arcilla']
    columnas_textura = [col for col in columnas_textura if col in gdf_analizado.columns]
    
    if columnas_textura:
        tabla_textura = gdf_analizado[columnas_textura].copy()
        tabla_textura.columns = ['Zona', 'Área (ha)', 'Textura USDA', 'Arena (%)', 'Limo (%)', 'Arcilla (%)']
        st.dataframe(tabla_textura)
    
    # Recomendaciones
    st.subheader("💡 RECOMENDACIONES DE MANEJO POR TEXTURA USDA")
    if 'textura_suelo' in gdf_analizado.columns:
        textura_predominante = gdf_analizado['textura_suelo'].mode()[0] if len(gdf_analizado) > 0 else "Sin datos"
        if textura_predominante in RECOMENDACIONES_TEXTURA:
            st.markdown(f"#### 🏗️ **{textura_predominante.upper()}**")
            info_textura = RECOMENDACIONES_TEXTURA[textura_predominante]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**✅ PROPIEDADES FÍSICAS**")
                for prop in info_textura['propiedades']:
                    st.markdown(f"• {prop}")
            with col2:
                st.markdown("**⚠️ LIMITANTES**")
                for lim in info_textura['limitantes']:
                    st.markdown(f"• {lim}")
            with col3:
                st.markdown("**🛠️ MANEJO RECOMENDADO**")
                for man in info_textura['manejo']:
                    st.markdown(f"• {man}")
        else:
            st.info(f"Textura '{textura_predominante}' - Consultar recomendaciones específicas para esta clase textural")
    
    # Botón de descarga
    st.subheader("💾 DESCARGAR RESULTADOS USDA")
    if 'columnas_textura' in locals() and columnas_textura:
        tabla_textura = gdf_analizado[columnas_textura].copy()
        tabla_textura.columns = ['Zona', 'Área (ha)', 'Textura USDA', 'Arena (%)', 'Limo (%)', 'Arcilla (%)']
        csv = tabla_textura.to_csv(index=False)
        st.download_button(
            "📥 Descargar CSV con Análisis de Textura USDA",
            csv,
            f"textura_usda_{cultivo}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            "text/csv"
        )
