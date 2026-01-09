# visualization/charts.py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

def crear_grafico_personalizado(series, titulo, ylabel, color_linea, 
                                fondo_grafico='#0f172a', color_texto='#ffffff'):
    """Crea gráfico de línea con estilo oscuro"""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_facecolor(fondo_grafico)
    fig.patch.set_facecolor(fondo_grafico)
    
    ax.plot(series.index, series.values, color=color_linea, linewidth=2.2)
    ax.set_title(titulo, fontsize=14, fontweight='bold', color=color_texto)
    ax.set_ylabel(ylabel, fontsize=12, color=color_texto)
    ax.set_xlabel("Fecha", fontsize=11, color=color_texto)
    ax.tick_params(axis='x', colors=color_texto, rotation=0)
    ax.tick_params(axis='y', colors=color_texto)
    ax.grid(True, color='#475569', linestyle='--', linewidth=0.7, alpha=0.7)
    
    for spine in ax.spines.values():
        spine.set_color('#475569')
    
    plt.tight_layout()
    return fig

def crear_grafico_barras_personalizado(series, titulo, ylabel, color_barra, 
                                       fondo_grafico='#0f172a', color_texto='#ffffff'):
    """Crea gráfico de barras con estilo oscuro"""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_facecolor(fondo_grafico)
    fig.patch.set_facecolor(fondo_grafico)
    
    ax.bar(series.index, series.values, color=color_barra, alpha=0.85)
    ax.set_title(titulo, fontsize=14, fontweight='bold', color=color_texto)
    ax.set_ylabel(ylabel, fontsize=12, color=color_texto)
    ax.set_xlabel("Fecha", fontsize=11, color=color_texto)
    ax.tick_params(axis='x', colors=color_texto, rotation=0)
    ax.tick_params(axis='y', colors=color_texto)
    ax.grid(axis='y', color='#475569', linestyle='--', linewidth=0.7, alpha=0.7)
    
    for spine in ax.spines.values():
        spine.set_color('#475569')
    
    plt.tight_layout()
    return fig

def crear_grafico_npk_integrado(gdf_analizado):
    """Crea gráfico del índice NPK integrado por zona"""
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')
    
    # Preparar datos
    zonas = gdf_analizado['id_zona']
    valores = gdf_analizado['npk_integrado']
    
    # Crear gráfico de barras
    bars = ax.bar(zonas.astype(str), valores, 
                  color=plt.cm.RdYlGn(valores),
                  edgecolor='white', linewidth=1)
    
    # Línea de referencia para fertilidad óptima
    ax.axhline(y=0.7, color='cyan', linestyle='--', linewidth=2, alpha=0.7, 
               label='Fertilidad Óptima (0.7)')
    ax.axhline(y=0.5, color='yellow', linestyle='--', linewidth=2, alpha=0.7, 
               label='Fertilidad Adecuada (0.5)')
    
    # Configurar gráfico
    ax.set_title('Índice de Fertilidad NPK por Zona', fontsize=16, 
                 fontweight='bold', color='white', pad=20)
    ax.set_xlabel('Zona', fontsize=12, color='white')
    ax.set_ylabel('Índice NPK (0-1)', fontsize=12, color='white')
    ax.tick_params(colors='white')
    ax.grid(True, alpha=0.2, color='#475569')
    ax.legend(facecolor='#1e293b', edgecolor='white', labelcolor='white')
    
    # Agregar etiquetas de valor
    for bar, valor in zip(bars, valores):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{valor:.3f}', ha='center', va='bottom', 
                color='white', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    return fig

def crear_grafico_rendimiento_comparativo(gdf_analizado):
    """Crea gráfico comparativo de rendimiento actual vs proyectado"""
    if 'rendimiento_actual' not in gdf_analizado.columns:
        return None
    
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')
    
    # Preparar datos
    zonas = gdf_analizado['id_zona']
    rend_actual = gdf_analizado['rendimiento_actual']
    
    # Ancho de barras
    bar_width = 0.35
    index = np.arange(len(zonas))
    
    # Barras de rendimiento actual
    bars1 = ax.bar(index, rend_actual, bar_width,
                   label='Rendimiento Actual',
                   color='#3b82f6', alpha=0.8)
    
    # Si hay rendimiento proyectado, agregar barras
    if 'rendimiento_proyectado' in gdf_analizado.columns:
        rend_proy = gdf_analizado['rendimiento_proyectado']
        bars2 = ax.bar(index + bar_width, rend_proy, bar_width,
                       label='Rendimiento Proyectado',
                       color='#10b981', alpha=0.8)
    
    # Configurar gráfico
    ax.set_title('Comparativa de Rendimiento por Zona', fontsize=16, 
                 fontweight='bold', color='white', pad=20)
    ax.set_xlabel('Zona', fontsize=12, color='white')
    ax.set_ylabel('Rendimiento (ton/ha)', fontsize=12, color='white')
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(zonas.astype(str), color='white')
    ax.tick_params(colors='white')
    ax.grid(True, alpha=0.2, color='#475569')
    ax.legend(facecolor='#1e293b', edgecolor='white', labelcolor='white')
    
    # Agregar etiquetas de valor
    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{height:.1f}', ha='center', va='bottom', 
                color='white', fontsize=8)
    
    if 'rendimiento_proyectado' in gdf_analizado.columns:
        for bar in bars2:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                    f'{height:.1f}', ha='center', va='bottom', 
                    color='white', fontsize=8)
    
    plt.tight_layout()
    return fig

def crear_grafico_nutrientes(gdf_analizado):
    """Crea gráfico de barras agrupadas para N, P, K"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.patch.set_facecolor('#0f172a')
    
    nutrientes = ['nitrogeno_actual', 'fosforo_actual', 'potasio_actual']
    titulos = ['Nitrógeno (kg/ha)', 'Fósforo (kg/ha)', 'Potasio (kg/ha)']
    colores = ['#00ff00', '#0000ff', '#8A2BE2']
    
    for idx, (nutriente, titulo, color) in enumerate(zip(nutrientes, titulos, colores)):
        ax = axes[idx]
        ax.set_facecolor('#0f172a')
        
        if nutriente in gdf_analizado.columns:
            valores = gdf_analizado[nutriente]
            zonas = gdf_analizado['id_zona']
            
            bars = ax.bar(zonas.astype(str), valores, color=color, alpha=0.8)
            ax.set_title(titulo, fontsize=12, fontweight='bold', color='white')
            ax.set_xlabel('Zona', fontsize=10, color='white')
            ax.set_ylabel('kg/ha', fontsize=10, color='white')
            ax.tick_params(colors='white')
            ax.grid(True, alpha=0.2, color='#475569')
            
            # Agregar etiquetas de valor
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{height:.0f}', ha='center', va='bottom', 
                        color='white', fontsize=8)
        else:
            ax.text(0.5, 0.5, f'Datos de {titulo}\nno disponibles',
                    transform=ax.transAxes, ha='center', va='center',
                    fontsize=10, color='white')
    
    plt.tight_layout()
    return fig

def crear_grafico_textura_triangulo(gdf_analizado):
    """Crea gráfico del triángulo de texturas USDA"""
    try:
        from matplotlib.patches import Polygon as MplPolygon
        
        fig, ax = plt.subplots(figsize=(8, 8))
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#0f172a')
        
        # Definir el triángulo de texturas (coordenadas USDA)
        # Vertices: Arena (100,0,0), Limo (0,100,0), Arcilla (0,0,100)
        triangle = MplPolygon([[100, 0], [0, 100], [0, 0]], 
                              closed=True, fill=False, 
                              edgecolor='white', linewidth=2)
        ax.add_patch(triangle)
        
        # Agregar líneas de clasificación (simplificado)
        # Líneas de arena
        ax.plot([100, 0], [0, 100], 'white', alpha=0.3, linewidth=0.5)  # Diagonal
        
        # Agregar puntos de datos
        if all(col in gdf_analizado.columns for col in ['arena', 'limo', 'arcilla']):
            for idx, row in gdf_analizado.iterrows():
                arena = row['arena']
                limo = row['limo']
                arcilla = row['arcilla']
                
                # Convertir a coordenadas del triángulo
                x = arena + (limo / 2)
                y = limo * 0.866  # sin(60) = 0.866
                
                ax.plot(x, y, 'o', markersize=8, 
                       label=f"Zona {row['id_zona']}",
                       alpha=0.7)
                
                ax.annotate(f"Z{row['id_zona']}", (x, y),
                           xytext=(5, 5), textcoords="offset points",
                           fontsize=8, color='white')
        
        # Configurar gráfico
        ax.set_title('Triángulo de Texturas USDA', fontsize=14, 
                     fontweight='bold', color='white', pad=20)
        ax.set_xlabel('Arena →', fontsize=12, color='white')
        ax.set_ylabel('Arcilla ↗', fontsize=12, color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.1, color='#475569')
        
        # Ajustar límites
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 95)
        ax.set_aspect('equal')
        
        # Leyenda
        ax.legend(facecolor='#1e293b', edgecolor='white', labelcolor='white',
                 loc='upper right')
        
        plt.tight_layout()
        return fig
    except Exception as e:
        st.warning(f"No se pudo crear el triángulo de texturas: {str(e)}")
        return None
