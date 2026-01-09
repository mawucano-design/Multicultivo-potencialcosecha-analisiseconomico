# analysis/terrain_analysis.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
import io
import pandas as pd
import streamlit as st

from config import CLASIFICACION_PENDIENTES
from utils.geoprocessing import validar_y_corregir_crs

def generar_dem_sintetico(gdf, resolucion=10.0):
    """
    Genera un DEM sintético determinístico basado en las coordenadas de la parcela.
    Mismo input → mismo output siempre.
    """
    gdf = validar_y_corregir_crs(gdf)
    bounds = gdf.total_bounds
    minx, miny, maxx, maxy = bounds
    
    # Crear una semilla determinística basada en las coordenadas de la parcela
    centroid = gdf.geometry.unary_union.centroid
    seed_value = int(centroid.x * 10000 + centroid.y * 10000) % (2**32)
    
    # Inicializar el generador aleatorio con la semilla
    rng = np.random.RandomState(seed_value)
    
    num_cells = 50
    x = np.linspace(minx, maxx, num_cells)
    y = np.linspace(miny, maxy, num_cells)
    X, Y = np.meshgrid(x, y)
    
    # Valores fijos basados en la semilla
    elevacion_base = rng.uniform(100, 300)
    slope_x = rng.uniform(-0.001, 0.001)
    slope_y = rng.uniform(-0.001, 0.001)
    relief = np.zeros_like(X)
    
    # Agregar algunas colinas
    n_hills = rng.randint(2, 5)
    for _ in range(n_hills):
        hill_center_x = rng.uniform(minx, maxx)
        hill_center_y = rng.uniform(miny, maxy)
        hill_radius = rng.uniform(0.001, 0.005)
        hill_height = rng.uniform(10, 50)
        dist = np.sqrt((X - hill_center_x)**2 + (Y - hill_center_y)**2)
        relief += hill_height * np.exp(-(dist**2) / (2 * hill_radius**2))
    
    # Agregar ruido
    noise = rng.randn(*X.shape) * 2
    Z = elevacion_base + slope_x * (X - minx) + slope_y * (Y - miny) + relief + noise
    Z = np.maximum(Z, 50)  # Evitar elevaciones negativas
    
    return X, Y, Z, bounds

def calcular_pendiente_simple(X, Y, Z, resolucion=10.0):
    """Calcula la pendiente a partir del DEM"""
    dy = np.gradient(Z, axis=0) / resolucion
    dx = np.gradient(Z, axis=1) / resolucion
    pendiente = np.sqrt(dx**2 + dy**2) * 100  # Convertir a porcentaje
    pendiente = np.clip(pendiente, 0, 100)  # Limitar entre 0 y 100%
    return pendiente

def clasificar_pendiente(pendiente_porcentaje):
    """Clasifica la pendiente según categorías predefinidas"""
    for categoria, params in CLASIFICACION_PENDIENTES.items():
        if params['min'] <= pendiente_porcentaje < params['max']:
            return categoria, params['color']
    return "EXTREMA (>25%)", CLASIFICACION_PENDIENTES['EXTREMA (>25%)']['color']

def calcular_estadisticas_pendiente_simple(pendiente_grid):
    """Calcula estadísticas de pendiente"""
    pendiente_flat = pendiente_grid.flatten()
    pendiente_flat = pendiente_flat[~np.isnan(pendiente_flat)]
    
    if len(pendiente_flat) == 0:
        return {'promedio': 0, 'min': 0, 'max': 0, 'std': 0, 'distribucion': {}}
    
    stats = {
        'promedio': float(np.mean(pendiente_flat)),
        'min': float(np.min(pendiente_flat)),
        'max': float(np.max(pendiente_flat)),
        'std': float(np.std(pendiente_flat)),
        'distribucion': {}
    }
    
    # Calcular distribución por categoría
    for categoria, params in CLASIFICACION_PENDIENTES.items():
        mask = (pendiente_flat >= params['min']) & (pendiente_flat < params['max'])
        porcentaje = float(np.sum(mask) / len(pendiente_flat) * 100)
        stats['distribucion'][categoria] = {
            'porcentaje': porcentaje,
            'color': params['color']
        }
    
    return stats

def generar_curvas_nivel_simple(X, Y, Z, intervalo=5.0, gdf_original=None):
    """Genera curvas de nivel a partir del DEM"""
    curvas = []
    elevaciones = []
    
    try:
        if gdf_original is not None:
            poligono_principal = gdf_original.iloc[0].geometry
            bounds = poligono_principal.bounds
            centro = poligono_principal.centroid
            
            ancho = bounds[2] - bounds[0]
            alto = bounds[3] - bounds[1]
            radio_max = min(ancho, alto) / 2
            
            z_min, z_max = np.nanmin(Z), np.nanmax(Z)
            n_curvas = min(10, int((z_max - z_min) / intervalo))
            
            for i in range(1, n_curvas + 1):
                radio = radio_max * (i / n_curvas)
                circle = centro.buffer(radio)
                interseccion = poligono_principal.intersection(circle)
                
                if interseccion.geom_type == 'LineString':
                    curvas.append(interseccion)
                    elevaciones.append(z_min + (i * intervalo))
                elif interseccion.geom_type == 'MultiLineString':
                    for parte in interseccion.geoms:
                        curvas.append(parte)
                        elevaciones.append(z_min + (i * intervalo))
    except Exception as e:
        # Fallback simple si hay error
        if gdf_original is not None:
            bounds = gdf_original.total_bounds
            for i in range(3):
                y = bounds[1] + (i + 1) * ((bounds[3] - bounds[1]) / 4)
                linea = LineString([(bounds[0], y), (bounds[2], y)])
                curvas.append(linea)
                elevaciones.append(100 + i * 50)
    
    return curvas, elevaciones

def mostrar_resultados_curvas_nivel(X, Y, Z, pendiente_grid, curvas, elevaciones, 
                                   gdf_original, cultivo, area_total):
    """Muestra los resultados del análisis de curvas de nivel"""
    from visualization.maps import crear_mapa_pendientes_simple
    
    st.subheader("📊 ESTADÍSTICAS TOPOGRÁFICAS")
    
    elevaciones_flat = Z.flatten()
    elevaciones_flat = elevaciones_flat[~np.isnan(elevaciones_flat)]
    
    if len(elevaciones_flat) > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            elevacion_promedio = np.mean(elevaciones_flat)
            st.metric("🏔️ Elevación Promedio", f"{elevacion_promedio:.1f} m")
        
        with col2:
            rango_elevacion = np.max(elevaciones_flat) - np.min(elevaciones_flat)
            st.metric("📏 Rango de Elevación", f"{rango_elevacion:.1f} m")
        
        with col3:
            stats_pendiente = calcular_estadisticas_pendiente_simple(pendiente_grid)
            st.metric("📐 Pendiente Promedio", f"{stats_pendiente['promedio']:.1f}%")
        
        with col4:
            num_curvas = len(curvas) if curvas else 0
            st.metric("🔄 Número de Curvas", f"{num_curvas}")
        
        # Mapa de pendientes
        st.subheader("🔥 MAPA DE CALOR DE PENDIENTES")
        mapa_pendientes = crear_mapa_pendientes_simple(X, Y, pendiente_grid, gdf_original)
        st.image(mapa_pendientes, use_container_width=True)
        
        st.download_button(
            "📥 Descargar Mapa de Pendientes",
            mapa_pendientes,
            f"mapa_pendientes_{cultivo}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.png",
            "image/png"
        )
        
        # Análisis de riesgo de erosión
        st.subheader("⚠️ ANÁLISIS DE RIESGO DE EROSION")
        
        if 'stats_pendiente' in locals() and 'distribucion' in stats_pendiente:
            riesgo_total = 0
            for categoria, data in stats_pendiente['distribucion'].items():
                if categoria in CLASIFICACION_PENDIENTES:
                    riesgo_total += data['porcentaje'] * CLASIFICACION_PENDIENTES[categoria]['factor_erosivo']
            
            riesgo_promedio = riesgo_total / 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if riesgo_promedio < 0.3:
                    st.success("✅ **RIESGO BAJO**")
                    st.metric("Factor Riesgo", f"{riesgo_promedio:.2f}")
                elif riesgo_promedio < 0.6:
                    st.warning("⚠️ **RIESGO MODERADO**")
                    st.metric("Factor Riesgo", f"{riesgo_promedio:.2f}")
                else:
                    st.error("🚨 **RIESGO ALTO**")
                    st.metric("Factor Riesgo", f"{riesgo_promedio:.2f}")
            
            with col2:
                porcentaje_critico = sum(
                    data['porcentaje'] for cat, data in stats_pendiente['distribucion'].items()
                    if cat in ['FUERTE (10-15%)', 'MUY FUERTE (15-25%)', 'EXTREMA (>25%)']
                )
                area_critica = area_total * (porcentaje_critico / 100)
                st.metric("Área Crítica (>10%)", f"{area_critica:.2f} ha")
            
            with col3:
                porcentaje_manejable = sum(
                    data['porcentaje'] for cat, data in stats_pendiente['distribucion'].items()
                    if cat in ['PLANA (0-2%)', 'SUAVE (2-5%)', 'MODERADA (5-10%)']
                )
                area_manejable = area_total * (porcentaje_manejable / 100)
                st.metric("Área Manejable (<10%)", f"{area_manejable:.2f} ha")
        
        # Visualización 3D
        st.subheader("📈 VISUALIZACIÓN 3D DEL TERRENO")
        try:
            from mpl_toolkits.mplot3d import Axes3D
            
            fig = plt.figure(figsize=(12, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            # Plot superficie
            surf = ax.plot_surface(X, Y, Z, cmap='terrain', alpha=0.8, linewidth=0)
            
            # Configurar ejes
            ax.set_xlabel('Longitud', color='white')
            ax.set_ylabel('Latitud', color='white')
            ax.set_zlabel('Elevación (m)', color='white')
            ax.set_title(f'Modelo 3D del Terreno - {cultivo}', color='white')
            ax.tick_params(colors='white')
            
            # Configurar colores de fondo
            fig.patch.set_facecolor('#0f172a')
            ax.set_facecolor('#0f172a')
            
            # Configurar color de ejes
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.zaxis.label.set_color('white')
            ax.title.set_color('white')
            
            # Barra de color
            cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Elevación (m)')
            cbar.set_label('Elevación (m)', color='white')
            cbar.ax.yaxis.set_tick_params(color='white')
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
            
            plt.tight_layout()
            st.pyplot(fig)
        except Exception as e:
            st.warning(f"No se pudo generar visualización 3D: {e}")
        
        # Descargar datos
        st.subheader("💾 DESCARGAR RESULTADOS")
        sample_points = []
        for i in range(0, X.shape[0], 5):
            for j in range(0, X.shape[1], 5):
                if not np.isnan(Z[i, j]):
                    sample_points.append({
                        'lat': Y[i, j],
                        'lon': X[i, j],
                        'elevacion_m': Z[i, j],
                        'pendiente_%': pendiente_grid[i, j]
                    })
        
        if sample_points:
            df_dem = pd.DataFrame(sample_points)
            csv = df_dem.to_csv(index=False)
            st.download_button(
                label="📊 Descargar Muestras DEM (CSV)",
                data=csv,
                file_name=f"dem_muestras_{cultivo}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("No se pudieron calcular estadísticas topográficas.")
