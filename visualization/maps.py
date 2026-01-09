# visualization/maps.py
import matplotlib.pyplot as plt
import contextily as ctx
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
import io
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
import streamlit as st

from config import PALETAS_GEE, ICONOS_CULTIVOS, SATELITES_DISPONIBLES
from utils.geoprocessing import validar_y_corregir_crs

def crear_mapa_npk_con_esri(gdf_analizado, nutriente, cultivo, satelite):
    """Crea mapa de NPK con fondo ESRI Satellite"""
    try:
        # Convertir a Web Mercator para el mapa base
        gdf_plot = gdf_analizado.to_crs(epsg=3857)
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Configurar estilo oscuro
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#0f172a')
        
        # Mapear nutriente con tilde a clave sin tilde
        mapeo_nutriente = {
            'NITRÓGENO': ('nitrogeno_actual', 'NITROGENO', 'NITRÓGENO (kg/ha)'),
            'FÓSFORO': ('fosforo_actual', 'FOSFORO', 'FÓSFORO (kg/ha)'),
            'POTASIO': ('potasio_actual', 'POTASIO', 'POTASIO (kg/ha)')
        }
        
        if nutriente not in mapeo_nutriente:
            st.error(f"❌ Nutriente '{nutriente}' no reconocido")
            return None
            
        columna, clave_param, titulo_nutriente = mapeo_nutriente[nutriente]
        
        # Seleccionar columna y paleta según nutriente
        if nutriente == "NITRÓGENO":
            cmap = LinearSegmentedColormap.from_list('nitrogeno_gee', PALETAS_GEE['NITROGENO'])
        elif nutriente == "FÓSFORO":
            cmap = LinearSegmentedColormap.from_list('fosforo_gee', PALETAS_GEE['FOSFORO'])
        else:  # POTASIO
            cmap = LinearSegmentedColormap.from_list('potasio_gee', PALETAS_GEE['POTASIO'])
        
        # Determinar rango de valores
        valores = gdf_plot[columna]
        vmin = valores.min() * 0.8
        vmax = valores.max() * 1.2
        
        # Plot de las zonas con colores según valor
        for idx, row in gdf_plot.iterrows():
            valor = row[columna]
            valor_norm = (valor - vmin) / (vmax - vmin) if vmax != vmin else 0.5
            valor_norm = max(0, min(1, valor_norm))
            color = cmap(valor_norm)
            
            # Dibujar polígono
            gdf_plot.iloc[[idx]].plot(ax=ax, color=color, edgecolor='white', linewidth=1.5, alpha=0.7)
            
            # Etiqueta de zona
            centroid = row.geometry.centroid
            ax.annotate(f"Z{row['id_zona']}\n{valor:.0f}", (centroid.x, centroid.y),
                        xytext=(5, 5), textcoords="offset points",
                        fontsize=8, color='white', weight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", 
                                 facecolor=(30/255, 41/255, 59/255, 0.9), 
                                 edgecolor='white'))
        
        # Agregar mapa base ESRI Satellite
        try:
            ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, alpha=0.4)
        except:
            st.warning("⚠️ No se pudo cargar el mapa base ESRI. Verifica la conexión a internet.")
        
        info_satelite = SATELITES_DISPONIBLES.get(satelite, SATELITES_DISPONIBLES['DATOS_SIMULADOS'])
        ax.set_title(f'{ICONOS_CULTIVOS[cultivo]} ANÁLISIS DE {nutriente} - {cultivo}\n'
                     f'{info_satelite["icono"]} {info_satelite["nombre"]} - {titulo_nutriente}',
                     fontsize=16, fontweight='bold', pad=20, color='white')
        ax.set_xlabel('Longitud', color='white')
        ax.set_ylabel('Latitud', color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.3, color='#475569')
        
        # Barra de colores
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.8)
        cbar.set_label(titulo_nutriente, fontsize=12, fontweight='bold', color='white')
        cbar.ax.yaxis.set_tick_params(color='white')
        cbar.outline.set_edgecolor('white')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
        buf.seek(0)
        plt.close()
        return buf
    except Exception as e:
        st.error(f"❌ Error creando mapa NPK con ESRI: {str(e)}")
        import traceback
        st.error(f"Detalle: {traceback.format_exc()}")
        return None

def crear_mapa_fertilidad_integrada(gdf_analizado, cultivo, satelite):
    """Crea mapa de fertilidad integrada (NPK combinado)"""
    try:
        gdf_plot = gdf_analizado.to_crs(epsg=3857)
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#0f172a')
        
        cmap = LinearSegmentedColormap.from_list('fertilidad_gee', PALETAS_GEE['FERTILIDAD'])
        
        for idx, row in gdf_plot.iterrows():
            valor = row['npk_integrado']
            color = cmap(valor)
            gdf_plot.iloc[[idx]].plot(ax=ax, color=color, edgecolor='white', linewidth=1.5, alpha=0.7)
            
            centroid = row.geometry.centroid
            ax.annotate(f"Z{row['id_zona']}\n{valor:.2f}", (centroid.x, centroid.y),
                        xytext=(5, 5), textcoords="offset points",
                        fontsize=8, color='white', weight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", 
                                 facecolor=(30/255, 41/255, 59/255, 0.9), 
                                 edgecolor='white'))
        
        try:
            ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, alpha=0.4)
        except:
            pass
        
        info_satelite = SATELITES_DISPONIBLES.get(satelite, SATELITES_DISPONIBLES['DATOS_SIMULADOS'])
        ax.set_title(f'{ICONOS_CULTIVOS[cultivo]} FERTILIDAD INTEGRADA (NPK) - {cultivo}\n'
                     f'{info_satelite["icono"]} {info_satelite["nombre"]}',
                     fontsize=16, fontweight='bold', pad=20, color='white')
        
        ax.set_xlabel('Longitud', color='white')
        ax.set_ylabel('Latitud', color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.3, color='#475569')
        
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.8)
        cbar.set_label('Índice de Fertilidad (0-1)', fontsize=12, fontweight='bold', color='white')
        cbar.ax.yaxis.set_tick_params(color='white')
        cbar.outline.set_edgecolor('white')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
        buf.seek(0)
        plt.close()
        return buf
    except Exception as e:
        st.error(f"❌ Error creando mapa fertilidad: {str(e)}")
        return None

def crear_mapa_texturas_con_esri(gdf_analizado, cultivo):
    """Crea mapa de texturas con fondo ESRI Satellite"""
    try:
        # Convertir a Web Mercator
        gdf_plot = gdf_analizado.to_crs(epsg=3857)
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Configurar estilo oscuro
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#0f172a')
        
        colores_textura = {
            'Franco limoso': '#c7eae5',
            'Franco': '#a6d96a',
            'Franco arcilloso limoso': '#5ab4ac',
            'Franco arenoso': '#f6e8c3',
            'Arcilla': '#01665e',
            'Arcilla limosa': '#003c30',
            'Arena franca': '#d8b365',
            'Limo': '#8c510a',
            'Franco arcilloso': '#35978f',
            'Franco arcilloso arenoso': '#80cdc1',
            'Limo arenoso': '#dfc27d',
            'Arena': '#f6e8c3',
            'Arcilla arenosa': '#01665e',
            'Franco limoso arenoso': '#a6d96a',
            'Sin datos': '#999999'
        }
        
        # Plot de cada zona con su color según textura
        for idx, row in gdf_plot.iterrows():
            textura = row['textura_suelo']
            color = colores_textura.get(textura, '#999999')
            gdf_plot.iloc[[idx]].plot(ax=ax, color=color, edgecolor='white', linewidth=1.5, alpha=0.8)
            
            # Etiqueta de zona (abreviada si es muy larga)
            textura_abrev = textura[:12] + '...' if len(textura) > 15 else textura
            centroid = row.geometry.centroid
            ax.annotate(f"Z{row['id_zona']}\n{textura_abrev}", (centroid.x, centroid.y),
                        xytext=(5, 5), textcoords="offset points",
                        fontsize=8, color='black', weight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9))
        
        # Agregar mapa base ESRI Satellite
        try:
            ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, alpha=0.4)
        except:
            st.warning("⚠️ No se pudo cargar el mapa base ESRI. Verifica la conexión a internet.")
        
        ax.set_title(f'{ICONOS_CULTIVOS[cultivo]} MAPA DE TEXTURAS USDA - {cultivo}',
                     fontsize=16, fontweight='bold', pad=20, color='white')
        ax.set_xlabel('Longitud', color='white')
        ax.set_ylabel('Latitud', color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.3, color='#475569')
        
        # Leyenda (solo las texturas presentes en el mapa)
        from matplotlib.patches import Patch
        texturas_presentes = gdf_analizado['textura_suelo'].unique()
        legend_elements = [Patch(facecolor=colores_textura.get(textura, '#999999'), 
                                edgecolor='white', label=textura)
                          for textura in texturas_presentes if textura in colores_textura]
        
        if legend_elements:
            legend = ax.legend(handles=legend_elements, title='Texturas USDA', 
                             loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=9)
            legend.get_title().set_color('white')
            for text in legend.get_texts():
                text.set_color('white')
            legend.get_frame().set_facecolor((30/255, 41/255, 59/255, 0.9))
            legend.get_frame().set_edgecolor('white')
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
        buf.seek(0)
        plt.close()
        return buf
    except Exception as e:
        st.error(f"Error creando mapa de texturas: {str(e)}")
        return None

def crear_mapa_calor_rendimiento_actual(gdf_analizado, cultivo):
    """Crea mapa de calor para rendimiento actual con visualización suave y profesional"""
    try:
        if 'rendimiento_actual' not in gdf_analizado.columns:
            return None
            
        gdf_plot = gdf_analizado.to_crs(epsg=3857)
        
        # Crear figura con estilo moderno
        fig, ax = plt.subplots(1, 1, figsize=(14, 8))
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#0f172a')
        
        # Obtener los centroides para interpolación
        centroids = gdf_plot.geometry.centroid
        x = np.array([c.x for c in centroids])
        y = np.array([c.y for c in centroids])
        z = gdf_plot['rendimiento_actual'].values
        
        # Crear malla para interpolación
        x_min, y_min, x_max, y_max = gdf_plot.total_bounds
        xi = np.linspace(x_min, x_max, 200)
        yi = np.linspace(y_min, y_max, 200)
        xi, yi = np.meshgrid(xi, yi)
        
        # Interpolación lineal para suavizar
        try:
            zi = griddata((x, y), z, (xi, yi), method='cubic', fill_value=np.nan)
        except:
            # Fallback a interpolación lineal
            zi = griddata((x, y), z, (xi, yi), method='linear', fill_value=np.nan)
        
        # Crear mapa de calor suave
        im = ax.contourf(xi, yi, zi, levels=50, cmap='RdYlGn', alpha=0.8, 
                        vmin=z.min()*0.9, vmax=z.max()*1.1)
        
        # Agregar líneas de contorno
        contour = ax.contour(xi, yi, zi, levels=10, colors='white', linewidths=0.5, alpha=0.5)
        
        # Agregar etiquetas en los centroides
        for idx, (centroid, valor) in enumerate(zip(centroids, z)):
            ax.plot(centroid.x, centroid.y, 'o', markersize=8, 
                   markeredgecolor='white', markerfacecolor=plt.cm.RdYlGn((valor - z.min())/(z.max() - z.min())))
            
            # Etiqueta con valor
            if idx % 2 == 0:  # Mostrar solo algunas etiquetas para evitar sobrecarga
                ax.annotate(f"{valor:.1f}t", 
                           (centroid.x, centroid.y),
                           xytext=(0, 10), textcoords="offset points",
                           fontsize=8, color='white', weight='bold',
                           ha='center', va='center',
                           bbox=dict(boxstyle="round,pad=0.2", 
                                    facecolor=(0, 0, 0, 0.7), 
                                    alpha=0.8))
        
        # Agregar mapa base
        try:
            ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, alpha=0.4)
        except:
            pass
        
        # Configurar título y etiquetas
        ax.set_title(f'🌾 MAPA DE CALOR - RENDIMIENTO ACTUAL\n{cultivo} (ton/ha)',
                     fontsize=16, fontweight='bold', pad=20, color='white')
        ax.set_xlabel('Longitud', color='white')
        ax.set_ylabel('Latitud', color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.1, color='#475569', linestyle='--')
        
        # Barra de colores profesional
        cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
        cbar.set_label('Rendimiento (ton/ha)', fontsize=12, fontweight='bold', color='white')
        cbar.ax.yaxis.set_tick_params(color='white')
        cbar.outline.set_edgecolor('white')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
        
        # Leyenda de interpretación
        stats = {
            'promedio': z.mean(),
            'min': z.min(),
            'max': z.max(),
            'std': z.std()
        }
        
        info_text = f"""
        📊 ESTADÍSTICAS:
        • Promedio: {stats['promedio']:.1f} ton/ha
        • Mínimo: {stats['min']:.1f} ton/ha
        • Máximo: {stats['max']:.1f} ton/ha
        • Variación: {stats['std']:.1f} ton/ha
        """
        
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=9, 
                verticalalignment='top', color='white',
                bbox=dict(boxstyle="round,pad=0.3", 
                         facecolor=(30/255, 41/255, 59/255, 0.9), 
                         alpha=0.9, edgecolor='white'))
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', 
                   facecolor='#0f172a', transparent=False)
        buf.seek(0)
        plt.close()
        return buf
        
    except Exception as e:
        st.error(f"Error creando mapa de calor actual: {str(e)}")
        return None

def crear_mapa_calor_rendimiento_proyectado(gdf_analizado, cultivo):
    """Crea mapa de calor para rendimiento proyectado con visualización profesional"""
    try:
        if 'rendimiento_proyectado' not in gdf_analizado.columns:
            return None
            
        gdf_plot = gdf_analizado.to_crs(epsg=3857)
        
        # Crear figura con estilo moderno
        fig, ax = plt.subplots(1, 1, figsize=(14, 8))
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#0f172a')
        
        # Obtener datos para interpolación
        centroids = gdf_plot.geometry.centroid
        x = np.array([c.x for c in centroids])
        y = np.array([c.y for c in centroids])
        z_proyectado = gdf_plot['rendimiento_proyectado'].values
        z_actual = gdf_plot['rendimiento_actual'].values
        incrementos = z_proyectado - z_actual
        
        # Crear malla para interpolación
        x_min, y_min, x_max, y_max = gdf_plot.total_bounds
        xi = np.linspace(x_min, x_max, 200)
        yi = np.linspace(y_min, y_max, 200)
        xi, yi = np.meshgrid(xi, yi)
        
        # Interpolación del rendimiento proyectado
        try:
            zi_proyectado = griddata((x, y), z_proyectado, (xi, yi), method='cubic', fill_value=np.nan)
            zi_incremento = griddata((x, y), incrementos, (xi, yi), method='cubic', fill_value=np.nan)
        except:
            zi_proyectado = griddata((x, y), z_proyectado, (xi, yi), method='linear', fill_value=np.nan)
            zi_incremento = griddata((x, y), incrementos, (xi, yi), method='linear', fill_value=np.nan)
        
        # Crear mapa de calor con dos capas
        im_proyectado = ax.contourf(xi, yi, zi_proyectado, levels=50, cmap='RdYlGn', alpha=0.7, 
                                   vmin=z_proyectado.min()*0.9, vmax=z_proyectado.max()*1.1)
        
        # Superponer mapa de incrementos con transparencia
        im_incremento = ax.contourf(xi, yi, zi_incremento, levels=20, cmap='viridis', alpha=0.4)
        
        # Agregar líneas de contorno para rendimiento proyectado
        contour = ax.contour(xi, yi, zi_proyectado, levels=8, colors='white', linewidths=1, alpha=0.6)
        
        # Etiquetar las líneas de contorno
        ax.clabel(contour, inline=True, fontsize=8, colors='white', fmt='%1.1f t')
        
        # Agregar puntos de datos
        for idx, (centroid, valor_proy, valor_act, inc) in enumerate(zip(centroids, z_proyectado, z_actual, incrementos)):
            # Punto con tamaño proporcional al incremento
            marker_size = 6 + (inc / max(incrementos) * 10) if max(incrementos) > 0 else 8
            
            ax.plot(centroid.x, centroid.y, 'o', markersize=marker_size,
                   markeredgecolor='white', markerfacecolor=plt.cm.RdYlGn((valor_proy - z_proyectado.min())/(z_proyectado.max() - z_proyectado.min())),
                   markeredgewidth=1)
            
            # Etiqueta con incremento
            if idx % 3 == 0:  # Mostrar algunas etiquetas
                ax.annotate(f"+{inc:.1f}t", 
                           (centroid.x, centroid.y),
                           xytext=(0, 15), textcoords="offset points",
                           fontsize=7, color='cyan', weight='bold',
                           ha='center', va='center',
                           bbox=dict(boxstyle="round,pad=0.2", 
                                    facecolor=(0, 0, 0, 0.7), 
                                    alpha=0.8))
        
        # Agregar mapa base
        try:
            ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, alpha=0.3)
        except:
            pass
        
        # Configurar título y etiquetas
        ax.set_title(f'🚀 MAPA DE CALOR - RENDIMIENTO PROYECTADO\n{cultivo} (con fertilización óptima)',
                     fontsize=16, fontweight='bold', pad=20, color='white')
        ax.set_xlabel('Longitud', color='white')
        ax.set_ylabel('Latitud', color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.1, color='#475569', linestyle='--')
        
        # Barra de colores principal
        cbar1 = plt.colorbar(im_proyectado, ax=ax, shrink=0.8, pad=0.02)
        cbar1.set_label('Rendimiento Proyectado (ton/ha)', fontsize=12, fontweight='bold', color='white')
        cbar1.ax.yaxis.set_tick_params(color='white')
        
        # Barra de colores para incrementos (más pequeña)
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        divider = make_axes_locatable(ax)
        cax2 = divider.append_axes("right", size="3%", pad=0.15)
        cbar2 = plt.colorbar(im_incremento, cax=cax2)
        cbar2.set_label('Incremento (ton/ha)', fontsize=9, color='white')
        cbar2.ax.yaxis.set_tick_params(color='white')
        
        # Configurar colores de barras
        for cbar in [cbar1, cbar2]:
            cbar.outline.set_edgecolor('white')
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
        
        # Estadísticas
        stats_text = f"""
        📈 ESTADÍSTICAS DE POTENCIAL:
        • Actual: {z_actual.mean():.1f} ton/ha
        • Proyectado: {z_proyectado.mean():.1f} ton/ha
        • Incremento: +{incrementos.mean():.1f} ton/ha
        • Aumento: +{(incrementos.mean()/z_actual.mean()*100 if z_actual.mean()>0 else 0):.1f}%
        """
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9, 
                verticalalignment='top', color='white',
                bbox=dict(boxstyle="round,pad=0.3", 
                         facecolor=(30/255, 41/255, 59/255, 0.9), 
                         alpha=0.9, edgecolor='white'))
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', 
                   facecolor='#0f172a', transparent=False)
        buf.seek(0)
        plt.close()
        return buf
        
    except Exception as e:
        st.error(f"Error creando mapa de calor proyectado: {str(e)}")
        return None

def crear_mapa_pendientes_simple(X, Y, pendiente_grid, gdf_original):
    """Crea mapa de pendientes simple"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Configurar estilo oscuro
    fig.patch.set_facecolor('#0f172a')
    ax1.set_facecolor('#0f172a')
    ax2.set_facecolor('#0f172a')
    
    X_flat = X.flatten()
    Y_flat = Y.flatten()
    Z_flat = pendiente_grid.flatten()
    valid_mask = ~np.isnan(Z_flat)
    
    if np.sum(valid_mask) > 10:
        scatter = ax1.scatter(X_flat[valid_mask], Y_flat[valid_mask], 
                             c=Z_flat[valid_mask], cmap='RdYlGn_r', 
                             s=20, alpha=0.7, vmin=0, vmax=30)
        
        cbar = plt.colorbar(scatter, ax=ax1, shrink=0.8)
        cbar.set_label('Pendiente (%)', color='white')
        cbar.ax.yaxis.set_tick_params(color='white')
        cbar.outline.set_edgecolor('white')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
        
        # Agregar etiquetas de porcentaje
        for porcentaje in [2, 5, 10, 15, 25]:
            mask_cat = (Z_flat[valid_mask] >= porcentaje-1) & (Z_flat[valid_mask] <= porcentaje+1)
            if np.sum(mask_cat) > 0:
                x_center = np.mean(X_flat[valid_mask][mask_cat])
                y_center = np.mean(Y_flat[valid_mask][mask_cat])
                ax1.text(x_center, y_center, f'{porcentaje}%', 
                        fontsize=8, fontweight='bold', ha='center', va='center', 
                        bbox=dict(boxstyle="round,pad=0.3", 
                                 facecolor=(30/255, 41/255, 59/255, 0.9), 
                                 edgecolor='white'), color='white')
    else:
        ax1.text(0.5, 0.5, 'Datos insuficientes\npara mapa de calor', 
                transform=ax1.transAxes, ha='center', va='center', 
                fontsize=12, color='white')
    
    # Dibujar contorno de la parcela
    gdf_original.to_crs(epsg=3857).plot(ax=ax1, color='none', edgecolor='white', linewidth=2)
    
    ax1.set_title('Mapa de Calor de Pendientes', fontsize=12, fontweight='bold', color='white')
    ax1.set_xlabel('Longitud', color='white')
    ax1.set_ylabel('Latitud', color='white')
    ax1.tick_params(colors='white')
    ax1.grid(True, alpha=0.3, color='#475569')
    
    # Histograma de pendientes
    if np.sum(valid_mask) > 0:
        pendiente_data = Z_flat[valid_mask]
        ax2.hist(pendiente_data, bins=30, edgecolor='white', color='#3b82f6', alpha=0.7)
        
        # Líneas de referencia para clasificación
        for porcentaje, color in [(2, '#4daf4a'), (5, '#a6d96a'), (10, '#ffffbf'), 
                                 (15, '#fdae61'), (25, '#f46d43')]:
            ax2.axvline(x=porcentaje, color=color, linestyle='--', linewidth=1, alpha=0.7)
            ax2.text(porcentaje+0.5, ax2.get_ylim()[1]*0.9, f'{porcentaje}%', 
                    color=color, fontsize=8)
        
        ax2.set_xlabel('Pendiente (%)', color='white')
        ax2.set_ylabel('Frecuencia', color='white')
        ax2.set_title('Distribución de Pendientes', fontsize=12, fontweight='bold', color='white')
        ax2.tick_params(colors='white')
        ax2.grid(True, alpha=0.3, color='#475569')
    else:
        ax2.text(0.5, 0.5, 'Sin datos de pendiente', 
                transform=ax2.transAxes, ha='center', va='center', fontsize=12, color='white')
    
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
    buf.seek(0)
    plt.close()
    return buf
